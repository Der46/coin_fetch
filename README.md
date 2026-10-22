<p align="center">
  <img src="docs/icons/icon.svg" width="128" height="128" alt="Coin Rewards icon">
</p>

<h1 align="center">Coin Master Daily Rewards</h1>

<p align="center">
  每日自動抓取 Coin Master 免費獎勵連結（旋轉 / 能量 / 金幣），並透過 GitHub Pages 以可安裝的 PWA 網頁呈現。
</p>

<p align="center">
  <a href="https://der46.github.io/coin_fetch/"><b>👉 開啟網頁</b></a>
</p>

---

## 功能

- **自動更新**：GitHub Actions 每 2 小時抓取一次公開獎勵頁面，有新資料才重新產生網頁並提交。
- **一鍵領取**：每筆獎勵都有「領取」按鈕，直接開啟遊戲連結。
- **已領取紀錄**：可標記已領取、隱藏已領取項目，紀錄存在瀏覽器本機（localStorage）。
- **多語系**：中文、English、Tiếng Việt、日本語、한국어、ไทย、Bahasa Indonesia、Español、Português，並依語系顯示當地時間。
- **PWA**：可「加入主畫面」當成 App 使用，支援離線瀏覽（Service Worker 快取）。

## 安裝到手機桌面

- **Android / Chrome**：開啟網頁後點「安裝到手機桌面」按鈕，或從瀏覽器選單選「加到主畫面」。
- **iPhone / iPad**：用 Safari 開啟，點「分享」→「加入主畫面」。

## 專案結構

```
.
├── fetch_rewards.py              # 抓取並解析獎勵連結，輸出 JSON
├── generate_site.py              # 由 JSON 產生 docs/ 靜態網站（HTML、manifest、Service Worker）
├── requirements.txt
├── output/
│   └── coinmaster_rewards.json   # 抓取結果
├── docs/                         # GitHub Pages 網站根目錄
│   ├── index.html
│   ├── manifest.webmanifest
│   ├── sw.js
│   └── icons/
│       ├── icon.svg              # App icon 原始向量檔
│       ├── icon-192.png
│       ├── icon-512.png
│       └── apple-touch-icon.png  # 180×180，iOS 主畫面使用
└── .github/workflows/daily-fetch.yml
```

## 本機執行

需要 Python 3.12 以上（使用 `zoneinfo`）。

```bash
pip install -r requirements.txt
```

```bash
python fetch_rewards.py --output-dir output
```

```bash
python generate_site.py
```

產生的網站在 `docs/index.html`，可直接用瀏覽器開啟，或用任一靜態伺服器預覽：

```bash
python -m http.server 8000 --directory docs
```

### `fetch_rewards.py` 參數

| 參數 | 說明 |
|---|---|
| `--output-dir` | 輸出資料夾，預設 `output` |
| `--prefix` | 輸出檔名前綴，預設 `coinmaster_rewards` |
| `--date YYYYMMDD` | 只保留指定 campaign 日期的獎勵 |
| `--display-date MM/DD/YYYY` | 只保留指定顯示日期的獎勵 |
| `--today` | 使用台北時區的今天日期過濾 |
| `--allow-empty` | 抓不到資料時允許覆蓋成空 JSON（預設會保留舊資料） |

## App Icon

圖示原始檔為 [`docs/icons/icon.svg`](docs/icons/icon.svg)：紅色背景搭配金幣與閃電（代表免費旋轉 / 能量）。背景滿版、主體位於中央 80% 安全區內，因此也可作為 maskable icon。

修改 SVG 後，需要重新輸出 PNG（192、512、180 三種尺寸），例如：

```bash
npx @resvg/resvg-js-cli@2.6.2-beta.1 --fit-width 512 docs/icons/icon.svg docs/icons/icon-512.png
```

## 自動更新時間

Workflow 排程為 `0 */2 * * *`（UTC），也可在 Actions 頁面手動執行（`workflow_dispatch`）。

| **UTC 時間** | **台灣時間 UTC+8** |
|---|---|
| 00:00 | 08:00 |
| 02:00 | 10:00 |
| 04:00 | 12:00 |
| 06:00 | 14:00 |
| 08:00 | 16:00 |
| 10:00 | 18:00 |
| 12:00 | 20:00 |
| 14:00 | 22:00 |
| 16:00 | 00:00 |
| 18:00 | 02:00 |
| 20:00 | 04:00 |
| 22:00 | 06:00 |

> GitHub Actions 的排程在尖峰時段可能延遲數分鐘到數十分鐘。

## 免責聲明

本專案僅整理公開網頁上的獎勵連結，與 Moon Active 或 Coin Master 官方無關。連結有效性與實際領取狀態以遊戲內顯示為準。
