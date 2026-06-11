import asyncio
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta

import pandas as pd

from backend.core.event_bus import event_bus
from backend.models.market import IndexData

logger = logging.getLogger(__name__)

CN_INDICES = {
    "000001": "上证指数",
    "399001": "深证成指",
    "399006": "创业板指",
    "000688": "科创50",
}

HK_INDICES = {
    "HSI": "恒生指数",
    "HSCEI": "国企指数",
    "HSTECH": "恒生科技指数",
}

GLOBAL_INDICES = {
    "^GSPC": "标普500",
    "^IXIC": "纳斯达克",
    "^DJI": "道琼斯",
    "^N225": "日经225",
    "^KS11": "KOSPI",
    "^FTSE": "富时100",
    "^GDAXI": "德国DAX",
    "^FCHI": "法国CAC40",
    "GC=F": "黄金",
    "CL=F": "原油WTI",
    "SI=F": "白银",
}

REGION_MAP = {
    "000001": "A股", "399001": "A股", "399006": "A股", "000688": "A股",
    "HSI": "港股", "HSCEI": "港股", "HSTECH": "港股",
    "^GSPC": "美股", "^IXIC": "美股", "^DJI": "美股",
    "^N225": "日股", "^KS11": "韩股",
    "^FTSE": "欧洲", "^GDAXI": "欧洲", "^FCHI": "欧洲",
    "GC=F": "大宗商品", "CL=F": "大宗商品", "SI=F": "大宗商品",
}

COMMODITY_UNITS = {
    "GC=F": {"default": "美元/盎司", "alt": "元/克", "factor": 0.03215 * 7.25},
    "CL=F": {"default": "美元/桶", "alt": "元/升", "factor": 7.25 / 158.987},
    "SI=F": {"default": "美元/盎司", "alt": "元/克", "factor": 0.03215 * 7.25},
}

_SINA_GLOBAL_MAP = {
    "^DJI": "gb_dji", "^IXIC": "gb_ixic", "^GSPC": "gb_inx",
    "^N225": "int_nikkei", "^FTSE": "int_ftse",
    "^GDAXI": "int_gdaxi", "^FCHI": "int_fchi",
}

_SINA_COMMODITY_MAP = {
    "GC=F": "hf_GC",
    "CL=F": "hf_CL",
    "SI=F": "hf_SI",
}

_TWELVEDATA_MAP = {
    "^GSPC": "SPY",
    "^IXIC": "QQQ",
    "^DJI": "DIA",
    "GC=F": "GLD",
    "CL=F": "USO",
}

_kline_cache: dict[str, tuple[float, dict]] = {}
KLINE_CACHE_TTL = 300


