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
REWARD_URL_PREFIX = "https://rewards.coinmaster.com/rewards/rewards.html?c="


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
    只保留這種格式：
    https://rewards.coinmaster.com/rewards/rewards.html?c=xxxx
    """
    return url.startswith(REWARD_URL_PREFIX)


def extract_campaign_code(url):
    """
    從網址取得 c 參數。
    例如：
    https://rewards.coinmaster.com/rewards/rewards.html?c=pe_EMAILBNfzwg_20260531

    回傳：
    pe_EMAILBNfzwg_20260531
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


def scrape_rewards(html):
    soup = BeautifulSoup(html, "lxml")

    blocks = soup.select(".fs-wrapper .fs-block")

    records = []

    for block in blocks:
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

        campaign_code = extract_campaign_code(reward_url)

        if not campaign_code:
            continue

        campaign_date = extract_campaign_date_from_code(campaign_code)
        display_date = campaign_date_to_display_date(campaign_date)

        gift_id = button_el.get("data-id", "").strip()

        campaign = f"coinmaster_reward_{campaign_code}"

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
        help="依日期過濾，格式 YYYYMMDD，例如 20260531"
    )

    parser.add_argument(
        "--display-date",
        help="依顯示日期過濾，格式例如 05/31/2026"
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
        target_date = datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y%m%d")

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
