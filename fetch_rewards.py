import argparse
import json
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urljoin, urlparse, parse_qs

import pandas as pd
import requests
from bs4 import BeautifulSoup

PAGE_URL = "https://mycoinmaster.com/"
REWARD_URL_BASE_HOST = "rewards.coinmaster.com"
REWARD_URL_BASE_PATH = "/rewards/rewards.html"
DEFAULT_TIMEZONE = "Asia/Taipei"


def fetch_html(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,*/*;q=0.8"
        ),
        "Referer": PAGE_URL,
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def normalize_reward_text(text):
    text = re.sub(r"\s+", " ", text).strip()

    match = re.search(
        r"(\d+)\s*(free\s*)?(spins?|coins?)",
        text,
        re.IGNORECASE
    )

    if not match:
        return text

    amount = match.group(1)
    reward_type = match.group(3).lower()

    if reward_type.startswith("spin"):
        return f"{amount} 能量"

    if reward_type.startswith("coin"):
        return f"{amount} 金幣"

    return text


def build_reward_url(raw_url):
    return urljoin(PAGE_URL, raw_url)


def build_mobile_reward_url(url):
    """
    mycoinmaster.com 的連結本身就是 rewards.coinmaster.com 官方領取入口。
    mobile_url 保留是為了相容舊版 JSON 結構。
    """
    return url


def is_valid_reward_url(url):
    """
    只要符合 rewards.coinmaster.com/rewards/rewards.html 的連結就抓。

    會抓：
    https://rewards.coinmaster.com/rewards/rewards.html
    https://rewards.coinmaster.com/rewards/rewards.html?c=pe_EMAILBNfzwg_20260531

    不會抓：
    https://coinmasterfreespins.online/
    https://rewards.coinmaster.com/other.html?c=xxx
    """
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return False

    if parsed.netloc.lower() != REWARD_URL_BASE_HOST:
        return False

    if parsed.path != REWARD_URL_BASE_PATH:
        return False

    return True


def extract_campaign_code(url):
    """
    從網址取得 c 參數。
    c 參數用於區分不同獎勵。

    例如：
    https://rewards.coinmaster.com/rewards/rewards.html?c=pe_EMAILBNfzwg_20260531

    回傳：
    pe_EMAILBNfzwg_20260531

    如果沒有 c，回傳空字串。
    """
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    codes = query.get("c", [])

    if not codes:
        return ""

    return codes[0].strip()


def extract_campaign_date_from_code(campaign_code):
    """
    從 campaign code 最後面抽出 YYYYMMDD。

    例如：
    pe_EMAILBNfzwg_20260531 -> 20260531
    pe_FCBGZQHsy_20260603 -> 20260603

    如果沒有日期格式，回傳空字串。
    """
    match = re.search(r"_(\d{8})$", campaign_code)

    if not match:
        return ""

    return match.group(1)


def campaign_date_to_display_date(campaign_date):
    if not campaign_date:
        return "Unknown"

    try:
        dt = datetime.strptime(campaign_date, "%Y%m%d")
        return dt.strftime("%m/%d/%Y")
    except Exception:
        return "Unknown"


def extract_page_modified_date(soup):
    """
    從頁面的 meta dateModified 取得網站更新日期。

    例如：
    <meta name="dateModified" content="2026-06-03 09:00:10">

    回傳：
    20260603

    如果沒有 dateModified，就用台北時區今天。
    """
    meta = soup.select_one('meta[name="dateModified"]')

    if meta:
        content = meta.get("content", "").strip()

        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(content, fmt)
                return dt.strftime("%Y%m%d")
            except Exception:
                pass

    return datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).strftime("%Y%m%d")


def get_base_year_from_date(date_text):
    if not date_text or len(date_text) < 4:
        return datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).year

    try:
        return int(date_text[:4])
    except Exception:
        return datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).year


def parse_heading_date(heading_text, page_date):
    """
    從 fs-heading 標題解析區塊日期。

    可處理：
    - Coin Master Free Spins Today
    - Coin Master Free Spins 02-June
    - Coin Master Free Spins 01-June
    - Coin Master Free Spins Bonus

    Today 使用頁面 dateModified。
    02-June / 01-June 使用 page_date 的年份。
    Bonus 無明確日期，回傳空字串。
    """
    heading_text = re.sub(r"\s+", " ", heading_text).strip()

    if re.search(r"\bToday\b", heading_text, re.IGNORECASE):
        return page_date

    match = re.search(
        r"(\d{1,2})\s*[- ]\s*"
        r"(January|February|March|April|May|June|July|August|September|October|November|December|"
        r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)",
        heading_text,
        re.IGNORECASE
    )

    if not match:
        return ""

    day = int(match.group(1))
    month_name = match.group(2).lower()

    month_map = {
        "january": 1,
        "jan": 1,
        "february": 2,
        "feb": 2,
        "march": 3,
        "mar": 3,
        "april": 4,
        "apr": 4,
        "may": 5,
        "june": 6,
        "jun": 6,
        "july": 7,
        "jul": 7,
        "august": 8,
        "aug": 8,
        "september": 9,
        "sep": 9,
        "sept": 9,
        "october": 10,
        "oct": 10,
        "november": 11,
        "nov": 11,
        "december": 12,
        "dec": 12,
    }

    month = month_map.get(month_name)

    if not month:
        return ""

    year = get_base_year_from_date(page_date)

    try:
        dt = datetime(year, month, day)
        return dt.strftime("%Y%m%d")
    except Exception:
        return ""


def build_campaign_id(campaign_code, reward_url, gift_id):
    """
    建立唯一 campaign id。

    優先順序：
    1. 有 c 參數：用 c 參數區分不同獎勵
    2. 沒有 c 參數但有 data-id：用 data-id
    3. 都沒有：用完整 URL
    """
    if campaign_code:
        return f"coinmaster_reward_{campaign_code}"

    if gift_id:
        return f"coinmaster_reward_id_{gift_id}"

    safe_url = re.sub(r"[^a-zA-Z0-9]+", "_", reward_url).strip("_")
    return f"coinmaster_reward_url_{safe_url}"


def scrape_rewards(html):
    soup = BeautifulSoup(html, "lxml")

    wrapper = soup.select_one(".fs-wrapper")

    if not wrapper:
        return []

    page_date = extract_page_modified_date(soup)

    records = []

    current_section_title = ""
    current_section_date = ""

    for child in wrapper.children:
        if not getattr(child, "name", None):
            continue

        classes = child.get("class", [])

        if "fs-heading" in classes:
            current_section_title = child.get_text(" ", strip=True)
            current_section_date = parse_heading_date(
                current_section_title,
                page_date
            )
            continue

        if "fs-block" not in classes:
            continue

        block = child

        bonus_el = block.select_one(".fs-bonus")
        button_el = block.select_one(".fs-collect button[data-url]")

        if not bonus_el or not button_el:
            continue

        reward_text = normalize_reward_text(
            bonus_el.get_text(" ", strip=True)
        )

        raw_url = button_el.get("data-url", "").strip()

        if not raw_url:
            continue

        reward_url = build_reward_url(raw_url)

        if not is_valid_reward_url(reward_url):
            continue

        gift_id = button_el.get("data-id", "").strip()

        campaign_code = extract_campaign_code(reward_url)
        campaign_code_date = extract_campaign_date_from_code(campaign_code)

        campaign_date = current_section_date
        display_date = campaign_date_to_display_date(campaign_date)

        campaign = build_campaign_id(
            campaign_code=campaign_code,
            reward_url=reward_url,
            gift_id=gift_id
        )

        records.append({
            "display_date": display_date,
            "campaign_date": campaign_date,
            "reward": reward_text,
            "campaign": campaign,
            "url": reward_url,
            "mobile_url": build_mobile_reward_url(reward_url),
            "source": PAGE_URL,
            "gift_id": gift_id,
            "campaign_code": campaign_code,
            "campaign_code_date": campaign_code_date,
            "section_title": current_section_title,
            "published_at": "",
        })

    unique = {}

    for item in records:
        unique[item["campaign"]] = item

    result = list(unique.values())

    result.sort(
        key=lambda item: (
            item.get("campaign_date") or "",
            item.get("gift_id") or "",
            item.get("campaign_code") or "",
            item.get("url") or "",
        ),
        reverse=True
    )

    return result


def filter_rewards(records, target_date=None, display_date=None):
    result = records

    if target_date:
        result = [
            item for item in result
            if item.get("campaign_date") == target_date
        ]

    if display_date:
        result = [
            item for item in result
            if item.get("display_date") == display_date
        ]

    return result


def save_outputs(records, output_dir, prefix):
    os.makedirs(output_dir, exist_ok=True)

    json_path = os.path.join(output_dir, f"{prefix}.json")
    csv_path = os.path.join(output_dir, f"{prefix}.csv")
    txt_path = os.path.join(output_dir, f"{prefix}.txt")
    mobile_txt_path = os.path.join(output_dir, f"{prefix}_mobile.txt")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    df = pd.DataFrame(records)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    with open(txt_path, "w", encoding="utf-8") as f:
        for item in records:
            f.write(item["url"] + "\n")

    with open(mobile_txt_path, "w", encoding="utf-8") as f:
        for item in records:
            f.write(item["mobile_url"] + "\n")

    return json_path, csv_path, txt_path, mobile_txt_path


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Coin Master reward links from mycoinmaster.com"
    )

    parser.add_argument(
        "--date",
        help="依網頁區塊日期過濾，格式 YYYYMMDD，例如 20260603"
    )

    parser.add_argument(
        "--display-date",
        help="依顯示日期過濾，格式例如 06/03/2026"
    )

    parser.add_argument(
        "--today",
        action="store_true",
        help="使用台北時區的今天日期作為過濾日期"
    )

    parser.add_argument(
        "--output-dir",
        default="output",
        help="輸出資料夾，預設 output"
    )

    parser.add_argument(
        "--prefix",
        default="coinmaster_rewards",
        help="輸出檔名前綴"
    )

    args = parser.parse_args()

    target_date = args.date

    if args.today:
        target_date = datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).strftime("%Y%m%d")

    print(f"Fetching page: {PAGE_URL}")

    html = fetch_html(PAGE_URL)
    records = scrape_rewards(html)

    print(f"Total valid rewards found: {len(records)}")

    filtered = filter_rewards(
        records,
        target_date=target_date,
        display_date=args.display_date
    )

    print(f"Filtered rewards: {len(filtered)}")

    for item in filtered:
        print(
            f'{item["display_date"]} | '
            f'{item["campaign_date"]} | '
            f'{item["reward"]} | '
            f'{item["section_title"]} | '
            f'{item["campaign"]} | '
            f'{item["url"]}'
        )

    if target_date:
        prefix = f"{args.prefix}_{target_date}"
    elif args.display_date:
        safe_display_date = args.display_date.replace("/", "-")
        prefix = f"{args.prefix}_{safe_display_date}"
    else:
        prefix = args.prefix

    output_paths = save_outputs(
        filtered,
        args.output_dir,
        prefix
    )

    print("Output files:")

    for path in output_paths:
        print(path)


if __name__ == "__main__":
    main()
