import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import defaultdict
import html

INPUT_JSON = "output/coinmaster_rewards.json"
OUTPUT_HTML = "docs/index.html"


def load_rewards():
    if not os.path.exists(INPUT_JSON):
        raise FileNotFoundError(f"找不到 {INPUT_JSON}")

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def group_by_display_date(records):
    grouped = defaultdict(list)

    for item in records:
        display_date = item.get("display_date", "Unknown")
        grouped[display_date].append(item)

    return grouped


def date_sort_key(date_text):
    try:
        return datetime.strptime(date_text, "%m/%d/%Y")
    except Exception:
        return datetime.min


def generate_html(records):
    now = datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d %H:%M:%S")

    grouped = group_by_display_date(records)
    sorted_dates = sorted(grouped.keys(), key=date_sort_key, reverse=True)

    total = len(records)

    rows_html = []

    for display_date in sorted_dates:
        items = grouped[display_date]

        rows_html.append(f"""
        <section class="date-section">
          <h2>{html.escape(display_date)}</h2>
          <div class="cards">
        """)

        for item in items:
            reward = html.escape(item.get("reward", ""))
            campaign = html.escape(item.get("campaign", ""))
            campaign_date = html.escape(item.get("campaign_date", ""))
            url = html.escape(item.get("url", ""))
            mobile_url = html.escape(item.get("mobile_url", ""))

            rows_html.append(f"""
            <article class="card reward-card" data-campaign="{campaign}">
              <div class="claimed-badge">已領取</div>

              <div class="reward">{reward}</div>
              <div class="meta">Campaign Date：{campaign_date}</div>
              <div class="campaign">{campaign}</div>

              <div class="actions">
                <a href="{url}" target="_blank" rel="noopener">網頁領取</a>
                <a href="{mobile_url}" target="_blank" rel="noopener">手機領取</a>
                <button type="button" class="claim-toggle" data-campaign="{campaign}">
                  標記已領
                </button>
              </div>
            </article>
            """)

        rows_html.append("""
          </div>
        </section>
        """)

    body = "\n".join(rows_html)

    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Coin Master 每日獎勵連結</title>

  <style>
    :root {{
      --bg: #f6f7fb;
      --card: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --primary: #ff4848;
      --primary-dark: #dc2626;
      --border: #e5e7eb;
      --success: #16a34a;
      --dark: #374151;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans TC", "Microsoft JhengHei", sans-serif;
      background: var(--bg);
      color: var(--text);
    }}

    header {{
      background: linear-gradient(135deg, #ff4848, #ff8a65);
      color: white;
      padding: 40px 20px;
      text-align: center;
    }}

    header h1 {{
      margin: 0 0 10px;
      font-size: 32px;
    }}

    header p {{
      margin: 6px 0;
      opacity: 0.95;
    }}

    main {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 24px 16px 60px;
    }}

    .summary {{
      background: white;
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 18px 20px;
      margin-top: -24px;
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);

      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: center;
      flex-wrap: wrap;
    }}

    .summary strong {{
      color: var(--primary);
    }}

    .summary-controls {{
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}

    .filter-control {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-weight: 600;
      cursor: pointer;
      user-select: none;
    }}

    .filter-control input {{
      width: 18px;
      height: 18px;
      cursor: pointer;
    }}

    .clear-claimed {{
      border: 1px solid var(--border);
      background: white;
      color: var(--muted);
      padding: 8px 12px;
      border-radius: 10px;
      font-weight: 600;
      cursor: pointer;
    }}

    .clear-claimed:hover {{
      color: var(--primary-dark);
      border-color: var(--primary);
    }}

    .date-section {{
      margin-top: 30px;
    }}

    .date-section h2 {{
      font-size: 24px;
      border-left: 6px solid var(--primary);
      padding-left: 12px;
      margin-bottom: 16px;
    }}

    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 16px;
    }}

    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
    }}

    .reward-card {{
      position: relative;
      transition:
        opacity 0.2s ease,
        transform 0.2s ease,
        background-color 0.2s ease,
        border-color 0.2s ease;
    }}

    .reward-card:hover {{
      transform: translateY(-2px);
    }}

    .reward-card.claimed {{
      background: #f3f4f6;
      opacity: 0.62;
      border-color: #d1d5db;
    }}

    .reward-card.claimed:hover {{
      transform: none;
    }}

    .reward {{
      display: inline-block;
      background: #fff1f1;
      color: var(--primary-dark);
      font-weight: 700;
      padding: 6px 12px;
      border-radius: 999px;
      margin-bottom: 12px;
    }}

    .reward-card.claimed .reward {{
      background: #e5e7eb;
      color: #6b7280;
    }}

    .meta {{
      color: var(--muted);
      font-size: 14px;
      margin-bottom: 8px;
    }}

    .campaign {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 13px;
      background: #f3f4f6;
      padding: 8px;
      border-radius: 8px;
      word-break: break-all;
      margin-bottom: 14px;
    }}

    .reward-card.claimed .campaign {{
      color: #6b7280;
      text-decoration: line-through;
    }}

    .claimed-badge {{
      display: none;
      position: absolute;
      top: 14px;
      right: 14px;
      background: var(--success);
      color: white;
      font-size: 13px;
      font-weight: 700;
      padding: 5px 10px;
      border-radius: 999px;
    }}

    .reward-card.claimed .claimed-badge {{
      display: inline-block;
    }}

    .actions {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }}

    .actions a {{
      text-decoration: none;
      background: var(--primary);
      color: white;
      padding: 9px 12px;
      border-radius: 10px;
      font-weight: 600;
      font-size: 14px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }}

    .actions a:hover {{
      background: var(--primary-dark);
    }}

    .claim-toggle {{
      border: none;
      cursor: pointer;
      background: var(--dark);
      color: white;
      padding: 9px 12px;
      border-radius: 10px;
      font-weight: 600;
      font-size: 14px;
    }}

    .claim-toggle:hover {{
      background: #111827;
    }}

    .reward-card.claimed .claim-toggle {{
      background: #9ca3af;
    }}

    .reward-card.claimed .claim-toggle:hover {{
      background: #6b7280;
    }}

    .empty-message {{
      display: none;
      margin-top: 24px;
      padding: 18px 20px;
      background: white;
      border: 1px dashed var(--border);
      border-radius: 16px;
      color: var(--muted);
      text-align: center;
      font-weight: 600;
    }}

    footer {{
      text-align: center;
      color: var(--muted);
      padding: 24px 12px;
      font-size: 14px;
    }}

    @media (max-width: 600px) {{
      header h1 {{
        font-size: 26px;
      }}

      .cards {{
        grid-template-columns: 1fr;
      }}

      .summary {{
        align-items: flex-start;
      }}

      .summary-controls {{
        width: 100%;
      }}

      .clear-claimed {{
        width: 100%;
      }}
    }}
  </style>
