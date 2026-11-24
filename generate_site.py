import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import defaultdict
import html
import re

INPUT_JSON = "output/coinmaster_rewards.json"

OUTPUT_HTML = "docs/index.html"
OUTPUT_MANIFEST = "docs/manifest.webmanifest"
OUTPUT_SW = "docs/sw.js"

DEFAULT_TIMEZONE = "Asia/Taipei"


LANGUAGE_CONFIG = {
    "zh-Hant": {
        "label": "中文",
        "timezone": "Asia/Taipei",
        "timezone_label": "台北時間",
        "locale": "zh-TW",
    },
    "en": {
        "label": "English",
        "timezone": "UTC",
        "timezone_label": "UTC",
        "locale": "en-US",
    },
    "vi": {
        "label": "Tiếng Việt",
        "timezone": "Asia/Ho_Chi_Minh",
        "timezone_label": "Giờ Việt Nam",
        "locale": "vi-VN",
    },
    "ja": {
        "label": "日本語",
        "timezone": "Asia/Tokyo",
        "timezone_label": "日本時間",
        "locale": "ja-JP",
    },
    "ko": {
        "label": "한국어",
        "timezone": "Asia/Seoul",
        "timezone_label": "한국 시간",
        "locale": "ko-KR",
    },
    "th": {
        "label": "ไทย",
        "timezone": "Asia/Bangkok",
        "timezone_label": "เวลาไทย",
        "locale": "th-TH",
    },
    "id": {
        "label": "Bahasa Indonesia",
        "timezone": "Asia/Jakarta",
        "timezone_label": "Waktu Indonesia Barat",
        "locale": "id-ID",
    },
    "es": {
        "label": "Español",
        "timezone": "Europe/Madrid",
        "timezone_label": "Hora de España",
        "locale": "es-ES",
    },
    "pt": {
        "label": "Português",
        "timezone": "Europe/Lisbon",
        "timezone_label": "Hora de Portugal",
        "locale": "pt-PT",
    },
}


