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

PAGE_URL = "https://levvvel.com/zh-hant/coin-master-free-spins-code/"


def fetch_html(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,*/*;q=0.8"
        ),
    }

    response = requests.get(url, headers=headers, timeout=30)
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


def normalize_reward_text(text):
    text = re.sub(r"\s+", " ", text).strip()

    replacements = {
        "能量": "能量",
        "旋轉": "旋轉",
        "硬幣": "硬幣",
        "coins": "金幣",
        "spins": "旋轉",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def campaign_date_to_display_date(campaign_date):
    if not campaign_date:
        return "Unknown"

    try:
        dt = datetime.strptime(campaign_date, "%Y%m%d")
        return dt.strftime("%m/%d/%Y")
    except Exception:
        return "Unknown"


def extract_display_date_from_heading(heading_text, fallback_campaign_date=""):
    """
    LEVVVEL 的繁中標題可能長這樣：
    - 今天的 Coin Master 免費能量和金幣
    - Coin Master 免費能量和金幣 年五月30日
    - Coin Master 免費能量和金幣 年六月1日

    因為標題翻譯格式不一定穩定，所以最可靠來源仍是 campaign 裡面的 YYYYMMDD。
    這個函式只做輔助，最後仍會 fallback 到 campaign_date。
    """
    heading_text = re.sub(r"\s+", "", heading_text)

    now = datetime.now(ZoneInfo("Asia/Taipei"))

    if "今天" in heading_text:
        return now.strftime("%m/%d/%Y")

    month_map = {
        "一月": 1,
        "二月": 2,
        "三月": 3,
        "四月": 4,
        "五月": 5,
        "六月": 6,
        "七月": 7,
        "八月": 8,
        "九月": 9,
        "十月": 10,
        "十一月": 11,
        "十二月": 12,
    }

    for month_text, month_num in month_map.items():
        match = re.search(month_text + r"(\d{1,2})日", heading_text)
        if match:
            day = int(match.group(1))
            year = now.year

            try:
                return datetime(year, month_num, day).strftime("%m/%d/%Y")
            except Exception:
                break

    return campaign_date_to_display_date(fallback_campaign_date)


def is_reward_heading(text):
    text = re.sub(r"\s+", "", text)

    keywords = [
        "CoinMaster免費能量和金幣",
        "免費能量和金幣",
        "免費旋轉和硬幣",
        "今天的CoinMaster",
    ]

    return any(keyword in text for keyword in keywords)


def scrape_rewards(html):
    soup = BeautifulSoup(html, "lxml")

    content = soup.select_one(".entry-content")

    if not content:
        content = soup

    records = []
    current_heading = ""
    current_display_date = ""

    for element in content.find_all(["h2", "ol"]):
        if element.name == "h2":
            heading_text = element.get_text(" ", strip=True)

            if is_reward_heading(heading_text):
                current_heading = heading_text
            else:
                current_heading = ""

            continue

        if element.name != "ol":
            continue

        if not current_heading:
            continue

        links = element.select('a[href*="rewards.coinmaster.com"]')

        for a in links:
            reward_url = a.get("href", "").strip()
            reward_text = normalize_reward_text(a.get_text(" ", strip=True))

            if not reward_url:
                continue

            campaign, campaign_date = parse_campaign(reward_url)

            if not campaign:
                continue

            heading_display_date = extract_display_date_from_heading(
                current_heading,
                fallback_campaign_date=campaign_date
            )

            campaign_display_date = campaign_date_to_display_date(campaign_date)

            display_date = (
                campaign_display_date
                if campaign_display_date != "Unknown"
                else heading_display_date
            )

            records.append({
                "display_date": display_date,
                "campaign_date": campaign_date,
                "reward": reward_text,
                "campaign": campaign,
                "url": reward_url,
                "mobile_url": build_mobile_reward_url(campaign),
                "source": PAGE_URL,
                "source_heading": current_heading,
            })

    unique = {}

    for item in records:
        unique[item["campaign"]] = item

    result = list(unique.values())

    result.sort(
        key=lambda item: (
            item.get("campaign_date") or "",
            item.get("campaign") or "",
        ),
        reverse=True
    )

    return result


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
        description="Fetch Coin Master reward links from LEVVVEL"
    )

    parser.add_argument(
        "--date",
        help="依 campaign 日期過濾，格式 YYYYMMDD，例如 20260531"
    )

    parser.add_argument(
        "--display-date",
        help="依顯示日期過濾，格式例如 05/31/2026"
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
