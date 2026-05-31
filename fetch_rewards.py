import argparse
import json
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

PAGE_URL = "https://coinmaster-daily.com/"


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
        "Referer": "https://coinmaster-daily.com/",
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def normalize_reward_text(text):
    text = re.sub(r"\s+", " ", text).strip()

    match = re.search(r"(\d+)\s*(spins?|coins?)", text, re.IGNORECASE)

    if not match:
        return text

    amount = match.group(1)
    reward_type = match.group(2).lower()

    if reward_type.startswith("spin"):
        return f"{amount} 能量"

    if reward_type.startswith("coin"):
        return f"{amount} 金幣"

    return text


def parse_pub_datetime(text):
    text = re.sub(r"\s+", " ", text).strip()

    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def datetime_to_campaign_date(dt):
    if not dt:
        return ""

    return dt.strftime("%Y%m%d")


def datetime_to_display_date(dt):
    if not dt:
        return "Unknown"

    return dt.strftime("%m/%d/%Y")


def build_reward_url(href):
    return urljoin(PAGE_URL, href)


def build_mobile_reward_url(url):
    """
    coinmaster-daily.com 這個來源目前只有 /?gift=xxxx 這種領取入口。
    你前面已經把前端改成只顯示「領取」按鈕，所以 mobile_url 不會被使用。
    這裡保留欄位只是為了相容舊版 JSON 結構。
    """
    return url


def extract_gift_id(block, url):
    gift_id = block.get("data-id", "").strip()

    if gift_id:
        return gift_id

    match = re.search(r"[?&]gift=(\d+)", url)

    if match:
        return match.group(1)

    return ""


def extract_datetime_from_block(block):
    meta_items = block.select(".fs-meta .fs-clicks")

    for item in meta_items:
        text = item.get_text(" ", strip=True)
        dt = parse_pub_datetime(text)

        if dt:
            return dt

    return None


def scrape_rewards(html):
    soup = BeautifulSoup(html, "lxml")

    blocks = soup.select(".fs-wrapper .fs-block")

    records = []

    for block in blocks:
        bonus_el = block.select_one(".fs-bonus")
        link_el = block.select_one(".fs-collect a[href]")

        if not bonus_el or not link_el:
            continue

        reward_text = normalize_reward_text(
            bonus_el.get_text(" ", strip=True)
        )

        href = link_el.get("href", "").strip()

        if not href:
            continue

        reward_url = build_reward_url(href)
        gift_id = extract_gift_id(block, reward_url)

        if not gift_id:
            continue

        published_dt = extract_datetime_from_block(block)

        campaign_date = datetime_to_campaign_date(published_dt)
        display_date = datetime_to_display_date(published_dt)

        campaign = f"coinmaster_daily_gift_{gift_id}"

        records.append({
            "display_date": display_date,
            "campaign_date": campaign_date,
            "reward": reward_text,
            "campaign": campaign,
            "url": reward_url,
            "mobile_url": build_mobile_reward_url(reward_url),
            "source": PAGE_URL,
            "gift_id": gift_id,
            "published_at": (
                published_dt.strftime("%Y-%m-%d %H:%M:%S")
                if published_dt
                else ""
            ),
        })

    unique = {}

    for item in records:
        unique[item["campaign"]] = item

    result = list(unique.values())

    result.sort(
        key=lambda item: (
            item.get("campaign_date") or "",
            item.get("published_at") or "",
            item.get("gift_id") or "",
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
        description="Fetch Coin Master reward links from coinmaster-daily.com"
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

    print(f"Total rewards found: {len(records)}")

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