I18N = {
    "zh-Hant": {
        "languageLabel": "語言",
        "siteTitle": "Coin Master 每日獎勵連結",
        "siteSubtitle": "每日自動更新免費能量 / 旋轉 / 金幣連結",
        "lastUpdated": "最後更新",
        "baseTimeNotice": "由大佬群CSL製作",
        "unitSpin": "能量",
        "unitCoin": "金幣",
        "summaryPrefix": "目前共收錄",
        "summarySuffix": "筆獎勵連結。",
        "summaryNotice": "資料來源為公開網頁整理，點擊前請自行確認連結狀態。",
        "hideClaimed": "隱藏已領取",
        "clearClaimed": "清除已領取紀錄",
        "emptyMessage": "目前沒有可顯示的獎勵。可能全部都已標記為已領取。",
        "claimedBadge": "已領取",
        "claim": "領取",
        "claimed": "已領取",
        "markClaimed": "標記已領",
        "unmarkClaimed": "取消標記",
        "clearConfirm": "確定要清除所有已領取紀錄嗎？",
        "cancel": "取消",
        "confirmClear": "清除",
        "close": "關閉",
        "installButton": "安裝到手機桌面",
        "iosHintTitle": "iPhone / iPad 安裝提示",
        "iosHintText": "請點選 Safari 分享按鈕，然後選擇「加入主畫面」。",
        "footerText": "本頁僅整理公開獎勵連結，實際領取狀態以遊戲內顯示為準。",
    },
    "en": {
        "languageLabel": "Language",
        "siteTitle": "Coin Master Daily Reward Links",
        "siteSubtitle": "Automatically updated daily free spins, energy, and coin links",
        "lastUpdated": "Last updated",
        "baseTimeNotice": "Made by 大佬群CSL",
        "unitSpin": "Spins",
        "unitCoin": "Coins",
        "summaryPrefix": "Currently collected",
        "summarySuffix": "reward links.",
        "summaryNotice": "Data is collected from public webpages. Please verify each link before opening.",
        "hideClaimed": "Hide claimed",
        "clearClaimed": "Clear claimed records",
        "emptyMessage": "No rewards are currently visible. They may all be marked as claimed.",
        "claimedBadge": "Claimed",
        "claim": "Claim",
        "claimed": "Claimed",
        "markClaimed": "Mark claimed",
        "unmarkClaimed": "Unmark",
        "clearConfirm": "Are you sure you want to clear all claimed records?",
        "cancel": "Cancel",
        "confirmClear": "Clear",
        "close": "Close",
        "installButton": "Install to Home Screen",
        "iosHintTitle": "iPhone / iPad install tip",
        "iosHintText": "Tap the Safari Share button, then choose “Add to Home Screen”.",
        "footerText": "This page only organizes public reward links. Actual claim status depends on the game.",
    },
    "vi": {
        "languageLabel": "Ngôn ngữ",
        "siteTitle": "Liên kết phần thưởng Coin Master hằng ngày",
        "siteSubtitle": "Tự động cập nhật liên kết vòng quay, năng lượng và xu miễn phí mỗi ngày",
        "lastUpdated": "Cập nhật lần cuối",
        "baseTimeNotice": "Được thực hiện bởi 大佬群CSL",
        "unitSpin": "Lượt quay",
        "unitCoin": "Xu",
        "summaryPrefix": "Hiện có",
        "summarySuffix": "liên kết phần thưởng.",
        "summaryNotice": "Dữ liệu được tổng hợp từ các trang công khai. Vui lòng kiểm tra liên kết trước khi mở.",
        "hideClaimed": "Ẩn đã nhận",
        "clearClaimed": "Xóa lịch sử đã nhận",
        "emptyMessage": "Hiện không có phần thưởng nào để hiển thị. Có thể tất cả đã được đánh dấu là đã nhận.",
        "claimedBadge": "Đã nhận",
        "claim": "Nhận",
        "claimed": "Đã nhận",
        "markClaimed": "Đánh dấu đã nhận",
        "unmarkClaimed": "Bỏ đánh dấu",
        "clearConfirm": "Bạn có chắc muốn xóa toàn bộ lịch sử đã nhận không?",
        "cancel": "Hủy",
        "confirmClear": "Xóa",
        "close": "Đóng",
        "installButton": "Cài vào màn hình chính",
        "iosHintTitle": "Gợi ý cài đặt trên iPhone / iPad",
        "iosHintText": "Nhấn nút Chia sẻ trong Safari, rồi chọn “Thêm vào Màn hình chính”.",
        "footerText": "Trang này chỉ tổng hợp liên kết quà công khai. Trạng thái nhận thực tế phụ thuộc vào trò chơi.",
    },
    "ja": {
        "languageLabel": "言語",
        "siteTitle": "Coin Master デイリー報酬リンク",
        "siteSubtitle": "無料スピン、エネルギー、コインリンクを毎日自動更新",
        "lastUpdated": "最終更新",
        "baseTimeNotice": "大佬群CSL 制作",
        "unitSpin": "スピン",
        "unitCoin": "コイン",
        "summaryPrefix": "現在",
        "summarySuffix": "件の報酬リンクがあります。",
        "summaryNotice": "データは公開ページから収集されています。リンクを開く前に状態をご確認ください。",
        "hideClaimed": "受取済みを非表示",
        "clearClaimed": "受取済み履歴を削除",
        "emptyMessage": "表示できる報酬がありません。すべて受取済みに設定されている可能性があります。",
        "claimedBadge": "受取済み",
        "claim": "受け取る",
        "claimed": "受取済み",
        "markClaimed": "受取済みにする",
        "unmarkClaimed": "解除",
        "clearConfirm": "すべての受取済み履歴を削除しますか？",
        "cancel": "キャンセル",
        "confirmClear": "削除する",
        "close": "閉じる",
        "installButton": "ホーム画面にインストール",
        "iosHintTitle": "iPhone / iPad インストール方法",
        "iosHintText": "Safari の共有ボタンを押して、「ホーム画面に追加」を選択してください。",
        "footerText": "このページは公開報酬リンクを整理したものです。実際の受取状況はゲーム内表示に従ってください。",
    },
    "ko": {
        "languageLabel": "언어",
        "siteTitle": "Coin Master 일일 보상 링크",
        "siteSubtitle": "무료 스핀, 에너지, 코인 링크를 매일 자동 업데이트합니다",
        "lastUpdated": "마지막 업데이트",
        "baseTimeNotice": "大佬群CSL 제작",
        "unitSpin": "스핀",
        "unitCoin": "코인",
        "summaryPrefix": "현재",
        "summarySuffix": "개의 보상 링크가 있습니다.",
        "summaryNotice": "데이터는 공개 웹페이지에서 수집되었습니다. 링크를 열기 전에 상태를 확인하세요.",
        "hideClaimed": "수령 완료 숨기기",
        "clearClaimed": "수령 기록 삭제",
        "emptyMessage": "현재 표시할 보상이 없습니다. 모두 수령 완료로 표시되었을 수 있습니다.",
        "claimedBadge": "수령 완료",
        "claim": "받기",
        "claimed": "수령 완료",
        "markClaimed": "수령 표시",
        "unmarkClaimed": "표시 해제",
        "clearConfirm": "모든 수령 기록을 삭제하시겠습니까?",
        "cancel": "취소",
        "confirmClear": "삭제",
        "close": "닫기",
        "installButton": "홈 화면에 설치",
        "iosHintTitle": "iPhone / iPad 설치 안내",
        "iosHintText": "Safari 공유 버튼을 누른 뒤 “홈 화면에 추가”를 선택하세요.",
        "footerText": "이 페이지는 공개 보상 링크를 정리한 것입니다. 실제 수령 상태는 게임 내 표시를 따릅니다.",
    },
    "th": {
        "languageLabel": "ภาษา",
        "siteTitle": "ลิงก์รางวัลรายวัน Coin Master",
        "siteSubtitle": "อัปเดตลิงก์ฟรีสปิน พลังงาน และเหรียญโดยอัตโนมัติทุกวัน",
        "lastUpdated": "อัปเดตล่าสุด",
        "baseTimeNotice": "จัดทำโดย 大佬群CSL",
        "unitSpin": "สปิน",
        "unitCoin": "เหรียญ",
        "summaryPrefix": "ขณะนี้มี",
        "summarySuffix": "ลิงก์รางวัล",
        "summaryNotice": "ข้อมูลรวบรวมจากหน้าเว็บสาธารณะ โปรดตรวจสอบลิงก์ก่อนเปิด",
        "hideClaimed": "ซ่อนที่รับแล้ว",
        "clearClaimed": "ล้างประวัติที่รับแล้ว",
        "emptyMessage": "ไม่มีรางวัลที่แสดงได้ในขณะนี้ อาจถูกทำเครื่องหมายว่ารับแล้วทั้งหมด",
        "claimedBadge": "รับแล้ว",
        "claim": "รับ",
        "claimed": "รับแล้ว",
        "markClaimed": "ทำเครื่องหมายว่ารับแล้ว",
        "unmarkClaimed": "ยกเลิกเครื่องหมาย",
        "clearConfirm": "คุณแน่ใจหรือไม่ว่าต้องการล้างประวัติที่รับแล้วทั้งหมด?",
        "cancel": "ยกเลิก",
        "confirmClear": "ล้าง",
        "close": "ปิด",
        "installButton": "ติดตั้งไปยังหน้าจอหลัก",
        "iosHintTitle": "วิธีติดตั้งบน iPhone / iPad",
        "iosHintText": "แตะปุ่มแชร์ใน Safari แล้วเลือก “เพิ่มไปยังหน้าจอโฮม”",
        "footerText": "หน้านี้รวบรวมเฉพาะลิงก์รางวัลสาธารณะ สถานะการรับจริงขึ้นอยู่กับในเกม",
    },
    "id": {
        "languageLabel": "Bahasa",
        "siteTitle": "Tautan Hadiah Harian Coin Master",
        "siteSubtitle": "Tautan spin gratis, energi, dan koin diperbarui otomatis setiap hari",
        "lastUpdated": "Terakhir diperbarui",
        "baseTimeNotice": "Dibuat oleh 大佬群CSL",
        "unitSpin": "Spin",
        "unitCoin": "Koin",
        "summaryPrefix": "Saat ini ada",
        "summarySuffix": "tautan hadiah.",
        "summaryNotice": "Data dikumpulkan dari halaman publik. Harap periksa tautan sebelum membukanya.",
        "hideClaimed": "Sembunyikan yang diklaim",
        "clearClaimed": "Hapus riwayat klaim",
        "emptyMessage": "Tidak ada hadiah yang dapat ditampilkan. Mungkin semuanya telah ditandai sebagai diklaim.",
        "claimedBadge": "Diklaim",
        "claim": "Klaim",
        "claimed": "Diklaim",
        "markClaimed": "Tandai diklaim",
        "unmarkClaimed": "Batalkan tanda",
        "clearConfirm": "Yakin ingin menghapus semua riwayat klaim?",
        "cancel": "Batal",
        "confirmClear": "Hapus",
        "close": "Tutup",
        "installButton": "Instal ke Layar Utama",
        "iosHintTitle": "Tips instal iPhone / iPad",
        "iosHintText": "Ketuk tombol Bagikan di Safari, lalu pilih “Tambahkan ke Layar Utama”.",
        "footerText": "Halaman ini hanya mengatur tautan hadiah publik. Status klaim sebenarnya bergantung pada game.",
    },
    "es": {
        "languageLabel": "Idioma",
        "siteTitle": "Enlaces diarios de recompensas de Coin Master",
        "siteSubtitle": "Actualización automática diaria de giros, energía y monedas gratis",
        "lastUpdated": "Última actualización",
        "baseTimeNotice": "Hecho por 大佬群CSL",
        "unitSpin": "Tiradas",
        "unitCoin": "Monedas",
        "summaryPrefix": "Hay",
        "summarySuffix": "enlaces de recompensa.",
        "summaryNotice": "Los datos se recopilan de páginas públicas. Verifica cada enlace antes de abrirlo.",
        "hideClaimed": "Ocultar reclamados",
        "clearClaimed": "Borrar registros reclamados",
        "emptyMessage": "No hay recompensas visibles. Puede que todas estén marcadas como reclamadas.",
        "claimedBadge": "Reclamado",
        "claim": "Reclamar",
        "claimed": "Reclamado",
        "markClaimed": "Marcar reclamado",
        "unmarkClaimed": "Desmarcar",
        "clearConfirm": "¿Seguro que quieres borrar todos los registros reclamados?",
        "cancel": "Cancelar",
        "confirmClear": "Borrar",
        "close": "Cerrar",
        "installButton": "Instalar en la pantalla de inicio",
        "iosHintTitle": "Consejo de instalación en iPhone / iPad",
        "iosHintText": "Toca el botón Compartir en Safari y elige “Añadir a pantalla de inicio”.",
        "footerText": "Esta página solo organiza enlaces públicos de recompensa. El estado real depende del juego.",
    },
    "pt": {
        "languageLabel": "Idioma",
        "siteTitle": "Links diários de recompensas Coin Master",
        "siteSubtitle": "Links de giros, energia e moedas grátis atualizados automaticamente todos os dias",
        "lastUpdated": "Última atualização",
        "baseTimeNotice": "Feito por 大佬群CSL",
        "unitSpin": "Giros",
        "unitCoin": "Moedas",
        "summaryPrefix": "Há",
        "summarySuffix": "links de recompensa.",
        "summaryNotice": "Os dados são coletados de páginas públicas. Verifique cada link antes de abrir.",
        "hideClaimed": "Ocultar resgatados",
        "clearClaimed": "Limpar registros resgatados",
        "emptyMessage": "Nenhuma recompensa está visível. Talvez todas estejam marcadas como resgatadas.",
        "claimedBadge": "Resgatado",
        "claim": "Resgatar",
        "claimed": "Resgatado",
        "markClaimed": "Marcar como resgatado",
        "unmarkClaimed": "Desmarcar",
        "clearConfirm": "Tem certeza de que deseja limpar todos os registros resgatados?",
        "cancel": "Cancelar",
        "confirmClear": "Limpar",
        "close": "Fechar",
        "installButton": "Instalar na tela inicial",
        "iosHintTitle": "Dica de instalação no iPhone / iPad",
        "iosHintText": "Toque no botão Compartilhar no Safari e escolha “Adicionar à Tela de Início”.",
        "footerText": "Esta página apenas organiza links públicos de recompensa. O status real depende do jogo.",
    },
}


