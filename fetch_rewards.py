import argparse
import json
import os
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

PAGE_URL = "https://mycoinmaster.com/"

# 舊版 Coin Master rewards 入口
REWARD_URL_BASE_HOST = "rewards.coinmaster.com"
REWARD_URL_BASE_PATH = "/rewards/rewards.html"

# 新版 MyCoinMaster 目前使用 AppsFlyer OneLink
ONELINK_REWARD_HOST = "coinmaster.onelink.me"
ONELINK_REWARD_PATH = "/2792196939"

DEFAULT_TIMEZONE = "Asia/Taipei"


def fetch_html(url, retries=3, timeout=30):
    """
    抓取 HTML，並在網路錯誤時自動重試。
    """
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
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    last_error = None

    for attempt in range(1, retries + 1):
        try:
            print(f"Fetch attempt {attempt}/{retries}: {url}")

            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                allow_redirects=True,
            )
            response.raise_for_status()

            print("Fetch successful.")
            print(f"Final URL: {response.url}")
            print(f"Status code: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', '')}")
            print(f"HTML length: {len(response.text)}")

            return response.text

        except requests.exceptions.RequestException as e:
            last_error = e

            print("")
            print(f"WARNING: Fetch attempt {attempt}/{retries} failed.")
            print(f"Reason: {e}")

            if attempt < retries:
                wait_seconds = attempt * 10
                print(f"Retrying in {wait_seconds} seconds...")
                print("")
                time.sleep(wait_seconds)

    raise last_error


def get_existing_output_json_path(output_dir, prefix, target_date=None, display_date=None):
    if target_date:
        output_prefix = f"{prefix}_{target_date}"
    elif display_date:
        safe_display_date = display_date.replace("/", "-")
        output_prefix = f"{prefix}_{safe_display_date}"
    else:
        output_prefix = prefix

    return os.path.join(output_dir, f"{output_prefix}.json")


def has_existing_output(output_dir, prefix, target_date=None, display_date=None):
    json_path = get_existing_output_json_path(
        output_dir=output_dir,
        prefix=prefix,
        target_date=target_date,
        display_date=display_date,
    )

    if not os.path.exists(json_path):
        return False

    if os.path.getsize(json_path) <= 0:
        return False

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return isinstance(data, list) and len(data) > 0

    except Exception:
        return False


def skip_fetch_with_existing_data(reason, output_dir, prefix, target_date=None, display_date=None):
    json_path = get_existing_output_json_path(
        output_dir=output_dir,
        prefix=prefix,
        target_date=target_date,
        display_date=display_date,
    )

    print("")
    print("=" * 70)
    print("WARNING: 無法抓取最新 Coin Master rewards。")
    print("=" * 70)
    print(f"原因：{reason}")
    print("")
    print(f"已找到既有資料：{json_path}")
    print("本次將沿用舊資料，workflow 會繼續執行。")
    print("=" * 70)
    print("")


def handle_fetch_failure(reason, output_dir, prefix, target_date=None, display_date=None):
    if has_existing_output(
        output_dir=output_dir,
        prefix=prefix,
        target_date=target_date,
        display_date=display_date,
    ):
        skip_fetch_with_existing_data(
            reason=reason,
            output_dir=output_dir,
            prefix=prefix,
            target_date=target_date,
            display_date=display_date,
        )
        return True

    expected_json_path = get_existing_output_json_path(
        output_dir=output_dir,
        prefix=prefix,
        target_date=target_date,
        display_date=display_date,
    )

    print("")
    print("=" * 70)
    print("ERROR: 無法抓取資料，而且沒有既有 output 可沿用。")
    print("=" * 70)
    print(f"原因：{reason}")
    print("")
    print(f"找不到可沿用的既有資料：{expected_json_path}")
    print("=" * 70)
    print("")

    return False


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
    raw_url = raw_url.replace("&amp;", "&").strip()
    return urljoin(PAGE_URL, raw_url)


def build_mobile_reward_url(url):
    return url


