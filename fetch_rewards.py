import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import re
import json
import os
import argparse

PAGE_URL = "https://www.tech-girlz.com/2021/01/coin-master-free-spin.html"


def fetch_html(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    }

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    return response.text


def parse_campaign(url):
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    campaign = params.get("c", [""])[0]

    campaign_date = ""
    match = re.search(r"_(\d{8})$", campaign)
    if match:
        campaign_date = match.group(1)

    return campaign, campaign_date


def scrape_rewards(html):
    soup = BeautifulSoup(html, "lxml")

    table = soup.select_one("table.tablepress-id-266")

    if not table:
        raise RuntimeError("找不到 table.tablepress-id-266，可能網頁結構改了")

    records = []
    current_display_date = None

    for row in table.select("tbody tr"):
        cols = row.select("td")

        if not cols:
            continue

        if len(cols) >= 3:
            display_date = cols[0].get_text(strip=True)
            reward_text = cols[1].get_text(strip=True)
            link_col = cols[2]

            if display_date:
                current_display_date = display_date

        elif len(cols) == 2:
            reward_text = cols[0].get_text(strip=True)
            link_col = cols[1]

        else:
            continue

        a = link_col.select_one('a[href*="rewards.coinmaster.com"]')

        if not a:
            continue

        reward_url = a.get("href", "").strip()

        campaign, campaign_date = parse_campaign(reward_url)

        if not campaign:
            continue

        records.append({
            "display_date": current_display_date,
            "campaign_date": campaign_date,
            "reward": reward_text,
            "campaign": campaign,
            "url": reward_url,
            "source": PAGE_URL
        })

    unique = {}
    for item in records:
        unique[item["campaign"]] = item

    return list(unique.values())


def build_mobile_reward_url(campaign):
    return (
        "https://rewards.coinmaster.com/rewards/playonmobile.png"
        "?deep_link_sub1=promotions"
        f"&c={campaign}"
        "&pid=Reward%20link"
        "&deep_link_value=coinmaster%3A%2F%2F"
        "&af_xp=social"
        "&af_adset=no_source"
        "&af_force_deeplink=true"
    )


def add_mobile_urls(records):
    for item in records:
        item["mobile_url"] = build_mobile_reward_url(item["campaign"])
    return records


def filter_rewards(records, target_date=None, display_date=None):
    result = records

    if target_date:
        result = [
            item for item in result
            if item["campaign_date"] == target_date
        ]

    if display_date:
        result = [
            item for item in result
            if item["display_date"] == display_date
        ]

    return result


def save_outputs(records, output_dir, prefix):
    os.makedirs(output_dir, exist_ok=True)

    json_path = os.path.join(output_dir, f"{prefix}.json")
    csv_path = os.path.join(output_dir, f"{prefix}.csv")
    txt_path = os.path.join(output_dir, f"{prefix}.txt")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    df = pd.DataFrame(records)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    with open(txt_path, "w", encoding="utf-8") as f:
        for item in records:
            f.write(item["url"] + "\n")

    return json_path, csv_path, txt_path


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Coin Master reward links from tech-girlz.com"
    )

    parser.add_argument(
        "--date",
        help="依 campaign 日期過濾，格式 YYYYMMDD，例如 20260529"
    )

    parser.add_argument(
        "--display-date",
        help="依網頁表格日期過濾，格式例如 05/29/2026"
    )

    parser.add_argument(
        "--today",
        action="store_true",
        help="使用台北時區的今天日期作為 campaign 日期"
    )

    parser.add_argument(
        "--output-dir",
        default="/coin_fetch/output",
        help="輸出資料夾，預設 /coin_fetch/output"
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
    records = add_mobile_urls(records)

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
            f'{item["campaign"]}'
        )

    if target_date:
        prefix = f"{args.prefix}_{target_date}"
    elif args.display_date:
        safe_display_date = args.display_date.replace("/", "-")
        prefix = f"{args.prefix}_{safe_display_date}"
    else:
        prefix = args.prefix

    json_path, csv_path, txt_path = save_outputs(
        filtered,
        args.output_dir,
        prefix
    )

    print("Output files:")
    print(json_path)
    print(csv_path)
    print(txt_path)


if __name__ == "__main__":
    main()