def load_rewards():
    if not os.path.exists(INPUT_JSON):
        raise FileNotFoundError(f"找不到 {INPUT_JSON}")

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_docs_dir():
    os.makedirs("docs", exist_ok=True)
    os.makedirs("docs/icons", exist_ok=True)


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


def escape_json_for_script(data):
    return (
        json.dumps(data, ensure_ascii=False)
        .replace("</", "<\\/")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def build_local_update_times(base_time):
    """
    base_time 是 Asia/Taipei 的 datetime。
    這裡將同一個更新時間換算成各語言對應地區的當地時間。
    """
    result = {}

    for lang, config in LANGUAGE_CONFIG.items():
        timezone_name = config["timezone"]
        local_time = base_time.astimezone(ZoneInfo(timezone_name))

        result[lang] = {
            "time": local_time.strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": timezone_name,
            "timezone_label": config["timezone_label"],
            "locale": config["locale"],
        }

    return result


def parse_display_date(date_text):
    try:
        return datetime.strptime(date_text, "%m/%d/%Y")
    except (TypeError, ValueError):
        return None


# fetch_rewards.py 會把獎勵正規化成「<數量> 能量」或「<數量> 金幣」。
REWARD_UNITS = {
    "能量": ("unitSpin", "spin"),
    "金幣": ("unitCoin", "coin"),
}

BOLT_ICON = (
    '<svg class="reward-icon" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/></svg>'
)

COIN_ICON = (
    '<svg class="reward-icon" viewBox="0 0 24 24" aria-hidden="true">'
    '<circle cx="12" cy="12" r="9"/></svg>'
)


def build_reward_html(reward_text):
    """把「50 能量」拆成數字 + 可翻譯的單位；無法辨識時原樣顯示。"""
    match = re.fullmatch(r"\s*(\d+)\s*(\S+)\s*", reward_text or "")

    if match and match.group(2) in REWARD_UNITS:
        amount, unit = match.group(1), match.group(2)
        i18n_key, kind = REWARD_UNITS[unit]
        icon = BOLT_ICON if kind == "spin" else COIN_ICON

        return (
            f'<p class="reward reward-{kind}">{icon}'
            f'<span class="reward-amount">{amount}</span> '
            f'<span class="reward-unit" data-i18n="{i18n_key}">{unit}</span></p>'
        )

    return f'<p class="reward">{html.escape(reward_text or "")}</p>'


def build_rows_html(records):
    grouped = group_by_display_date(records)
    sorted_dates = sorted(grouped.keys(), key=date_sort_key, reverse=True)

    rows_html = []

    for display_date in sorted_dates:
        items = grouped[display_date]
        parsed = parse_display_date(display_date)
        datetime_attr = f' datetime="{parsed.strftime("%Y-%m-%d")}"' if parsed else ""

        rows_html.append(f"""
        <section class="date-section">
          <h2><time{datetime_attr}>{html.escape(display_date)}</time></h2>
          <div class="cards">
        """)

        for item in items:
            reward_html = build_reward_html(item.get("reward", ""))
            # campaign 只當作 localStorage 的領取紀錄 key，不顯示給使用者。
            campaign = html.escape(item.get("campaign", ""))
            url = html.escape(item.get("url", ""))

            rows_html.append(f"""
            <article class="card reward-card" data-campaign="{campaign}">
              <header class="card-head">
                {reward_html}
                <span class="claimed-badge" data-i18n="claimedBadge">已領取</span>
              </header>

              <footer class="actions">
                <a
                  href="{url}"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="btn btn-primary claim-link"
                >領取</a>

                <button type="button" class="btn btn-secondary claim-toggle">標記已領</button>
              </footer>
            </article>
            """)

        rows_html.append("""
          </div>
        </section>
        """)

    return "\n".join(rows_html)


def build_language_options():
    return "\n".join(
        f'          <option value="{html.escape(code)}" lang="{html.escape(code)}">'
        f'{html.escape(config["label"])}</option>'
        for code, config in LANGUAGE_CONFIG.items()
    )


# 使用 __TOKEN__ 佔位符而非 f-string，CSS / JS 的大括號不必再成對跳脫。
PAGE_TEMPLATE = r"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="color-scheme" content="light dark">

  <meta name="theme-color" content="__THEME_COLOR__">
  <meta name="description" content="Coin Master daily reward links with multilingual and PWA support.">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="Coin Rewards">

  <title>Coin Master 每日獎勵連結</title>

  <link rel="manifest" href="./manifest.webmanifest">
  <link rel="icon" type="image/svg+xml" href="./icons/icon.svg">
  <link rel="icon" type="image/png" sizes="192x192" href="./icons/icon-192.png">
  <link rel="apple-touch-icon" sizes="180x180" href="./icons/apple-touch-icon.png">

  <style>
    :root {
      color-scheme: light dark;

      --bg: #f6f7fb;
      --surface: #ffffff;
      --surface-muted: #f3f4f6;
      --text: #1f2937;
      --muted: #5b6472;
      --border: #e5e7eb;
      --shadow: 0 8px 24px rgb(15 23 42 / 0.06);
      --shadow-hover: 0 14px 32px rgb(15 23 42 / 0.12);

      /* 白字需 >= 4.5:1：#c62828 = 5.62、#15803d = 5.02 */
      --brand: #c62828;
      --brand-hover: #a51d1d;
      --brand-soft: #fdecec;
      --brand-soft-text: #a51d1d;
      --success: #15803d;
      --success-hover: #166534;
      --success-soft: #dcfce7;
      --success-soft-text: #166534;
      --neutral: #374151;
      --neutral-hover: #111827;
      --claimed-surface: #f1f3f5;
      --hint-bg: #fff7ed;
      --hint-border: #fed7aa;
      --hint-text: #9a3412;
      --focus: #1d4ed8;

      --radius-lg: 16px;
      --radius-md: 10px;
      --tap: 44px;

      accent-color: var(--brand);
    }

    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #0f1115;
        --surface: #191c22;
        --surface-muted: #22262e;
        --text: #e5e7eb;
        --muted: #a1a8b3;
        --border: #2c313a;
        --shadow: 0 8px 24px rgb(0 0 0 / 0.35);
        --shadow-hover: 0 14px 32px rgb(0 0 0 / 0.5);

        --brand-soft: #3a1d1d;
        --brand-soft-text: #fca5a5;
        --success-soft: #14301f;
        --success-soft-text: #86efac;
        --neutral: #3b4250;
        --neutral-hover: #4b5363;
        --claimed-surface: #15171c;
        --hint-bg: #2b1d12;
        --hint-border: #7c2d12;
        --hint-text: #fdba74;
        --focus: #93c5fd;

        accent-color: #f87171;
      }
    }

    *, *::before, *::after {
      box-sizing: border-box;
    }

    html {
      -webkit-text-size-adjust: 100%;
      text-size-adjust: 100%;
    }

    body {
      margin: 0;
      font-family:
        system-ui,
        -apple-system,
        "Segoe UI",
        "Noto Sans TC",
        "Noto Sans JP",
        "Noto Sans KR",
        "Noto Sans Thai",
        "Microsoft JhengHei",
        sans-serif;
      font-size: 16px;
      line-height: 1.5;
      background: var(--bg);
      color: var(--text);
    }

    h1, h2 {
      text-wrap: balance;
    }

    p {
      text-wrap: pretty;
    }

    :where(a, button, input, select, summary):focus-visible {
      outline: 3px solid var(--focus);
      outline-offset: 2px;
    }

    /* ---------- Header ---------- */

    .site-header {
      --focus: #ffffff;
      background: linear-gradient(135deg, #c62828, #bf360c);
      color: #ffffff;
      padding:
        max(24px, env(safe-area-inset-top))
        max(20px, env(safe-area-inset-right))
        44px
        max(20px, env(safe-area-inset-left));
      text-align: center;
    }

    .site-header h1 {
      margin: 0 0 8px;
      font-size: clamp(1.625rem, 5vw, 2.25rem);
      line-height: 1.2;
    }

    .site-header p {
      margin: 4px auto;
      max-width: 760px;
    }

    /* 作者徽章：深綠底、金框、金字＋皇冠 */
    .site-header .credit-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-top: 12px;
      padding: 6px 16px 6px 12px;
      border: 2px solid #c9a24a;
      border-radius: 8px;
      background: linear-gradient(180deg, #1e4a3b, #12322a);
      box-shadow:
        inset 0 0 0 1px rgb(0 0 0 / 0.45),
        inset 0 1px 0 rgb(255 255 255 / 0.12),
        0 3px 10px rgb(0 0 0 / 0.3);
      color: #f3cf6b;
      font-size: 1rem;
      font-weight: 800;
      letter-spacing: 0.04em;
      text-shadow: 0 1px 0 rgb(0 0 0 / 0.5);
    }

    .credit-badge svg {
      flex: none;
      width: 22px;
      height: 22px;
      fill: #f3c24c;
      filter: drop-shadow(0 1px 0 rgb(0 0 0 / 0.5));
    }

    .top-controls {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 20px;
    }

    .language-switcher {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgb(255 255 255 / 0.16);
      border: 1px solid rgb(255 255 255 / 0.35);
      border-radius: 999px;
      padding: 6px 6px 6px 14px;
      max-width: 100%;
    }

    .language-switcher label {
      font-size: 0.875rem;
      font-weight: 700;
      white-space: nowrap;
    }

    .language-switcher select {
      color-scheme: light;
      min-height: 36px;
      min-width: 160px;
      max-width: 100%;
      border: none;
      border-radius: 999px;
      padding: 6px 12px;
      font: inherit;
      font-weight: 700;
      color: #1f2937;
      background-color: #ffffff;
      cursor: pointer;
    }

    .install-button {
      min-height: var(--tap);
      border: 1px solid rgb(255 255 255 / 0.6);
      background: rgb(255 255 255 / 0.16);
      color: #ffffff;
      border-radius: 999px;
      padding: 8px 16px;
      font: inherit;
      font-weight: 800;
      cursor: pointer;
      transition: background-color 150ms ease-out;
    }

    .install-button:hover {
      background: rgb(255 255 255 / 0.28);
    }

    .install-button[hidden] {
      display: none;
    }

    @media (display-mode: standalone) {
      .install-button {
        display: none;
      }
    }

    /* ---------- Main ---------- */

    main {
      max-width: 1100px;
      margin: 0 auto;
      padding:
        0
        max(16px, env(safe-area-inset-right))
        48px
        max(16px, env(safe-area-inset-left));
    }

    .summary {
      position: relative;
      margin-top: -24px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 18px 20px;
      box-shadow: var(--shadow);
      display: grid;
      gap: 14px;
    }

    .summary p {
      margin: 0;
    }

    .summary strong {
      color: var(--brand-soft-text);
      font-variant-numeric: tabular-nums;
    }

    .summary-notice {
      color: var(--muted);
      font-size: 0.875rem;
    }

    .progress-row {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .progress-row progress {
      flex: 1;
      min-width: 0;
      height: 10px;
    }

    .progress-text {
      font-weight: 700;
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
    }

    .summary-controls {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }

    .filter-control {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      min-height: var(--tap);
      font-weight: 600;
      cursor: pointer;
      user-select: none;
    }

    .filter-control input {
      width: 20px;
      height: 20px;
      margin: 0;
      cursor: pointer;
    }

    .ios-hint {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      margin-top: 16px;
      padding: 14px 8px 14px 16px;
      border-radius: var(--radius-lg);
      background: var(--hint-bg);
      border: 1px solid var(--hint-border);
      color: var(--hint-text);
      font-weight: 600;
    }

    .ios-hint[hidden] {
      display: none;
    }

    .ios-hint > div {
      flex: 1;
    }

    .ios-hint strong {
      display: block;
      margin-bottom: 4px;
    }

    .icon-button {
      flex: none;
      display: inline-grid;
      place-items: center;
      width: var(--tap);
      height: var(--tap);
      margin: -8px 0;
      border: none;
      border-radius: 999px;
      background: transparent;
      color: inherit;
      cursor: pointer;
    }

    .icon-button:hover {
      background: rgb(127 127 127 / 0.15);
    }

    .date-section {
      margin-top: 32px;
    }

    .date-section[hidden] {
      display: none;
    }

    .date-section h2 {
      font-size: 1.375rem;
      border-left: 6px solid var(--brand);
      padding-left: 12px;
      margin: 0 0 16px;
    }

    .cards {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(min(100%, 240px), 1fr));
      gap: 16px;
    }

    /* ---------- Card ---------- */

    .card {
      display: flex;
      flex-direction: column;
      gap: 10px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 18px;
      box-shadow: var(--shadow);
      transition:
        translate 200ms ease-out,
        box-shadow 200ms ease-out,
        background-color 200ms ease-out,
        border-color 200ms ease-out;
    }

    .card[hidden] {
      display: none;
    }

    .card p {
      margin: 0;
    }

    @media (hover: hover) and (prefers-reduced-motion: no-preference) {
      .reward-card:not(.claimed):hover {
        translate: 0 -2px;
        box-shadow: var(--shadow-hover);
      }
    }

    .card-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 8px;
    }

    .reward {
      display: flex;
      align-items: center;
      gap: 6px;
      margin: 0;
      color: var(--brand-soft-text);
      font-weight: 800;
      line-height: 1.1;
    }

    .reward-icon {
      flex: none;
      width: 36px;
      height: 36px;
      padding: 7px;
      border-radius: 999px;
      background: var(--brand-soft);
      fill: currentColor;
    }

    .reward-amount {
      font-size: 2rem;
      font-variant-numeric: tabular-nums;
      letter-spacing: -0.01em;
    }

    .reward-unit {
      font-size: 1rem;
      color: var(--text);
    }

    .claimed-badge {
      display: none;
      flex: none;
      background: var(--success);
      color: #ffffff;
      font-size: 0.8125rem;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 999px;
    }

    .actions {
      display: flex;
      gap: 8px;
      margin-top: auto;
      padding-top: 4px;
    }

    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: var(--tap);
      padding: 8px 14px;
      border: none;
      border-radius: var(--radius-md);
      font: inherit;
      font-size: 0.9375rem;
      font-weight: 700;
      text-decoration: none;
      color: #ffffff;
      cursor: pointer;
      transition:
        background-color 150ms ease-out,
        color 150ms ease-out,
        border-color 150ms ease-out,
        scale 150ms ease-out;
    }

    @media (prefers-reduced-motion: no-preference) {
      .btn:active {
        scale: 0.97;
      }
    }

    .btn-primary {
      flex: 1;
      background: var(--brand);
    }

    .btn-primary:hover,
    .btn-danger:hover {
      background: var(--brand-hover);
    }

    .btn-danger {
      background: var(--brand);
    }

    .btn-secondary {
      background: var(--neutral);
    }

    .btn-secondary:hover {
      background: var(--neutral-hover);
    }

    .btn-ghost {
      background: transparent;
      color: var(--muted);
      border: 1px solid var(--border);
    }

    .btn-ghost:hover {
      color: var(--brand-soft-text);
      border-color: currentColor;
    }

    /* Claimed state */

    .reward-card.claimed {
      background: var(--claimed-surface);
      box-shadow: none;
    }

    .reward-card.claimed .reward {
      color: var(--success-soft-text);
    }

    .reward-card.claimed .reward-icon {
      background: var(--success-soft);
    }

    .reward-card.claimed .reward-unit {
      color: var(--muted);
    }

    .reward-card.claimed .claimed-badge {
      display: inline-block;
    }

    .reward-card.claimed .claim-link {
      background: var(--success);
    }

    .reward-card.claimed .claim-link:hover {
      background: var(--success-hover);
    }

    .empty-message {
      margin-top: 24px;
      padding: 18px 20px;
      background: var(--surface);
      border: 1px dashed var(--border);
      border-radius: var(--radius-lg);
      color: var(--muted);
      text-align: center;
      font-weight: 600;
    }

    .empty-message[hidden] {
      display: none;
    }

    /* ---------- Confirm dialog ---------- */

    dialog {
      width: min(100% - 32px, 420px);
      padding: 24px;
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      background: var(--surface);
      color: var(--text);
      box-shadow: 0 24px 60px rgb(0 0 0 / 0.3);
    }

    dialog:modal {
      overscroll-behavior: contain;
    }

    dialog::backdrop {
      background: rgb(15 23 42 / 0.55);
      overflow: hidden;
      overscroll-behavior: contain;
    }

    dialog h1 {
      margin: 0 0 20px;
      font-size: 1.125rem;
      line-height: 1.4;
    }

    .dialog-actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
    }

    @media (prefers-reduced-motion: no-preference) {
      dialog[open] {
        animation: dialog-in 200ms ease-out;
      }
    }

    @keyframes dialog-in {
      from {
        opacity: 0;
        scale: 0.96;
      }
    }

    /* ---------- Footer ---------- */

    .site-footer {
      text-align: center;
      color: var(--muted);
      padding: 24px 16px max(24px, env(safe-area-inset-bottom));
      font-size: 0.875rem;
    }

    .site-footer p {
      margin: 0 0 4px;
    }

    @media (max-width: 720px) {
      .language-switcher {
        width: 100%;
        justify-content: center;
        border-radius: 18px;
      }

      .language-switcher select {
        flex: 1;
        min-width: 0;
        max-width: 320px;
      }

      .install-button {
        width: 100%;
      }

      .summary-controls .btn {
        width: 100%;
      }
    }
  </style>