def extract_campaign_code(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    codes = query.get("c", [])

    if not codes:
        return ""

    return codes[0].strip()


def is_valid_campaign_code(campaign_code):
    if not campaign_code:
        return False

    return bool(re.match(r"^pe_[A-Za-z0-9]+_\d{8}$", campaign_code))


def is_valid_reward_url(url):
    """
    支援：
    - https://coinmaster.onelink.me/2792196939?...&c=pe_xxx_YYYYMMDD
    - https://rewards.coinmaster.com/rewards/rewards.html?c=pe_xxx_YYYYMMDD
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path

    if parsed.scheme not in ("http", "https"):
        return False

    campaign_code = extract_campaign_code(url)

    if host == ONELINK_REWARD_HOST and path == ONELINK_REWARD_PATH:
        return True

    if host == REWARD_URL_BASE_HOST and path == REWARD_URL_BASE_PATH:
        return True

    trusted_hosts = {
        ONELINK_REWARD_HOST,
        REWARD_URL_BASE_HOST,
    }

    if host in trusted_hosts and is_valid_campaign_code(campaign_code):
        return True

    return False


def extract_campaign_date_from_code(campaign_code):
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
    if campaign_code:
        return f"coinmaster_reward_{campaign_code}"

    if gift_id:
        return f"coinmaster_reward_id_{gift_id}"

    safe_url = re.sub(r"[^a-zA-Z0-9]+", "_", reward_url).strip("_")
    return f"coinmaster_reward_url_{safe_url}"


def find_section_for_block(block, page_date):
    """
    從目前 fs-block 往前找最近的 .fs-heading。
    這比依賴 wrapper.children 更穩。
    """
    heading = block.find_previous(class_="fs-heading")

    if not heading:
        return "", ""

    title = heading.get_text(" ", strip=True)
    section_date = parse_heading_date(title, page_date)

    return title, section_date


def extract_reward_text_from_block(block):
    bonus_el = block.select_one(".fs-bonus")

    if bonus_el:
        return normalize_reward_text(bonus_el.get_text(" ", strip=True))

    # fallback：從圖片 alt 抓，例如 75 free spins
    img = block.select_one("img[alt]")

    if img:
        return normalize_reward_text(img.get("alt", "").strip())

    return ""


def scrape_rewards(html):
    soup = BeautifulSoup(html, "lxml")

    page_date = extract_page_modified_date(soup)

    # Debug：確認 GitHub Actions 實際抓到什麼
    fs_wrapper_count = len(soup.select(".fs-wrapper"))
    fs_block_count = len(soup.select(".fs-block"))
    button_count = len(soup.select("button[data-url]"))

    print(f"Debug: .fs-wrapper count: {fs_wrapper_count}")
    print(f"Debug: .fs-block count: {fs_block_count}")
    print(f"Debug: button[data-url] count: {button_count}")
    print(f"Debug: page_date: {page_date}")

    # 關鍵修正：
    # 不再依賴 .fs-wrapper.children。
    # 直接掃全頁 button[data-url]，再往上找 .fs-block。
    buttons = soup.select("button[data-url]")

    records = []
    skipped_invalid_url = 0
    skipped_missing_data = 0

    for button_el in buttons:
        raw_url = button_el.get("data-url", "").strip()
        raw_url = raw_url.replace("&amp;", "&")

        if not raw_url:
            skipped_missing_data += 1
            continue

        reward_url = build_reward_url(raw_url)

        if not is_valid_reward_url(reward_url):
            skipped_invalid_url += 1
            continue

        block = button_el.find_parent(class_="fs-block")

        if not block:
            skipped_missing_data += 1
            continue

        reward_text = extract_reward_text_from_block(block)

        if not reward_text:
            skipped_missing_data += 1
            continue

        gift_id = button_el.get("data-id", "").strip()

        section_title, section_date = find_section_for_block(block, page_date)

        campaign_code = extract_campaign_code(reward_url)
        campaign_code_date = extract_campaign_date_from_code(campaign_code)

        # 優先用 URL campaign code 的日期
        campaign_date = campaign_code_date or section_date
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
            "section_title": section_title,
            "published_at": "",
        })

    unique = {}

    for item in records:
        unique[item["campaign"]] = item

    result = list(unique.values())

    result.sort(
        key=lambda item: (
            item.get("campaign_date") or "",
            int(item.get("gift_id") or 0) if str(item.get("gift_id") or "").isdigit() else 0,
            item.get("campaign_code") or "",
            item.get("url") or "",
        ),
        reverse=True
    )

    print(f"Debug: skipped missing data: {skipped_missing_data}")
    print(f"Debug: skipped invalid url: {skipped_invalid_url}")
    print(f"Debug: unique valid rewards: {len(result)}")

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


def cleanup_legacy_outputs(output_dir, output_prefix):
    legacy_paths = [
        os.path.join(output_dir, f"{output_prefix}.csv"),
        os.path.join(output_dir, f"{output_prefix}.txt"),
        os.path.join(output_dir, f"{output_prefix}_mobile.txt"),
    ]

    for path in legacy_paths:
        if os.path.exists(path):
            os.remove(path)
            print(f"Removed legacy output: {path}")


def save_outputs(records, output_dir, output_prefix):
    os.makedirs(output_dir, exist_ok=True)

    cleanup_legacy_outputs(output_dir, output_prefix)

    json_path = os.path.join(output_dir, f"{output_prefix}.json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    return json_path


def save_debug_html(html, output_dir):
    """
    儲存 GitHub Actions 實際抓到的 HTML。
    若之後又變空，可以直接看 output/debug_mycoinmaster.html。
    """
    os.makedirs(output_dir, exist_ok=True)

    debug_path = os.path.join(output_dir, "debug_mycoinmaster.html")

    with open(debug_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Debug HTML saved: {debug_path}")

    return debug_path


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Coin Master reward links from mycoinmaster.com"
    )

    parser.add_argument(
        "--date",
        help="依 campaign 日期過濾，格式 YYYYMMDD，例如 20260904"
    )

    parser.add_argument(
        "--display-date",
        help="依顯示日期過濾，格式例如 09/04/2026"
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

    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="允許在抓不到資料時覆蓋成空 JSON。預設不允許。"
    )

    args = parser.parse_args()

    target_date = args.date

    if args.today:
        target_date = datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).strftime("%Y%m%d")

    print(f"Fetching page: {PAGE_URL}")

    try:
        html = fetch_html(PAGE_URL)
    except requests.exceptions.RequestException as e:
        if handle_fetch_failure(
            reason=e,
            output_dir=args.output_dir,
            prefix=args.prefix,
            target_date=target_date,
            display_date=args.display_date,
        ):
            return

        raise
    except Exception as e:
        if handle_fetch_failure(
            reason=e,
            output_dir=args.output_dir,
            prefix=args.prefix,
            target_date=target_date,
            display_date=args.display_date,
        ):
            return

        raise

    # 永遠保存 debug HTML，方便排查 GitHub Actions 實際抓到的內容
    save_debug_html(html, args.output_dir)

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
        output_prefix = f"{args.prefix}_{target_date}"
    elif args.display_date:
        safe_display_date = args.display_date.replace("/", "-")
        output_prefix = f"{args.prefix}_{safe_display_date}"
    else:
        output_prefix = args.prefix

    # 重要修正：
    # 如果抓不到資料，預設不要覆蓋既有 JSON。
    # 否則一次抓取異常就會把 output/coinmaster_rewards.json 變成 []。
    if len(filtered) == 0 and not args.allow_empty:
        reason = "本次解析結果為 0 筆，為避免覆蓋既有資料，停止寫入空 JSON。"

        if has_existing_output(
            output_dir=args.output_dir,
            prefix=args.prefix,
            target_date=target_date,
            display_date=args.display_date,
        ):
            skip_fetch_with_existing_data(
                reason=reason,
                output_dir=args.output_dir,
                prefix=args.prefix,
                target_date=target_date,
                display_date=args.display_date,
            )
            return

        print("")
        print("=" * 70)
        print("ERROR: 抓取結果為 0，而且沒有既有非空 JSON 可沿用。")
        print("=" * 70)
        print("請檢查 output/debug_mycoinmaster.html 內容。")
        print("可能原因：")
        print("1. GitHub Actions 抓到的頁面不是正常 rewards HTML")
        print("2. 來源網站擋 GitHub Actions IP")
        print("3. 網頁結構再次變更")
        print("4. 來源網站目前沒有獎勵資料")
        print("=" * 70)
        print("")

        raise RuntimeError("No rewards found; refuse to overwrite JSON with empty list.")

    output_path = save_outputs(
        records=filtered,
        output_dir=args.output_dir,
        output_prefix=output_prefix
    )

    print("Output file:")
    print(output_path)


if __name__ == "__main__":
    main()
