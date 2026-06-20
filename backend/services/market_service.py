import asyncio
import logging
import time
from collections import defaultdict
from datetime import datetime

import pandas as pd

from backend.core.event_bus import event_bus
from backend.models.market import IndexData

logger = logging.getLogger(__name__)

CN_INDICES = {
    "000001": "上证指数",
    "399001": "深证成指",
    "399006": "创业板指",
    "000680": "科创综指",
}

HK_INDICES = {
    "HSI": "恒生指数",
    "HSCEI": "国企指数",
    "HSTECH": "恒生科技指数",
}

GLOBAL_INDICES = {
    "^DJI": {"name": "道琼斯", "region": "美股"},
    "^IXIC": {"name": "纳斯达克", "region": "美股"},
    "^GSPC": {"name": "标普500", "region": "美股"},
    "^N225": {"name": "日经225", "region": "日股"},
    "^KS11": {"name": "KOSPI", "region": "韩股"},
    "^FTSE": {"name": "富时100", "region": "欧洲"},
}

_SINA_GLOBAL_MAP = {
    "^DJI": "gb_dji",
    "^IXIC": "gb_ixic",
    "^GSPC": "gb_inx",
}

_SINA_COMMODITY_MAP = {
    "GC=F": ("黄金", "美元/盎司", "元/克"),
    "CL=F": ("原油WTI", "美元/桶", ""),
    "SI=F": ("白银", "美元/盎司", "元/克"),
}

_AKSHARE_EM_NAMES = {
    "^N225": "日经225",
    "^KS11": "韩国KOSPI",
}

_kline_cache: dict[str, tuple[float, dict]] = {}
KLINE_CACHE_TTL = 300

_MARKET_HOURS_UTC = {
    "A股": (1, 30, 7, 0),
    "港股": (1, 30, 8, 0),
    "美股": (13, 30, 20, 0),
    "日股": (23, 30, 5, 0),
    "韩股": (23, 30, 5, 0),
    "欧洲": (7, 0, 15, 30),
    "大宗商品": (0, 0, 23, 59),
}


def _is_market_open(region: str, now_utc: datetime | None = None) -> bool:
    if now_utc is None:
        now_utc = datetime.utcnow()
    if now_utc.weekday() >= 5:
        return region == "大宗商品"
    hours = _MARKET_HOURS_UTC.get(region)
    if not hours:
        return False
    start_m = hours[0] * 60 + hours[1]
    end_m = hours[2] * 60 + hours[3]
    cur_m = now_utc.hour * 60 + now_utc.minute
    if start_m <= end_m:
        return start_m <= cur_m <= end_m
    return cur_m >= start_m or cur_m <= end_m


def _any_market_open(now_utc: datetime | None = None) -> bool:
    return any(_is_market_open(r, now_utc) for r in _MARKET_HOURS_UTC)