</head>

<body>
  <header class="site-header">
    <div class="top-controls">
      <div class="language-switcher">
        <label for="languageSelect" data-i18n="languageLabel">語言</label>
        <select id="languageSelect">
__LANGUAGE_OPTIONS__
        </select>
      </div>

      <button id="installButton" class="install-button" type="button" hidden data-i18n="installButton">安裝到手機桌面</button>
    </div>

    <h1 data-i18n="siteTitle">Coin Master 每日獎勵連結</h1>
    <p data-i18n="siteSubtitle">每日自動更新免費能量 / 旋轉 / 金幣連結</p>

    <p>
      <span data-i18n="lastUpdated">最後更新</span>：
      <strong><time id="localizedUpdateTime" datetime="__UPDATED_ISO__"></time></strong>
      <span id="localizedTimezoneLabel"></span>
    </p>

    <p class="credit-badge">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 7.5 7.5 11 12 4.5 16.5 11 21 7.5 19 18H5z"/><rect x="5" y="19.25" width="14" height="2" rx="1"/></svg>
      <span data-i18n="baseTimeNotice">由大佬群CSL製作</span>
    </p>
  </header>

  <main>
    <section class="summary">
      <div>
        <p>
          <span data-i18n="summaryPrefix">目前共收錄</span>
          <strong>__TOTAL__</strong>
          <span data-i18n="summarySuffix">筆獎勵連結。</span>
        </p>
        <p class="summary-notice" data-i18n="summaryNotice">資料來源為公開網頁整理，點擊前請自行確認連結狀態。</p>
      </div>

      <div class="progress-row">
        <progress id="claimProgress" max="__TOTAL__" value="0" aria-labelledby="claimProgressText"></progress>
        <span id="claimProgressText" class="progress-text" aria-live="polite"></span>
      </div>

      <div class="summary-controls">
        <label class="filter-control">
          <input type="checkbox" switch id="hideClaimed">
          <span data-i18n="hideClaimed">隱藏已領取</span>
        </label>

        <button type="button" id="clearClaimed" class="btn btn-ghost" data-i18n="clearClaimed">清除已領取紀錄</button>
      </div>
    </section>

    <aside class="ios-hint" id="iosHint" hidden>
      <div>
        <strong data-i18n="iosHintTitle">iPhone / iPad 安裝提示</strong>
        <span data-i18n="iosHintText">請點選 Safari 分享按鈕，然後選擇「加入主畫面」。</span>
      </div>
      <button type="button" class="icon-button" id="iosHintClose" aria-label="關閉" data-i18n-aria="close">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.25" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>
      </button>
    </aside>

    <p id="emptyMessage" class="empty-message" data-i18n="emptyMessage" hidden>目前沒有可顯示的獎勵。可能全部都已標記為已領取。</p>