</head>

<body>
  <header>
    <h1>Coin Master 每日獎勵連結</h1>
    <p>每日自動更新免費能量 / 旋轉 / 金幣連結</p>
    <p>最後更新：{html.escape(now)} Asia/Taipei</p>
  </header>

  <main>
    <div class="summary">
      <div>
        目前共收錄 <strong>{total}</strong> 筆獎勵連結。
        資料來源為公開網頁整理，點擊前請自行確認連結狀態。
      </div>

      <div class="summary-controls">
        <label class="filter-control">
          <input type="checkbox" id="hideClaimed">
          隱藏已領取
        </label>

        <button type="button" id="clearClaimed" class="clear-claimed">
          清除已領取紀錄
        </button>
      </div>
    </div>

    <div id="emptyMessage" class="empty-message">
      目前沒有可顯示的獎勵。可能全部都已標記為已領取。
    </div>

    {body}
  </main>

    <footer>
      © {datetime.now(ZoneInfo("Asia/Taipei")).year} Coin999-長長久久隊伍. All rights reserved.
    </footer>

  <script>
    const STORAGE_PREFIX = "coinmaster_claimed_";
    const HIDE_CLAIMED_KEY = "coinmaster_hide_claimed";

    function getStorageKey(campaign) {{
      return STORAGE_PREFIX + campaign;
    }}

    function applyEmptyMessage() {{
      const cards = Array.from(document.querySelectorAll(".reward-card"));
      const emptyMessage = document.querySelector("#emptyMessage");

      if (!emptyMessage) return;

      const visibleCards = cards.filter(card => card.style.display !== "none");

      if (cards.length > 0 && visibleCards.length === 0) {{
        emptyMessage.style.display = "block";
      }} else {{
        emptyMessage.style.display = "none";
      }}
    }}

    function applyDateSectionVisibility() {{
      const sections = document.querySelectorAll(".date-section");

      sections.forEach(section => {{
        const cards = Array.from(section.querySelectorAll(".reward-card"));
        const visibleCards = cards.filter(card => card.style.display !== "none");

        if (cards.length > 0 && visibleCards.length === 0) {{
          section.style.display = "none";
        }} else {{
          section.style.display = "";
        }}
      }});
    }}

    function applyHideClaimedFilter() {{
      const checkbox = document.querySelector("#hideClaimed");
      const hideClaimed = checkbox && checkbox.checked;

      document.querySelectorAll(".reward-card").forEach(card => {{
        if (hideClaimed && card.classList.contains("claimed")) {{
          card.style.display = "none";
        }} else {{
          card.style.display = "";
        }}
      }});

      applyDateSectionVisibility();
      applyEmptyMessage();
    }}

    function applyClaimedState(card, claimed) {{
      const button = card.querySelector(".claim-toggle");

      if (claimed) {{
        card.classList.add("claimed");

        if (button) {{
          button.textContent = "取消標記";
        }}
      }} else {{
        card.classList.remove("claimed");

        if (button) {{
          button.textContent = "標記已領";
        }}
      }}

      applyHideClaimedFilter();
    }}

    function initClaimedRewards() {{
      const cards = document.querySelectorAll(".reward-card");

      cards.forEach(card => {{
        const campaign = card.dataset.campaign;

        if (!campaign) return;

        const claimed = localStorage.getItem(getStorageKey(campaign)) === "1";
        applyClaimedState(card, claimed);
      }});
    }}

    function bindClaimButtons() {{
      const buttons = document.querySelectorAll(".claim-toggle");

      buttons.forEach(button => {{
        button.addEventListener("click", () => {{
          const campaign = button.dataset.campaign;
          const card = button.closest(".reward-card");

          if (!campaign || !card) return;

          const key = getStorageKey(campaign);
          const claimed = localStorage.getItem(key) === "1";

          if (claimed) {{
            localStorage.removeItem(key);
            applyClaimedState(card, false);
          }} else {{
            localStorage.setItem(key, "1");
            applyClaimedState(card, true);
          }}
        }});
      }});
    }}

    function bindHideClaimedFilter() {{
      const checkbox = document.querySelector("#hideClaimed");

      if (!checkbox) return;

      const saved = localStorage.getItem(HIDE_CLAIMED_KEY) === "1";
      checkbox.checked = saved;

      checkbox.addEventListener("change", () => {{
        if (checkbox.checked) {{
          localStorage.setItem(HIDE_CLAIMED_KEY, "1");
        }} else {{
          localStorage.removeItem(HIDE_CLAIMED_KEY);
        }}

        applyHideClaimedFilter();
      }});

      applyHideClaimedFilter();
    }}

    function bindClearClaimed() {{
      const button = document.querySelector("#clearClaimed");

      if (!button) return;

      button.addEventListener("click", () => {{
        const confirmed = window.confirm("確定要清除所有已領取紀錄嗎？");

        if (!confirmed) return;

        const keysToRemove = [];

        for (let i = 0; i < localStorage.length; i++) {{
          const key = localStorage.key(i);

          if (key && key.startsWith(STORAGE_PREFIX)) {{
            keysToRemove.push(key);
          }}
        }}

        keysToRemove.forEach(key => localStorage.removeItem(key));

        document.querySelectorAll(".reward-card").forEach(card => {{
          applyClaimedState(card, false);
        }});

        applyHideClaimedFilter();
      }});
    }}

    document.addEventListener("DOMContentLoaded", () => {{
      initClaimedRewards();
      bindClaimButtons();
      bindHideClaimedFilter();
      bindClearClaimed();
    }});
  </script>
</body>
</html>
"""


def main():
    records = load_rewards()

    os.makedirs("docs", exist_ok=True)

    html_content = generate_html(records)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