class MarketDataService:
    def __init__(self, settings=None):
        self._cache: dict[str, IndexData] = {}
        self._history: dict[str, list[float]] = defaultdict(list)
        self._settings = settings

    def get_cached(self) -> dict[str, list[IndexData]]:
        grouped: dict[str, list[IndexData]] = defaultdict(list)
        for data in self._cache.values():
            grouped[data.region].append(data)
        return dict(grouped)

    def get_index(self, symbol: str) -> IndexData | None:
        return self._cache.get(symbol)

    def get_market_status(self) -> dict:
        now = datetime.utcnow()
        return {
            "utc_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "any_open": _any_market_open(now),
            "markets": {r: _is_market_open(r, now) for r in _MARKET_HOURS_UTC},
        }

    @staticmethod
    def _generate_sparkline(price: float, change: float, points: int = 20) -> list[float]:
        import random
        if price == 0:
            return [price] * points
        prev = price - change
        result = []
        for i in range(points):
            t = i / (points - 1) if points > 1 else 1
            base = prev + (price - prev) * t
            noise = random.gauss(0, abs(change) * 0.15 + price * 0.0002)
            result.append(round(base + noise, 2))
        result[-1] = price
        return result

    # ── Main refresh ──────────────────────────────────────────────

    async def refresh_all(self) -> dict[str, list[IndexData]]:
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._fetch_all_sync)
            if result:
                await event_bus.publish("market_update", result)
            return result
        except Exception as e:
            logger.error("刷新市场数据失败: %s", e)
            return self.get_cached()

    def _fetch_all_sync(self) -> dict[str, list[IndexData]]:
        result: dict[str, list[IndexData]] = defaultdict(list)
        now = datetime.utcnow()

        self._fetch_cn(result, now)
        time.sleep(0.5)
        self._fetch_hk(result, now)
        time.sleep(0.5)
        self._fetch_global_sina(result, now)
        time.sleep(0.5)
        self._fetch_global_akshare(result, now)
        time.sleep(0.5)
        self._fetch_commodities(result, now)

        for indices in result.values():
            for idx in indices:
                self._cache[idx.symbol] = idx
        return dict(result)

    # ── A股 (新浪实时 + K线缩略图) ────────────────────────────────

    def _fetch_cn(self, result: dict, now: datetime):
        import requests as req
        prefix_map = {c: ("sh" if c.startswith("0000") or c.startswith("0006") else "sz") for c in CN_INDICES}
        codes = ",".join(f"{prefix_map[c]}{c}" for c in CN_INDICES)
        try:
            resp = req.get(f"https://hq.sinajs.cn/list={codes}",
                           headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
            resp.encoding = "gbk"
            for line in resp.text.strip().split("\n"):
                if '="' not in line:
                    continue
                raw_code = line.split("hq_str_")[1].split("=")[0]
                code = raw_code[2:]
                fields = line.split('="', 1)[1].rstrip('";').split(",")
                if len(fields) < 4:
                    continue
                name = CN_INDICES.get(code, fields[0])
                price = float(fields[3])
                prev_close = float(fields[2])
                change = price - prev_close
                change_pct = (change / prev_close * 100) if prev_close else 0

                sparkline = self._get_cn_sparkline(code, prefix_map[code])
                if not sparkline:
                    self._history[code].append(price)
                    sparkline = self._history[code][-20:] if len(self._history[code]) >= 5 \
                        else self._generate_sparkline(price, change)

                result["A股"].append(IndexData(
                    symbol=code, name=name, region="A股",
                    price=round(price, 2), change=round(change, 2),
                    change_percent=round(change_pct, 2),
                    sparkline=sparkline, updated_at=now,
                ))
                logger.info("A股 %s: %.2f (%.2f%%)", name, price, change_pct)
        except Exception as e:
            logger.error("A股获取失败: %s", e)

    def _get_cn_sparkline(self, code: str, prefix: str) -> list[float]:
        try:
            import requests as req
            url = (f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
                   f"CN_MarketData.getKLineData?symbol={prefix}{code}&scale=5&ma=no&datalen=20")
            resp = req.get(url, headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
            data = resp.json()
            if data:
                return [float(d["close"]) for d in data[-20:]]
        except Exception:
            pass
        return []

    # ── 港股 (腾讯) ──────────────────────────────────────────────

    def _fetch_hk(self, result: dict, now: datetime):
        import requests as req
        codes = ",".join(f"hk{c}" for c in HK_INDICES)
        try:
            resp = req.get(f"https://qt.gtimg.cn/q={codes}", timeout=10)
            data = resp.content.decode("gbk")
            code_list = list(HK_INDICES.keys())
            for i, line in enumerate(data.strip().split(";")):
                if '="' not in line:
                    continue
                parts = line.split('"')
                if len(parts) < 2:
                    continue
                fields = parts[1].split("~")
                if len(fields) < 45:
                    continue
                code = code_list[i] if i < len(code_list) else ""
                name = HK_INDICES.get(code, fields[1])
                price = float(fields[3])
                change = float(fields[31]) if len(fields) > 31 else 0
                change_pct = float(fields[32]) if len(fields) > 32 else 0

                self._history[code].append(price)
                sparkline = self._history[code][-20:] if len(self._history[code]) >= 5 \
                    else self._generate_sparkline(price, change)

                result["港股"].append(IndexData(
                    symbol=code, name=name, region="港股",
                    price=round(price, 2), change=round(change, 2),
                    change_percent=round(change_pct, 2),
                    sparkline=sparkline, updated_at=now,
                ))
                logger.info("港股 %s: %.2f (%.2f%%)", name, price, change_pct)
        except Exception as e:
            logger.error("港股获取失败: %s", e)

    # ── 美股 (新浪 gb_ 实时) ─────────────────────────────────────

    def _fetch_global_sina(self, result: dict, now: datetime):
        import requests as req
        codes = ",".join(_SINA_GLOBAL_MAP.values())
        try:
            resp = req.get(f"https://hq.sinajs.cn/list={codes}",
                           headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
            resp.encoding = "gbk"
            for line in resp.text.strip().split("\n"):
                if '="' not in line:
                    continue
                var_part, data_part = line.split('="', 1)
                sina_code = var_part.rsplit("_", 1)[0].split("_")[-1] + "_" + var_part.rsplit("_", 1)[-1]
                fields = data_part.rstrip('";').split(",")
                if len(fields) < 5 or not fields[1]:
                    continue

                yf_sym = None
                for ys, ss in _SINA_GLOBAL_MAP.items():
                    if ss == sina_code:
                        yf_sym = ys
                        break
                if not yf_sym:
                    continue

                info = GLOBAL_INDICES.get(yf_sym, {})
                name = info.get("name", fields[0])
                region = info.get("region", "其他")
                price = float(fields[1])
                change_pct = float(fields[2])
                change = float(fields[4]) if fields[4] else price * change_pct / 100

                self._history[yf_sym].append(price)
                sparkline = self._history[yf_sym][-20:] if len(self._history[yf_sym]) >= 5 \
                    else self._generate_sparkline(price, change)

                result[region].append(IndexData(
                    symbol=yf_sym, name=name, region=region,
                    price=round(price, 2), change=round(change, 2),
                    change_percent=round(change_pct, 2),
                    sparkline=sparkline, updated_at=now,
                ))
                logger.info("全球(新浪) %s: %.2f (%.2f%%)", name, price, change_pct)
        except Exception as e:
            logger.error("全球(新浪)获取失败: %s", e)

        # FTSE via int_ code (separate since format differs)
        try:
            resp = req.get("https://hq.sinajs.cn/list=int_ftse",
                           headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
            resp.encoding = "gbk"
            for line in resp.text.strip().split("\n"):
                if '="' not in line:
                    continue
                fields = line.split('="', 1)[1].rstrip('";').split(",")
                if len(fields) < 4 or not fields[1]:
                    continue
                price = float(fields[1])
                change = float(fields[2])
                change_pct = float(fields[3]) if fields[3] else 0
                self._history["^FTSE"].append(price)
                sparkline = self._history["^FTSE"][-20:] if len(self._history["^FTSE"]) >= 5 \
                    else self._generate_sparkline(price, change)
                result["欧洲"].append(IndexData(
                    symbol="^FTSE", name="富时100", region="欧洲",
                    price=round(price, 2), change=round(change, 2),
                    change_percent=round(change_pct, 2),
                    sparkline=sparkline, updated_at=now,
                ))
                logger.info("全球(新浪) 富时100: %.2f (%.2f%%)", price, change_pct)
        except Exception as e:
            logger.warning("富时100获取失败: %s", e)

    # ── 日韩 (AKShare 东方财富历史取最新值) ───────────────────────

    def _fetch_global_akshare(self, result: dict, now: datetime):
        existing = {idx.symbol for indices in result.values() for idx in indices}
        try:
            import akshare as ak
            for sym, em_name in _AKSHARE_EM_NAMES.items():
                if sym in existing:
                    continue
                try:
                    df = ak.index_global_hist_em(symbol=em_name)
                    if df is None or df.empty:
                        continue
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest
                    info = GLOBAL_INDICES.get(sym, {})
                    name = info.get("name", em_name)
                    region = info.get("region", "其他")

                    close_col = "最新价" if "最新价" in df.columns else ("收盘" if "收盘" in df.columns else "close")
                    open_col = "开盘" if "开盘" in df.columns else "open"
                    high_col = "最高" if "最高" in df.columns else "high"
                    low_col = "最低" if "最低" in df.columns else "low"
                    price = float(latest[close_col])
                    prev_close = float(prev[close_col])
                    change = price - prev_close
                    change_pct = (change / prev_close * 100) if prev_close else 0

                    hist_closes = [float(row[close_col]) for _, row in df.tail(20).iterrows()]
                    sparkline = hist_closes if len(hist_closes) >= 5 \
                        else self._generate_sparkline(price, change)

                    result[region].append(IndexData(
                        symbol=sym, name=name, region=region,
                        price=round(price, 2), change=round(change, 2),
                        change_percent=round(change_pct, 2),
                        sparkline=sparkline, updated_at=now,
                    ))
                    logger.info("全球(AK) %s: %.2f (%.2f%%)", name, price, change_pct)
                except Exception as e:
                    logger.warning("AKShare %s 获取失败: %s", em_name, e)
        except ImportError:
            logger.warning("akshare 未安装")

    # ── 大宗商品 (新浪期货) ───────────────────────────────────────

    def _fetch_commodities(self, result: dict, now: datetime):
        import requests as req
        usd_cny = self._fetch_usd_cny()
        # Build map: sina_code -> our_symbol  e.g. "hf_GC" -> "GC=F"
        sina_to_sym = {f"hf_{s.split('=')[0]}": s for s in _SINA_COMMODITY_MAP}
        codes = ",".join(sina_to_sym.keys())
        try:
            resp = req.get(f"https://hq.sinajs.cn/list={codes}",
                           headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
            resp.encoding = "gbk"
            for line in resp.text.strip().split("\n"):
                if '="' not in line:
                    continue
                var_part, data_part = line.split('="', 1)
                hf_code = "hf_" + var_part.rsplit("_", 1)[-1]
                fields = data_part.rstrip('";').split(",")
                if len(fields) < 8 or not fields[0]:
                    continue

                sym = sina_to_sym.get(hf_code)
                if not sym:
                    continue

                name, unit, alt_unit = _SINA_COMMODITY_MAP[sym]
                price = float(fields[0])
                prev_close = float(fields[7]) if fields[7] else price
                change = price - prev_close
                change_pct = (change / prev_close * 100) if prev_close else 0

                self._history[sym].append(price)
                sparkline = self._history[sym][-20:] if len(self._history[sym]) >= 5 \
                    else self._generate_sparkline(price, change)

                alt_price = None
                if alt_unit and sym in ("GC=F", "SI=F"):
                    alt_price = round(price * usd_cny / 31.1035, 2)

                result["大宗商品"].append(IndexData(
                    symbol=sym, name=name, region="大宗商品",
                    price=round(price, 2), change=round(change, 2),
                    change_percent=round(change_pct, 2),
                    sparkline=sparkline, updated_at=now,
                    unit=unit, alt_price=alt_price, alt_unit=alt_unit,
                ))
                logger.info("商品 %s: %.2f %s (中国:%.2f %s)", name, price, unit, alt_price or 0, alt_unit)
        except Exception as e:
            logger.error("大宗商品获取失败: %s", e)

    def _fetch_usd_cny(self) -> float:
        try:
            import requests as req
            resp = req.get("https://hq.sinajs.cn/list=fx_susdcny",
                           headers={"Referer": "https://finance.sina.com.cn"}, timeout=5)
            resp.encoding = "gbk"
            for line in resp.text.strip().split("\n"):
                if '="' in line:
                    fields = line.split('="')[1].rstrip('";').split(",")
                    if len(fields) > 1 and fields[1]:
                        return float(fields[1])
        except Exception:
            pass
        return 7.25

    # ── K线数据 ──────────────────────────────────────────────────

    def get_kline(self, symbol: str, period: str = "day") -> dict:
        cache_key = f"{symbol}:{period}"
        if cache_key in _kline_cache:
            ts, data = _kline_cache[cache_key]
            if time.time() - ts < KLINE_CACHE_TTL:
                return data
        try:
            if symbol in CN_INDICES:
                data = self._kline_cn(symbol, period)
            elif symbol in HK_INDICES:
                data = self._kline_hk(symbol, period)
            elif symbol in _AKSHARE_EM_NAMES:
                data = self._kline_akshare_em(symbol, period)
            else:
                data = self._kline_yf(symbol, period)
            _kline_cache[cache_key] = (time.time(), data)
            return data
        except Exception as e:
            logger.error("K线获取失败 %s/%s: %s", symbol, period, e)
            return {"dates": [], "opens": [], "highs": [], "lows": [],
                    "closes": [], "volumes": [], "name": symbol}

    def _kline_cn(self, symbol: str, period: str) -> dict:
        import requests as req
        name = CN_INDICES.get(symbol, symbol)
        prefix = "sh" if symbol.startswith("0000") or symbol.startswith("0006") else "sz"
        scale_map = {"minute": "5", "5day": "5", "week": "1200", "day": "240"}
        datalen_map = {"minute": "48", "5day": "240", "week": "52", "day": "120"}
        url = (f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
               f"CN_MarketData.getKLineData?symbol={prefix}{symbol}"
               f"&scale={scale_map.get(period, '240')}&ma=no&datalen={datalen_map.get(period, '120')}")
        resp = req.get(url, headers={"Referer": "https://finance.sina.com.cn"}, timeout=15)
        data = resp.json()
        if not data:
            return {"dates": [], "opens": [], "highs": [], "lows": [], "closes": [], "volumes": [], "name": name}
        return {
            "dates": [d["day"] for d in data],
            "opens": [float(d["open"]) for d in data],
            "highs": [float(d["high"]) for d in data],
            "lows": [float(d["low"]) for d in data],
            "closes": [float(d["close"]) for d in data],
            "volumes": [float(d["volume"]) for d in data],
            "name": name,
        }

    def _kline_hk(self, symbol: str, period: str) -> dict:
        name = HK_INDICES.get(symbol, symbol)
        yf_map = {"HSI": "^HSI", "HSCEI": "^HSCE", "HSTECH": "^HSTECH"}
        return self._kline_yf(yf_map.get(symbol, "^HSI"), period, name)

    def _kline_akshare_em(self, symbol: str, period: str) -> dict:
        import akshare as ak
        em_name = _AKSHARE_EM_NAMES.get(symbol, symbol)
        info = GLOBAL_INDICES.get(symbol, {})
        name = info.get("name", em_name)
        df = ak.index_global_hist_em(symbol=em_name)
        if period == "week":
            df = df.tail(52)
        else:
            df = df.tail(120)
        date_col = "日期" if "日期" in df.columns else "date"
        close_col = "最新价" if "最新价" in df.columns else ("收盘" if "收盘" in df.columns else "close")
        open_col = "开盘" if "开盘" in df.columns else "open"
        high_col = "最高" if "最高" in df.columns else "high"
        low_col = "最低" if "最低" in df.columns else "low"
        vol_col = "成交量" if "成交量" in df.columns else ("volume" if "volume" in df.columns else None)
        return {
            "dates": df[date_col].astype(str).tolist(),
            "opens": df[open_col].astype(float).tolist() if open_col in df.columns else [0] * len(df),
            "highs": df[high_col].astype(float).tolist() if high_col in df.columns else [0] * len(df),
            "lows": df[low_col].astype(float).tolist() if low_col in df.columns else [0] * len(df),
            "closes": df[close_col].astype(float).tolist(),
            "volumes": df[vol_col].astype(float).tolist() if vol_col else [0] * len(df),
            "name": name,
        }

    def _kline_yf(self, symbol: str, period: str, name: str = "") -> dict:
        import yfinance as yf
        if not name:
            info = GLOBAL_INDICES.get(symbol, {})
            name = info.get("name", symbol)
        kw = {"tickers": symbol, "progress": False}
        if period == "minute":
            kw.update(period="1d", interval="5m")
        elif period == "5day":
            kw.update(period="5d", interval="15m")
        elif period == "week":
            kw.update(period="1y", interval="1wk")
        else:
            kw.update(period="6mo", interval="1d")
        df = yf.download(**kw)
        if df is None or df.empty:
            return {"dates": [], "opens": [], "highs": [], "lows": [], "closes": [], "volumes": [], "name": name}
        if isinstance(df.columns, pd.MultiIndex) and symbol in df.columns.get_level_values(0):
            df = df[symbol]
        fmt = "%Y-%m-%d %H:%M" if period in ("minute", "5day") else "%Y-%m-%d"
        return {
            "dates": df.index.strftime(fmt).tolist(),
            "opens": df["Open"].round(2).tolist(),
            "highs": df["High"].round(2).tolist(),
            "lows": df["Low"].round(2).tolist(),
            "closes": df["Close"].round(2).tolist(),
            "volumes": df["Volume"].astype(int).tolist() if "Volume" in df.columns else [0] * len(df),
            "name": name,
        }