__BODY__
  </main>

  <footer class="site-footer">
    <p data-i18n="footerText">本頁僅整理公開獎勵連結，實際領取狀態以遊戲內顯示為準。</p>
    <p>© __YEAR__ 大佬群CSL. All rights reserved.</p>
  </footer>

  <dialog id="clearDialog" aria-labelledby="clearDialogTitle" closedby="any">
    <h1 id="clearDialogTitle" data-i18n="clearConfirm">確定要清除所有已領取紀錄嗎？</h1>
    <form method="dialog" class="dialog-actions">
      <button type="submit" value="cancel" class="btn btn-ghost" autofocus data-i18n="cancel">取消</button>
      <button type="submit" value="confirm" class="btn btn-danger" data-i18n="confirmClear">清除</button>
    </form>
  </dialog>

  <script>
    const STORAGE_PREFIX = "coinmaster_claimed_";
    const HIDE_CLAIMED_KEY = "coinmaster_hide_claimed";
    const LANGUAGE_KEY = "coinmaster_language";
    const IOS_HINT_DISMISSED_KEY = "coinmaster_ios_hint_dismissed";
    const DEFAULT_LANGUAGE = "zh-Hant";

    const I18N = __I18N_JSON__;
    const UPDATE_TIMES = __UPDATE_TIMES_JSON__;

    const cards = Array.from(document.querySelectorAll(".reward-card"));
    const sections = Array.from(document.querySelectorAll(".date-section"));
    const hideClaimedInput = document.querySelector("#hideClaimed");
    const emptyMessage = document.querySelector("#emptyMessage");
    const progress = document.querySelector("#claimProgress");
    const progressText = document.querySelector("#claimProgressText");
    const languageSelect = document.querySelector("#languageSelect");
    const clearDialog = document.querySelector("#clearDialog");

    let currentLanguage = detectLanguage();

    function detectLanguage() {
      const saved = localStorage.getItem(LANGUAGE_KEY);

      if (saved && I18N[saved]) return saved;

      const preferred = navigator.languages?.length ? navigator.languages : [navigator.language];

      for (const tag of preferred) {
        const base = String(tag || "").toLowerCase().split("-")[0];

        if (base === "zh") return "zh-Hant";
        if (I18N[base]) return base;
      }

      return DEFAULT_LANGUAGE;
    }

    function t(key) {
      return I18N[currentLanguage]?.[key] ?? I18N[DEFAULT_LANGUAGE][key] ?? key;
    }

    const storageKey = campaign => STORAGE_PREFIX + campaign;
    const isClaimed = campaign => localStorage.getItem(storageKey(campaign)) === "1";

    function setClaimed(campaign, claimed) {
      if (!campaign) return;

      if (claimed) {
        localStorage.setItem(storageKey(campaign), "1");
      } else {
        localStorage.removeItem(storageKey(campaign));
      }
    }

    function renderCard(card) {
      const claimed = isClaimed(card.dataset.campaign);

      card.classList.toggle("claimed", claimed);
      card.querySelector(".claim-link").textContent = t(claimed ? "claimed" : "claim");
      card.querySelector(".claim-toggle").textContent = t(claimed ? "unmarkClaimed" : "markClaimed");
    }

    function applyFilter() {
      const hideClaimed = hideClaimedInput.checked;

      for (const card of cards) {
        card.hidden = hideClaimed && card.classList.contains("claimed");
      }

      for (const section of sections) {
        section.hidden = !section.querySelector(".reward-card:not([hidden])");
      }

      emptyMessage.hidden = !(cards.length > 0 && cards.every(card => card.hidden));
    }

    function renderProgress() {
      const claimedCount = cards.filter(card => card.classList.contains("claimed")).length;

      progress.max = Math.max(cards.length, 1);
      progress.value = claimedCount;
      progressText.textContent = `${t("claimed")} ${claimedCount} / ${cards.length}`;
    }

    function render() {
      cards.forEach(renderCard);
      applyFilter();
      renderProgress();
    }

    function updateCard(card, claimed) {
      setClaimed(card.dataset.campaign, claimed);
      renderCard(card);
      applyFilter();
      renderProgress();
    }

    function applyLanguage(language) {
      currentLanguage = I18N[language] ? language : DEFAULT_LANGUAGE;

      localStorage.setItem(LANGUAGE_KEY, currentLanguage);
      document.documentElement.lang = currentLanguage;
      document.title = t("siteTitle");
      languageSelect.value = currentLanguage;

      for (const element of document.querySelectorAll("[data-i18n]")) {
        element.textContent = t(element.dataset.i18n);
      }

      for (const element of document.querySelectorAll("[data-i18n-aria]")) {
        element.setAttribute("aria-label", t(element.dataset.i18nAria));
      }

      const updateInfo = UPDATE_TIMES[currentLanguage] || UPDATE_TIMES[DEFAULT_LANGUAGE];
      document.querySelector("#localizedUpdateTime").textContent = updateInfo.time;
      document.querySelector("#localizedTimezoneLabel").textContent = updateInfo.timezone_label || updateInfo.timezone;

      render();
    }

    function bindCardActions() {
      const main = document.querySelector("main");

      // 事件委派：一個監聽器處理所有卡片。
      const onLinkActivate = event => {
        const link = event.target.closest(".claim-link");

        if (link) updateCard(link.closest(".reward-card"), true);
      };

      main.addEventListener("click", event => {
        onLinkActivate(event);

        const toggle = event.target.closest(".claim-toggle");

        if (toggle) {
          const card = toggle.closest(".reward-card");
          updateCard(card, !isClaimed(card.dataset.campaign));
        }
      });

      // 滑鼠中鍵開新分頁也算領取。
      main.addEventListener("auxclick", event => {
        if (event.button === 1) onLinkActivate(event);
      });
    }

    function bindHideClaimed() {
      hideClaimedInput.checked = localStorage.getItem(HIDE_CLAIMED_KEY) === "1";

      hideClaimedInput.addEventListener("change", () => {
        if (hideClaimedInput.checked) {
          localStorage.setItem(HIDE_CLAIMED_KEY, "1");
        } else {
          localStorage.removeItem(HIDE_CLAIMED_KEY);
        }

        applyFilter();
      });
    }

    function bindClearClaimed() {
      document.querySelector("#clearClaimed").addEventListener("click", () => {
        clearDialog.showModal();
      });

      clearDialog.addEventListener("close", () => {
        const choice = clearDialog.returnValue;
        clearDialog.returnValue = "";

        if (choice !== "confirm") return;

        Object.keys(localStorage)
          .filter(key => key.startsWith(STORAGE_PREFIX))
          .forEach(key => localStorage.removeItem(key));

        render();
      });

      // closedby="any" 尚未支援的瀏覽器（Safari）補上點背景關閉。
      if (!("closedBy" in HTMLDialogElement.prototype)) {
        const isOutside = event => {
          const rect = clearDialog.getBoundingClientRect();

          return event.clientX < rect.left || event.clientX > rect.right ||
            event.clientY < rect.top || event.clientY > rect.bottom;
        };

        let pressedOutside = false;

        clearDialog.addEventListener("pointerdown", event => {
          pressedOutside = isOutside(event);
        });

        clearDialog.addEventListener("pointerup", event => {
          if (pressedOutside && isOutside(event)) clearDialog.close();
        });
      }
    }

    function isStandaloneMode() {
      return window.matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
    }

    function setupPwaInstall() {
      const installButton = document.querySelector("#installButton");
      const iosHint = document.querySelector("#iosHint");
      const isIos = /iphone|ipad|ipod/i.test(navigator.userAgent) ||
        (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);

      if (isIos && !isStandaloneMode() && localStorage.getItem(IOS_HINT_DISMISSED_KEY) !== "1") {
        iosHint.hidden = false;
      }

      document.querySelector("#iosHintClose").addEventListener("click", () => {
        iosHint.hidden = true;
        localStorage.setItem(IOS_HINT_DISMISSED_KEY, "1");
      });

      const supportsWebInstall = typeof Navigator.prototype.install === "function";
      let deferredInstallPrompt;

      if (supportsWebInstall && !isStandaloneMode()) {
        installButton.hidden = false;
      }

      window.addEventListener("beforeinstallprompt", event => {
        event.preventDefault();
        deferredInstallPrompt = event;

        if (!supportsWebInstall) installButton.hidden = false;
      });

      installButton.addEventListener("click", async () => {
        if (installButton.getAttribute("aria-disabled") === "true") return;

        installButton.setAttribute("aria-disabled", "true");

        try {
          if (supportsWebInstall) {
            await navigator.install();
            installButton.hidden = true;
          } else if (deferredInstallPrompt) {
            const promptEvent = deferredInstallPrompt;
            deferredInstallPrompt = undefined;
            await promptEvent.prompt();
            await promptEvent.userChoice;

            if (!deferredInstallPrompt) installButton.hidden = true;
          }
        } catch (error) {
          if (error.name !== "AbortError") console.error(error);
        } finally {
          installButton.removeAttribute("aria-disabled");
        }
      });

      window.addEventListener("appinstalled", () => {
        deferredInstallPrompt = undefined;
        installButton.hidden = true;
      });
    }

    function registerServiceWorker() {
      if (!("serviceWorker" in navigator)) return;

      window.addEventListener("load", () => {
        navigator.serviceWorker.register("./sw.js").catch(error => {
          console.warn("Service Worker registration failed:", error);
        });
      });
    }

    languageSelect.addEventListener("change", () => applyLanguage(languageSelect.value));
    bindHideClaimed();
    bindCardActions();
    bindClearClaimed();
    applyLanguage(currentLanguage);
    setupPwaInstall();
    registerServiceWorker();
  </script>
