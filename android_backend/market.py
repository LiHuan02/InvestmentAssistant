"""
Market data service using direct HTTP calls to Sina/Tencent finance APIs.
No external dependencies beyond 'requests'.
"""
import re
import time
import logging
import requests

logger = logging.getLogger(__name__)

# ── A股 (Sina Finance) ──────────────────────────────────────

CN_INDICES = {
    "sh000001": ("上证指数", "A股"),
    "sz399001": ("深证成指", "A股"),
    "sz399006": ("创业板指", "A股"),
    "sh000688": ("科创综指", "A股"),
}


def fetch_cn_indices() -> list[dict]:
    """Fetch A-share indices from Sina Finance."""
    codes = ",".join(CN_INDICES.keys())
    url = f"https://hq.sinajs.cn/list={codes}"
    try:
        resp = requests.get(url, headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
        resp.encoding = "gbk"
        results = []
        for line in resp.text.strip().split("\n"):
            if '="' not in line:
                continue
            raw_code = line.split("hq_str_")[1].split("=")[0]
            fields = line.split('="', 1)[1].rstrip('";').split(",")
            if len(fields) < 4:
                continue
            meta = CN_INDICES.get(raw_code)
            if not meta:
                continue
            name, region = meta
            price = float(fields[3])
            prev_close = float(fields[2]) if fields[2] else price
            change = round(price - prev_close, 2)
            change_pct = round((change / prev_close * 100), 2) if prev_close else 0
            results.append({
                "symbol": raw_code[2:],
                "name": name,
                "region": region,
                "price": round(price, 2),
                "change": change,
                "change_percent": change_pct,
                "sparkline": [],
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            })
        return results
    except Exception as e:
        logger.warning("A股数据获取失败: %s", e)
        return []


# ── 港股 (Tencent Finance) ────────────────────────────────

HK_INDICES = {
    "hkHSI": ("恒生指数", "港股"),
    "hkHSCEI": ("国企指数", "港股"),
    "hkHSTECH": ("恒生科技指数", "港股"),
}


def fetch_hk_indices() -> list[dict]:
    """Fetch HK indices from Tencent Finance."""
    codes = ",".join(HK_INDICES.keys())
    url = f"https://qt.gtimg.cn/q={codes}"
    try:
        resp = requests.get(url, timeout=10)
        resp.encoding = "gbk"
        results = []
        code_list = list(HK_INDICES.keys())
        for i, line in enumerate(resp.text.strip().split(";")):
            if '="' not in line:
                continue
            parts = line.split('"')
            if len(parts) < 2:
                continue
            fields = parts[1].split("~")
            if len(fields) < 45:
                continue
            raw_code = code_list[i] if i < len(code_list) else ""
            meta = HK_INDICES.get(raw_code)
            if not meta:
                continue
            name, region = meta
            price = float(fields[3])
            change = float(fields[31]) if len(fields) > 31 else 0
            change_pct = float(fields[32]) if len(fields) > 32 else 0
            results.append({
                "symbol": raw_code[2:],
                "name": name,
                "region": region,
                "price": round(price, 2),
                "change": round(change, 2),
                "change_percent": round(change_pct, 2),
                "sparkline": [],
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            })
        return results
    except Exception as e:
        logger.warning("港股数据获取失败: %s", e)
        return []


# ── 全球指数 (Sina Finance gb_) ──────────────────────────

GLOBAL_INDICES = {
    "gb_dji": ("^DJI", "道琼斯", "美股"),
    "gb_ixic": ("^IXIC", "纳斯达克", "美股"),
    "gb_inx": ("^GSPC", "标普500", "美股"),
    "int_nikkei": ("^N225", "日经225", "日股"),
    "int_ftse": ("^FTSE", "富时100", "欧洲"),
}


def fetch_global_indices() -> list[dict]:
    """Fetch global indices from Sina Finance."""
    codes = ",".join(GLOBAL_INDICES.keys())
    url = f"https://hq.sinajs.cn/list={codes}"
    try:
        resp = requests.get(url, headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
        resp.encoding = "gbk"
        results = []
        for line in resp.text.strip().split("\n"):
            if '="' not in line:
                continue
            raw_code = line.split("hq_str_")[1].split("=")[0]
            fields = line.split('="', 1)[1].rstrip('";').split(",")
            if len(fields) < 4 or not fields[1]:
                continue
            meta = GLOBAL_INDICES.get(raw_code)
            if not meta:
                continue
            symbol, name, region = meta
            price = float(fields[1])
            change = float(fields[2]) if len(fields) > 2 else 0
            change_pct = float(fields[3]) if len(fields) > 3 else 0
            results.append({
                "symbol": symbol,
                "name": name,
                "region": region,
                "price": round(price, 2),
                "change": round(change, 2),
                "change_percent": round(change_pct, 2),
                "sparkline": [],
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            })
        return results
    except Exception as e:
        logger.warning("全球指数获取失败: %s", e)
        return []


# ── 大宗商品 (Sina Finance hf_) ──────────────────────────

COMMODITY_INDICES = {
    "hf_GC": ("GC=F", "黄金", "大宗商品", "美元/盎司"),
    "hf_CL": ("CL=F", "原油WTI", "大宗商品", "美元/桶"),
    "hf_SI": ("SI=F", "白银", "大宗商品", "美元/盎司"),
}


def fetch_commodities() -> list[dict]:
    """Fetch commodity prices from Sina Finance."""
    codes = ",".join(COMMODITY_INDICES.keys())
    url = f"https://hq.sinajs.cn/list={codes}"
    try:
        resp = requests.get(url, headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
        resp.encoding = "gbk"
        results = []
        for line in resp.text.strip().split("\n"):
            if '="' not in line:
                continue
            raw_code = line.split("hq_str_")[1].split("=")[0]
            fields = line.split('="', 1)[1].rstrip('";').split(",")
            if len(fields) < 8 or not fields[0]:
                continue
            meta = COMMODITY_INDICES.get(raw_code)
            if not meta:
                continue
            symbol, name, region, unit = meta
            price = float(fields[0])
            prev_close = float(fields[7]) if fields[7] else price
            change = round(price - prev_close, 2)
            change_pct = round((change / prev_close * 100), 2) if prev_close else 0
            results.append({
                "symbol": symbol,
                "name": name,
                "region": region,
                "price": round(price, 2),
                "change": change,
                "change_percent": change_pct,
                "sparkline": [],
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "unit": unit,
            })
        return results
    except Exception as e:
        logger.warning("大宗商品数据获取失败: %s", e)
        return []


def fetch_all_indices() -> dict[str, list[dict]]:
    """Fetch all market indices grouped by region."""
    all_data = []
    all_data.extend(fetch_cn_indices())
    all_data.extend(fetch_hk_indices())
    all_data.extend(fetch_global_indices())
    all_data.extend(fetch_commodities())

    grouped: dict[str, list[dict]] = {}
    for item in all_data:
        region = item["region"]
        if region not in grouped:
            grouped[region] = []
        grouped[region].append(item)
    return grouped