class MarketDataService:
    def __init__(self, settings=None):
        self._cache: dict[str, IndexData] = {}
        self._history: dict[str, list[float]] = defaultdict(list)
        self._td_api_key = getattr(settings, "twelvedata_api", "") if settings else ""

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

    def get_cached(self) -> dict[str, list[IndexData]]:
        grouped: dict[str, list[IndexData]] = defaultdict(list)
        for data in self._cache.values():
            grouped[data.region].append(data)
        return dict(grouped)

    def get_index(self, symbol: str) -> IndexData | None:
        return self._cache.get(symbol)

    def _fetch_all_sync(self) -> dict[str, list[IndexData]]:
        result: dict[str, list[IndexData]] = defaultdict(list)
        now = datetime.utcnow()

        self._fetch_cn_indices(result, now)
        time.sleep(1)
        self._fetch_hk_indices(result, now)
        time.sleep(1)
        self._fetch_global_indices(result, now)

        for region, indices in result.items():
            for idx in indices:
                self._cache[idx.symbol] = idx

        return dict(result)

    def _seed_sparkline_sina(self, symbol: str, prefix: str) -> list[float]:
        try:
            import requests as req
            sina_sym = f"{prefix}{symbol}"
            url = (
                f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
                f"CN_MarketData.getKLineData?symbol={sina_sym}&scale=5&ma=no&datalen=20"
            )
            resp = req.get(url, headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
            data = resp.json()
            if data:
                return [float(d["close"]) for d in data[-20:]]
        except Exception:
            pass
        return []

    def _fetch_cn_indices(self, result: dict, now: datetime):
        self._fetch_cn_sina(result, now)

        if len(result.get("A股", [])) < len(CN_INDICES):
            try:
                import akshare as ak
                df = ak.stock_zh_index_spot_em()
                existing = {idx.symbol for idx in result.get("A股", [])}
                for code, name in CN_INDICES.items():
                    if code in existing:
                        continue
                    try:
                        row = df[df["代码"] == code]
                        if row.empty:
                            continue
                        row = row.iloc[0]
                        price = float(row["最新价"])
                        change = float(row.get("涨跌额", 0))
                        change_pct = float(row.get("涨跌幅", 0))
                        if code not in self._history or len(self._history[code]) < 5:
                            seed = self._seed_sparkline_sina(code, "sh" if code.startswith("0000") or code.startswith("0006") else "sz")
                            if seed:
                                self._history[code] = seed
                        self._history[code].append(price)
                        if len(self._history[code]) > 20:
                            self._history[code] = self._history[code][-20:]
                        idx = IndexData(
                            symbol=code, name=name, region="A股",
                            price=round(price, 2), change=round(change, 2),
                            change_percent=round(change_pct, 2),
                            sparkline=self._history[code].copy(),
                            updated_at=now,
                        )
                        result["A股"].append(idx)
                        logger.info("A股(AK补充) %s: %.2f (%.2f%%)", name, price, change_pct)
                    except Exception as e:
                        logger.warning("AKShare补充A股 %s 失败: %s", code, e)
            except Exception as e:
                logger.warning("AKShare A股补充不可用: %s", e)

    def _fetch_cn_sina(self, result: dict, now: datetime):
        try:
            import requests as req
            codes = ",".join(f"sh{c}" if c.startswith("0000") or c.startswith("0006")
                             else f"sz{c}" for c in CN_INDICES)
            url = f"https://hq.sinajs.cn/list={codes}"
            resp = req.get(url, headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
            resp.encoding = "gbk"
            for line in resp.text.strip().split("\n"):
                if '="' not in line:
                    continue
                var_part, data_part = line.split('="', 1)
                code_raw = var_part.split("_")[-1]
                code = code_raw[2:]
                fields = data_part.rstrip('";').split(",")
                if len(fields) < 4:
                    continue
                name = CN_INDICES.get(code, fields[0])
                price = float(fields[3])
                prev_close = float(fields[2])
                change = price - prev_close
                change_pct = (change / prev_close * 100) if prev_close else 0

                if code not in self._history or len(self._history[code]) < 5:
                    prefix = "sh" if code.startswith("0000") or code.startswith("0006") else "sz"
                    seed = self._seed_sparkline_sina(code, prefix)
                    if seed:
                        self._history[code] = seed

                self._history[code].append(price)
                if len(self._history[code]) > 20:
                    self._history[code] = self._history[code][-20:]
                idx = IndexData(
                    symbol=code, name=name, region="A股",
                    price=round(price, 2), change=round(change, 2),
                    change_percent=round(change_pct, 2),
                    sparkline=self._history[code].copy(),
                    updated_at=now,
                )
                result["A股"].append(idx)
                logger.info("A股(新浪) %s: %.2f", name, price)
        except Exception as e:
            logger.error("新浪备用API也失败: %s", e)

    def _fetch_hk_indices(self, result: dict, now: datetime):
        try:
            import akshare as ak
            df = ak.stock_hk_index_spot_em()
            for code, name in HK_INDICES.items():
                try:
                    row = df[df["代码"] == code]
                    if row.empty:
                        row = df[df["名称"].str.contains(name[:2], na=False)]
                    if row.empty:
                        continue
                    row = row.iloc[0]
                    price = float(row["最新价"])
                    change = float(row.get("涨跌额", 0))
                    change_pct = float(row.get("涨跌幅", 0))

                    self._history[code].append(price)
                    if len(self._history[code]) > 20:
                        self._history[code] = self._history[code][-20:]
                    sparkline = self._history[code].copy() if len(self._history[code]) >= 5 \
                        else self._generate_sparkline(price, change)

                    idx = IndexData(
                        symbol=code, name=name, region="港股",
                        price=round(price, 2), change=round(change, 2),
                        change_percent=round(change_pct, 2),
                        sparkline=sparkline,
                        updated_at=now,
                    )
                    result["港股"].append(idx)
                    logger.info("港股 %s: %.2f (%.2f%%)", name, price, change_pct)
                except Exception as e:
                    logger.warning("解析港股指数 %s 失败: %s", code, e)
        except Exception as e:
            logger.warning("AKShare 获取港股指数失败: %s, 尝试腾讯备用", e)
            self._fetch_hk_tencent(result, now)

    def _fetch_hk_tencent(self, result: dict, now: datetime):
        try:
            import requests as req
            codes = ",".join(f"hk{code}" for code in HK_INDICES)
            url = f"https://qt.gtimg.cn/q={codes}"
            resp = req.get(url, timeout=10)
            data = resp.content.decode("gbk")
            code_list = list(HK_INDICES.keys())
            for i, line in enumerate(data.strip().split(";")):
                if '="' not in line:
                    continue
                fields_match = line.split('"')
                if len(fields_match) < 2:
                    continue
                fields = fields_match[1].split("~")
                if len(fields) < 45:
                    continue
                code = code_list[i] if i < len(code_list) else ""
                name = HK_INDICES.get(code, fields[1])
                price = float(fields[3])
                change = float(fields[31]) if len(fields) > 31 else 0
                change_pct = float(fields[32]) if len(fields) > 32 else 0

                self._history[code].append(price)
                if len(self._history[code]) > 20:
                    self._history[code] = self._history[code][-20:]
                sparkline = self._history[code].copy() if len(self._history[code]) >= 5 \
                    else self._generate_sparkline(price, change)

                idx = IndexData(
                    symbol=code, name=name, region="港股",
                    price=round(price, 2), change=round(change, 2),
                    change_percent=round(change_pct, 2),
                    sparkline=sparkline,
                    updated_at=now,
                )
                result["港股"].append(idx)
                logger.info("港股(腾讯) %s: %.2f", name, price)
        except Exception as e:
            logger.error("腾讯备用API也失败: %s", e)

    def _fetch_global_indices(self, result: dict, now: datetime):
        self._fetch_global_sina(result, now)

        existing_syms = set()
        for indices in result.values():
            for idx in indices:
                existing_syms.add(idx.symbol)

        missing = [s for s in GLOBAL_INDICES if s not in _SINA_COMMODITY_MAP and s not in existing_syms]
        if missing:
            self._fetch_global_yfinance(result, now, missing)

        existing_commodities = {idx.symbol for idx in result.get("大宗商品", [])}
        missing_commodities = set(_SINA_COMMODITY_MAP.keys()) - existing_commodities
        if missing_commodities or not result.get("大宗商品"):
            self._fetch_commodities_sina(result, now)

    def _fetch_global_yfinance(self, result: dict, now: datetime, symbols: list[str]):
        import yfinance as yf
        batch_size = 4
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            try:
                df = yf.download(
                    tickers=batch, period="5d", interval="15m",
                    group_by="ticker", progress=False, threads=False,
                )
                if df is None or df.empty:
                    continue
                for sym in batch:
                    try:
                        name = GLOBAL_INDICES[sym]
                        region = REGION_MAP.get(sym, "其他")
                        if len(batch) == 1:
                            ticker_df = df
                        elif sym in df.columns.get_level_values(0):
                            ticker_df = df[sym]
                        else:
                            continue
                        prices = ticker_df["Close"].dropna()
                        if len(prices) < 2:
                            continue
                        current_price = float(prices.iloc[-1])
                        prev_price = float(prices.iloc[-2])
                        if current_price == 0 or prev_price == 0:
                            continue
                        change = current_price - prev_price
                        change_pct = (change / prev_price) * 100
                        if sym not in self._history or len(self._history[sym]) < 5:
                            self._history[sym] = [float(p) for p in prices.tail(20).tolist()]
                        self._history[sym].append(current_price)
                        if len(self._history[sym]) > 20:
                            self._history[sym] = self._history[sym][-20:]
                        idx = IndexData(
                            symbol=sym, name=name, region=region,
                            price=round(current_price, 2),
                            change=round(change, 2),
                            change_percent=round(change_pct, 2),
                            sparkline=self._history[sym].copy(),
                            updated_at=now,
                        )
                        result[region].append(idx)
                        logger.info("全球(yf) %s: %.2f (%.2f%%)", name, current_price, change_pct)
                    except Exception as e:
                        logger.warning("解析全球指数 %s 失败: %s", sym, e)
            except Exception as e:
                logger.warning("yfinance 批次 %s 失败: %s", batch, e)
            if i + batch_size < len(symbols):
                time.sleep(3)

    def _fetch_global_twelvedata(self, result: dict, now: datetime):
        import requests as req
        for our_sym, td_sym in _TWELVEDATA_MAP.items():
            try:
                url = f"https://api.twelvedata.com/quote?symbol={td_sym}&apikey={self._td_api_key}"
                resp = req.get(url, timeout=10)
                data = resp.json()
                if data.get("status") == "error":
                    logger.warning("TwelveData %s 错误: %s", td_sym, data.get("message", ""))
                    continue
                close = float(data.get("close", 0))
                prev_close = float(data.get("previous_close", 0))
                change = float(data.get("change", 0))
                change_pct = float(data.get("percent_change", 0))
                if close == 0:
                    continue

                name = GLOBAL_INDICES.get(our_sym, td_sym)
                region = REGION_MAP.get(our_sym, "其他")

                self._history[our_sym].append(close)
                if len(self._history[our_sym]) > 20:
                    self._history[our_sym] = self._history[our_sym][-20:]
                sparkline = self._history[our_sym].copy() if len(self._history[our_sym]) >= 5 \
                    else self._generate_sparkline(close, change)

                idx = IndexData(
                    symbol=our_sym, name=name, region=region,
                    price=round(close, 2), change=round(change, 2),
                    change_percent=round(change_pct, 2),
                    sparkline=sparkline, updated_at=now,
                )
                result[region].append(idx)
                logger.info("全球(TD/%s) %s: %.2f (%.2f%%)", td_sym, name, close, change_pct)
                time.sleep(0.5)
            except Exception as e:
                logger.warning("TwelveData %s 失败: %s", td_sym, e)

    def _fetch_global_sina(self, result: dict, now: datetime):
        try:
            import requests as req
            codes = ",".join(_SINA_GLOBAL_MAP.values())
            url = f"https://hq.sinajs.cn/list={codes}"
            resp = req.get(url, headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
            resp.encoding = "gbk"
            for line in resp.text.strip().split("\n"):
                if '="' not in line:
                    continue
                var_part, data_part = line.split('="', 1)
                sina_code = var_part.rsplit("_", 1)[0].split("_")[-1] + "_" + var_part.rsplit("_", 1)[-1]
                fields = data_part.rstrip('";').split(",")
                if len(fields) < 4 or not fields[1]:
                    continue
                yf_sym = None
                for yf_s, sina_s in _SINA_GLOBAL_MAP.items():
                    if sina_s == sina_code:
                        yf_sym = yf_s
                        break
                if not yf_sym:
                    continue
                name = GLOBAL_INDICES.get(yf_sym, fields[0])
                region = REGION_MAP.get(yf_sym, "其他")
                price = float(fields[1])
                if sina_code.startswith("gb_"):
                    change_pct = float(fields[2])
                    change = float(fields[4]) if len(fields) > 4 and fields[4] else price * change_pct / 100
                else:
                    change = float(fields[2])
                    change_pct = float(fields[3]) if fields[3] else 0

                self._history[yf_sym].append(price)
                if len(self._history[yf_sym]) > 20:
                    self._history[yf_sym] = self._history[yf_sym][-20:]
                sparkline = self._history[yf_sym].copy() if len(self._history[yf_sym]) >= 5 \
                    else self._generate_sparkline(price, change)

                idx = IndexData(
                    symbol=yf_sym, name=name, region=region,
                    price=round(price, 2), change=round(change, 2),
                    change_percent=round(change_pct, 2),
                    sparkline=sparkline,
                    updated_at=now,
                )
                result[region].append(idx)
                logger.info("全球(新浪) %s: %.2f (%.2f%%)", name, price, change_pct)
        except Exception as e:
            logger.error("新浪全球指数也失败: %s", e)

    _COMMODITY_UNITS = {
        "GC=F": ("美元/盎司", "元/克"),
        "CL=F": ("美元/桶", ""),
        "SI=F": ("美元/盎司", "元/克"),
    }

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

    def _fetch_commodities_sina(self, result: dict, now: datetime):
        existing = {idx.symbol for idx in result.get("大宗商品", [])}
        usd_cny = self._fetch_usd_cny()
        try:
            import requests as req
            codes = ",".join(_SINA_COMMODITY_MAP.values())
            url = f"https://hq.sinajs.cn/list={codes}"
            resp = req.get(url, headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
            resp.encoding = "gbk"
            for line in resp.text.strip().split("\n"):
                if '="' not in line:
                    continue
                var_part, data_part = line.split('="', 1)
                sina_code = "hf_" + var_part.rsplit("_", 1)[-1]
                fields = data_part.rstrip('";').split(",")
                if len(fields) < 8 or not fields[0]:
                    continue
                yf_sym = None
                for yf_s, sina_s in _SINA_COMMODITY_MAP.items():
                    if sina_s == sina_code:
                        yf_sym = yf_s
                        break
                if not yf_sym or yf_sym in existing:
                    continue
                name = GLOBAL_INDICES.get(yf_sym, fields[0])
                price = float(fields[0])
                prev_close = float(fields[7]) if fields[7] else price
                change = price - prev_close
                change_pct = (change / prev_close * 100) if prev_close else 0

                self._history[yf_sym].append(price)
                if len(self._history[yf_sym]) > 20:
                    self._history[yf_sym] = self._history[yf_sym][-20:]
                sparkline = self._history[yf_sym].copy() if len(self._history[yf_sym]) >= 5 \
                    else self._generate_sparkline(price, change)

                units = self._COMMODITY_UNITS.get(yf_sym, ("", ""))
                alt_price = None
                if units[1] and yf_sym in ("GC=F", "SI=F"):
                    alt_price = round(price * usd_cny / 31.1035, 2)

                idx = IndexData(
                    symbol=yf_sym, name=name, region="大宗商品",
                    price=round(price, 2), change=round(change, 2),
                    change_percent=round(change_pct, 2),
                    sparkline=sparkline, updated_at=now,
                    unit=units[0], alt_price=alt_price, alt_unit=units[1],
                )
                result["大宗商品"].append(idx)
                logger.info("大宗商品(新浪) %s: %.2f %s (中国:%.2f %s)",
                            name, price, units[0], alt_price or 0, units[1])
        except Exception as e:
            logger.error("新浪大宗商品备用也失败: %s", e)

    def get_kline(self, symbol: str, period: str = "day") -> dict:
        cache_key = f"{symbol}:{period}"
        if cache_key in _kline_cache:
            cached_time, cached_data = _kline_cache[cache_key]
            if time.time() - cached_time < KLINE_CACHE_TTL:
                return cached_data

        try:
            if symbol in CN_INDICES:
                data = self._get_cn_kline(symbol, period)
            elif symbol in HK_INDICES:
                data = self._get_hk_kline(symbol, period)
            else:
                data = self._get_global_kline(symbol, period)
            _kline_cache[cache_key] = (time.time(), data)
            return data
        except Exception as e:
            logger.error("获取K线数据失败 %s/%s: %s", symbol, period, e)
            return {"dates": [], "opens": [], "highs": [], "lows": [],
                    "closes": [], "volumes": [], "name": symbol}

    def _get_cn_kline(self, symbol: str, period: str) -> dict:
        name = CN_INDICES.get(symbol, symbol)
        try:
            return self._get_cn_kline_akshare(symbol, period, name)
        except Exception as e:
            logger.warning("AKShare K线失败, 尝试新浪备用: %s", e)
            return self._get_cn_kline_sina(symbol, period, name)

    def _get_cn_kline_akshare(self, symbol: str, period: str, name: str) -> dict:
        import akshare as ak
        if period == "minute":
            df = ak.index_zh_a_hist_min_em(symbol=symbol, period="5")
            df = df.tail(48)
        elif period == "5day":
            df = ak.index_zh_a_hist_min_em(symbol=symbol, period="5")
            df = df.tail(240)
        elif period == "week":
            end = datetime.now().strftime("%Y%m%d")
            start = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            df = ak.index_zh_a_hist(symbol=symbol, period="weekly", start_date=start, end_date=end)
        else:
            end = datetime.now().strftime("%Y%m%d")
            start = (datetime.now() - timedelta(days=180)).strftime("%Y%m%d")
            df = ak.index_zh_a_hist(symbol=symbol, period="daily", start_date=start, end_date=end)
            df = df.tail(120)
        dates = df["时间"].astype(str).tolist() if period in ("minute", "5day") else df["日期"].astype(str).tolist()
        return {
            "dates": dates,
            "opens": df["开盘"].astype(float).tolist(),
            "highs": df["最高"].astype(float).tolist(),
            "lows": df["最低"].astype(float).tolist(),
            "closes": df["收盘"].astype(float).tolist(),
            "volumes": df["成交量"].astype(float).tolist() if "成交量" in df.columns else [0] * len(dates),
            "name": name,
        }

    def _get_cn_kline_sina(self, symbol: str, period: str, name: str) -> dict:
        import requests as req
        prefix = "sh" if symbol.startswith("0000") or symbol.startswith("0006") else "sz"
        sina_symbol = f"{prefix}{symbol}"
        if period == "minute":
            scale, datalen = "5", "48"
        elif period == "5day":
            scale, datalen = "5", "240"
        elif period == "week":
            scale, datalen = "1200", "52"
        else:
            scale, datalen = "240", "120"
        url = (
            f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
            f"CN_MarketData.getKLineData?symbol={sina_symbol}&scale={scale}&ma=no&datalen={datalen}"
        )
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

    def _get_hk_kline(self, symbol: str, period: str) -> dict:
        name = HK_INDICES.get(symbol, symbol)
        if period in ("minute", "5day"):
            return self._get_global_kline_yf(
                {"HSI": "^HSI", "HSCEI": "^HSCE", "HSTECH": "^HSTECH"}.get(symbol, "^HSI"),
                period, name,
            )
        try:
            import akshare as ak
            df = ak.stock_hk_index_hist_em(symbol=symbol)
        except Exception:
            import akshare as ak
            df = ak.stock_hk_index_daily_sina(symbol=symbol)
        df = df.tail(52 if period == "week" else 120)
        date_col = "日期" if "日期" in df.columns else "date"
        close_col = "收盘" if "收盘" in df.columns else "close"
        open_col = "开盘" if "开盘" in df.columns else "open"
        high_col = "最高" if "最高" in df.columns else "high"
        low_col = "最低" if "最低" in df.columns else "low"
        vol_col = "成交量" if "成交量" in df.columns else ("volume" if "volume" in df.columns else None)
        return {
            "dates": df[date_col].astype(str).tolist(),
            "opens": df[open_col].astype(float).tolist(),
            "highs": df[high_col].astype(float).tolist(),
            "lows": df[low_col].astype(float).tolist(),
            "closes": df[close_col].astype(float).tolist(),
            "volumes": df[vol_col].astype(float).tolist() if vol_col else [0] * len(df),
            "name": name,
        }

    def _get_global_kline(self, symbol: str, period: str) -> dict:
        name = GLOBAL_INDICES.get(symbol, symbol)
        if self._td_api_key and symbol in _TWELVEDATA_MAP:
            try:
                return self._get_global_kline_td(symbol, period, name)
            except Exception as e:
                logger.warning("TwelveData K线失败 %s: %s, 尝试yfinance", symbol, e)
        return self._get_global_kline_yf(symbol, period, name)

    def _get_global_kline_td(self, symbol: str, period: str, name: str) -> dict:
        import requests as req
        td_sym = _TWELVEDATA_MAP[symbol]
        if period == "minute":
            interval, outputsize = "5min", 48
        elif period == "5day":
            interval, outputsize = "15min", 240
        elif period == "week":
            interval, outputsize = "1week", 52
        else:
            interval, outputsize = "1day", 120
        url = (
            f"https://api.twelvedata.com/time_series?symbol={td_sym}"
            f"&interval={interval}&outputsize={outputsize}&apikey={self._td_api_key}"
        )
        resp = req.get(url, timeout=15)
        data = resp.json()
        if "values" not in data:
            raise ValueError(data.get("message", "no data"))
        values = list(reversed(data["values"]))
        return {
            "dates": [v["datetime"] for v in values],
            "opens": [float(v["open"]) for v in values],
            "highs": [float(v["high"]) for v in values],
            "lows": [float(v["low"]) for v in values],
            "closes": [float(v["close"]) for v in values],
            "volumes": [int(float(v.get("volume", 0))) for v in values],
            "name": name,
        }

    def _get_global_kline_yf(self, symbol: str, period: str, name: str) -> dict:
        import yfinance as yf
        if period == "minute":
            kwargs = dict(tickers=symbol, period="1d", interval="5m", progress=False)
        elif period == "5day":
            kwargs = dict(tickers=symbol, period="5d", interval="15m", progress=False)
        elif period == "week":
            kwargs = dict(tickers=symbol, period="1y", interval="1wk", progress=False)
        else:
            kwargs = dict(tickers=symbol, period="6mo", interval="1d", progress=False)
        df = yf.download(**kwargs)
        if df is None or df.empty:
            return {"dates": [], "opens": [], "highs": [], "lows": [], "closes": [], "volumes": [], "name": name}
        if isinstance(df.columns, pd.MultiIndex):
            df = df[symbol] if symbol in df.columns.get_level_values(0) else df
        dates = df.index.strftime("%Y-%m-%d %H:%M").tolist() if period in ("minute", "5day") \
            else df.index.strftime("%Y-%m-%d").tolist()
        return {
            "dates": dates,
            "opens": df["Open"].round(2).tolist(),
            "highs": df["High"].round(2).tolist(),
            "lows": df["Low"].round(2).tolist(),
            "closes": df["Close"].round(2).tolist(),
            "volumes": df["Volume"].astype(int).tolist() if "Volume" in df.columns else [0] * len(df),
            "name": name,
        }