</body>
</html>
"""


THEME_COLOR = "#c62828"


def generate_html(records):
    current_time_taipei = datetime.now(ZoneInfo(DEFAULT_TIMEZONE))
    local_update_times = build_local_update_times(current_time_taipei)

    replacements = {
        "__THEME_COLOR__": THEME_COLOR,
        "__LANGUAGE_OPTIONS__": build_language_options(),
        "__UPDATED_ISO__": current_time_taipei.isoformat(timespec="seconds"),
        "__TOTAL__": str(len(records)),
        "__BODY__": build_rows_html(records),
        "__YEAR__": str(current_time_taipei.year),
        "__I18N_JSON__": escape_json_for_script(I18N),
        "__UPDATE_TIMES_JSON__": escape_json_for_script(local_update_times),
    }

    page = PAGE_TEMPLATE

    for token, value in replacements.items():
        page = page.replace(token, value)

    return page


def generate_manifest():
    manifest = {
        "id": "./",
        "name": "Coin Master Daily Rewards",
        "short_name": "Coin Rewards",
        "description": "Daily Coin Master reward links with multilingual and offline support.",
        "start_url": "./index.html",
        "scope": "./",
        "display": "standalone",
        "background_color": "#f6f7fb",
        "theme_color": THEME_COLOR,
        "orientation": "portrait-primary",
        "lang": "zh-Hant",
        "icons": [
            {
                "src": "./icons/icon.svg",
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "any",
            },
            {
                "src": "./icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable",
            },
            {
                "src": "./icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable",
            },
        ],
        "categories": ["utilities", "games"],
    }

    with open(OUTPUT_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def generate_service_worker():
    cache_version = datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).strftime("%Y%m%d%H%M%S")

    sw = f"""const CACHE_NAME = "coinmaster-rewards-{cache_version}";

const APP_SHELL = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icons/icon.svg",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/apple-touch-icon.png"
];

self.addEventListener("install", event => {{
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(APP_SHELL))
      .catch(() => null)
  );

  self.skipWaiting();
}});

self.addEventListener("activate", event => {{
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => caches.delete(key))
      )
    )
  );

  self.clients.claim();
}});

self.addEventListener("fetch", event => {{
  if (event.request.method !== "GET") {{
    return;
  }}

  const requestUrl = new URL(event.request.url);

  if (requestUrl.origin !== location.origin) {{
    return;
  }}

  event.respondWith(
    fetch(event.request)
      .then(response => {{
        if (response.ok) {{
          const responseClone = response.clone();
          event.waitUntil(
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, responseClone))
          );
        }}

        return response;
      }})
      .catch(async () => {{
        const cachedResponse = await caches.match(event.request);

        if (cachedResponse) return cachedResponse;
        if (event.request.mode === "navigate") return caches.match("./index.html");

        return Response.error();
      }})
  );
}});
"""

    with open(OUTPUT_SW, "w", encoding="utf-8") as f:
        f.write(sw)


def cleanup_legacy_docs_files():
    """
    專案目前只需要 output/coinmaster_rewards.json 作為資料來源。

    不再需要：
    docs/coinmaster_rewards.json
    """
    legacy_files = [
        "docs/coinmaster_rewards.json",
    ]

    for path in legacy_files:
        if os.path.exists(path):
            os.remove(path)
            print(f"Removed legacy docs file: {path}")


def main():
    ensure_docs_dir()
    cleanup_legacy_docs_files()

    records = load_rewards()
    html_content = generate_html(records)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    generate_manifest()
    generate_service_worker()

    print(f"Generated {OUTPUT_HTML}")
    print(f"Generated {OUTPUT_MANIFEST}")
    print(f"Generated {OUTPUT_SW}")


if __name__ == "__main__":
    main()
