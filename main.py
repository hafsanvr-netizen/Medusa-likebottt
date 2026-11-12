#!/usr/bin/env python3
"""
𝐌𝐄𝐃𝐔𝐒𝐀 𝐋𝐈𝐊𝐄 𝐁𝐎𝐓 — Premium 4-API Fallback Edition
"""
import json, os, logging, asyncio, sys, threading, shutil, time as _time, re, random
from datetime import datetime, date, time, timedelta, timezone

import aiohttp
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeChat,
    ReactionTypeEmoji, ForceReply, ChatMemberLeft, ChatMemberBanned, LinkPreviewOptions
)
from telegram.ext import (
    Application, CommandHandler, ContextTypes, ExtBot,
    MessageHandler, filters, CallbackQueryHandler, ChatMemberHandler,
    TypeHandler, ApplicationHandlerStop
)
from telegram.request import HTTPXRequest
from telegram.constants import ParseMode

load_dotenv()

# ══════════════════════════════════════════════════
#  LOGGING
# ══════════════════════════════════════════════════
logging.basicConfig(
    format='%(asctime)s | %(levelname)s | %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler('bot.log', encoding='utf-8')]
)
for _n in ('httpx', 'httpcore', 'telegram', 'urllib3', 'aiohttp', 'apscheduler'):
    logging.getLogger(_n).setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════
#  TERMINAL UI
# ══════════════════════════════════════════════════
_FONT = {
    "M": ["█   █", "██ ██", "█ █ █", "█   █", "█   █"],
    "E": ["█████", "█    ", "████ ", "█    ", "█████"],
    "D": ["████ ", "█   █", "█   █", "█   █", "████ "],
    "U": ["█   █", "█   █", "█   █", "█   █", " ███ "],
    "S": [" ████", "█    ", " ███ ", "    █", "████ "],
    "A": [" ███ ", "█   █", "█████", "█   █", "█   █"],
}
_ICE = (231, 195, 159, 123, 87)          # উপর থেকে নিচে: সাদা বরফ → নীল বরফ

def _c(n): return f"\033[38;5;{n}m"
_R = "\033[0m"

_DIG = {
    "0": ["███", "█ █", "█ █", "█ █", "███"],
    "1": [" █ ", "██ ", " █ ", " █ ", "███"],
    "2": ["███", "  █", "███", "█  ", "███"],
    "3": ["███", "  █", "███", "  █", "███"],
    "4": ["█ █", "█ █", "███", "  █", "  █"],
    "5": ["███", "█  ", "███", "  █", "███"],
    "6": ["███", "█  ", "███", "█ █", "███"],
    "7": ["███", "  █", "  █", "  █", "  █"],
    "8": ["███", "█ █", "███", "█ █", "███"],
    "9": ["███", "█ █", "███", "  █", "███"],
    ":": [" ", "█", " ", "█", " "],
}
_CLOCK_ICE = (195, 159, 123, 87, 51)

def _stretch(line, h):
    return "".join(ch * h for ch in line)

def clock_lines(w, wide):
    """বড় ডিজিটাল ঘড়ি (BD সময়) — ৫ লাইন, মাঝখানে বসানো।"""
    tm = now_bd().strftime("%H:%M:%S")
    h = 2 if wide else 1
    out = []
    for r in range(5):
        row = " ".join(_stretch(_DIG[ch][r], h) for ch in tm)
        pad = " " * max(0, (w - len(row)) // 2)
        out.append(pad + "\033[1m" + _c(_CLOCK_ICE[r]) + row + _R)
    return out

def print_banner():
    """উপরে অনেক বড় বরফ-রঙের MEDUSA + নিচে বড় লাইভ ঘড়ির জায়গা।
       রিটার্ন: (ঘড়ির শুরুর রো, wide?) — টার্মিনাল না হলে None।"""
    try:
        if not sys.stdout.isatty(): return None
        size = shutil.get_terminal_size((40, 24))
        w, rows = size.columns, size.lines
        wide = w >= 72                          # বড় স্ক্রিনে ডাবল চওড়া
        hs = 2 if wide else 1                   # আড়াআড়ি স্কেল
        vs = 2 if (wide and rows >= 30) else 1  # লম্বালম্বি স্কেল
        base = [" ".join(_FONT[ch][r] for ch in "MEDUSA") for r in range(5)]
        art = []
        for r, line in enumerate(base):
            big = _stretch(line, hs)
            art += [(big, _ICE[r])] * vs
        bw = len(art[0][0])
        pad = " " * max(0, (w - bw) // 2)
        lines = [""]
        top = "❄ " + "─" * 3 + " ✦ " + "─" * 3 + " ❄"
        lines.append(" " * max(0, (w - len(top)) // 2) + _c(117) + top + _R)
        lines.append("")
        n = len(art)
        for i, (line, col) in enumerate(art):
            # vs=2 হলে উপর→নিচে আরও মসৃণ গ্রেডিয়েন্ট
            col = _ICE[min(len(_ICE) - 1, i * len(_ICE) // n)]
            lines.append(pad + "\033[1m" + _c(col) + line + _R)
        tag = "❄  L I K E   B O T  ❄"
        lines.append("")
        lines.append(" " * max(0, (w - len(tag)) // 2) + _c(159) + tag + _R)
        bot = "─" * min(bw, w - 2)
        lines.append(" " * max(0, (w - len(bot)) // 2) + _c(75) + bot + _R)
        lines.append("")
        clock_row = len(lines) + 1              # ১-ভিত্তিক রো নম্বর
        lines += [""] * 5                       # ঘড়ির জায়গা
        lines.append("")
        sys.stdout.write("\033[2J\033[H" + "\n".join(lines) + "\n")
        sys.stdout.flush()
        return clock_row, wide
    except Exception:
        return None

class TermUI:
    """উপরে MEDUSA ব্যানার, একদম নিচের লাইনে স্ট্যাটাস বার (স্ক্রল রিজিয়নে আটকানো)।"""
    def __init__(self):
        self._lock = threading.RLock()
        self._status = ""
        self._running = False
        self._thread = None
        self._rows = 0
        self._tty = False
        self._clock = None            # (row, wide)

    def _size_rows(self):
        return shutil.get_terminal_size((40, 24)).lines

    def _render(self):
        if not self._tty: return
        with self._lock:
            try:
                rows = self._size_rows()
                out = "\0337"                                   # কার্সর সেভ
                if rows != self._rows:                           # কীবোর্ড খুললে/বন্ধ হলে
                    if self._rows:                               # পুরনো বার মুছে ফেলা (আটকে থাকা সময় আর থাকবে না)
                        out += f"\033[{self._rows};1H\033[2K"
                    self._rows = rows
                out += f"\033[1;{max(1, rows - 1)}r"            # স্ক্রল রিজিয়ন প্রতিবার ঠিক রাখা
                if self._clock:
                    crow, wide = self._clock
                    if crow + 4 < rows:                          # জায়গা থাকলে বড় ঘড়ি আঁকা
                        w = shutil.get_terminal_size((40, 24)).columns
                        for i, ln in enumerate(clock_lines(w, wide and w >= 72)):
                            out += f"\033[{crow + i};1H\033[2K" + ln
                bar = "\033[48;5;17m" + self._status + "\033[K\033[0m"
                out += f"\033[{rows};1H" + bar + "\0338"       # নিচের লাইনে বার, কার্সর রিস্টোর
                sys.stdout.write(out); sys.stdout.flush()
            except Exception:
                pass

    def _loop(self):
        while self._running:
            try:
                refresh_status()
            except Exception:
                pass
            self._render()
            _time.sleep(1)

    def start(self):
        if self._running: return
        self._tty = sys.stdout.isatty()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if not self._tty: return
        with self._lock:
            try:
                rows = self._size_rows()
                sys.stdout.write(f"\033[r\033[{rows};1H\033[2K\n")
                sys.stdout.flush()
            except Exception:
                pass

    def set_clock(self, info):
        with self._lock:
            self._clock = info

    def set_status(self, text):
        with self._lock:
            self._status = text

    def log(self, msg):
        with self._lock:
            try:
                sys.stdout.write(msg + "\n"); sys.stdout.flush()
            except Exception:
                pass

term = TermUI()

# ══════════════════════════════════════════════════
#  ══════════ 4 API CONFIG ══════════
# ══════════════════════════════════════════════════
def _norm(u):
    u = (u or "").strip()
    return u + "/" if u and not u.endswith("/") else u

APIS = []
for i in range(1, 5):
    url = _norm(os.getenv(f"API_{i}_URL", ""))
    key = os.getenv(f"API_{i}_KEY", "").strip()
    if url and key:
        APIS.append({"name": f"API-{i}", "num": i, "url": url, "key": key})

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# আলাদা MAX Like API — সাধারণ API_1..API_4 থেকে সম্পূর্ণ স্বাধীন
MAX_API_URL = _norm(os.getenv("MAX_API_URL", ""))
MAX_API_KEY = os.getenv("MAX_API_KEY", "").strip()
MAX_STATE_FILE = "max_like_state.json"
max_like_state = {"enabled": False}


def _parse_ids(*vals):
    out = []
    for v in vals:
        for x in (v or "").replace(";", ",").split(","):
            x = x.strip()
            if x.lstrip("-").isdigit() and int(x) not in out:
                out.append(int(x))
    return out

# ADMIN_1_ID = মূল এডমিন (সব ক্ষমতা) | ADMIN_2_ID = আরেক এডমিন
# (গ্রুপ/চ্যানেল add-remove-allow-block ছাড়া বাকি সব কমান্ড একই)
OWNER_IDS = _parse_ids(os.getenv("ADMIN_1_ID")) or [8728427543]
_CO_IDS = [i for i in _parse_ids(os.getenv("ADMIN_2_ID"), os.getenv("ADMIN_2_IDS"), os.getenv("ADMIN_IDS")) if i not in OWNER_IDS]
ADMIN_IDS = OWNER_IDS + _CO_IDS

BD_TZ = timezone(timedelta(hours=6))
PUB_VIP_LIMIT = 3
BOT_USERNAME = ""
LINE = "━━━━━━━━━━━━━━━━━━━━━━"

FILE_100 = '100like_state.json'
FILE_PUB = 'public_state.json'
FILE_PHOTO = 'like_photo.json'
FILE_BLOCKED = 'blocked_groups.json'
FILE_MUTED = 'muted_groups.json'
FILE_REFER = 'referrals.json'
FILE_REFER_GOAL = 'refer_10plus.json'
REFER_GOAL = 10     # এই সংখ্যা পূর্ণ হলে refer_10plus.json এ যাবে + মালিকের কাছে নোটিফিকেশন
OWNER_LINK = "https://t.me/HAFSAN_KUN"
GROUP_LINK = "https://t.me/MEDUSA_LIKE"   # Official Like Group

# ══════════════════════════════════════════════════
#  REGION CONFIG (সব সাপোর্টেড সার্ভার)
# ══════════════════════════════════════════════════
DEFAULT_LIKE_REGION = "bd"
ALLOWED_REGIONS = {
    "bd", "ind", "pk", "sg", "id", "br",
    "us", "ru", "th", "vn", "tw", "me", "cis"
}

# ══════════════════════════════════════════════════
#  STATE
# ══════════════════════════════════════════════════
like100 = {"config": {"status": "on", "public": False, "limit": 1},
           "groups": {}, "channels": {}, "vip": {}, "users": {}, "stats": {}}
public = {"config": {"status": "on", "mode": "public", "limit": 1},
          "groups": {}, "chats": {}, "force_join": {"groups": [], "channels": []},
          "vip": {}, "banned": {}, "users": {}, "stats": {}, "names": {}}
photo_state = {"file_id": None, "set_by": None, "date": None}
blocked_groups = {}
referral = {"users": {}, "referred": {}, "pending": {}, "notified": []}
muted_groups = {}      # /like_bot_mute দেওয়া গ্রুপ — বট ওখানে একদম চুপ

# ══════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════
def now_bd(): return datetime.now(BD_TZ)
def today_str(): return str(now_bd().date())
def is_admin(uid): return uid in ADMIN_IDS
def is_owner(uid): return uid in OWNER_IDS

def admin_only(fn):
    async def w(update, context):
        if not update.effective_user or not is_admin(update.effective_user.id): return
        return await fn(update, context)
    w.__name__ = fn.__name__
    return w

def owner_only(fn):
    """গ্রুপ/চ্যানেল ম্যানেজমেন্ট কমান্ড — অন্য কেউ চালালে বট চুপ থাকবে"""
    async def w(update, context):
        if not update.effective_user or not is_owner(update.effective_user.id): return
        return await fn(update, context)
    w.__name__ = fn.__name__
    return w

def build_status():
    t = today_str()
    s1 = like100.get("stats", {}).get(t, {}).get("total", 0)
    s2 = public.get("stats", {}).get(t, {}).get("total", 0)
    b1 = "🟢" if like100["config"]["status"] == "on" else "🔴"
    b2 = "🟢" if public["config"]["status"] == "on" else "🔴"
    tm = now_bd().strftime("%H:%M:%S")
    ph = "📸" if photo_state.get("file_id") else "🚫"
    bl = f"🚫{len(blocked_groups)}" if blocked_groups else ""
    sep = f"\033[38;5;75m │ \033[38;5;231m"
    return ("\033[38;5;231m" + f" ⏰ {tm}{sep}{b1} 100:{s1}{sep}{b2} Pub:{s2}{sep}"
            f"🔌{len(active_apis())}/{len(APIS)}{sep}{ph} {bl} ")
def refresh_status(): term.set_status(build_status())

def load_json(p, d):
    if not os.path.exists(p): return d
    try:
        with open(p, 'r', encoding='utf-8') as f: return json.load(f)
    except Exception as e:
        logger.error(f"load {p}: {e} — corrupt file backed up")
        try: os.replace(p, p + ".corrupt")
        except Exception: pass
        return d
_save_lock = threading.Lock()
def save_json(p, d):
    try:
        with _save_lock:
            tmp = p + ".tmp"
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(d, f, indent=2, ensure_ascii=False)
            os.replace(tmp, p)   # atomic — মাঝপথে বন্ধ হলেও ফাইল নষ্ট হবে না
    except Exception as e: logger.error(f"save {p}: {e}")

def load_data():
    global like100, public, photo_state, blocked_groups, muted_groups, referral, shop, max_like_state
    max_like_state = load_json(MAX_STATE_FILE, {"enabled": False})
    if not isinstance(max_like_state, dict): max_like_state = {"enabled": False}
    max_like_state.setdefault("enabled", False)
    like100 = load_json(FILE_100, like100)
    public = load_json(FILE_PUB, public)
    photo_state = load_json(FILE_PHOTO, photo_state)
    blocked_groups = load_json(FILE_BLOCKED, {})
    muted_groups = load_json(FILE_MUTED, {})
    _old = [g for g, c in muted_groups.items() if isinstance(c, dict) and c.get("auto")]
    for g in _old: muted_groups.pop(g, None)          # পুরনো লো-লাইক অটো-মিউট বাদ
    if _old: save_json(FILE_MUTED, muted_groups)
    referral = load_json(FILE_REFER, referral)
    for k in ("users", "referred", "pending"): referral.setdefault(k, {})
    referral.setdefault("notified", [])   # ১০ পূর্ণ হওয়ার নোটিফিকেশন যাদের গেছে
    public.setdefault("chats", {}); public.setdefault("groups", {})
    public.setdefault("banned", {}); public.setdefault("vip", {}); public.setdefault("names", {})
    for k in ("groups", "channels", "vip", "users", "stats"): like100.setdefault(k, {})
    like100.setdefault("config", {}); like100["config"].setdefault("status", "on")
    like100["config"].setdefault("public", False); like100["config"].setdefault("limit", 1)
    public.setdefault("force_join", {"groups": [], "channels": []})
    public["config"].setdefault("mode", "public")
    photo_state.setdefault("file_id", None)
    shop = load_json(FILE_SHOP, shop)
    if not isinstance(shop, dict):
        shop = {"users": {}, "auto": {}, "auto_groups": {}}
    shop.setdefault("users", {}); shop.setdefault("auto", {}); shop.setdefault("auto_groups", {})
    if not isinstance(shop["users"], dict): shop["users"] = {}
    if not isinstance(shop["auto"], dict): shop["auto"] = {}
    if not isinstance(shop["auto_groups"], dict): shop["auto_groups"] = {}

def save_100(): save_json(FILE_100, like100)
def save_pub(): save_json(FILE_PUB, public)
def save_photo(): save_json(FILE_PHOTO, photo_state)
def save_blocked(): save_json(FILE_BLOCKED, blocked_groups)
def save_muted(): save_json(FILE_MUTED, muted_groups)
def save_all(): save_100(); save_pub(); save_photo(); save_blocked(); save_muted(); save_refer(); save_shop()

def next_reset_str():
    now = now_bd()
    nxt = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    s = int((nxt - now).total_seconds())
    return f"{s//3600}h {(s%3600)//60}m"
def mask_key(k):
    if not k: return "—"
    if len(k) <= 4: return "*"*len(k)
    return k[:2] + "*"*(len(k)-4) + k[-2:]
def is_group_blocked(cid): return str(cid) in blocked_groups
def is_group_muted(cid): return str(cid) in muted_groups

# ══════════════════════════════════════════════════
#  DESIGNED BUTTONS + EXT BOT
# ══════════════════════════════════════════════════
def add_group_url(): return f"https://t.me/{BOT_USERNAME}?startgroup=true"
def cbtn(text, style="success", **kw):
    try: return InlineKeyboardButton(text, style=style, **kw)
    except TypeError: return InlineKeyboardButton(text, api_kwargs={"style": style}, **kw)

def owner_button():
    return cbtn("👑 ✨ 𝗢𝗪𝗡𝗘𝗥 ✨ 💎", "danger", url=OWNER_LINK)

def group_button():
    return cbtn("💎 ᴏꜰꜰɪᴄɪᴀʟ ʟɪᴋᴇ ɢʀᴏᴜᴘ", "primary", url=GROUP_LINK)

def is_store_markup(markup):
    rows = markup.inline_keyboard
    return len(rows) == 1 and len(rows[0]) == 1 and getattr(rows[0][0], "url", None) == OWNER_LINK

def with_add_button(markup):
    """প্রতিটি মেসেজের নিচে: ➕ Add me + 💎 Official Like Group + 👑 OWNER বাটন (একবারই বসে)"""
    if isinstance(markup, InlineKeyboardMarkup) and (is_store_markup(markup) or is_shop_markup(markup)):
        return markup                                            # Shop/Store screens keep only their own buttons
    add_url = add_group_url() if BOT_USERNAME else None
    rows = [list(r) for r in markup.inline_keyboard] if isinstance(markup, InlineKeyboardMarkup) else []
    if markup is not None and not isinstance(markup, InlineKeyboardMarkup):
        return markup
    urls = {getattr(b, "url", None) for r in rows for b in r}
    if add_url and add_url not in urls:
        rows.append([cbtn("➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ", "success", url=add_url)])
    if GROUP_LINK not in urls:
        rows.append([group_button()])
    if OWNER_LINK not in urls and not is_shop_markup(markup):   # 🛍 Shop-এর নিচে OWNER বাটন নেই
        rows.append([owner_button()])
    return InlineKeyboardMarkup(rows) if rows else markup

def _cid(a, kw):
    return kw.get("chat_id") if kw.get("chat_id") is not None else (a[0] if a else None)

class AddGroupBot(ExtBot):
    async def send_message(self, *a, **kw):
        if is_group_muted(_cid(a, kw)): return None
        kw["reply_markup"] = with_add_button(kw.get("reply_markup"))
        return await super().send_message(*a, **kw)
    async def edit_message_text(self, *a, **kw):
        if is_group_muted(_cid(a, kw)): return None
        kw["reply_markup"] = with_add_button(kw.get("reply_markup"))
        return await super().edit_message_text(*a, **kw)
    async def send_photo(self, *a, **kw):
        if is_group_muted(_cid(a, kw)): return None
        kw["reply_markup"] = with_add_button(kw.get("reply_markup"))
        return await super().send_photo(*a, **kw)
    async def edit_message_caption(self, *a, **kw):
        if is_group_muted(_cid(a, kw)): return None
        kw["reply_markup"] = with_add_button(kw.get("reply_markup"))
        return await super().edit_message_caption(*a, **kw)
    async def set_message_reaction(self, *a, **kw):
        if is_group_muted(_cid(a, kw)): return None
        return await super().set_message_reaction(*a, **kw)
    async def copy_message(self, *a, **kw):
        if is_group_muted(kw.get("chat_id")): return None
        kw["reply_markup"] = with_add_button(kw.get("reply_markup"))
        return await super().copy_message(*a, **kw)
    async def send_document(self, *a, **kw):
        if is_group_muted(_cid(a, kw)): return None
        kw["reply_markup"] = with_add_button(kw.get("reply_markup"))
        return await super().send_document(*a, **kw)

# ══════════════════════════════════════════════════
#  LIMIT / USED
# ══════════════════════════════════════════════════
def get_100_limit(uid):
    if is_owner(uid): return 999999
    if uid in _CO_IDS: return 10
    vip = like100["vip"].get(str(uid))
    if vip:
        pd = vip.get("per_day")
        return 999999 if (pd is None or int(pd) <= 0) else int(pd)
    return like100["config"]["limit"]
def get_100_used(uid):
    t = today_str(); u = like100["users"].get(str(uid))
    if not u or u.get("date") != t: return 0
    return u.get("count", 0)
def can_100_like(uid):
    if is_owner(uid): return True
    return get_100_used(uid) < get_100_limit(uid)
def update_100_used(uid):
    if is_owner(uid): return
    t = today_str(); k = str(uid)
    u = like100["users"].setdefault(k, {"date": t, "count": 0})
    if u.get("date") != t: u["date"] = t; u["count"] = 0
    u["count"] += 1
    st = like100["stats"].setdefault(t, {"total": 0, "users": {}})
    st["total"] += 1
    st["users"][k] = st["users"].get(k, 0) + 1
    save_100()

def get_pub_limit(uid):
    if uid in _CO_IDS and not is_owner(uid): return 10
    base = _pub_base_limit(uid)
    if base >= 999999 or str(uid) in public["banned"]: return base
    return base + shop_bonus(uid)      # 🛍 MyShop থেকে কেনা +limit

def _pub_base_limit(uid):
    if is_owner(uid): return 999999
    if uid in _CO_IDS: return 10
    if str(uid) in public["banned"]: return 0
    v = public["vip"].get(str(uid))
    if v:
        pd = v.get("per_day") if isinstance(v, dict) else None
        return PUB_VIP_LIMIT if pd is None else (999999 if int(pd) <= 0 else int(pd))
    return public["config"]["limit"]
def get_pub_used(uid):
    t = today_str(); u = public["users"].get(str(uid))
    if not u or u.get("date") != t: return 0
    return u.get("count", 0)
def can_pub_like(uid):
    if is_owner(uid): return True
    if str(uid) in public["banned"]: return False
    return get_pub_used(uid) < get_pub_limit(uid)
def update_pub_used(uid):
    if is_owner(uid): return
    t = today_str(); k = str(uid)
    u = public["users"].setdefault(k, {"date": t, "count": 0})
    if u.get("date") != t: u["date"] = t; u["count"] = 0
    u["count"] += 1
    st = public["stats"].setdefault(t, {"total": 0, "users": {}})
    st["total"] += 1
    st["users"][k] = st["users"].get(k, 0) + 1
    save_pub()

def _is_member(m):
    if m.status in ("member", "administrator", "creator"): return True
    if m.status == "restricted": return bool(getattr(m, "is_member", False))
    return False

async def user_in_100_community(bot, uid):
    if not like100["groups"] and not like100["channels"]: return False
    for gid in list(like100["groups"].keys()):
        try:
            m = await bot.get_chat_member(int(gid), uid)
            if _is_member(m): return True
        except: continue
    for uname, info in like100["channels"].items():
        try:
            cid = info.get("id")
            if cid: m = await bot.get_chat_member(cid, uid)
            else:
                chat = await bot.get_chat(uname)
                m = await bot.get_chat_member(chat.id, uid)
            if _is_member(m): return True
        except: continue
    return False

def pub_join_keyboard(missing=None):
    """missing দিলে শুধু যেগুলোতে ইউজার এখনো জয়েন করেনি সেগুলোর বাটন দেখায়"""
    fj = public["force_join"]
    if missing is None:
        missing = fj.get("groups", []) + fj.get("channels", [])
    rows = []
    for c in missing:
        is_ch = c in fj.get("channels", [])
        label = c.get("title") or ("ᴄʜᴀɴɴᴇʟ" if is_ch else "ɢʀᴏᴜᴘ")
        rows.append([cbtn(f"➤ ᴊᴏɪɴ {label[:25]}", "primary", url=c['invite_link'])])
    if rows:
        rows.append([cbtn("✅ ᴠᴇʀɪꜰʏ", "success", callback_data="verify_join")])
    return InlineKeyboardMarkup(rows) if rows else None

_join_ok = {}          # uid -> expiry (সব ফোর্স-জয়েন পূরণ থাকলে)
_join_ok_chats = {}    # uid -> কোন চ্যাট-সেটের জন্য ক্যাশ (লিস্ট বদলালে ক্যাশ বাতিল)
def _chat_sig(chats): return tuple(sorted(c.get("chat_id", 0) for c in chats))

async def get_missing_joins(bot, uid):
    """যেসব ফোর্স-জয়েন গ্রুপ/চ্যানেলে ইউজার এখনো নেই তার লিস্ট"""
    fj = public["force_join"]
    chats = fj.get("groups", []) + fj.get("channels", [])
    now = _time.time()
    # জয়েন করা ইউজারকে ৫ মিনিট আবার চেক করা হয় না (Telegram কল বাঁচে)
    if _join_ok.get(uid, 0) > now and _join_ok_chats.get(uid) == _chat_sig(chats):
        return []

    async def one(c):
        try:
            m = await asyncio.wait_for(bot.get_chat_member(c['chat_id'], uid), timeout=6)
            return None if _is_member(m) else c
        except Exception as e:
            # বট ওই চ্যাটে না থাকলে/নেটওয়ার্ক সমস্যায় সবাইকে আটকে না দিয়ে শুধু লগ রাখা হয়
            logger.warning(f"pub_join chat={c.get('chat_id')} uid={uid}: {e.__class__.__name__}")
            return None
    # সবগুলো গ্রুপ/চ্যানেল একসাথে চেক (আগে একটার পর একটা হতো)
    res = await asyncio.gather(*(one(c) for c in chats))
    missing = [c for c in res if c]
    if not missing:
        _join_ok[uid] = now + 300
        _join_ok_chats[uid] = _chat_sig(chats)
        if len(_join_ok) > 5000:
            for k in [k for k, v in _join_ok.items() if v < now]:
                _join_ok.pop(k, None); _join_ok_chats.pop(k, None)
    return missing

async def check_pub_join(bot, uid):
    return not await get_missing_joins(bot, uid)

# ══════════════════════════════════════════════════
#  ══════════ 4-API FALLBACK CALL (Fixed) ══════════
# ══════════════════════════════════════════════════
QUOTA_FALLBACK = os.getenv("QUOTA_FALLBACK", "1").strip() != "0"
QUOTA_TTL = 900                 # সব API লিমিটে থাকলে ১৫ মিনিট আবার API কল করা হয় না
_quota_cache = {}               # (region, uid) -> expiry
_inflight = set()               # একই ইউজারের একসাথে একাধিক রিকোয়েস্ট ঠেকানো

def _to_int(v):
    try: return int(v or 0)
    except (TypeError, ValueError): return 0

def md_escape(t):
    return re.sub(r'([_*`\[])', r'\\\1', str(t))

_api_session = None
_api_down = {}          # api name -> সময় পর্যন্ত স্কিপ (টাইমআউট/এরর হলে ৪৫ সেকেন্ড)
API_DOWN_SECS = 120      # টাইমআউট/এরর দেওয়া API এতক্ষণ স্কিপ — পরের ইউজারদের আর অপেক্ষা করতে হয় না
HEDGE_SECS = float(os.getenv("HEDGE_SECS", "5"))   # বর্তমান API এতক্ষণে সাড়া না দিলে পরের API-ও চালু (প্রথমটা বন্ধ না করে)
_api_liked = {}          # (api name, uid) -> তারিখ: আজ এই API এই UID-তে লাইক দিয়েছে (পরে লিমিট বললে সেটা UID-র লিমিট, API-র নয়)
_uid_quota = {}          # (api name, uid) -> তারিখ: আজ ওই UID-তে ওই API লাইক দিতে পারেনি → আবার চেষ্টা নয়
API_TIMEOUT = 8          # প্রতিটি API-র সর্বোচ্চ অপেক্ষা (সেকেন্ড) — স্লো হলে পরের API-তে যাবে

def get_api_session():
    """একটাই শেয়ার্ড সেশন — প্রতি লাইকে নতুন TLS হ্যান্ডশেক করতে হয় না"""
    global _api_session
    if _api_session is None or _api_session.closed:
        _api_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=100, ttl_dns_cache=300, keepalive_timeout=60))
    return _api_session

async def _call_one_api(session, api, region, uid):
    """একটা API-তে কল। রিটার্ন: (name, info_dict, raw_data_or_None)"""
    name = api["name"]
    try:
        async with session.get(
                f"{api['url']}like",
                params={"key": api["key"], "uid": uid, "server_name": region},
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT, connect=3)) as r:
            if r.status != 200:
                _api_down[name] = _time.time() + API_DOWN_SECS
                return name, {"status": "error", "likes": 0, "error": f"HTTP {r.status}"}, None
            data = await r.json(content_type=None)
    except asyncio.CancelledError:
        raise
    except asyncio.TimeoutError:
        _api_down[name] = _time.time() + API_DOWN_SECS
        return name, {"status": "error", "likes": 0, "error": "timeout"}, None
    except Exception as e:
        # e-র টেক্সটে key সহ URL থাকতে পারে, তাই শুধু টাইপ লগ করা হয়
        _api_down[name] = _time.time() + API_DOWN_SECS
        logger.warning(f"{name} request failed: {e.__class__.__name__}")
        return name, {"status": "error", "likes": 0, "error": e.__class__.__name__}, None

    if not isinstance(data, dict):
        return name, {"status": "error", "likes": 0, "error": "bad response"}, None

    st = _to_int(data.get("status"))
    given = _to_int(data.get("LikesGivenByAPI"))
    _api_down.pop(name, None)                      # সাড়া দিয়েছে = আবার সুস্থ
    if st == 1 and given > 0:
        return name, {"status": "ok", "likes": given}, data
    if st in (1, 2):                               # লাইক 0 / status 2 = লিমিট শেষ
        return name, {"status": "quota", "likes": 0}, data
    return name, {"status": "error", "likes": 0,
                  "error": str(data.get("error") or f"status {st}")[:60]}, data

# ── API হেলথ: টানা API_MAX_FAILS বার ফেল করলে ওই দিনের জন্য API বন্ধ (BD সময় ১২টায় রিসেট) ──
API_MAX_FAILS = 0        # 0 = অটো-বন্ধ সিস্টেম OFF (আগের মতো সব API সবসময় চলবে) | 4 = টানা ৪ বার ফেলে সেদিনের জন্য বন্ধ
FILE_API_HEALTH = "api_health.json"
API_QUOTA_STRIKES = 1    # এতগুলো আলাদা UID-তে (লাইক দিতে না পেরে, অথচ পরের API দিতে পেরেছে) → API-র আজকের মেয়াদ শেষ ধরে বন্ধ। ১ = সঙ্গে সঙ্গে বন্ধ
_BOT_REF = None          # post_init-এ বসে — মালিককে নোটিশ পাঠাতে
_api_health = load_json(FILE_API_HEALTH, {"date": "", "fails": {}, "disabled": [], "quota": {}})
if not isinstance(_api_health, dict): _api_health = {"date": "", "fails": {}, "disabled": [], "quota": {}}
_api_health.setdefault("fails", {}); _api_health.setdefault("disabled", []); _api_health.setdefault("quota", {})

def _health_roll():
    """নতুন দিন শুরু হলে সব API আবার চালু।"""
    t = today_str()
    if _api_health.get("date") != t:
        _api_health.update({"date": t, "fails": {}, "disabled": [], "quota": {}})
        save_json(FILE_API_HEALTH, _api_health)

def api_disabled(name):
    _health_roll()
    return name in _api_health["disabled"]

def active_apis():
    return [a for a in APIS if not api_disabled(a["name"])]

def api_record(name, ok):
    """সফল হলে কাউন্টার ০; ফেল হলে +১, টানা ৪ বার হলে আজকের জন্য বন্ধ।"""
    if API_MAX_FAILS <= 0: return
    _health_roll()
    if ok:
        if _api_health["fails"].get(name): 
            _api_health["fails"][name] = 0
            save_json(FILE_API_HEALTH, _api_health)
        return
    n = _api_health["fails"].get(name, 0) + 1
    _api_health["fails"][name] = n
    if n >= API_MAX_FAILS and name not in _api_health["disabled"]:
        _api_health["disabled"].append(name)
        logger.warning(f"{name} disabled for today after {n} consecutive failures")
    save_json(FILE_API_HEALTH, _api_health)

def _notify_owner(text):
    """মালিকের ইনবক্সে নোটিশ (ব্যাকগ্রাউন্ডে, লাইক আটকায় না)।"""
    if _BOT_REF is None: return
    async def _send():
        for oid in OWNER_IDS:
            try: await _BOT_REF.send_message(oid, text)
            except Exception as e: logger.warning(f"notify owner {oid}: {e.__class__.__name__}")
    try: asyncio.get_running_loop().create_task(_send())
    except RuntimeError: pass

def api_quota_clear(name):
    if _api_health["quota"].pop(name, None) is not None:
        save_json(FILE_API_HEALTH, _api_health)

def api_quota_hit(name, uid):
    """API লাইক দিতে পারেনি অথচ পরের API দিয়েছে। আলাদা আলাদা UID-তে API_QUOTA_STRIKES বার হলে
       ধরে নেওয়া হয় ওই API-র আজকের মেয়াদ শেষ → আজকের জন্য বন্ধ + মালিককে নোটিশ।"""
    _health_roll()
    if name in _api_health["disabled"]: return
    if _api_liked.get((name, str(uid))) == today_str(): return   # আজ এই UID-তে নিজেই দিয়েছে → UID-র লিমিট, API বন্ধ নয়
    q = _api_health["quota"].setdefault(name, [])
    if str(uid) not in q: q.append(str(uid))
    if len(q) >= API_QUOTA_STRIKES:
        _api_health["disabled"].append(name)
        _api_health["quota"].pop(name, None)
        logger.warning(f"{name} disabled for today (daily limit finished)")
        left = [a["name"] for a in APIS if a["name"] not in _api_health["disabled"]]
        _notify_owner(
            f"⚠️ {name} — আজকের লাইক লিমিট শেষ!\n"
            f"এই API আজকের জন্য বন্ধ করা হলো (রাত ১২টায় (BD) আবার চালু হবে)।\n"
            f"✅ এখন চালু: {', '.join(left) if left else 'কোনো API নেই!'}\n"
            f"♻️ জোর করে চালু করতে: /apireset {name[-1]}")
    save_json(FILE_API_HEALTH, _api_health)

def api_reset(name=None):
    _health_roll()
    if name is None:
        _api_health.update({"fails": {}, "disabled": [], "quota": {}})
    else:
        _api_health["fails"].pop(name, None); _api_health["quota"].pop(name, None)
        if name in _api_health["disabled"]: _api_health["disabled"].remove(name)
    save_json(FILE_API_HEALTH, _api_health)

async def call_api_with_fallback(region, uid):
    """র‍্যান্ডম ক্রমে চেষ্টা: যেকোনো একটা API আগে, ফেল হলে পরেরটা (বাকি চালু API-গুলো থেকে)।
       প্রথম যে API লাইক দেবে সেখানেই থামবে। কোনো API টানা ৪ বার লাইক দিতে
       না পারলে ওই দিনের জন্য সেটা বন্ধ — আর ব্যবহার হবে না।"""
    if not APIS:
        return {"error": "No API configured in .env"}

    ck = (region, str(uid))
    if _quota_cache.get(ck, 0) > _time.time():
        return {"status": 2, "cached": True,
                "per_api": {a["name"]: {"status": "quota", "likes": 0} for a in APIS}}

    enabled = active_apis()
    if not enabled:
        return {"error": "All APIs are disabled for today. Resets 12 AM (BD).",
                "per_api": {a["name"]: {"status": "disabled", "likes": 0} for a in APIS}}

    session = get_api_session()
    _now = _time.time()
    # কিছুক্ষণ আগে ডাউন থাকা API স্কিপ (সবগুলো ডাউন হলে সবই চেষ্টা)
    live = [a for a in enabled if _api_down.get(a["name"], 0) <= _now] or list(enabled)

    # আজ এই UID-তে যে API আগেই "লিমিট" দিয়েছে তাকে আবার ডাকা হয় না (সময় বাঁচে)
    _t = today_str()
    if len(_uid_quota) > 5000:
        for k in [k for k, v in _uid_quota.items() if v != _t]: _uid_quota.pop(k, None)
    tryable = [a for a in live if _uid_quota.get((a["name"], str(uid))) != _t]
    if not tryable:
        return {"status": 2, "per_api": {a["name"]: {"status": "quota", "likes": 0} for a in APIS}}

    random.shuffle(tryable)            # চারটা API-র মধ্যে র‍্যান্ডম ক্রমে — লোড ভাগ হয়
    per_api = {}
    winner = None
    running = {}                       # task -> api
    queue = list(tryable)

    def _start_next():
        api = queue.pop(0)
        t = asyncio.create_task(_call_one_api(session, api, region, uid))
        running[t] = api

    try:
        _start_next()
        while running and winner is None:
            # চলমান API সাড়া না দিলে HEDGE_SECS পর পরের API-ও শুরু (থাকলে); নইলে শেষ অপেক্ষা
            wait_t = HEDGE_SECS if queue else None
            done, _ = await asyncio.wait(list(running), timeout=wait_t, return_when=asyncio.FIRST_COMPLETED)
            if not done:
                _start_next(); continue
            for t in done:
                api = running.pop(t)
                try:
                    name, info, data = t.result()
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    name = api["name"]
                    info, data = {"status": "error", "likes": 0, "error": e.__class__.__name__}, None
                per_api[name] = info
                if info["status"] == "quota":
                    _uid_quota[(name, str(uid))] = _t
                if info["status"] == "ok" and winner is None:
                    winner = (name, info, data)
            if winner is None and not running and queue:
                _start_next()          # ফেল হয়েছে → সঙ্গে সঙ্গে পরের API, অপেক্ষা ছাড়া
    finally:
        for t in running:              # বাকি চলমান রিকোয়েস্ট বাতিল
            t.cancel()
        if running:
            await asyncio.gather(*running, return_exceptions=True)

    # হেলথ আপডেট: error সবসময় ফেল গোনা হয়। quota শুধু তখনই ফেল যখন পরের API লাইক দিতে পেরেছে
    # (সব API quota দিলে বুঝতে হবে UID-র নিজের লিমিট শেষ — API-র দোষ নয়)।
    for name, info in per_api.items():
        if info["status"] == "ok":
            api_record(name, True); api_quota_clear(name); _api_liked[(name, str(uid))] = today_str()
        elif info["status"] == "error": api_record(name, False)
        elif info["status"] == "quota" and winner: api_quota_hit(name, uid)

    for other in APIS:
        if api_disabled(other["name"]) and other["name"] not in per_api:
            per_api[other["name"]] = {"status": "disabled", "likes": 0}
        elif other not in live and other["name"] not in per_api:   # ডাউন থাকায় স্কিপ
            per_api[other["name"]] = {"status": "error", "likes": 0, "error": "temporarily down"}
        per_api.setdefault(other["name"], {"status": "skipped", "likes": 0})

    if winner:
        name, info, data = winner
        return {
            "status": 1, "used_api": name,
            "PlayerNickname": data.get("PlayerNickname") or "Unknown",
            "UID": data.get("UID", uid), "Region": region,
            "LikesbeforeCommand": _to_int(data.get("LikesbeforeCommand")),
            "LikesafterCommand": _to_int(data.get("LikesafterCommand")),
            "LikesGivenByAPI": info["likes"], "per_api": per_api,
        }

    if any(v["status"] == "quota" for v in per_api.values()):
        if all(v["status"] in ("quota", "disabled") for v in per_api.values()):
            _quota_cache[ck] = _time.time() + QUOTA_TTL
        return {"status": 2, "per_api": per_api}
    return {"error": "All API servers are having issues. Please try again in a moment.", "per_api": per_api}

# ══════════════════════════════════════════════════
async def call_all_four_apis(region, uid):
    """Auto Like: call every configured API and aggregate successful likes."""
    apis = active_apis()
    if not apis:
        return {"error": "No active API (all disabled for today or not configured)."}

    async def one(session, api):
        name = api["name"]
        try:
            async with session.get(
                f"{api['url']}like",
                params={"key": api["key"], "uid": uid, "server_name": region},
                timeout=aiohttp.ClientTimeout(total=15, connect=5),
            ) as resp:
                if resp.status != 200:
                    return name, {"status": "error", "likes": 0, "error": f"HTTP {resp.status}"}, None
                data = await resp.json(content_type=None)
            if not isinstance(data, dict):
                return name, {"status": "error", "likes": 0, "error": "bad response"}, None
            status = _to_int(data.get("status"))
            given = _to_int(data.get("LikesGivenByAPI"))
            if status == 1 and given > 0:
                return name, {"status": "ok", "likes": given}, data
            if status in (1, 2):
                return name, {"status": "quota", "likes": 0}, data
            return name, {"status": "error", "likes": 0,
                          "error": str(data.get("error") or f"status {status}")[:60]}, data
        except asyncio.TimeoutError:
            return name, {"status": "error", "likes": 0, "error": "timeout"}, None
        except Exception as exc:
            logger.warning("%s auto API failed: %s", name, exc.__class__.__name__)
            return name, {"status": "error", "likes": 0, "error": exc.__class__.__name__}, None

    session = get_api_session()
    results = await asyncio.gather(*(one(session, api) for api in apis))

    per_api = {name: info for name, info, _ in results}
    successes = [(name, data, info["likes"]) for name, info, data in results
                 if info.get("status") == "ok" and data]
    if not successes:
        if any(info.get("status") == "quota" for info in per_api.values()):
            return {"status": 2, "per_api": per_api}
        return {"error": "All Like API servers are unavailable.", "per_api": per_api}

    first = successes[0][1]
    total_given = sum(item[2] for item in successes)
    before = _to_int(first.get("LikesbeforeCommand"))
    return {
        "status": 1, "used_api": ", ".join(item[0] for item in successes),
        "PlayerNickname": first.get("PlayerNickname") or "Unknown",
        "UID": first.get("UID", uid), "Region": region,
        "LikesbeforeCommand": before, "LikesafterCommand": before + total_given,
        "LikesGivenByAPI": total_given, "per_api": per_api,
    }

#  UI HELPERS
# ══════════════════════════════════════════════════
async def reply(update, text, **kw):
    try:
        await update.effective_message.reply_text(
            text, parse_mode=ParseMode.MARKDOWN,
            link_preview_options=LinkPreviewOptions(is_disabled=True), **kw)
    except Exception:
        try: await update.effective_message.reply_text(text, **kw)
        except Exception as e: logger.error(f"reply: {e}")

async def react(update, emoji="🎉"):
    try:
        await update.effective_message.set_reaction(reaction=[ReactionTypeEmoji(emoji=emoji)])
    except: pass

# ══════════════════════════════════════════════════
#  FORMATTERS
# ══════════════════════════════════════════════════
def fmt_success(used_api, player, uid, region, before, given, after, per_api=None):
    per_api = per_api or {}
    api_lines = []
    for api in APIS:
        name = api["name"]
        info = per_api.get(name, {"status": "off", "likes": 0})
        st = info.get("status")
        likes = info.get("likes", 0)
        if st == "ok":
            api_lines.append(f"`{name}` = *{likes}* ✅")
        elif st == "quota":
            api_lines.append(f"`{name}` = *0* ⏰")
        elif st == "error":
            api_lines.append(f"`{name}` = *0* ❌")
        elif st == "skipped":
            api_lines.append(f"`{name}` = *skip* ⚪")
        elif st == "disabled":
            api_lines.append(f"`{name}` = *off today* 🚫")
        elif st == "empty":
            api_lines.append(f"`{name}` = *0* ⚪")
        else:
            api_lines.append(f"`{name}` = *0* ⚪")
    api_block = "\n".join(api_lines)
    return (
        f"✅ *𝗟𝗜𝗞𝗘𝗦 𝗦𝗘𝗡𝗧 𝗦𝗨𝗖𝗖𝗘𝗦𝗦𝗙𝗨𝗟𝗟𝗬*\n{LINE}\n"
        f"🔌 𝗨𝘀𝗲𝗱 𝗔𝗣𝗜 : *{used_api}*\n"
        f"👤 𝗡𝗔𝗠𝗘 : *{md_escape(player)}*\n"
        f"🆔 𝗨𝗜𝗗 : `{uid}`\n"
        f"🌐 𝗦𝗘𝗥𝗩𝗘𝗥 : *{region.upper()}*\n{LINE}\n"
        f"📊 𝗕𝗘𝗙𝗢𝗥𝗘 : *{before}*\n"
        f"💎 𝗔𝗗𝗗𝗘𝗗 : *+{given}*\n"
        f"🔥 𝗔𝗙𝗧𝗘𝗥 : *{after}*\n{LINE}\n"
        f"🔢 *𝗔𝗣𝗜 𝗕𝗥𝗘𝗔𝗞𝗗𝗢𝗪𝗡*\n{api_block}\n{LINE}"
    )

def limit_footer(uid, is_100=False):
    """লাইক সাকসেস মেসেজের নিচে ইউজারের ডেইলি লিমিট (এডমিন = ∞ Unlimited)"""
    lim = get_100_limit(uid) if is_100 else get_pub_limit(uid)
    used = get_100_used(uid) if is_100 else get_pub_used(uid)
    if lim >= 999999:
        return (f"👑 *𝗬𝗢𝗨𝗥 𝗟𝗜𝗠𝗜𝗧* : ♾ *∞ 𝗨𝗡𝗟𝗜𝗠𝗜𝗧𝗘𝗗*\n"
                f"▰▰▰▰▰▰▰▰▰▰  ✨ _Owner access_\n{LINE}")
    left = max(0, lim - used)
    n = 10
    filled = n if lim <= 0 else min(n, round(n * min(used, lim) / lim))
    bar = "▰" * filled + "▱" * (n - filled)
    tail = ("🔒 _Limit finished — resets 12 AM (BD)_" if left == 0
            else "🛍 _Need more? /myshop → buy +1 limit_")
    return (f"🎫 *𝗬𝗢𝗨𝗥 𝗗𝗔𝗜𝗟𝗬 𝗟𝗜𝗠𝗜𝗧*\n"
            f"📊 𝗨𝘀𝗲𝗱 : *{used}*  │  ⏳ 𝗟𝗲𝗳𝘁 : *{left}*  │  🎯 𝗧𝗼𝘁𝗮𝗹 : *{lim}*\n"
            f"{bar}\n{tail}\n{LINE}")

def fmt_already():
    return (f"⏰ *𝗔𝗣𝗜 𝗟𝗜𝗠𝗜𝗧 𝗥𝗘𝗔𝗖𝗛𝗘𝗗*\n{LINE}\n"
            f"🕐 𝗡𝗘𝗫𝗧 𝗥𝗘𝗦𝗘𝗧 : *{next_reset_str()}*\n{LINE}\n"
            f"💡 𝗧𝗿𝘆 𝗮𝗴𝗮𝗶𝗻 𝗮𝗳𝘁𝗲𝗿 𝗿𝗲𝘀𝗲𝘁 (BD 12 AM)")

def fmt_error(msg):
    return f"❌ *𝗘𝗥𝗥𝗢𝗥*\n{LINE}\n{msg}"

# ══════════════════════════════════════════════════
#  🎨 /START
# ══════════════════════════════════════════════════
def start_design(name, chat_type, uid):
    is_admin_user = is_admin(uid)
    l100 = get_100_limit(uid); u100 = get_100_used(uid)
    lpub = get_pub_limit(uid); upub = get_pub_used(uid)
    is_vip100 = str(uid) in like100["vip"]
    is_vippub = str(uid) in public["vip"]
    vip100_tag = "💠 𝗩𝗜𝗣" if is_vip100 else ""
    vippub_tag = "💠 𝗩𝗜𝗣" if is_vippub else ""

    if chat_type != "private" and not is_admin_user:
        return (
            f"✨ 𝗠𝗘𝗗𝗨𝗦𝗔 𝗟𝗜𝗞𝗘 𝗕𝗢𝗧 ✨\n{LINE}\n"
            f"🌐 `/like <uid>` – BD only\n"
            f"🌐 `/like <region> <uid>` – any region\n"
            f"🌐 `/like <uid> <region>` – any region\n"
            f"📌 Regions: `{' '.join(sorted(ALLOWED_REGIONS))}`\n"
            f"📌 Example: `/like bd 11214489525`\n{LINE}\n"
            f"📊 `/myinfo` – Your limit\n"
            f"🆔 `/id` – Group ID\n{LINE}\n"
            f"👇 Tap the button below to add the bot"
        )

    if is_admin_user:
        return (
            f"👑 𝗔𝗗𝗠𝗜𝗡 𝗖𝗢𝗡𝗧𝗥𝗢𝗟 𝗣𝗔𝗡𝗘𝗟 👑\n{LINE}\n"
            f"👋 স্বাগতম, *{name}*\n\n"
            f"🔌 *APIs Loaded* : `{len(APIS)}/4`\n"
            f"📸 *Like Photo* : {'✅ Set' if photo_state.get('file_id') else '❌ Not set'}\n"
            f"🚫 *Blocked Groups* : `{len(blocked_groups)}`\n\n"
            f"💎 *Premium-Like* : `{like100['config']['status'].upper()}` | "
            f"lim=`{like100['config']['limit']}`\n"
            f"🌐 *Public* : `{public['config']['status'].upper()}` | "
            f"lim=`{public['config']['limit']}`\n{LINE}\n"
            f"📋 /help – সব কমান্ড\n"
            f"⚙️ /admin – প্যানেল"
        )

    return (
        f"🐍 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗠𝗘𝗗𝗨𝗦𝗔 𝗟𝗜𝗞𝗘 𝗕𝗢𝗧 🐍\n{LINE}\n"
        f"❤️ *Welcome, Free Fire Players!*\n\n"
        f"🔥 Join our Official Group to get free Likes on your Free Fire ID and "
        f"exchange Likes with other players.\n\n"
        f"💎 *𝗠𝗘𝗗𝗨𝗦𝗔 𝗟𝗜𝗞𝗘 𝗚𝗥𝗢𝗨𝗣*\n"
        f"🎁 Free Like Community\n"
        f"⚡ Easy & Fast Like Service\n"
        f"🤝 Friendly Gaming Community\n\n"
        f"👇 *𝗝𝗢𝗜𝗡 𝗢𝗨𝗥 𝗢𝗙𝗙𝗜𝗖𝗜𝗔𝗟 𝗚𝗥𝗢𝗨𝗣 𝗡𝗢𝗪* 👇\n"
        f"🔗 [t.me/MEDUSA LIKE](https://t.me/MEDUSA_LIKE)\n{LINE}\n"
        f"👋 Hello, *{name}*\n\n"
        f"💎 *𝗣𝗿𝗲𝗺𝗶𝘂𝗺-𝗟𝗶𝗸𝗲 (𝗕𝗗)* {vip100_tag}\n"
        f"   `/premium <uid>`\n"
        f"   📅 {u100}/{l100 if l100<999999 else '∞'}\n\n"
        f"🌐 *𝗣𝘂𝗯𝗹𝗶𝗰-𝗟𝗶𝗸𝗲 (𝗕𝗗)* {vippub_tag}\n"
        f"   `/like <uid>`  → BD\n"
        f"   `/like <region> <uid>`  → any region\n"
        f"   `/like <uid> <region>`  → any region\n"
        f"   📅 {upub}/{lpub if lpub<999999 else '∞'}\n{LINE}\n"
        f"📖 `/help` – Full guide\n"
        f"🎁 `/myrefer` – Referral link & profile\n"
        f"🛍 `/myshop` – Premium MyShop\n"
        f"🏆 `/leaderboard` – Referral leaderboard\n"
        f"📊 `/myinfo` – Your limit\n"
        f"🆔 `/id` – Group/User ID\n{LINE}\n"
        f"🎨 *Want to build your own bot?* Tap the button below 👇\n{LINE}\n"
        f"❤️ *𝗧𝗛𝗔𝗡𝗞 𝗬𝗢𝗨 𝗙𝗢𝗥 𝗨𝗦𝗜𝗡𝗚 𝗠𝗘𝗗𝗨𝗦𝗔 𝗕𝗢𝗧!* 🐍"
    )

def start_keyboard():
    row0 = [cbtn("💎 ᴊᴏɪɴ ᴍᴇᴅᴜꜱᴀ ʟɪᴋᴇ ɢʀᴏᴜᴘ", "success", url="https://t.me/MEDUSA_LIKE")]
    row1 = [
        cbtn("🤖 ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ ʙᴏᴛ", "primary", url="https://t.me/HAFSAN_KUN"),
    ]
    return InlineKeyboardMarkup([row0, row1])

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name or "User"
    chat_type = update.effective_chat.type

    if chat_type == "private" and context.args and context.args[0].startswith("ref_"):
        refer_register(update.effective_user, context.args[0])

    if chat_type == "private" and not is_admin(uid):
        missing = await get_missing_joins(context.bot, uid)
        if missing:
            await update.message.reply_text(
                f"🔒 *𝗝𝗢𝗜𝗡 𝗥𝗘𝗤𝗨𝗜𝗥𝗘𝗗*\n{LINE}\n"
                f"To use this bot, please join the groups/channels below\n"
                f"and then send `/start` again.\n\n👇",
                parse_mode=ParseMode.MARKDOWN, reply_markup=pub_join_keyboard(missing)
            ); return
        await refer_credit(context, update.effective_user)

    if chat_type == "private" and context.args and context.args[0].startswith("shop_auto"):
        payload = context.args[0].split("_")
        context.user_data["auto_days"] = int(payload[2]) if len(payload) > 2 and payload[2].isdigit() else None
        await shop_auto_start(update, context); return

    text = start_design(name, chat_type, uid)
    await reply(update, text, reply_markup=start_keyboard())

# ══════════════════════════════════════════════════
#  📖 /HELP (Full Guide)
# ══════════════════════════════════════════════════
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lines = [
        f"📖 𝗖𝗢𝗠𝗠𝗔𝗡𝗗 𝗚𝗨𝗜𝗗𝗘 📖", LINE, "",
        "👤 *𝗨𝘀𝗲𝗿 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀*", LINE,
        "`/start` – Welcome message",
        "`/help` – This guide",
        "`/myrefer` – Referral link, coins & 🛍 MyShop 🎁",
        "`/myshop` – 🛍 Open MyShop directly (premium store)",
        "`/leaderboard` – Referral leaderboard 🏆",
        "`/myinfo` – Your limit",
        "`/like (uid)` – Public like (BD)",
        "`/like (region) (uid)` – Specific region",
        "`/like (uid) (region)` – Specific region",
        "`/premium (uid)` – Premium likes (BD)",
        "`/max <uid>` – MAX Like (শুধু Owner চালু করলে)",
        "`/id` – Group/User ID",
        "`/tg_id` – Reply to a message to get that user's ID",
        "`/top` – Today's top like users",
        "",
        "🌐 *𝗦𝘂𝗽𝗽𝗼𝗿𝘁𝗲𝗱 𝗥𝗲𝗴𝗶𝗼𝗻𝘀*", LINE,
        "`bd ind pk sg id br us ru th vn tw me cis`",
        "",
        "💡 *𝗟𝗶𝗸𝗲 𝗥𝘂𝗹𝗲𝘀*", LINE,
        "• `/like <uid>` → BD server only",
        "• Other servers only work when a region is given",
        "• 🎉 reaction on success",
        "• 😐 reaction when your limit is reached",
        "• Resets daily at 12 AM (BD time)",
        "• 4 APIs are tried in order",
        "• The first one that succeeds is used",
        "",
    ]
    owner = is_owner(uid)
    if is_admin(uid):
        lines += [
            "👑 *𝗔𝗱𝗺𝗶𝗻 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀*", LINE,
            "",
            "🎁 *𝗥𝗲𝗳𝗲𝗿*", LINE,
            "`/all_user_refer` – সবার রেফার লিস্ট (ইনবক্সে)",
            "`/med_x (id) (n)` – রেফার সেট | `+n` বাড়াও | `-n` কমাও",
            "",
            "📸 *𝗣𝗵𝗼𝘁𝗼*", LINE,
            "`/set_photo_like_ms` – লাইক মেসেজে ছবি",
            "`/remove_photo` – ছবি সরাও",
            "",
            "💎 *𝗣𝗿𝗲𝗺𝗶𝘂𝗺-𝗟𝗶𝗸𝗲 𝗔𝗱𝗺𝗶𝗻*", LINE,
            "`/premium_bot_open` – Premium চালু",
            "`/premium_bot_off` – Premium বন্ধ",
            ] + (["`/max_like_on` – MAX Like চালু + status pin", "`/max_like_off` – MAX Like বন্ধ + status pin"] if owner else []) + (["`/premium_allow` – গ্রুপ allowed"] if owner else []) + [
            "`/setlimit_premium (n)` – লিমিট সেট",
            "",
            "🌐 *𝗣𝘂𝗯𝗹𝗶𝗰 𝗔𝗱𝗺𝗶𝗻*", LINE,
            "`/public_bot_on` – চালু",
            "`/public_bot_off` – বন্ধ",
            ] + (["`/public_bot_allow` – গ্রুপ allowed"] if owner else []) + [
            "`/setlimitpub (n)` – লিমিট সেট",
            "`/public_mode public|private` – যেকোনো গ্রুপে / শুধু allowed গ্রুপে",
            "`/groups` – বট যেসব গ্রুপে আছে",
            "",
            ] + ([
            "🛡 *𝗙𝗼𝗿𝗰𝗲-𝗝𝗼𝗶𝗻*", LINE,
            "`/add_group @username` – গ্রুপ যোগ",
            "`/ban_add_group @username` – গ্রুপ সরাও",
            "`/add_channel @username` – চ্যানেল যোগ",
            "`/ban_add_channel @username` – চ্যানেল সরাও",
            ""] if owner else []) + [
            "💎 *𝗩𝗜𝗣 𝗦𝘆𝘀𝘁𝗲𝗺*", LINE,
            "`/VIP (id) (limit)` – VIP + daily limit",
            "`/banvip (id)` – VIP সরাও",
            "`/vip_list` – সব VIP দেখাও",
            "",
            "⛔ *𝗨𝘀𝗲𝗿 𝗕𝗮𝗻*", LINE,
            "`/ban_user (id)` – ইউজার ব্যান (রিপ্লাই দিয়েও হয়)",
            "`/unban_user (id)` – আনব্যান",
            "",
            ] + ([
            "🚫 *𝗚𝗿𝗼𝘂𝗽 𝗕𝗹𝗼𝗰𝗸*", LINE,
            "`/Bend_group` – গ্রুপ ব্লক",
            "`/Bend_group_id (id)` – আইডি দিয়ে ব্লক",
            "`/Unblock_group_id (id)` – আনব্লক",
            ""] if owner else []) + [
            "`/blocked_groups` – ব্লকড লিস্ট",
            "",
            "🔇 *𝗠𝘂𝘁𝗲*", LINE,
            "`/like_bot_mute` – এই গ্রুপে বট চুপ (মেসেজ/রিয়্যাকশন কিছুই না)",
            "`/like_bot_unmute` – আবার চালু",
            "`/muted_groups` – মিউট গ্রুপ লিস্ট",
            "",
            "📊 *𝗦𝘁𝗮𝘁𝘀 & 𝗠𝗶𝘀𝗰*", LINE,
            "`/admin` – কন্ট্রোল প্যানেল",
            "`/stats` – আজকের stats",
            "`/user_like` – আজকের সব ইউজার",
            "`/api` – API স্ট্যাটাস",
            "`/api_check` – API সার্ভার লাইভ চেক",
            "`/backup` – ডাটা ফাইল ব্যাকআপ (ইনবক্সে)",
            "`/broadcast` – সব গ্রুপে পাঠাও",
            "`/cancel` – বাতিল",
        ]
        
    lines.append(LINE)
    lines.append("💡 *4 APIs are tried in order*")
    
    try:
        await reply(update, "\n".join(lines))
    except Exception as e:
        logger.error(f"Help command error: {e}")
        await update.effective_message.reply_text("\n".join(lines))

# ══════════════════════════════════════════════════
#  📸 PHOTO
# ══════════════════════════════════════════════════
async def set_photo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid): await reply(update, "⛔ Admin only."); return
    msg = update.effective_message
    target = None
    if msg.reply_to_message and msg.reply_to_message.photo:
        target = msg.reply_to_message.photo[-1].file_id
    elif msg.photo:
        target = msg.photo[-1].file_id
    elif msg.reply_to_message and msg.reply_to_message.document:
        if (msg.reply_to_message.document.mime_type or "").startswith("image/"):
            target = msg.reply_to_message.document.file_id
    if not target:
        await reply(update,
            f"📸 *𝗦𝗘𝗧 𝗟𝗜𝗞𝗘 𝗣𝗛𝗢𝗧𝗢*\n{LINE}\n"
            f"❌ ছবি পাওয়া যায়নি।\n\n"
            f"📌 দুইভাবে সেট করুন:\n"
            f"1️⃣ ছবির caption-এ `/set_photo_like_ms`\n"
            f"2️⃣ ছবিতে reply দিয়ে কমান্ড")
        return
    photo_state["file_id"] = target
    photo_state["set_by"] = uid
    photo_state["date"] = today_str()
    save_photo()
    await reply(update,
        f"✅ *𝗟𝗜𝗞𝗘 𝗣𝗛𝗢𝗧𝗢 𝗦𝗘𝗧*\n{LINE}\n"
        f"📸 File ID: `{target[:24]}…`\n"
        f"👤 Set by: `{uid}`\n"
        f"📅 Date: `{today_str()}`\n{LINE}\n"
        f"সরাতে: `/remove_photo`")

async def remove_photo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await reply(update, "⛔ Admin only."); return
    old = photo_state.get("file_id")
    photo_state["file_id"] = None
    save_photo()
    await reply(update, f"🗑 *𝗣𝗛𝗢𝗧𝗢 𝗥𝗘𝗠𝗢𝗩𝗘𝗗*\n{LINE}\n"
                        f"{'ছবি সরানো হয়েছে।' if old else 'কোনো ছবি সেট ছিল না।'}")

# ══════════════════════════════════════════════════
#  🆔 /id
# ══════════════════════════════════════════════════
async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    if chat.type == "private":
        text = (f"🆔 *𝗜𝗗 𝗜𝗡𝗙𝗢*\n{LINE}\n"
                f"👤 *Your User ID* : `{user.id}`\n"
                f"📛 *Name* : {user.full_name}\n"
                f"🔗 *Username* : {'@'+user.username if user.username else '—'}\n"
                f"💬 *Chat Type* : Private\n{LINE}")
        if msg.reply_to_message and msg.reply_to_message.from_user:
            t = msg.reply_to_message.from_user
            text += (f"\n👤 *Replied User ID* : `{t.id}`\n"
                     f"📛 *Name* : {t.full_name}\n"
                     f"🔗 *Username* : {'@'+t.username if t.username else '—'}\n")
    else:
        blocked = " 🚫 BLOCKED" if is_group_blocked(chat.id) else ""
        text = (f"🆔 *𝗚𝗥𝗢𝗨𝗣 𝗜𝗗{blocked}*\n{LINE}\n"
                f"📛 *Name* : {chat.title}\n"
                f"🆔 *Chat ID* : `{chat.id}`\n"
                f"🔗 *Username* : {'@'+chat.username if chat.username else '—'}\n"
                f"💬 *Type* : {chat.type}\n"
                f"👤 *Your ID* : `{user.id}`\n{LINE}")
        if msg.reply_to_message and msg.reply_to_message.from_user:
            t = msg.reply_to_message.from_user
            text += (f"\n👤 *Replied User ID* : `{t.id}`\n"
                     f"📛 *Name* : {t.full_name}\n"
                     f"🔗 *Username* : {'@'+t.username if t.username else '—'}\n")
    await reply(update, text)

async def tg_id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg: return
    target = msg.reply_to_message
    if target is None:
        u = update.effective_user
        await reply(update, f"🆔 *𝗬𝗢𝗨𝗥 𝗜𝗗*\n{LINE}\n👤 {u.full_name}\n🆔 `{u.id}`")
        return
    u = target.from_user
    if not u:
        await reply(update, "❌ Couldn't find an ID for this message."); return
    await reply(update, f"🆔 *𝗨𝗦𝗘𝗥 𝗜𝗗*\n{LINE}\n👤 {u.full_name}\n🆔 `{u.id}`")

# ══════════════════════════════════════════════════
#  🚫 BLOCK GROUP
# ══════════════════════════════════════════════════
@owner_only
async def bend_group_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        await reply(update, "❌ গ্রুপে ব্যবহার করুন।"); return
    gid = str(chat.id)
    if gid in blocked_groups:
        await reply(update, "⚠️ ইতিমধ্যে ব্লকড।"); return
    blocked_groups[gid] = {
        "name": chat.title or gid,
        "username": f"@{chat.username}" if chat.username else None,
        "by": update.effective_user.id, "date": today_str()
    }
    save_blocked()
    await reply(update, f"🚫 *𝗚𝗥𝗢𝗨𝗣 𝗕𝗟𝗢𝗖𝗞𝗘𝗗*\n{LINE}\n"
                        f"📛 {chat.title}\n🆔 `{gid}`\n{LINE}\n"
                        f"আনব্লক: `/Unblock_group_id {gid}`")

@owner_only
async def bend_group_id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        await reply(update, "❌ ইনবক্সে ব্যবহার করুন।"); return
    if len(context.args) != 1:
        await reply(update, "❌ `/Bend_group_id <id>`"); return
    try: gid = str(int(context.args[0].strip()))
    except ValueError: await reply(update, "❌ সংখ্যা দিন।"); return
    if gid in blocked_groups:
        await reply(update, f"⚠️ `{gid}` ইতিমধ্যে ব্লকড।"); return
    name = gid; username = None
    try:
        chat = await context.bot.get_chat(int(gid))
        name = chat.title or gid
        username = f"@{chat.username}" if chat.username else None
    except: pass
    blocked_groups[gid] = {"name": name, "username": username,
                           "by": update.effective_user.id, "date": today_str()}
    save_blocked()
    await reply(update, f"🚫 *𝗚𝗥𝗢𝗨𝗣 𝗕𝗟𝗢𝗖𝗞𝗘𝗗*\n{LINE}\n"
                        f"📛 {name}\n🆔 `{gid}`\n🔗 {username or '—'}\n{LINE}")

@owner_only
async def unblock_group_id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await reply(update, "❌ `/Unblock_group_id <id>`"); return
    try: gid = str(int(context.args[0].strip()))
    except ValueError: await reply(update, "❌ সংখ্যা দিন।"); return
    if gid not in blocked_groups:
        await reply(update, f"ℹ️ `{gid}` ব্লকড লিস্টে নেই।"); return
    info = blocked_groups.pop(gid); save_blocked()
    await reply(update, f"✅ *𝗚𝗥𝗢𝗨𝗣 𝗨𝗡𝗕𝗟𝗢𝗖𝗞𝗘𝗗*\n{LINE}\n"
                        f"📛 {info.get('name', gid)}\n🆔 `{gid}`\n{LINE}")

async def blocked_groups_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await reply(update, "⛔ Admin only."); return
    if not blocked_groups:
        await reply(update, f"📋 *𝗕𝗟𝗢𝗖𝗞𝗘𝗗*\n{LINE}\n✅ কোনো গ্রুপ নেই।"); return
    lines = [f"📋 *𝗕𝗟𝗢𝗖𝗞𝗘𝗗 𝗚𝗥𝗢𝗨𝗣𝗦* ({len(blocked_groups)})\n{LINE}"]
    for i, (gid, info) in enumerate(blocked_groups.items(), 1):
        lines.append(f"{i}. 🚫 *{info.get('name','?')}*\n"
                     f"   🆔 `{gid}`\n"
                     f"   🔗 {info.get('username') or '—'}\n"
                     f"   📅 {info.get('date','—')}\n")
    lines.append(LINE)
    lines.append("আনব্লক: `/Unblock_group_id <id>`")
    await reply(update, "\n".join(lines))

# ══════════════════════════════════════════════════
#  📊 /myinfo
# ══════════════════════════════════════════════════
@admin_only
async def apistatus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _health_roll()
    lines = [f"🔌 *𝗔𝗣𝗜 𝗦𝗧𝗔𝗧𝗨𝗦*\n{LINE}"]
    for a in APIS:
        n = a["name"]
        if n in _api_health["disabled"]:
            lines.append(f"`{n}` — 🚫 OFF today (লিমিট শেষ)")
        else:
            k = len(_api_health["quota"].get(n, []))
            extra = f" — ⚠️ strike {k}/{API_QUOTA_STRIKES}" if k else ""
            lines.append(f"`{n}` — 🟢 ON{extra}")
    lines.append(f"{LINE}\n♻️ `/apireset` – সব চালু | `/apireset 2` – শুধু API-2")
    await reply(update, "\n".join(lines))

@admin_only
async def apireset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and context.args[0].isdigit():
        api_reset(f"API-{context.args[0]}")
        await reply(update, f"♻️ API-{context.args[0]} আবার চালু করা হলো।")
    else:
        api_reset()
        await reply(update, "♻️ সব API আবার চালু করা হলো।")

async def myinfo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    l100, u100 = get_100_limit(uid), get_100_used(uid)
    lpub, upub = get_pub_limit(uid), get_pub_used(uid)
    tag100 = "👑 𝗔𝗗𝗠𝗜𝗡" if is_admin(uid) else ("💎 𝗩𝗜𝗣" if str(uid) in like100["vip"] else "🆓 𝗣𝗨𝗕𝗟𝗜𝗖")
    tagpub = "👑 𝗔𝗗𝗠𝗜𝗡" if is_admin(uid) else ("💎 𝗩𝗜𝗣" if str(uid) in public["vip"] else ("🚫 𝗕𝗔𝗡𝗡𝗘𝗗" if str(uid) in public["banned"] else "🆓 𝗣𝗨𝗕𝗟𝗜𝗖"))
    msg = (f"📊 *𝗬𝗢𝗨𝗥 𝗜𝗡𝗙𝗢*\n{LINE}\n"
           f"🆔 𝗨𝗜𝗗 : `{uid}`\n{LINE}\n"
           f"💎 *𝗣𝗿𝗲𝗺𝗶𝘂𝗺-𝗟𝗶𝗸𝗲* ({tag100})\n"
           f"  📅 𝗟𝗶𝗺𝗶𝘁 : *{l100 if l100<999999 else '∞'}*\n"
           f"  ✅ 𝗨𝘀𝗲𝗱 : *{u100}*\n"
           f"  🎯 𝗥𝗲𝗺𝗮𝗶𝗻 : *{max(0, l100-u100) if l100<999999 else '∞'}*\n{LINE}\n"
           f"🌐 *𝗣𝘂𝗯𝗹𝗶𝗰-𝗟𝗶𝗸𝗲* ({tagpub})\n"
           f"  📅 𝗟𝗶𝗺𝗶𝘁 : *{lpub if lpub<999999 else '∞'}*\n"
           f"  ✅ 𝗨𝘀𝗲𝗱 : *{upub}*\n"
           f"  🎯 𝗥𝗲𝗺𝗮𝗶𝗻 : *{max(0, lpub-upub) if lpub<999999 else '∞'}*\n{LINE}\n"
           f"⏰ 𝗥𝗲𝘀𝗲𝘁 : *{next_reset_str()}*")
    await reply(update, msg)

# ══════════════════════════════════════════════════
#  ══════════ /VIP & /banvip ══════════
# ══════════════════════════════════════════════════
async def vip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await reply(update, "⛔ Admin only."); return
    if len(context.args) != 2:
        await reply(update,
            f"💎 *𝗩𝗜𝗣 𝗦𝗘𝗧𝗨𝗣*\n{LINE}\n"
            f"📌 ব্যবহার:\n`/VIP <telegram_id> <limit>`\n\n"
            f"📝 উদাহরণ:\n"
            f"`/VIP 8433104172 5` → দিনে ৫ বার\n"
            f"`/VIP 8433104172 999999` → আনলিমিটেড\n{LINE}")
        return
    uid_str, limit_str = context.args
    if not uid_str.isdigit() or not limit_str.isdigit():
        await reply(update, "❌ দুটোই সংখ্যা হতে হবে।"); return
    uid = int(uid_str); limit = int(limit_str)
    like100["vip"][str(uid)] = {"per_day": limit, "by": update.effective_user.id, "date": today_str()}
    public["vip"][str(uid)] = {"per_day": limit, "by": update.effective_user.id, "date": today_str()}
    save_100(); save_pub()
    await reply(update,
        f"💎 *𝗩𝗜𝗣 𝗔𝗗𝗗𝗘𝗗*\n{LINE}\n"
        f"👤 User ID : `{uid}`\n"
        f"📅 Daily Limit : *{limit if limit < 999999 else '∞'}*\n"
        f"✅ এখন থেকে এই ইউজার দিনে "
        f"*{limit if limit < 999999 else 'আনলিমিটেড'}* বার লাইক নিতে পারবে।\n{LINE}\n"
        f"সরাতে: `/banvip {uid}`")

async def banvip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await reply(update, "⛔ Admin only."); return
    if len(context.args) != 1 or not context.args[0].isdigit():
        await reply(update, "❌ `/banvip <telegram_id>`"); return
    uid = int(context.args[0])
    removed = False
    if str(uid) in like100["vip"]:
        del like100["vip"][str(uid)]; removed = True
    if str(uid) in public["vip"]:
        del public["vip"][str(uid)]; removed = True
    if not removed:
        await reply(update, f"ℹ️ `{uid}` VIP লিস্টে নেই।"); return
    save_100(); save_pub()
    await reply(update,
        f"🚫 *𝗩𝗜𝗣 𝗥𝗘𝗠𝗢𝗩𝗘𝗗*\n{LINE}\n"
        f"👤 User ID : `{uid}`\n"
        f"❌ আর VIP হিসেবে থাকবে না।\n{LINE}")

async def vip_list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await reply(update, "⛔ Admin only."); return
    vips = set(list(like100["vip"].keys()) + list(public["vip"].keys()))
    if not vips:
        await reply(update, f"💎 *𝗩𝗜𝗣 𝗟𝗜𝗦𝗧*\n{LINE}\n❌ কোনো VIP নেই।"); return
    lines = [f"💎 *𝗩𝗜𝗣 𝗟𝗜𝗦𝗧* ({len(vips)})\n{LINE}"]
    for i, uid in enumerate(sorted(vips), 1):
        info = like100["vip"].get(uid) or public["vip"].get(uid, {})
        lim = info.get("per_day", "∞")
        lines.append(f"{i}. `{uid}` — {lim if (lim and lim < 999999) else '∞'}/day")
    lines.append(LINE)
    await reply(update, "\n".join(lines))

# ══════════════════════════════════════════════════
#  ══════════ FORCE-JOIN ADD/REMOVE ══════════
# ══════════════════════════════════════════════════
async def _resolve_chat(bot, uname):
    uname = uname.strip()
    if uname.startswith("https://t.me/"):
        uname = "@" + uname.split("https://t.me/")[-1].split("?")[0].strip("/")
    if not uname.startswith("@"):
        uname = "@" + uname
    return await bot.get_chat(uname)

@owner_only
async def add_group_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await reply(update, f"❌ *𝗨𝘀𝗮𝗴𝗲*\n`/add_group @username`"); return
    target = context.args[0]
    try:
        chat = await _resolve_chat(context.bot, target)
    except Exception as e:
        await reply(update, f"❌ চ্যাট পাওয়া যায়নি: `{e}`"); return
    if chat.type not in ("group", "supergroup"):
        await reply(update, "❌ এটি গ্রুপ নয়।"); return
    invite = chat.invite_link or (f"https://t.me/{chat.username}" if chat.username else None)
    if not invite:
        try:
            inv = await context.bot.create_chat_invite_link(chat.id)
            invite = inv.invite_link
        except Exception as e:
            await reply(update, f"❌ Invite link বানানো যায়নি: `{e}`\nবটকে admin করুন।"); return

    for g in public["force_join"]["groups"]:
        if g.get("chat_id") == chat.id:
            await reply(update, "ℹ️ এই গ্রুপ আগেই যোগ করা আছে।"); return
    public["force_join"]["groups"].append({
        "chat_id": chat.id, "title": chat.title,
        "invite_link": invite,
        "username": chat.username
    })
    save_pub()
    tail = f"সরাতে: `/ban_add_group @{chat.username}`" if chat.username else f"সরাতে: `/ban_add_group {chat.id}`"
    await reply(update,
        f"✅ *𝗚𝗥𝗢𝗨𝗣 𝗔𝗗𝗗𝗘𝗗*\n{LINE}\n"
        f"📛 {chat.title}\n🆔 `{chat.id}`\n"
        f"🔗 {invite}\n{LINE}\n"
        f"এখন ইউজারদের এই গ্রুপে join করতে হবে।\n{tail}")

@owner_only
async def ban_add_group_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await reply(update, "❌ `/ban_add_group @username`"); return
    raw = context.args[0].strip()
    removed = None
    if raw.lstrip("-").isdigit():
        cid = int(raw)
        for g in list(public["force_join"]["groups"]):
            if g.get("chat_id") == cid:
                public["force_join"]["groups"].remove(g); removed = g; break
    else:
        uname = raw.lower().lstrip("@")
        for g in list(public["force_join"]["groups"]):
            if (g.get("username") or "").lower() == uname:
                public["force_join"]["groups"].remove(g); removed = g; break
    if not removed:
        await reply(update, f"ℹ️ `{raw}` লিস্টে নেই।"); return
    save_pub()
    await reply(update,
        f"✅ *𝗚𝗥𝗢𝗨𝗣 𝗥𝗘𝗠𝗢𝗩𝗘𝗗*\n{LINE}\n"
        f"📛 {removed.get('title')}\n"
        f"🆔 `{removed.get('chat_id')}`\n{LINE}")

@owner_only
async def add_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await reply(update, "❌ `/add_channel @username`"); return
    try:
        chat = await _resolve_chat(context.bot, context.args[0])
    except Exception as e:
        await reply(update, f"❌ পাওয়া যায়নি: `{e}`"); return
    if chat.type != "channel":
        await reply(update, "❌ এটি চ্যানেল নয়।"); return
    invite = chat.invite_link or (f"https://t.me/{chat.username}" if chat.username else None)
    if not invite:
        try:
            inv = await context.bot.create_chat_invite_link(chat.id)
            invite = inv.invite_link
        except Exception as e:
            await reply(update, f"❌ Invite link বানানো যায়নি: `{e}`\nবটকে admin করুন।"); return
    for c in public["force_join"]["channels"]:
        if c.get("chat_id") == chat.id:
            await reply(update, "ℹ️ আগেই যোগ আছে।"); return
    public["force_join"]["channels"].append({
        "chat_id": chat.id, "title": chat.title,
        "invite_link": invite, "username": chat.username
    })
    save_pub()
    tail = f"`@{chat.username}`" if chat.username else f"`{chat.id}`"
    await reply(update,
        f"✅ *𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗔𝗗𝗗𝗘𝗗*\n{LINE}\n"
        f"📛 {chat.title}\n🆔 `{chat.id}`\n🔗 {invite}\n{LINE}\n"
        f"সরাতে: `/ban_add_channel {tail}`")

@owner_only
async def ban_add_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await reply(update, "❌ `/ban_add_channel @username`"); return
    raw = context.args[0].strip()
    removed = None
    if raw.lstrip("-").isdigit():
        cid = int(raw)
        for c in list(public["force_join"]["channels"]):
            if c.get("chat_id") == cid:
                public["force_join"]["channels"].remove(c); removed = c; break
    else:
        uname = raw.lower().lstrip("@")
        for c in list(public["force_join"]["channels"]):
            if (c.get("username") or "").lower() == uname:
                public["force_join"]["channels"].remove(c); removed = c; break
    if not removed:
        await reply(update, f"ℹ️ `{raw}` লিস্টে নেই।"); return
    save_pub()
    await reply(update,
        f"✅ *𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗥𝗘𝗠𝗢𝗩𝗘𝗗*\n{LINE}\n"
        f"📛 {removed.get('title')}\n🆔 `{removed.get('chat_id')}`\n{LINE}")

# ══════════════════════════════════════════════════
#  LIKE COMMANDS
# ══════════════════════════════════════════════════
async def safe_edit(proc, text):
    """Markdown ভাঙলেও (নিকনেমে _ * থাকলে) মেসেজ আটকে থাকবে না"""
    for pm in (ParseMode.MARKDOWN, None):
        t = text if pm else text.replace("*", "").replace("`", "")
        try:
            if proc.photo: await proc.edit_caption(caption=t, parse_mode=pm)
            else: await proc.edit_text(t, parse_mode=pm)
            return True
        except Exception as e:
            if "not modified" in str(e).lower(): return True
            if "too long" in str(e).lower() and proc.photo:      # ছবির ক্যাপশন ১০২৪ ছাড়ালে নতুন মেসেজে পাঠাও
                try:
                    await proc.reply_text(t, parse_mode=pm); return True
                except Exception: pass
    return False

def remember_name(user):
    try:
        public.setdefault("names", {})[str(user.id)] = (user.full_name or "User")[:40]
    except Exception: pass

async def _do_like(update, context, target, region, is_100=False):
    uid = update.effective_user.id
    # একই ইউজার একসাথে অনেক কমান্ড দিয়ে লিমিট টপকাতে পারবে না
    if not is_admin(uid):
        if uid in _inflight:
            await reply(update, "⏳ Your previous request is still processing, please wait."); return
        _inflight.add(uid)
    try:
        await _do_like_inner(update, context, target, region, is_100)
    finally:
        _inflight.discard(uid)

# ══════════════════════════════════════════════════
#  💎 PREMIUM LOADING + 🎴 লাইকের আগে স্টিকার
# ══════════════════════════════════════════════════
LIKE_STICKER_PACK = "AlyaBotss"        # পাবলিক লাইক পেলে
FAIL_STICKER_PACK = "AlyaBottss"       # পাবলিক লাইক না পেলে
ADMIN_STICKER_PACK = "Hafsannnn57"     # এডমিন লাইক নিলে — ফলাফলের শেষে
_STK = {}                              # pack -> {"ids": [...], "t": ts}
LOAD_SECS = 3.0          # বারটা প্রায় এই সময়ে ৯৫% এ পৌঁছায় (API শেষ হলেই ফল দেখায়)
LOAD_TICK = 2.0           # কত সেকেন্ড পরপর মেসেজ এডিট (ফ্লাড লিমিট এড়াতে)
_SPIN = ("◐", "◓", "◑", "◒")
_STAGES = (
    (0,  "🔌 Connecting to premium servers"),
    (22, "🔐 Verifying UID & region"),
    (45, "🚀 Sending likes"),
    (70, "📡 Syncing results"),
    (88, "💎 Finalizing"),
)

async def _pick_like_sticker(bot, pack=None):
    """প্যাক থেকে র‍্যান্ডম স্টিকার (প্যাক ১ ঘণ্টা ক্যাশ)।"""
    pack = pack or LIKE_STICKER_PACK
    try:
        c = _STK.get(pack) or {"ids": [], "t": 0.0}
        if not c["ids"] or _time.time() - c["t"] > 3600:
            st = await bot.get_sticker_set(pack)
            ids = [x.file_id for x in st.stickers]
            if ids: c = _STK[pack] = {"ids": ids, "t": _time.time()}
        if c["ids"]:
            import random
            return random.choice(c["ids"])
    except Exception as e:
        logger.warning(f"sticker pack {pack}: {e}")
    return None

async def send_pack_sticker(update, context, pack):
    """প্যাক থেকে র‍্যান্ডম স্টিকার রিপ্লাই করে পাঠায় (ডিলিট হয় না)। এরর হলে চুপচাপ স্কিপ।"""
    try:
        sid = await asyncio.wait_for(_pick_like_sticker(context.bot, pack), timeout=4)
        if sid:
            await update.effective_message.reply_sticker(sticker=sid)
    except Exception as e:
        logger.warning(f"sticker {pack}: {e.__class__.__name__}")

def _bar(pct, n=12):
    f = int(round(n * pct / 100))
    return "▰" * f + "▱" * (n - f)

def _loading_text(target, region, pct, tick):
    stage = [t for p, t in _STAGES if pct >= p][-1]
    return (f"💎 *𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗟𝗜𝗞𝗘 𝗘𝗡𝗚𝗜𝗡𝗘*\n{LINE}\n"
            f"🆔 `{target}`   🌐 {region.upper()}   🔌 {len(APIS)} API\n{LINE}\n"
            f"{_SPIN[tick % 4]} {stage}...\n\n"
            f"`{_bar(pct)}` *{pct}%*\n{LINE}\n"
            f"✨ Please wait, your likes are on the way")

async def _loading_anim(proc, target, region):
    """API কলের সময় প্রিমিয়াম লোডিং বার চালায়; শেষ হলে cancel করা হয়।"""
    t0 = _time.time(); tick = 0
    try:
        while True:
            await asyncio.sleep(LOAD_TICK)
            tick += 1
            pct = min(95, int((_time.time() - t0) / LOAD_SECS * 95))
            txt = _loading_text(target, region, pct, tick)
            try:
                if proc.photo: await proc.edit_caption(caption=txt, parse_mode=ParseMode.MARKDOWN)
                else: await proc.edit_text(txt, parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                m = str(e).lower()
                if "retry" in m or "flood" in m: await asyncio.sleep(3)
    except asyncio.CancelledError:
        pass

async def _do_like_inner(update, context, target, region, is_100):
    stk_holder = []
    try:
        ok = await _do_like_core(update, context, target, region, is_100, stk_holder)
        if ok is not None:                                # ফলাফল দেখানোর পর স্টিকার
            if is_admin(update.effective_user.id):
                await send_pack_sticker(update, context, ADMIN_STICKER_PACK)
            else:
                await send_pack_sticker(update, context, LIKE_STICKER_PACK if ok else FAIL_STICKER_PACK)
    finally:
        for m in stk_holder:
            try: await m.delete()
            except Exception: pass

async def _do_like_core(update, context, target, region, is_100, stk_holder):
    uid = update.effective_user.id
    proc_text = _loading_text(target, region, 0, 0)
    # API শুরু করার আগে স্টিকার লোডে অপেক্ষা না করে সঙ্গে সঙ্গে loading message দেখানো হয়।
    stk_msg = None
    fid = photo_state.get("file_id")
    try:
        if fid:
            proc = await update.effective_message.reply_photo(
                photo=fid, caption=proc_text, parse_mode=ParseMode.MARKDOWN)
        else:
            proc = await update.effective_message.reply_text(proc_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"proc send: {e}")
        try: proc = await update.effective_message.reply_text(proc_text, parse_mode=ParseMode.MARKDOWN)
        except Exception as e2:
            logger.error(f"proc send fallback: {e2}"); return None

    anim = asyncio.create_task(_loading_anim(proc, target, region))
    try:
        data = await call_api_with_fallback(region, target)
    except Exception as e:
        logger.error(f"call_api crashed: {e}", exc_info=True)
        data = {"error": "Internal error, please try again."}
    finally:
        anim.cancel()
        try: await anim
        except Exception: pass

    if not data or "error" in data:
        await react(update, "😐")
        await safe_edit(proc, fmt_error(f"`{(data or {}).get('error', 'unknown')}`"))
        return False

    st = data.get("status")
    if st == 1 and data.get("LikesGivenByAPI", 0) > 0:
        given = data["LikesGivenByAPI"]
        remember_name(update.effective_user)
        if is_100: update_100_used(uid)
        else: update_pub_used(uid)
        if is_admin(uid): save_pub()
        msg = fmt_success(data.get("used_api", "?"),
            data.get("PlayerNickname", "Unknown"),
            data.get("UID", target), region,
            data.get("LikesbeforeCommand", 0), given,
            data.get("LikesafterCommand", 0),
            data.get("per_api", {}))
        msg += "\n" + limit_footer(uid, is_100)
        await safe_edit(proc, msg)
        await react(update, "🎉")
        return True
    elif st in (1, 2):
        await react(update, "😐")
        await safe_edit(proc, fmt_already())
    else:
        await react(update, "😐")
        await safe_edit(proc, fmt_error(f"*status:* `{st}`"))
    return False

async def like100_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    chat = update.effective_chat
    if chat.type != "private" and is_group_blocked(chat.id):
        await react(update, "😐"); return
    if chat.type == "private" and not is_admin(uid): return
    if chat.type != "private" and str(chat.id) not in like100["groups"]: return
    if str(uid) in public["banned"] and not is_admin(uid):
        await react(update, "😐"); return
    if like100["config"]["status"] == "off" or not like100["config"]["public"]:
        await reply(update, "🔴 *𝗣𝗿𝗲𝗺𝗶𝘂𝗺-𝗟𝗶𝗸𝗲 𝗕𝗢𝗧 𝗜𝗦 𝗢𝗙𝗙*"); return
    if len(context.args) != 1:
        await reply(update, "❌ `/premium <uid>`"); return
    target = context.args[0].strip()
    if not target.isdigit():
        await reply(update, "❌ UID must be a number."); return
    if not is_admin(uid) and str(uid) not in like100["vip"]:
        if not await user_in_100_community(context.bot, uid):
            await react(update, "😐")
            await reply(update, "🚫 *𝗝𝗢𝗜𝗡 𝗥𝗘𝗤𝗨𝗜𝗥𝗘𝗗*\nPlease join the allowed group/channel first."); return
    
    if not can_100_like(uid):
        await react(update, "😐"); await reply(update, fmt_already()); return
        
    await _do_like(update, context, target, "bd", is_100=True)

LIKE_USAGE = (
    "❌ *𝗨𝗦𝗔𝗚𝗘*\n"
    "`/like <uid>` → BD server\n"
    "`/like <region> <uid>` → any region\n"
    "`/like <uid> <region>` → any region\n"
    f"📌 Regions: `{' '.join(sorted(ALLOWED_REGIONS))}`\n"
    "📝 Example: `/like 11214489525`\n"
    "          `/like bd 11214489525`\n"
    "          `/like 11214489525 bd`"
)

def parse_like_args(args):
    """রিটার্ন: (uid, region) বা None।
       - ১টি আর্গুমেন্ট হলে → শুধু BD
       - ২টি হলে → region+uid বা uid+region
       - region অবশ্যই ALLOWED_REGIONS-এর মধ্যে থাকতে হবে"""
    args = [a.strip() for a in args if a.strip()]
    if len(args) == 1:
        return (args[0], DEFAULT_LIKE_REGION) if args[0].isdigit() else None
    if len(args) == 2:
        a, b = args
        # /like <region> <uid>
        if a.isalpha() and b.isdigit():
            reg = a.lower()
            if reg in ALLOWED_REGIONS:
                return b, reg
            return None
        # /like <uid> <region>
        if a.isdigit() and b.isalpha():
            reg = b.lower()
            if reg in ALLOWED_REGIONS:
                return a, reg
            return None
    return None

async def like_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    chat = update.effective_chat
    if chat.type != "private" and is_group_blocked(chat.id):
        await react(update, "😐"); return
    if chat.type == "private" and not is_admin(uid):
        await reply(update, f"🚫 *𝗜𝗡𝗕𝗢𝗫𝗘 𝗡𝗢𝗧 𝗔𝗟𝗟𝗢𝗪𝗘𝗗*\n{LINE}\n"
                            f"This command only works in groups."); return
    if public["config"]["status"] == "off" and not is_admin(uid): return
    if str(uid) in public["banned"]:
        await react(update, "😐"); await reply(update, "🚫 *𝗬𝗢𝗨 𝗔𝗥𝗘 𝗕𝗔𝗡𝗡𝗘𝗗*"); return
    parsed = parse_like_args(context.args)
    if not parsed:
        await reply(update, LIKE_USAGE); return
    target, region = parsed
    if not is_admin(uid):
        missing = await get_missing_joins(context.bot, uid)
        if missing:
            await react(update, "😐")
            await update.message.reply_text(
                f"🔒 *𝗝𝗢𝗜𝗡 𝗥𝗘𝗤𝗨𝗜𝗥𝗘𝗗*\n👇 Join and try again",
                parse_mode=ParseMode.MARKDOWN, reply_markup=pub_join_keyboard(missing)); return
    if chat.type != "private" and public["config"].get("mode") == "private":
        if str(chat.id) not in public["groups"]: return
        
    if not can_pub_like(uid):
        await react(update, "😐"); await reply(update, fmt_already()); return
        
    await _do_like(update, context, target, region, is_100=False)

# ══════════════════════════════════════════════════
#  ⚡ MAX LIKE — আলাদা API, Owner controlled
# ══════════════════════════════════════════════════
async def call_max_like_api(uid):
    if not MAX_API_URL or not MAX_API_KEY:
        return {"error": "MAX API সেট করা নেই। .env-এ MAX_API_URL ও MAX_API_KEY যোগ করুন।"}
    try:
        session = get_api_session()
        async with session.get(
            f"{MAX_API_URL}like",
            params={"key": MAX_API_KEY, "uid": uid, "server_name": DEFAULT_LIKE_REGION},
            timeout=aiohttp.ClientTimeout(total=15, connect=5),
        ) as resp:
            if resp.status != 200:
                return {"error": f"MAX API HTTP {resp.status}"}
            data = await resp.json(content_type=None)
        if not isinstance(data, dict):
            return {"error": "MAX API থেকে ভুল response এসেছে।"}
        status = _to_int(data.get("status"))
        given = _to_int(data.get("LikesGivenByAPI"))
        if status == 1 and given > 0:
            return {
                "status": 1,
                "PlayerNickname": data.get("PlayerNickname") or "Unknown",
                "UID": data.get("UID", uid),
                "LikesbeforeCommand": _to_int(data.get("LikesbeforeCommand")),
                "LikesafterCommand": _to_int(data.get("LikesafterCommand")),
                "LikesGivenByAPI": given,
            }
        if status in (1, 2):
            return {"status": 2}
        return {"error": str(data.get("error") or f"MAX API status {status}")[:100]}
    except asyncio.TimeoutError:
        return {"error": "MAX API timeout — পরে আবার চেষ্টা করুন।"}
    except Exception as exc:
        logger.warning("MAX API failed: %s", exc.__class__.__name__)
        return {"error": "MAX API-তে সংযোগ করা যাচ্ছে না।"}

async def max_like_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not max_like_state.get("enabled", False):
        await reply(update, f"🔒 *𝗠𝗔𝗫 𝗟𝗜𝗞𝗘 𝗜𝗦 𝗢𝗙𝗙*\n{LINE}\nএই ফিচারটি Owner এখনো চালু করেননি।")
        return
    if len(context.args) != 1 or not context.args[0].isdigit():
        await reply(update, "❌ সঠিক ব্যবহার: `/max <uid>`\nউদাহরণ: `/max 12345678`")
        return
    target = context.args[0]
    if uid in _inflight:
        await reply(update, "⏳ আপনার আগের request চলছে, একটু অপেক্ষা করুন।")
        return
    _inflight.add(uid)
    try:
        proc = await update.effective_message.reply_text(
            f"⚡ *𝗠𝗔𝗫 𝗟𝗜𝗞𝗘 𝗘𝗡𝗚𝗜𝗡𝗘*\n{LINE}\n🆔 UID: `{target}`\n🌐 Server: `BD`\n⏳ MAX API-তে request পাঠানো হচ্ছে...",
            parse_mode=ParseMode.MARKDOWN)
        data = await call_max_like_api(target)
        if data.get("status") == 1:
            text = (f"⚡ *𝗠𝗔𝗫 𝗟𝗜𝗞𝗘 𝗦𝗨𝗖𝗖𝗘𝗦𝗦*\n{LINE}\n"
                    f"👤 Name: *{md_escape(data.get('PlayerNickname', 'Unknown'))}*\n"
                    f"🆔 UID: `{data.get('UID', target)}`\n🌐 Server: *BD*\n{LINE}\n"
                    f"📊 Before: *{data.get('LikesbeforeCommand', 0)}*\n"
                    f"💎 Added: *+{data.get('LikesGivenByAPI', 0)}*\n"
                    f"🔥 After: *{data.get('LikesafterCommand', 0)}*\n{LINE}\n"
                    f"🔌 Source: *Separate MAX API*")
            await safe_edit(proc, text)
            await react(update, "🎉")
        elif data.get("status") == 2:
            await safe_edit(proc, f"⏰ *𝗠𝗔𝗫 𝗔𝗣𝗜 𝗟𝗜𝗠𝗜𝗧 𝗥𝗘𝗔𝗖𝗛𝗘𝗗*\n{LINE}\nএই UID-তে আপাতত আর লাইক দেওয়া যাচ্ছে না।")
            await react(update, "😐")
        else:
            await safe_edit(proc, fmt_error(md_escape(data.get("error", "Unknown error"))))
            await react(update, "😐")
    except Exception as exc:
        logger.warning("/max command failed: %s", exc.__class__.__name__)
        await reply(update, "❌ MAX request সম্পন্ন করা যায়নি।")
    finally:
        _inflight.discard(uid)

async def _set_max_like_status(update, context, enabled):
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        await reply(update, "📌 চালু/বন্ধের ঘোষণা পিন করতে এই কমান্ডটি একটি গ্রুপে ব্যবহার করুন।")
        return
    if bool(max_like_state.get("enabled")) == enabled:
        state = "চালু" if enabled else "বন্ধ"
        await reply(update, f"ℹ️ MAX Like Bot ইতিমধ্যেই {state} আছে।")
        return
    max_like_state["enabled"] = enabled
    save_json(MAX_STATE_FILE, max_like_state)
    if enabled:
        announcement = (
            f"⚡ *𝗠𝗔𝗫 𝗟𝗜𝗞𝗘 𝗕𝗢𝗧 — 𝗔𝗖𝗧𝗜𝗩𝗔𝗧𝗘𝗗*\n{LINE}\n"
            "🟢 *MAX Like Mode এখন চালু হয়েছে!*\n\n"
            "🚀 আলাদা MAX Like API এখন সক্রিয়।\n"
            "🎮 ব্যবহার: `/max <uid>`\n"
            "📝 উদাহরণ: `/max 12345678`\n\n"
            "🔐 এই ফিচার Owner-এর নিয়ন্ত্রণে থাকবে।\n"
            f"{LINE}\n✨ *MEDUSA LIKE BOT • MAX MODE ON*"
        )
    else:
        announcement = (
            f"🛑 *𝗠𝗔𝗫 𝗟𝗜𝗞𝗘 𝗕𝗢𝗧 — 𝗗𝗘𝗔𝗖𝗧𝗜𝗩𝗔𝗧𝗘𝗗*\n{LINE}\n"
            "🔴 *MAX Like Mode এখন বন্ধ করা হয়েছে।*\n\n"
            "⛔ `/max <uid>` কমান্ড সাময়িকভাবে নিষ্ক্রিয়।\n"
            "🔐 Owner পুনরায় চালু না করা পর্যন্ত এই ফিচার ব্যবহার করা যাবে না।\n"
            f"{LINE}\n✨ *MEDUSA LIKE BOT • MAX MODE OFF*"
        )
    msg = await update.effective_message.reply_text(announcement, parse_mode=ParseMode.MARKDOWN)
    try:
        await context.bot.pin_chat_message(chat_id=chat.id, message_id=msg.message_id, disable_notification=True)
        await reply(update, "📌 Status message সফলভাবে pin করা হয়েছে।")
    except Exception as exc:
        logger.warning("MAX status pin failed: %s", exc.__class__.__name__)
        await reply(update, "⚠️ Status update হয়েছে, তবে pin করা যায়নি। Bot-কে গ্রুপে Pin Messages permission দিন।")

async def max_like_on_cmd(update, context):
    await _set_max_like_status(update, context, True)

async def max_like_off_cmd(update, context):
    await _set_max_like_status(update, context, False)

# ══════════════════════════════════════════════════
#  100-Like ADMIN
# ══════════════════════════════════════════════════
@owner_only
async def allow_100like_group(update, context):
    chat = update.effective_chat
    if chat.type == "private":
        await reply(update, "❌ গ্রুপে ব্যবহার করুন।"); return
    gid = str(chat.id)
    like100["groups"][gid] = {
        'name': chat.title or gid,
        'username': f"@{chat.username}" if chat.username else None,
        'by': update.effective_user.id, 'date': today_str()
    }
    save_100()
    await reply(update, f"✅ *𝗚𝗥𝗢𝗨𝗣 𝗔𝗟𝗟𝗢𝗪𝗘𝗗*\n{LINE}\n📛 {chat.title}\n🆔 `{gid}`\n{LINE}")

@admin_only
async def bot100_off(update, context):
    like100["config"]["status"] = "off"; like100["config"]["public"] = False
    save_100(); await reply(update, "🔴 *𝗣𝗿𝗲𝗺𝗶𝘂𝗺-𝗟𝗶𝗸𝗲 𝗕𝗢𝗧 𝗢𝗙𝗙*")

@admin_only
async def bot100_on(update, context):
    like100["config"]["status"] = "on"; like100["config"]["public"] = True
    save_100(); await reply(update, "🟢 *𝗣𝗿𝗲𝗺𝗶𝘂𝗺-𝗟𝗶𝗸𝗲 𝗕𝗢𝗧 𝗢𝗡*")

# ══════════════════════════════════════════════════
#  PUBLIC ADMIN
# ══════════════════════════════════════════════════
@admin_only
async def pub_on(update, context):
    public["config"]["status"] = "on"; save_pub()
    await reply(update, "🟢 *𝗣𝘂𝗯𝗹𝗶𝗰 𝗕𝗢𝗧 𝗢𝗡*")

@admin_only
async def pub_off(update, context):
    public["config"]["status"] = "off"; save_pub()
    await reply(update, "🔴 *𝗣𝘂𝗯𝗹𝗶𝗰 𝗕𝗢𝗧 𝗢𝗙𝗙*")

@owner_only
async def pub_allow(update, context):
    chat = update.effective_chat
    if chat.type == "private":
        await reply(update, "❌ গ্রুপে ব্যবহার করুন।"); return
    gid = str(chat.id)
    public["groups"][gid] = {
        'name': chat.title or gid,
        'username': f"@{chat.username}" if chat.username else None,
        'by': update.effective_user.id, 'date': today_str()
    }
    save_pub()
    await reply(update, f"✅ *𝗚𝗥𝗢𝗨𝗣 𝗔𝗟𝗟𝗢𝗪𝗘𝗗*\n{LINE}\n📛 {chat.title}\n🆔 `{gid}`\n{LINE}")

# ══════════════════════════════════════════════════
#  SHARED ADMIN
# ══════════════════════════════════════════════════
@admin_only
async def admin_cmd(update, context):
    if is_owner(update.effective_user.id):
        api_lines = "\n".join(
            f"  • {a['name']}: `{a['url']}` key=`{mask_key(a['key'])}`"
            for a in APIS) or "  ⚠️ কোনো API নেই"
    else:
        api_lines = "\n".join(f"  • {a['name']}: ✅" for a in APIS) or "  ⚠️ কোনো API নেই"
    msg = (f"👑 *𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟*\n{LINE}\n"
           f"🔌 *APIs* : `{len(APIS)}/4` (fallback)\n{api_lines}\n{LINE}\n"
           f"📸 *Photo* : {'✅' if photo_state.get('file_id') else '❌'}\n"
           f"🚫 *Blocked* : `{len(blocked_groups)}`\n"
           f"💎 *VIP* : `{len(set(list(like100['vip'].keys())+list(public['vip'].keys())))}`\n{LINE}\n"
           f"💎 *Premium* : `{like100['config']['status'].upper()}` lim=`{like100['config']['limit']}`\n"
           f"🌐 *Public* : `{public['config']['status'].upper()}` lim=`{public['config']['limit']}`\n{LINE}\n"
           f"`/help` – সব কমান্ড")
    await reply(update, msg)

@admin_only
async def api_info(update, context):
    owner = is_owner(update.effective_user.id)
    lines = [f"🔌 *𝗔𝗣𝗜 𝗖𝗢𝗡𝗙𝗜𝗚*", LINE]
    for i in range(1, 5):
        url = _norm(os.getenv(f"API_{i}_URL", ""))
        key = os.getenv(f"API_{i}_KEY", "").strip()
        if url and key:
            if owner: lines.append(f"✅ *API-{i}*\n  URL: `{url}`\n  Key: `{mask_key(key)}`")
            else: lines.append(f"✅ *API-{i}*")
        else:
            lines.append(f"❌ *API-{i}* — missing")
    lines += [LINE,
              "🔄 *Fallback Order* : API-1 → API-2 → API-3 → API-4",
              f"📸 *Photo* : {'✅ Set' if photo_state.get('file_id') else '❌ Not set'}"]
    await reply(update, "\n".join(lines))

@admin_only
async def stats_cmd(update, context):
    t = today_str()
    s1 = like100["stats"].get(t, {"total":0, "users":{}})
    s2 = public["stats"].get(t, {"total":0, "users":{}})
    msg = (f"📊 *𝗧𝗢𝗗𝗔𝗬'𝗦 𝗦𝗧𝗔𝗧𝗦*\n{LINE}\n📅 `{t}`\n{LINE}\n"
           f"💎 *Premium-Like*\n  ❤️ Total : `{s1['total']}`\n  👥 Users : `{len(s1['users'])}`\n{LINE}\n"
           f"🌐 *Public*\n  ❤️ Total : `{s2['total']}`\n  👥 Users : `{len(s2['users'])}`\n{LINE}\n"
           f"🧮 *Grand Total* : `{s1['total'] + s2['total']}`\n"
           f"🚫 *Blocked* : `{len(blocked_groups)}`")
    await reply(update, msg)

@admin_only
async def user_like_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = today_str(); now = now_bd()
    nxt = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    secs = int((nxt - now).total_seconds()); hrs, mins = secs // 3600, (secs % 3600) // 60
    s1 = like100.get("stats", {}).get(t, {"total":0, "users":{}})
    s2 = public.get("stats", {}).get(t, {"total":0, "users":{}})
    merged = {}
    for uid, cnt in s1.get("users", {}).items(): merged[uid] = merged.get(uid, 0) + int(cnt)
    for uid, cnt in s2.get("users", {}).items(): merged[uid] = merged.get(uid, 0) + int(cnt)
    header = (f"📊 *𝗔𝗟𝗟 𝗨𝗦𝗘𝗥𝗦 𝗧𝗢𝗗𝗔𝗬*\n{LINE}\n📅 `{t}` | ⏰ `{hrs}h {mins}m`\n"
              f"👥 Users : `{len(merged)}`\n❤️ Likes : `{s1.get('total',0)+s2.get('total',0)}`\n{LINE}\n")
    if not merged:
        await reply(update, header + "⚠️ আজ কেউ লাইক নেয়নি।"); return
    sorted_users = sorted(merged.items(), key=lambda x: (-x[1], x[0]))
    chunks, cur, idx = [], header, 1
    for uid, cnt in sorted_users:
        line = f"{idx}. `{uid}` — *{cnt}*\n"
        if len(cur) + len(line) > 3800: chunks.append(cur); cur = ""
        cur += line; idx += 1
    if cur: chunks.append(cur)
    for chunk in chunks:
        try: await update.effective_message.reply_text(chunk, parse_mode=ParseMode.MARKDOWN)
        except: pass
        await asyncio.sleep(0.3)

@admin_only
async def setlimit100_cmd(update, context):
    if len(context.args) != 1 or not context.args[0].isdigit():
        await reply(update, "❌ `/setlimit_premium <n>`"); return
    like100["config"]["limit"] = int(context.args[0]); save_100()
    await reply(update, f"✅ *𝗣𝗿𝗲𝗺𝗶𝘂𝗺-𝗟𝗶𝗸𝗲 𝗟𝗶𝗺𝗶𝘁* : `{like100['config']['limit']}`")

@admin_only
async def setlimitpub_cmd(update, context):
    if len(context.args) != 1 or not context.args[0].isdigit():
        await reply(update, "❌ `/setlimitpub <n>`"); return
    public["config"]["limit"] = int(context.args[0]); save_pub()
    await reply(update, f"✅ *𝗣𝘂𝗯𝗹𝗶𝗰 𝗟𝗶𝗺𝗶𝘁* : `{public['config']['limit']}`")

# ══════════════════════════════════════════════════
#  🔇 GROUP MUTE
# ══════════════════════════════════════════════════
async def mute_gate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """muted গ্রুপের সব আপডেট এখানেই থামে — বট কিছুই করে না, রিয়্যাকশনও দেয় না।
       শুধু এডমিনের /like_bot_unmute যেতে পারে।"""
    chat = update.effective_chat
    if not chat or chat.type == "private" or not is_group_muted(chat.id): return
    if update.my_chat_member: return            # বট add/remove ট্র্যাকিং চলবে (কোনো মেসেজ ছাড়াই)
    m = update.effective_message
    user = update.effective_user
    if (m and m.text and user and is_admin(user.id)
            and re.match(r"^/like_bot_unmute(@\w+)?(\s|$)", m.text, re.I)):
        return
    raise ApplicationHandlerStop

@admin_only
async def like_bot_mute_cmd(update, context):
    chat = update.effective_chat
    if chat.type == "private": return
    gid = str(chat.id)
    if gid in muted_groups: return
    muted_groups[gid] = {"name": chat.title or gid,
                         "username": f"@{chat.username}" if chat.username else None,
                         "by": update.effective_user.id, "date": today_str()}
    save_muted()
    # গ্রুপে কিছুই লেখা হবে না — শুধু এডমিনকে ইনবক্সে জানানো হবে (বট স্টার্ট করা থাকলে)
    try:
        await context.bot.send_message(update.effective_user.id,
            f"🔇 Muted\n📛 {chat.title}\n🆔 {gid}\nআনমিউট: গ্রুপে /like_bot_unmute")
    except Exception: pass

@admin_only
async def like_bot_unmute_cmd(update, context):
    chat = update.effective_chat
    if chat.type == "private": return
    if muted_groups.pop(str(chat.id), None) is None: return
    save_muted()
    await reply(update, f"🔊 *𝗕𝗢𝗧 𝗨𝗡𝗠𝗨𝗧𝗘𝗗*\n{LINE}\nএই গ্রুপে বট আবার চালু।")

@admin_only
async def muted_groups_cmd(update, context):
    if not muted_groups:
        await reply(update, f"🔇 *𝗠𝗨𝗧𝗘𝗗*\n{LINE}\n✅ কোনো গ্রুপ মিউট নেই।"); return
    lines = [f"🔇 *𝗠𝗨𝗧𝗘𝗗 𝗚𝗥𝗢𝗨𝗣𝗦* ({len(muted_groups)})\n{LINE}"]
    for i, (gid, c) in enumerate(muted_groups.items(), 1):
        lines.append(f"{i}. {md_escape(c.get('name', gid))}\n   🆔 `{gid}`")
    await reply(update, "\n".join(lines))

# ══════════════════════════════════════════════════
#  ✨ NEW FEATURES
# ══════════════════════════════════════════════════
def _target_uid(update, context):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.from_user:
        return msg.reply_to_message.from_user.id
    if context.args and context.args[0].lstrip("-").isdigit():
        return int(context.args[0])
    return None

@admin_only
async def ban_user_cmd(update, context):
    t = _target_uid(update, context)
    if t is None:
        await reply(update, "❌ `/ban_user <id>` অথবা ইউজারের মেসেজে রিপ্লাই দিন।"); return
    if is_admin(t):
        await reply(update, "❌ এডমিনকে ব্যান করা যায় না।"); return
    public["banned"][str(t)] = {"by": update.effective_user.id, "date": today_str()}
    save_pub()
    await reply(update, f"⛔ *𝗨𝗦𝗘𝗥 𝗕𝗔𝗡𝗡𝗘𝗗*\n{LINE}\n🆔 `{t}`\nআনব্যান: `/unban_user {t}`")

@admin_only
async def unban_user_cmd(update, context):
    t = _target_uid(update, context)
    if t is None:
        await reply(update, "❌ `/unban_user <id>` অথবা রিপ্লাই দিন।"); return
    if public["banned"].pop(str(t), None) is None:
        await reply(update, f"ℹ️ `{t}` ব্যান লিস্টে নেই।"); return
    save_pub()
    await reply(update, f"✅ *𝗨𝗦𝗘𝗥 𝗨𝗡𝗕𝗔𝗡𝗡𝗘𝗗*\n{LINE}\n🆔 `{t}`")

@admin_only
async def public_mode_cmd(update, context):
    cur = public["config"].get("mode", "public")
    if len(context.args) != 1 or context.args[0].lower() not in ("public", "private"):
        await reply(update, f"🌐 *𝗣𝗨𝗕𝗟𝗜𝗖 𝗠𝗢𝗗𝗘* : `{cur}`\n{LINE}\n"
                            f"`/public_mode public` – যেকোনো গ্রুপে চলবে\n"
                            f"`/public_mode private` – শুধু allowed গ্রুপে"); return
    public["config"]["mode"] = context.args[0].lower(); save_pub()
    await reply(update, f"✅ *𝗠𝗢𝗗𝗘* : `{public['config']['mode']}`")

@admin_only
async def groups_cmd(update, context):
    chats = public.get("chats", {})
    if not chats:
        await reply(update, f"📋 *𝗚𝗥𝗢𝗨𝗣𝗦*\n{LINE}\n⚠️ কোনো গ্রুপ নেই।"); return
    head = f"📋 *𝗕𝗢𝗧 𝗚𝗥𝗢𝗨𝗣𝗦* ({len(chats)})\n{LINE}\n"
    cur = head
    for i, (gid, c) in enumerate(chats.items(), 1):
        blk = " 🚫" if is_group_blocked(gid) else ""
        line = f"{i}. {md_escape(c.get('name', gid))}{blk}\n   🆔 `{gid}`\n   🔗 {c.get('link') or '—'}\n"
        if len(cur) + len(line) > 3800:
            await reply(update, cur); cur = ""
        cur += line
    if cur: await reply(update, cur)

@admin_only
async def backup_cmd(update, context):
    if update.effective_chat.type != "private":
        await reply(update, "❌ ইনবক্সে ব্যবহার করুন।"); return
    sent = 0
    for f in (FILE_100, FILE_PUB, FILE_PHOTO, FILE_BLOCKED, FILE_REFER, FILE_REFER_GOAL):
        if os.path.exists(f):
            try:
                with open(f, "rb") as fh:
                    await context.bot.send_document(update.effective_chat.id, fh, filename=f)
                sent += 1
            except Exception as e:
                logger.warning(f"backup {f}: {e}")
    await reply(update, f"💾 *𝗕𝗔𝗖𝗞𝗨𝗣* : `{sent}` ফাইল পাঠানো হয়েছে।")

async def top_cmd(update, context):
    chat = update.effective_chat
    if chat.type != "private" and is_group_blocked(chat.id): return
    t = today_str()
    merged = {}
    for src in (like100["stats"].get(t, {}), public["stats"].get(t, {})):
        for u, c in src.get("users", {}).items(): merged[u] = merged.get(u, 0) + int(c)
    if not merged:
        await reply(update, f"🏆 *𝗧𝗢𝗗𝗔𝗬'𝗦 𝗧𝗢𝗣*\n{LINE}\n⚠️ Nobody has taken a like yet today."); return
    medals = ["🥇", "🥈", "🥉"]
    lines = [f"🏆 *𝗧𝗢𝗗𝗔𝗬'𝗦 𝗧𝗢𝗣*\n{LINE}"]
    for i, (u, c) in enumerate(sorted(merged.items(), key=lambda x: (-x[1], x[0]))[:10]):
        nm = md_escape(public.get("names", {}).get(u, f"User {u[-4:]}"))
        lines.append(f"{medals[i] if i < 3 else str(i+1)+'.'} {nm} — *{c}*")
    lines.append(LINE)
    await reply(update, "\n".join(lines))

@admin_only
async def api_check_cmd(update, context):
    owner = is_owner(update.effective_user.id)
    lines = [f"🩺 *𝗔𝗣𝗜 𝗛𝗘𝗔𝗟𝗧𝗛*\n{LINE}"]
    async with aiohttp.ClientSession() as s:
        for a in APIS:
            t0 = _time.time()
            try:
                async with s.get(a["url"], timeout=aiohttp.ClientTimeout(total=10)) as r:
                    ms = int((_time.time() - t0) * 1000)
                    ok = "✅" if r.status < 500 else "⚠️"
                    lines.append(f"{ok} *{a['name']}* — HTTP `{r.status}` — `{ms}ms`")
            except asyncio.TimeoutError:
                lines.append(f"❌ *{a['name']}* — timeout")
            except Exception as e:
                lines.append(f"❌ *{a['name']}* — {e.__class__.__name__}")
    if not APIS: lines.append("⚠️ কোনো API নেই")
    lines.append(LINE)
    await reply(update, "\n".join(lines))

async def daily_report(context):
    t = today_str()
    s1 = like100["stats"].get(t, {"total": 0, "users": {}})
    s2 = public["stats"].get(t, {"total": 0, "users": {}})
    users = set(s1["users"]) | set(s2["users"])
    await notify_admins(context.bot,
        f"📅 Daily Report — {t}\n{LINE}\n"
        f"💎 100-Like : {s1['total']}\n🌐 Public : {s2['total']}\n"
        f"🧮 Total : {s1['total'] + s2['total']}\n👥 Users : {len(users)}\n"
        f"🏘 Groups : {len(public.get('chats', {}))}")

# ══════════════════════════════════════════════════
#  BROADCAST
# ══════════════════════════════════════════════════
def broadcast_targets():
    t = {}
    for src in (public.get("chats", {}), public.get("groups", {}), like100.get("groups", {})):
        for gid, c in src.items():
            try: t.setdefault(int(gid), c.get("name", str(gid)))
            except: pass
    return t

@admin_only
async def broadcast_cmd(update, context):
    if update.effective_chat.type != "private":
        await update.effective_message.reply_text("❌ ইনবক্সে দিন।"); return
    context.user_data["bc_wait"] = True
    n = len(broadcast_targets())
    await update.effective_message.reply_text(
        f"📢 *𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗠𝗢𝗗𝗘*\n{LINE}\n"
        f"আমাকে যেকোনো কিছু পাঠান — সব {n} গ্রুপে যাবে।\n"
        f"❌ বাতিল: `/cancel`",
        parse_mode=ParseMode.MARKDOWN)

@admin_only
async def cancel_cmd(update, context):
    shop_flow = context.user_data.pop("auto_wait", None) or context.user_data.pop("auto_pending", None)
    context.user_data.pop("auto_pending", None)
    if shop_flow:
        await update.effective_message.reply_text("❌ Cancelled.")
    elif context.user_data.pop("gift_wait", None):
        await update.effective_message.reply_text("❌ Gift বাতিল।")
    elif context.user_data.pop("bc_wait", None):
        await update.effective_message.reply_text("❌ Broadcast বাতিল।")
    else:
        await update.effective_message.reply_text("ℹ️ কিছু নেই।")

async def do_broadcast(bot, admin_chat, src_chat, src_msg):
    targets = {g: n for g, n in broadcast_targets().items() if not is_group_blocked(g) and not is_group_muted(g)}
    total = len(targets)
    if not total:
        await bot.send_message(admin_chat, "⚠️ কোনো গ্রুপ নেই।"); return
    status = await bot.send_message(admin_chat, f"📤 0/{total}")
    sent, failed, dead = 0, [], 0
    for i, (gid, name) in enumerate(targets.items(), 1):
        try:
            await bot.copy_message(chat_id=gid, from_chat_id=src_chat, message_id=src_msg)
            sent += 1
        except Exception as e:
            failed.append((name, str(e)[:70]))
            if any(k in str(e).lower() for k in ("kicked", "chat not found", "forbidden", "deactivated")):
                public["chats"].pop(str(gid), None); dead += 1
        if i % 5 == 0 or i == total:
            try: await status.edit_text(f"📤 {i}/{total}")
            except: pass
        await asyncio.sleep(0.1)
    if dead: save_pub()
    try: await status.edit_text(f"✅ 𝗗𝗢𝗡𝗘\n📨 {sent}/{total}\n❌ {len(failed)}"
                                + (f"\n🧹 {dead} মৃত গ্রুপ লিস্ট থেকে সরানো হয়েছে" if dead else ""))
    except: pass

# ══════════════════════════════════════════════════
#  GROUP TRACK
# ══════════════════════════════════════════════════
async def get_group_link(bot, chat):
    if chat.username: return f"https://t.me/{chat.username}"
    try:
        full = await bot.get_chat(chat.id)
        if full.username: return f"https://t.me/{full.username}"
        if full.invite_link: return full.invite_link
    except: pass
    try:
        inv = await bot.create_chat_invite_link(chat.id, name="Owner link")
        return inv.invite_link
    except: pass
    return None

def _who(user):
    if not user: return "?"
    nm = user.full_name or "User"
    un = f" @{user.username}" if user.username else ""
    return f"{nm}{un} ({user.id})"

async def notify_admins(bot, text):
    for aid in OWNER_IDS:
        try: await bot.send_message(aid, text)
        except Exception as e: logger.warning(f"notify {aid}: {e}")

async def on_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ev = update.my_chat_member
    if not ev: return
    chat = ev.chat
    if chat.type not in ("group", "supergroup"): return
    gid = str(chat.id)
    new = ev.new_chat_member.status
    if new in ("member", "administrator"):
        rec = public["chats"].get(gid)
        first = rec is None
        link = rec.get("link") if rec else await get_group_link(context.bot, chat)
        public["chats"][gid] = {
            "name": chat.title or gid,
            "username": f"@{chat.username}" if chat.username else None,
            "by": ev.from_user.id if ev.from_user else None,
            "link": link,
            "date": (rec or {}).get("date", today_str())
        }
        save_pub()
        if first:
            try:
                await context.bot.send_message(chat.id,
                    f"🎉 *𝗧𝗛𝗔𝗡𝗞𝗦 𝗙𝗢𝗥 𝗔𝗗𝗗𝗜𝗡𝗚 𝗠𝗘!*\n{LINE}\n"
                    f"🌐 `/like <uid>` | `/like <region> <uid>`\n"
                    f"📌 `/like bd 11214489525`\n"
                    f"🆔 `/id` – Group ID\n{LINE}",
                    parse_mode=ParseMode.MARKDOWN)
            except: pass
        try: members = await context.bot.get_chat_member_count(chat.id)
        except: members = "?"
        await notify_admins(context.bot,
            f"➕ Bot added\n📛 {chat.title}\n🆔 {gid}\n👥 {members}\n👤 {_who(ev.from_user)}\n🔗 {link or '—'}")
    elif new in ("left", "kicked"):
        public["chats"].pop(gid, None); save_pub()
        await notify_admins(context.bot, f"➖ Bot removed\n📛 {chat.title}\n🆔 {gid}")

# ══════════════════════════════════════════════════
#  CALLBACKS
# ══════════════════════════════════════════════════
async def callback_handler(update, context):
    q = update.callback_query
    uid = q.from_user.id
    if q.data == "verify_join":
        missing = [] if is_admin(uid) else await get_missing_joins(context.bot, uid)
        if not missing:
            await q.answer("✅ Verified!")
            try:
                await q.message.edit_text(
                    f"✅ *𝗩𝗘𝗥𝗜𝗙𝗜𝗘𝗗*\n{LINE}\n🌐 `/like <uid>`\n{LINE}",
                    parse_mode=ParseMode.MARKDOWN)
            except: pass
            await refer_credit(context, q.from_user)     # রেফারার +১ পয়েন্ট
            try:
                await context.bot.send_message(
                    uid, start_design(q.from_user.first_name or "User", "private", uid),
                    parse_mode=ParseMode.MARKDOWN, reply_markup=start_keyboard(),
                    link_preview_options=LinkPreviewOptions(is_disabled=True))
            except Exception as e:
                logger.warning(f"verify welcome {uid}: {e}")
        else:
            await q.answer(f"❌ You still need to join {len(missing)} more!", show_alert=True)
            try: await q.message.edit_reply_markup(reply_markup=with_add_button(pub_join_keyboard(missing)))
            except Exception: pass   # বাটন একই থাকলে Telegram "not modified" দেয় — সমস্যা নেই
        return
    await q.answer()

# ══════════════════════════════════════════════════
#  PRIVATE FALLBACK
# ══════════════════════════════════════════════════
async def private_fallback(update, context):
    uid = update.effective_user.id
    w = context.user_data.get("auto_wait")
    if w:
        if _time.time() - w["ts"] > AUTO_WAIT_SECS:
            context.user_data.pop("auto_wait", None)
        else:
            await shop_uid_input(update, context, w); return
    if is_admin(uid):
        if context.user_data.pop("bc_wait", None):
            m = update.effective_message
            context.application.create_task(
                do_broadcast(context.bot, m.chat_id, m.chat_id, m.message_id))
            return
        await admin_cmd(update, context); return
    kb = pub_join_keyboard(await get_missing_joins(context.bot, uid))
    if kb:
        await update.message.reply_text(
            f"🔒 *𝗝𝗢𝗜𝗡 𝗥𝗘𝗤𝗨𝗜𝗥𝗘𝗗*\n👇 Join and send `/start`",
            parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    else:
        await update.message.reply_text("👋 Send `/start`", parse_mode=ParseMode.MARKDOWN)

async def photo_handler_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("bc_wait") and is_admin(update.effective_user.id):
        m = update.effective_message
        context.user_data.pop("bc_wait", None)
        context.application.create_task(
            do_broadcast(context.bot, m.chat_id, m.chat_id, m.message_id))

# ══════════════════════════════════════════════════
#  GLOBAL ERROR
# ══════════════════════════════════════════════════
async def global_error_handler(update, context):
    err = context.error
    try:
        if err.__class__.__name__ == "NetworkError":
            logger.warning(f"NetworkError: {err}"); return
        logger.error(f"Update error: {err}", exc_info=err)
    except: pass

# ══════════════════════════════════════════════════
#  RESET
# ══════════════════════════════════════════════════
async def reset_midnight(context):
    like100["users"] = {}; public["users"] = {}
    save_all()
    logger.info(f"✅ Daily reset at {now_bd()}")

# ══════════════════════════════════════════════════
#  🎁 REFERRAL SYSTEM
#  /myrefer          → রেফার লিংক + প্রোফাইল (সবার জন্য)
#  /all_user_refer   → সবার রেফার লিস্ট (এডমিন, ইনবক্সে)
#  /med_x <id> <n>   → রেফার সেট / +বাড়াও / -কমাও (এডমিন)
# ══════════════════════════════════════════════════
def save_refer(): save_json(FILE_REFER, referral)

def refer_link(uid):
    return f"https://t.me/{BOT_USERNAME}?start=ref_{uid}" if BOT_USERNAME else "—"

def _ref_entry(uid, user=None):
    """ইউজারের রেফার এন্ট্রি (না থাকলে বানায়), নাম/ইউজারনেম আপডেট রাখে"""
    e = referral["users"].setdefault(str(uid), {
        "name": public.get("names", {}).get(str(uid), f"User {str(uid)[-4:]}"),
        "username": "", "count": 0, "since": today_str()})
    if user is not None:
        e["name"] = (user.full_name or e["name"])[:40]
        e["username"] = user.username or ""
    return e

def refer_count(uid):
    return int(referral["users"].get(str(uid), {}).get("count", 0))

def refer_rank(uid):
    ranked = sorted(referral["users"].items(), key=lambda x: (-int(x[1].get("count", 0)), x[0]))
    for i, (u, _) in enumerate(ranked, 1):
        if u == str(uid): return i, len(ranked)
    return len(ranked) + 1, len(ranked)

def refer_goal_users():
    out = []
    for u, e in referral["users"].items():
        if int(e.get("count", 0)) >= REFER_GOAL:
            out.append({"telegram_id": int(u), "name": e.get("name", ""),
                        "username": ("@" + e["username"]) if e.get("username") else "",
                        "refers": int(e["count"])})
    out.sort(key=lambda x: (-x["refers"], x["telegram_id"]))
    return out

def write_goal_file():
    """১০+ রেফারকারীদের লিস্ট refer_10plus.json এ সেভ"""
    data = {"goal": REFER_GOAL, "updated": now_bd().strftime("%Y-%m-%d %H:%M:%S"),
            "total": 0, "users": refer_goal_users()}
    data["total"] = len(data["users"])
    save_json(FILE_REFER_GOAL, data)
    return data

def refer_bar(n):
    filled = min(10, int(n * 10 / REFER_GOAL)) if REFER_GOAL else 10
    return "▰" * filled + "▱" * (10 - filled)

def refer_register(user, payload):
    """/start ref_<id> — শুধু নতুন ইউজার pending এ যাবে (জয়েন শেষ হলে কাউন্ট হবে)"""
    try:
        rid = int(payload[4:])
    except (ValueError, IndexError):
        return
    uid = user.id
    if rid == uid or user.is_bot or is_admin(uid): return
    s = str(uid)
    if s in referral["referred"] or s in referral["pending"]: return
    if s in public.get("names", {}): return            # আগে থেকেই বটের ইউজার
    referral["pending"][s] = rid
    save_refer()

def profile_link(uid, username=""):
    return f"https://t.me/{username}" if username else f"tg://user?id={uid}"

async def goal_check(bot, uid):
    """রেফার REFER_GOAL (১০) বা তার বেশি হলে মালিকের কাছে ইউজারনেম + প্রোফাইল লিংক সহ নোটিফিকেশন (একবারই)"""
    uid = int(uid)
    e = referral["users"].get(str(uid))
    if not e: return
    n = int(e.get("count", 0))
    if n < REFER_GOAL:
        if uid in referral["notified"]:           # কমিয়ে দিলে আবার ১০ ছুঁলে নতুন করে জানাবে
            referral["notified"].remove(uid); save_refer()
        return
    if uid in referral["notified"] or is_admin(uid): return
    referral["notified"].append(uid); save_refer()
    write_goal_file()
    un = e.get("username", "")
    link = profile_link(uid, un)
    text = (f"🏆 {REFER_GOAL} রেফার পূর্ণ! 🏆\n{LINE}\n"
            f"👤 নাম : {e.get('name','?')}\n"
            f"🔖 ইউজারনেম : {('@' + un) if un else '—'}\n"
            f"🆔 Telegram ID : {uid}\n"
            f"👥 মোট রেফার : {n}\n"
            f"🔗 প্রোফাইল : {link}\n{LINE}\n"
            f"✅ এখন ওর সাথে যোগাযোগ করে কাজটা করে দিন।")
    kb = InlineKeyboardMarkup([[cbtn("👤 ᴏᴘᴇɴ ᴘʀᴏꜰɪʟᴇ", "primary", url=link)]])
    for aid in OWNER_IDS:
        try: await bot.send_message(aid, text, reply_markup=kb,
                                    link_preview_options=LinkPreviewOptions(is_disabled=True))
        except Exception as ex: logger.warning(f"goal notify {aid}: {ex}")

async def refer_credit(context, user):
    """নতুন ইউজার ফোর্স-জয়েন পার করলে রেফারারের কাউন্ট +1 ও মালিকের কাছে নোটিফিকেশন"""
    s = str(user.id)
    rid = referral["pending"].pop(s, None)
    if rid is None: return
    if s in referral["referred"]:
        save_refer(); return
    referral["referred"][s] = rid
    e = _ref_entry(rid)
    if e.get("name", "").startswith("User "):      # রেফারার নাম জানা না থাকলে টেলিগ্রাম থেকে আনো
        try:
            ch = await context.bot.get_chat(rid)
            e["name"] = (ch.full_name or e["name"])[:40]; e["username"] = ch.username or ""
        except Exception: pass
    e["count"] = int(e.get("count", 0)) + 1
    total = e["count"]
    save_refer()
    if total >= REFER_GOAL: write_goal_file()

    await notify_admins(context.bot,
        f"🎁 নতুন রেফার!\n{LINE}\n"
        f"👤 রেফারার : {e.get('name','?')} ({rid})\n"
        f"🆕 জয়েন করেছে : {_who(user)}\n"
        f"📊 রেফারারের মোট : {total}")
    await goal_check(context.bot, rid)
    try:
        await context.bot.send_message(
            rid, f"🎉 A new member joined through your link!\n"
                 f"👥 Your total referrals: {total}/{REFER_GOAL}")
    except Exception as ex:
        logger.warning(f"refer notify {rid}: {ex}")

def build_myrefer(user):
    e = _ref_entry(user.id, user)
    save_refer()
    n = int(e["count"])
    rank, total = refer_rank(user.id)
    link = refer_link(user.id)
    uname = f"@{user.username}" if user.username else "—"
    goal_line = ("🏆 *Goal reached! Congratulations* 🎉" if n >= REFER_GOAL
                 else f"🎯 Only `{REFER_GOAL - n}` more to reach {REFER_GOAL}")
    text = (
        f"🎁 𝗠𝗬 𝗥𝗘𝗙𝗘𝗥 𝗣𝗥𝗢𝗙𝗜𝗟𝗘 🎁\n{LINE}\n"
        f"👤 *Name* : {md_escape(user.full_name or 'User')}\n"
        f"🔖 *Username* : {md_escape(uname)}\n"
        f"🆔 *Telegram ID* : `{user.id}`\n"
        f"🏅 *Rank* : `#{rank}` / {total}\n{LINE}\n"
        f"👥 *Total Referrals* : `{n}`\n"
        f"{refer_bar(n)}  `{n}/{REFER_GOAL}`\n"
        f"{goal_line}\n{LINE}\n"
        f"🔗 *Your referral link* (tap to copy)\n`{link}`\n{LINE}\n"
        f"📌 Anyone new who joins the bot through this link counts as your referral.\n{LINE}\n"
        f"💰 *1 Referral = 1 Coin* — spend your coins in 🛍 MyShop 👇"
    )
    rows = [[cbtn("🛍 ✨ ᴍʏꜱʜᴏᴘ ✨ 🪙", "success", callback_data=f"shop:open:{user.id}")],
            [buy_coins_btn(user.id)]]
    if BOT_USERNAME:
        share = ("https://t.me/share/url?url=" + link +
                 "&text=" + "🔥 MEDUSA LIKE BOT — Free Free Fire Likes! Join 👇")
        rows.append([cbtn("📤 ꜱʜᴀʀᴇ ʏᴏᴜʀ ʟɪɴᴋ", "primary", url=share)])
    return text, InlineKeyboardMarkup(rows)

async def myrefer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type != "private" and is_group_blocked(chat.id): return
    text, kb = build_myrefer(user)
    await reply(update, text, reply_markup=kb)

async def myshop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/myshop — শুধু 🛍 MyShop দেখায় (প্রিমিয়াম ডিজাইন)"""
    chat = update.effective_chat
    user = update.effective_user
    if chat.type != "private" and is_group_blocked(chat.id): return
    _ref_entry(user.id, user); save_refer()
    await reply(update, shop_text(user.id, user.first_name or "User"), reply_markup=shop_kb(user.id))

async def leaderboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/leaderboard — সবচেয়ে বেশি রেফারকারী টপ ১ এ"""
    chat = update.effective_chat
    user = update.effective_user
    if chat.type != "private" and is_group_blocked(chat.id): return
    rows = sorted(((u, e) for u, e in referral["users"].items() if int(e.get("count", 0)) > 0),
                  key=lambda x: (-int(x[1].get("count", 0)), x[0]))
    if not rows:
        await reply(update, f"🏆 *𝗥𝗘𝗙𝗘𝗥 𝗟𝗘𝗔𝗗𝗘𝗥𝗕𝗢𝗔𝗥𝗗*\n{LINE}\n⚠️ Nobody has referred anyone yet.\n\n🎁 Use `/myrefer` to get your link and climb to the top!"); return
    medals = ["🥇", "🥈", "🥉"]
    lines = [f"🏆 *𝗥𝗘𝗙𝗘𝗥 𝗟𝗘𝗔𝗗𝗘𝗥𝗕𝗢𝗔𝗥𝗗* 🏆\n{LINE}"]
    for i, (u, e) in enumerate(rows[:10], 1):
        n = int(e["count"])
        un = f" (@{e['username']})" if e.get("username") else ""
        star = " 🏅" if n >= REFER_GOAL else ""
        mark = medals[i-1] if i <= 3 else f"{i}."
        lines.append(f"{mark} *{md_escape(e.get('name','?'))}*{md_escape(un)}{star}\n      👥 Referrals : *{n}*")
    lines.append(LINE)
    me = referral["users"].get(str(user.id))
    if me and int(me.get("count", 0)) > 0:
        rank, total = refer_rank(user.id)
        lines.append(f"📍 *Your rank* : `#{rank}` / {total}  │  👥 `{int(me['count'])}`")
    else:
        lines.append("📍 You're not on the leaderboard yet — use `/myrefer` to get your link 🎁")
    lines.append(f"🏅 = {REFER_GOAL}+ referrals reached")
    await reply(update, "\n".join(lines))

@admin_only
async def all_user_refer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        await reply(update, "❌ ইনবক্সে ব্যবহার করুন।"); return
    rows = sorted(referral["users"].items(), key=lambda x: (-int(x[1].get("count", 0)), x[0]))
    rows = [(u, e) for u, e in rows if int(e.get("count", 0)) > 0]
    if not rows:
        await reply(update, f"📊 *𝗔𝗟𝗟 𝗥𝗘𝗙𝗘𝗥*\n{LINE}\n⚠️ এখনো কেউ রেফার করেনি।"); return
    total_refs = sum(int(e["count"]) for _, e in rows)
    goal_n = len(refer_goal_users())
    head = (f"📊 *𝗔𝗟𝗟 𝗨𝗦𝗘𝗥 𝗥𝗘𝗙𝗘𝗥*\n{LINE}\n"
            f"👥 রেফারকারী : `{len(rows)}`\n"
            f"🔗 মোট রেফার : `{total_refs}`\n"
            f"🏆 {REFER_GOAL}+ : `{goal_n}` জন\n{LINE}\n")
    medals = ["🥇", "🥈", "🥉"]
    chunks, cur = [], head
    for i, (u, e) in enumerate(rows, 1):
        n = int(e["count"])
        un = f" @{e['username']}" if e.get("username") else ""
        mark = medals[i-1] if i <= 3 else f"{i}."
        star = " 🏆" if n >= REFER_GOAL else ""
        line = (f"{mark} *{md_escape(e.get('name','?'))}*{md_escape(un)}{star}\n"
                f"    🆔 `{u}` │ 👥 *{n}*\n")
        if len(cur) + len(line) > 3600:
            chunks.append(cur); cur = ""
        cur += line
    cur += f"{LINE}\n✏️ `/med_x <id> <n>` – সেট | `+n` বাড়াও | `-n` কমাও"
    chunks.append(cur)
    for c in chunks:
        await reply(update, c)
    if goal_n:
        data = write_goal_file()
        try:
            with open(FILE_REFER_GOAL, "rb") as fh:
                await context.bot.send_document(
                    update.effective_chat.id, fh, filename=FILE_REFER_GOAL,
                    caption=f"🏆 {REFER_GOAL}+ রেফার — {data['total']} জন (Telegram ID সহ)")
        except Exception as ex:
            logger.warning(f"refer goal file: {ex}")

@owner_only
async def med_x_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usage = (f"✏️ *𝗠𝗘𝗗_𝗫*\n{LINE}\n"
             f"`/med_x <telegram id> <n>` → রেফার ঠিক `n` করো\n"
             f"`/med_x <telegram id> +5` → ৫ বাড়াও\n"
             f"`/med_x <telegram id> -3` → ৩ কমাও")
    a = context.args
    if len(a) != 2 or not a[0].isdigit() or not re.fullmatch(r"[+-]?\d+", a[1]):
        await reply(update, usage); return
    uid = int(a[0])
    old = refer_count(uid)
    val = int(a[1])
    new = old + val if a[1][0] in "+-" else val
    new = max(0, new)
    e = _ref_entry(uid)
    e["count"] = new
    save_refer()
    write_goal_file()
    await goal_check(context.bot, uid)
    await reply(update,
        f"✅ *𝗥𝗘𝗙𝗘𝗥 𝗨𝗣𝗗𝗔𝗧𝗘𝗗*\n{LINE}\n"
        f"👤 {md_escape(e.get('name','?'))}\n🆔 `{uid}`\n"
        f"📉 আগে : `{old}`\n📈 এখন : `{new}`")


# ══════════════════════════════════════════════════
#  🛍 MYSHOP — referral coins  (1 referral = 1 coin)
#  ➕ +1 daily like limit ........ 2 coins
#  ⚡ 7 days Auto Like ........... 7 coins   (daily 04:10 AM BD time)
#  ⚡ Auto Like কেনা যায় শুধু MAIN bot-এ (@MEDUSA_LIKE_BoT) — অন্য বট থেকে main bot-এ পাঠানো হয়
#  coins = referral count - coins spent   (shop.json এ spent/bonus/auto সেভ হয়)
# ══════════════════════════════════════════════════
FILE_SHOP = 'shop.json'
SHOP_LIMIT_PRICE = 2                 # প্রথম +1 limit = 2 coins; এরপর প্রতিবার দাম +1 (2, 3, 4, 5 ...)
SHOP_AUTO_PRICE = 7                  # legacy default; selected duration is priced 1 coin/day
AUTO_DAY_OPTIONS = (7, 10, 15, 30, 60, 90, 120, 150, 180)
MAIN_BOT_USERNAME = (os.getenv('MAIN_BOT_USERNAME') or 'MEDUSA_LIKE_BoT').lstrip('@')
MAIN_BOT_AUTO_URL = f"https://t.me/{MAIN_BOT_USERNAME}?start=shop_auto"
SHOP_CB_ACTS = ('lim', 'auto', 'days', 'back', 'srv', 'cancel', 'ok', 'home')   # এই callback থাকলে মেসেজটা Shop স্ক্রিন

def is_main_bot():
    return (BOT_USERNAME or "").strip().lstrip("@").lower() == MAIN_BOT_USERNAME.lower()

def is_shop_markup(markup):
    if not isinstance(markup, InlineKeyboardMarkup): return False
    for r in markup.inline_keyboard:
        for b in r:
            cd = getattr(b, 'callback_data', None) or ''
            p = cd.split(':')
            if len(p) >= 2 and p[0] == 'shop' and p[1] in SHOP_CB_ACTS: return True
    return False
SHOP_AUTO_DAYS = 7
AUTO_HOUR, AUTO_MINUTE = 4, 10       # BD time — প্রথম বটের মতোই 04:10 AM
AUTO_TIME_LABEL = "04:10 AM"
AUTO_MAX_TRIES = 3                   # একদিনে একটা UID-তে সর্বোচ্চ কয়বার চেষ্টা
AUTO_WAIT_SECS = 600                 # UID দেওয়ার জন্য ১০ মিনিট সময়
REGION_FLAGS = {"bd": "🇧🇩", "ind": "🇮🇳", "pk": "🇵🇰", "sg": "🇸🇬", "id": "🇮🇩", "br": "🇧🇷",
                "us": "🇺🇸", "ru": "🇷🇺", "th": "🇹🇭", "vn": "🇻🇳", "tw": "🇹🇼", "me": "🌍", "cis": "🌐"}

shop = {"users": {}, "auto": {}}
auto_tries = {}                      # (sub_key, date) -> চেষ্টার সংখ্যা
auto_lock = asyncio.Lock()

def save_shop(): save_json(FILE_SHOP, shop)

def shop_user(uid):
    u = shop.setdefault("users", {}).get(str(uid))
    if not isinstance(u, dict):
        u = {"spent": 0, "bonus": 0}
        shop["users"][str(uid)] = u
    u.setdefault("spent", 0); u.setdefault("bonus", 0); u.setdefault("gift", 0)
    return u

def shop_bonus(uid):
    return int(shop["users"].get(str(uid), {}).get("bonus", 0))

def limit_price(uid):
    """পরের +1 limit-এর দাম = বেস দাম + এ পর্যন্ত কেনা limit সংখ্যা"""
    return SHOP_LIMIT_PRICE + shop_bonus(uid)

def coin_balance(uid):
    u = shop["users"].get(str(uid), {})
    if not isinstance(u, dict): u = {}
    spent = int(u.get("spent", 0)); gift = int(u.get("gift", 0))
    return max(0, refer_count(uid) + gift - spent)

def user_autos(uid, active_only=True):
    out = [v for v in shop["auto"].values() if v.get("owner") == uid]
    return [v for v in out if not v.get("completed")] if active_only else out

def shop_text(uid, name=None):
    bal = coin_balance(uid)
    lim = get_pub_limit(uid)
    bonus = shop_bonus(uid)
    lim_s = "∞" if lim >= 999999 else str(lim)
    lines = [
        "💎━━━━━━━━━━━━━━━━━━💎",
        "   🛍 ✨ 𝗠𝗬𝗦𝗛𝗢𝗣 ✨ 🛍",
        "      👑 ᴘʀᴇᴍɪᴜᴍ ꜱᴛᴏʀᴇ 👑",
        "💎━━━━━━━━━━━━━━━━━━💎",
    ]
    if name:
        lines.append(f"👋 Welcome, *{md_escape(name)}*")
        lines.append(LINE)
    lines += [
        f"🪙 *Your Coins* : `{bal}`",
        f"📅 *Daily Like Limit* : `{lim_s}`" + (f"  _(+{bonus} bought)_" if bonus else ""),
        LINE,
        "🛒 *𝗔𝗩𝗔𝗜𝗟𝗔𝗕𝗟𝗘 𝗜𝗧𝗘𝗠𝗦*",
        "",
        f"➕ *+1 Daily Like Limit*",
        f"     ╰─ 💰 Next price : `{limit_price(uid)}` coins  _(+1 after every purchase)_",
        "",
        "⚡ *𝗔𝗨𝗧𝗢 𝗟𝗜𝗞𝗘*",
        "     ╰─ Choose duration: 7 / 10 / 15 / 30 / 60 / 90 days",
        "     ╰─ 💰 Price: 1 coin per day",
        LINE,
    ]
    act = user_autos(uid)
    if act:
        lines.append("📋 *Your Active Auto Likes*")
        for v in act[:5]:
            lines.append(f"  ▸ `{v['uid']}` ({v['region'].upper()}) — {v['days_remaining']} day(s) left")
        lines.append(LINE)
    lines += [
        "📌 *Everyone keeps their current limit* — it never goes down.",
        f"⏰ Auto Like runs daily at *{AUTO_TIME_LABEL}* (BD time).",
        "🎁 *1 Referral = 1 Coin* — invite friends with /myrefer",
        "💎━━━━━━━━━━━━━━━━━━💎",
    ]
    return "\n".join(lines)

COIN_STORE_TEXT = """💎 𝗠𝗘𝗗𝗨𝗦𝗔 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗦𝗧𝗢𝗥𝗘 💎
━━━━━━━━━━━━━━━━━━━━━━

🔥 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗟𝗜𝗞𝗘 𝗣𝗔𝗖𝗞𝗔𝗚𝗘𝗦 🔥

❤️‍🔥 𝗣𝗘𝗥 𝗗𝗔𝗬 ➜ 𝟮𝟬𝟬+ 𝗟𝗜𝗞𝗘

❤️‍🔥 𝟳 𝗗𝗔𝗬 ➜ 𝟮𝟬𝟬+ 𝗟𝗜𝗞𝗘 ➜ ৳𝟵𝟴
❤️‍🔥 𝟭𝟱 𝗗𝗔𝗬 ➜ 𝟮𝟬𝟬+ 𝗟𝗜𝗞𝗘 ➜ ৳𝟮𝟭𝟬
❤️‍🔥 𝟯𝟬 𝗗𝗔𝗬 ➜ 𝟮𝟬𝟬+ 𝗟𝗜𝗞𝗘 ➜ ৳𝟰𝟮𝟬
❤️‍🔥 𝟲𝟬 𝗗𝗔𝗬 ➜ 𝟮𝟬𝟬+ 𝗟𝗜𝗞𝗘 ➜ ৳𝟴𝟰𝟬
❤️‍🔥 𝟵𝟬 𝗗𝗔𝗬 ➜ 𝟮𝟬𝟬+ 𝗟𝗜𝗞𝗘 ➜ ৳𝟭𝟮𝟲𝟬
❤️‍🔥 𝟭𝟮𝟬 𝗗𝗔𝗬 ➜ 𝟮𝟬𝟬+ 𝗟𝗜𝗞𝗘 ➜ ৳𝟭𝟲𝟴𝟬

━━━━━━━━━━━━━━━━━━━━━━

🪙 𝗠𝗘𝗗𝗨𝗦𝗔 𝗖𝗢𝗜𝗡 𝗣𝗥𝗜𝗖𝗘 𝗟𝗜𝗦𝗧
━━━━━━━━━━━━━━━━━━━━━━

🪙 𝟭 𝗖𝗢𝗜𝗡 ➜ ৳𝟳 𝗧𝗔𝗞𝗔
🪙 𝟳 𝗖𝗢𝗜𝗡 ➜ ৳𝟰𝟵 𝗧𝗔𝗞𝗔
🪙 𝟭𝟬 𝗖𝗢𝗜𝗡 ➜ ৳𝟳𝟬 𝗧𝗔𝗞𝗔
🪙 𝟭𝟱 𝗖𝗢𝗜𝗡 ➜ ৳𝟭𝟬𝟱 𝗧𝗔𝗞𝗔
🪙 𝟮𝟬 𝗖𝗢𝗜𝗡 ➜ ৳𝟭𝟰𝟬 𝗧𝗔𝗞𝗔
🪙 𝟯𝟬 𝗖𝗢𝗜𝗡 ➜ ৳𝟮𝟭𝟬 𝗧𝗔𝗞𝗔
🪙 𝟰𝟬 𝗖𝗢𝗜𝗡 ➜ ৳𝟮𝟴𝟬 𝗧𝗔𝗞𝗔
🪙 𝟱𝟬 𝗖𝗢𝗜𝗡 ➜ ৳𝟯𝟱𝟬 𝗧𝗔𝗞𝗔

━━━━━━━━━━━━━━━━━━━━━━
🔥 𝗕𝗨𝗬 𝗡𝗢𝗪 • 𝗘𝗡𝗝𝗢𝗬 𝗣𝗥𝗘𝗠𝗜𝗨𝗠! 💎"""

def store_kb():
    return InlineKeyboardMarkup([[cbtn("🛒 ✨ 𝗕𝗨𝗬 ✨ 💎", "success", url=OWNER_LINK)]])

def buy_coins_btn(uid):
    return cbtn("🪙 ⚡ 𝗕𝗨𝗬 𝗖𝗢𝗜𝗡𝗦 & 𝗔𝗨𝗧𝗢 𝗟𝗜𝗞𝗘 💎", "primary", callback_data=f"shop:store:{uid}")

def shop_kb(uid):
    return InlineKeyboardMarkup([
        [cbtn(f"➕ ʙᴜʏ +1 ʟɪᴍɪᴛ  •  {limit_price(uid)} 🪙", "success", callback_data=f"shop:lim:{uid}")],
        [cbtn("⚡ 𝗔𝗨𝗧𝗢 𝗟𝗜𝗞𝗘", "primary", callback_data=f"shop:auto:{uid}")],
        [buy_coins_btn(uid)],
    ])

def auto_duration_screen(uid):
    rows = []
    for i in range(0, len(AUTO_DAY_OPTIONS), 3):
        rows.append([cbtn(f"💎 {d} ᴅᴀʏꜱ • {d} 🪙", "primary",
                          callback_data=f"shop:days:{uid}:{d}") for d in AUTO_DAY_OPTIONS[i:i+3]])
    rows.append([cbtn("🔙 ʙᴀᴄᴋ", "danger", callback_data=f"shop:home:{uid}")])
    body = (f"🐍 *𝗠𝗘𝗗𝗨𝗦𝗔 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗔𝗨𝗧𝗢 𝗟𝗜𝗞𝗘𝗦*\n{LINE}\n"
            f"🔥 *𝗗𝗔𝗜𝗟𝗬 𝟭𝟬𝟬+ 𝗔𝗨𝗧𝗢 𝗟𝗜𝗞𝗘𝗦*\n\n"
            "📅 Select how many days you want\n🪙 1 day = 1 coin\n"
            f"💰 Your balance: *{coin_balance(uid)} coins*\n{LINE}\n"
            "💎 *𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗤𝗨𝗔𝗟𝗜𝗧𝗬 • 𝗔𝗨𝗧𝗢 𝗦𝗘𝗥𝗩𝗜𝗖𝗘*\n"
            "🐍 *𝗣𝗢𝗪𝗘𝗥𝗘𝗗 𝗕𝗬 𝗠𝗘𝗗𝗨𝗦𝗔*")
    return body, InlineKeyboardMarkup(rows)

def auto_server_screen(uid, days):
    price = int(days)
    body = (f"⚡ *𝗠𝗘𝗗𝗨𝗦𝗔 {days} 𝗗𝗔𝗬𝗦 𝗔𝗨𝗧𝗢 𝗟𝗜𝗞𝗘*\n{LINE}\n"
            f"💰 *Price* : `{price}` coins   |   Your coins : `{coin_balance(uid)}`\n"
            f"⏰ Daily at *{AUTO_TIME_LABEL}* (BD time)\n{LINE}\n"
            "🌐 *Select your Free Fire server* 👇")
    regs = ["bd"] + sorted(r for r in ALLOWED_REGIONS if r != "bd")
    btns = [cbtn(f"{REGION_FLAGS.get(r, '🌐')} {r.upper()}", "primary",
                 callback_data=f"shop:srv:{uid}:{r}:{days}") for r in regs]
    rows = [btns[i:i + 3] for i in range(0, len(btns), 3)]
    rows.append([cbtn("❌ ᴄᴀɴᴄᴇʟ", "danger", callback_data=f"shop:cancel:{uid}")])
    return body, InlineKeyboardMarkup(rows)

async def shop_edit(q, text, kb):
    for pm in (ParseMode.MARKDOWN, None):
        t = text if pm else text.replace("*", "").replace("`", "")
        try:
            await q.edit_message_text(t, parse_mode=pm, reply_markup=kb,
                                      link_preview_options=LinkPreviewOptions(is_disabled=True))
            return True
        except Exception as e:
            if "not modified" in str(e).lower(): return True
    return False

def _main_only_text():
    return (f"⚡ *Auto Like can only be bought in our MAIN bot:*\n`@{MAIN_BOT_USERNAME}`\n"
            "👇 Tap the button below to open it.")

def _main_only_kb():
    return InlineKeyboardMarkup([[cbtn("🤖 ᴏᴘᴇɴ ᴍᴀɪɴ ʙᴏᴛ", "success", url=MAIN_BOT_AUTO_URL)]])

def _no_coins_text(uid, price=SHOP_AUTO_PRICE):
    return (f"❌ Not enough coins!\nYou need {price} coins, you have {coin_balance(uid)}.\n"
            f"🎁 1 Referral = 1 Coin — use /myrefer to invite friends.")

async def shop_auto_start(update, context):
    """গ্রুপ থেকে বটের ইনবক্সে আসার পর (/start shop_auto) — সার্ভার সিলেক্ট"""
    uid = update.effective_user.id
    context.user_data.pop("auto_wait", None); context.user_data.pop("auto_pending", None)
    if not is_main_bot():
        await reply(update, _main_only_text(), reply_markup=_main_only_kb()); return
    days = context.user_data.get("auto_days")
    if days in AUTO_DAY_OPTIONS:
        price = days
        if coin_balance(uid) < price:
            await update.message.reply_text(_no_coins_text(uid, price)); return
        text, kb = auto_server_screen(uid, days)
    else:
        text, kb = auto_duration_screen(uid)
    await reply(update, text, reply_markup=kb)

async def shop_uid_input(update, context, wait):
    uid = update.effective_user.id
    text = (update.message.text or "").strip()
    if not text.isdigit() or not (6 <= len(text) <= 15):
        await reply(update, "❌ *Invalid UID*\nSend a numeric Free Fire UID (6–15 digits).\nSend /cancel to stop."); return
    region = wait["region"]
    days = int(wait.get("days", SHOP_AUTO_DAYS))
    price = days
    if coin_balance(uid) < price:
        context.user_data.pop("auto_wait", None)
        await update.message.reply_text(_no_coins_text(uid, price)); return
    old = shop["auto"].get(f"{text}_{region}")
    if old and not old.get("completed"):
        context.user_data.pop("auto_wait", None)
        await reply(update, f"⚠️ *Auto Like is already active* on `{text}` ({region.upper()}).\n"
                            f"📅 {old['days_remaining']} day(s) left."); return
    context.user_data.pop("auto_wait", None)
    context.user_data["auto_pending"] = {"uid": text, "region": region, "days": days, "ts": _time.time()}
    msg = (f"🧾 *𝗖𝗢𝗡𝗙𝗜𝗥𝗠 𝗣𝗨𝗥𝗖𝗛𝗔𝗦𝗘*\n{LINE}\n"
           f"🆔 *UID* : `{text}`\n"
           f"🌐 *Server* : *{region.upper()}* {REGION_FLAGS.get(region, '')}\n"
           f"📅 *Duration* : *{days} days*\n"
           f"⏰ *Daily* : *{AUTO_TIME_LABEL}* (BD time)\n"
           f"💰 *Price* : *{price} coins*\n{LINE}\n"
           "⚠️ Double-check your UID — coins are deducted when you confirm.")
    kb = InlineKeyboardMarkup([[
        cbtn(f"✅ ᴄᴏɴꜰɪʀᴍ  •  {price} 🪙", "success", callback_data=f"shop:ok:{uid}:{days}"),
        cbtn("❌ ᴄᴀɴᴄᴇʟ", "danger", callback_data=f"shop:cancel:{uid}")]])
    await reply(update, msg, reply_markup=kb)

async def shop_callback(update, context):
    q = update.callback_query
    parts = (q.data or "").split(":")
    try:
        act, owner = parts[1], int(parts[2])
    except (IndexError, ValueError):
        await q.answer(); return
    user = q.from_user; uid = user.id
    if uid != owner:
        await q.answer("🚫 This button is not for you. Send /myshop to open your own.", show_alert=True); return
    extra = parts[3] if len(parts) > 3 else ""
    private = bool(q.message and q.message.chat.type == "private")

    if act in ("open", "home"):
        await q.answer(); await shop_edit(q, shop_text(uid), shop_kb(uid))

    elif act == "store":
        await q.answer()
        await shop_edit(q, COIN_STORE_TEXT, store_kb())

    elif act == "back":
        await q.answer()
        context.user_data.pop("auto_wait", None); context.user_data.pop("auto_pending", None)
        text, kb = build_myrefer(user); await shop_edit(q, text, kb)

    elif act == "cancel":
        context.user_data.pop("auto_wait", None); context.user_data.pop("auto_pending", None)
        await q.answer("Cancelled")
        await shop_edit(q, shop_text(uid), shop_kb(uid))

    elif act == "lim":
        if get_pub_limit(uid) >= 999999:
            await q.answer("♾ You already have unlimited likes!", show_alert=True); return
        price = limit_price(uid)
        if coin_balance(uid) < price:
            await q.answer(f"❌ Not enough coins! This limit costs {price}, you have {coin_balance(uid)}.", show_alert=True); return
        u = shop_user(uid)
        u["spent"] = int(u.get("spent", 0)) + price
        u["bonus"] = int(u.get("bonus", 0)) + 1
        save_shop()
        await q.answer(f"✅ Daily limit +1  →  now {get_pub_limit(uid)}  (next: {limit_price(uid)} coins)", show_alert=False)
        await shop_edit(q, shop_text(uid), shop_kb(uid))

    elif act in ("auto", "days", "srv", "ok") and not is_main_bot():
        await q.answer()
        await shop_edit(q, _main_only_text(), _main_only_kb())

    elif act == "auto":
        if not private:
            try:
                await q.answer(url=MAIN_BOT_AUTO_URL)
            except Exception:
                await q.answer("Open the bot inbox to select your Auto Like duration.", show_alert=True)
            return
        await q.answer()
        text, kb = auto_duration_screen(uid); await shop_edit(q, text, kb)

    elif act == "days":
        try: days = int(extra)
        except ValueError: days = 0
        if days not in AUTO_DAY_OPTIONS:
            await q.answer("Invalid duration", show_alert=True); return
        if coin_balance(uid) < days:
            await q.answer(f"❌ You need {days} coins. You have {coin_balance(uid)}.", show_alert=True); return
        await q.answer()
        text, kb = auto_server_screen(uid, days); await shop_edit(q, text, kb)

    elif act == "srv":
        region = extra.lower()
        try: days = int(parts[4])
        except (IndexError, ValueError): days = SHOP_AUTO_DAYS
        if region not in ALLOWED_REGIONS or days not in AUTO_DAY_OPTIONS:
            await q.answer("Invalid server or duration", show_alert=True); return
        if coin_balance(uid) < days:
            await q.answer(f"❌ You need {days} coins. You have {coin_balance(uid)}.", show_alert=True); return
        await q.answer()
        context.user_data["auto_wait"] = {"region": region, "days": days, "ts": _time.time()}
        text = (f"⚡ *{days} 𝗗𝗔𝗬𝗦 𝗔𝗨𝗧𝗢 𝗟𝗜𝗞𝗘*\n{LINE}\n"
                f"🌐 *Server* : *{region.upper()}* {REGION_FLAGS.get(region, '')}\n{LINE}\n"
                "🆔 *Now send your Free Fire UID* 👇")
        kb = InlineKeyboardMarkup([[cbtn("❌ ᴄᴀɴᴄᴇʟ", "danger", callback_data=f"shop:cancel:{uid}")]])
        await shop_edit(q, text, kb)

    elif act == "ok":
        p = context.user_data.get("auto_pending")
        if not p or _time.time() - p["ts"] > AUTO_WAIT_SECS:
            context.user_data.pop("auto_pending", None)
            await q.answer("⌛ Expired. Open MyShop again.", show_alert=True); return
        days = int(p.get("days", SHOP_AUTO_DAYS))
        price = days
        if coin_balance(uid) < price:
            context.user_data.pop("auto_pending", None)
            await q.answer(f"❌ You need {price} coins. You have {coin_balance(uid)}.", show_alert=True); return
        key = f"{p['uid']}_{p['region']}"
        old = shop["auto"].get(key)
        if old and not old.get("completed"):
            context.user_data.pop("auto_pending", None)
            await q.answer("⚠️ Already active on this UID.", show_alert=True); return
        context.user_data.pop("auto_pending", None)
        u = shop_user(uid)
        u["spent"] = int(u.get("spent", 0)) + price
        shop["auto"][key] = {
            "uid": p["uid"], "region": p["region"], "owner": uid, "days_total": days,
            "days_remaining": days, "added_at": today_str(), "last_liked": None,
            "last_auto_day": None, "total_likes": 0, "completed": False}
        save_shop()
        await q.answer("✅ Auto Like activated!")
        now = now_bd()
        first = ("🚀 First like is being sent within a minute!" if (now.hour, now.minute) >= (AUTO_HOUR, AUTO_MINUTE)
                 else f"🚀 First like today at *{AUTO_TIME_LABEL}* (BD time).")
        text = (f"✅ *𝗔𝗨𝗧𝗢 𝗟𝗜𝗞𝗘 𝗔𝗖𝗧𝗜𝗩𝗔𝗧𝗘𝗗*\n{LINE}\n"
                f"🆔 *UID* : `{p['uid']}`\n"
                f"🌐 *Server* : *{p['region'].upper()}* {REGION_FLAGS.get(p['region'], '')}\n"
                f"📅 *Days* : *{days}*\n"
                f"⏰ *Daily* : *{AUTO_TIME_LABEL}* (BD time)\n"
                f"💰 *Coins left* : *{coin_balance(uid)}*\n{LINE}\n{first}")
        await shop_edit(q, text, InlineKeyboardMarkup([[cbtn("🛍 ᴍʏꜱʜᴏᴘ", "success", callback_data=f"shop:home:{uid}")]]))
        await notify_admins(context.bot,
            f"🛒 নতুন Auto Like কেনা হয়েছে!\n{LINE}\n👤 {_who(user)}\n"
            f"🆔 UID : {p['uid']}\n🌐 সার্ভার : {p['region'].upper()}\n📅 Days : {days}\n💰 কয়েন কাটা : {price}")
    else:
        await q.answer()

# ══════════════════════════════════════════════════
#  💰 /bal — কারো মেসেজে রিপ্লাই দিয়ে /bal = তার কয়েন | এডমিন 🎁 Gift Coins
# ══════════════════════════════════════════════════
GIFT_WAIT_SECS = 300

def bal_text(target):
    uid = target.id
    n = refer_count(uid)
    u = shop["users"].get(str(uid), {})
    gift = int(u.get("gift", 0)); spent = int(u.get("spent", 0))
    uname = f"@{target.username}" if target.username else "—"
    return (f"💰 *𝗖𝗢𝗜𝗡 𝗕𝗔𝗟𝗔𝗡𝗖𝗘*\n{LINE}\n"
            f"👤 *Name* : {md_escape(target.full_name or 'User')}\n"
            f"🔖 *Username* : {md_escape(uname)}\n"
            f"🆔 *ID* : `{uid}`\n{LINE}\n"
            f"🪙 *Coins* : `{coin_balance(uid)}`\n"
            f"👥 Referrals : `{n}`  |  🎁 Gifted : `{gift}`  |  🛒 Spent : `{spent}`")

async def bal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat; me = update.effective_user
    if chat.type != "private" and is_group_blocked(chat.id): return
    m = update.effective_message
    target = m.reply_to_message.from_user if (m and m.reply_to_message and m.reply_to_message.from_user) else me
    if target.is_bot:
        await reply(update, "🤖 Bots have no coins."); return
    kb = None
    if is_owner(me.id):                          # 🎁 Coin gift শুধু মূল মালিকের জন্য
        kb = InlineKeyboardMarkup([[cbtn("🎁 ɢɪꜰᴛ ᴄᴏɪɴꜱ", "success", callback_data=f"bal:gift:{me.id}:{target.id}")]])
    await reply(update, bal_text(target), reply_markup=kb)

async def bal_callback(update, context):
    q = update.callback_query
    p = (q.data or "").split(":")
    try: act, admin_id, target_id = p[1], int(p[2]), int(p[3])
    except (IndexError, ValueError):
        await q.answer(); return
    if q.from_user.id != admin_id or not is_owner(q.from_user.id):
        await q.answer("⛔ Admin only.", show_alert=True); return
    if act == "gift":
        context.user_data["gift_wait"] = {"target": target_id, "chat": q.message.chat.id, "ts": _time.time()}
        await q.answer()
        try:
            await q.message.reply_text(
                f"🎁 কত কয়েন গিফট করবেন? শুধু সংখ্যা লিখুন 👇\n🆔 `{target_id}`\n(বাতিল: /cancel)",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=ForceReply(selective=True, input_field_placeholder="কয়েনের সংখ্যা"))
        except Exception as e: logger.warning(f"gift prompt: {e}")
    else:
        await q.answer()

async def gift_input(update, context):
    """এডমিনের পরের মেসেজের সংখ্যাই ওই ইউজারের কয়েনে যোগ হবে"""
    w = context.user_data.get("gift_wait")
    m = update.effective_message
    if not w or not m or not update.effective_user or not is_owner(update.effective_user.id): return
    if m.chat_id != w["chat"] or is_group_muted(m.chat_id): return
    if _time.time() - w["ts"] > GIFT_WAIT_SECS:
        context.user_data.pop("gift_wait", None); return
    t = (m.text or "").strip()
    if not t.isdigit() or not (1 <= int(t) <= 10_000_000):
        await reply(update, "❌ শুধু সংখ্যা লিখুন (যেমন `5`)। বাতিল: /cancel")
        raise ApplicationHandlerStop
    amt = int(t); tid = w["target"]
    context.user_data.pop("gift_wait", None)
    u = shop_user(tid)
    if not isinstance(u, dict): u = shop["users"][str(tid)] = {"spent": 0, "bonus": 0}
    u["gift"] = int(u.get("gift", 0)) + amt
    save_shop()
    await reply(update, f"✅ *𝗚𝗜𝗙𝗧 𝗦𝗘𝗡𝗧*\n{LINE}\n🆔 `{tid}`\n🎁 +`{amt}` coins\n🪙 এখন মোট : `{coin_balance(tid)}`")
    try:
        await context.bot.send_message(tid, f"🎁 *You received {amt} coins!*\n🪙 Your coins : `{coin_balance(tid)}`\n🛍 Spend them in /myshop",
                                       parse_mode=ParseMode.MARKDOWN)
    except Exception: pass
    raise ApplicationHandlerStop

# ───────── daily auto-like (প্রতিদিন 04:10 AM BD) ─────────
async def _auto_send(bot, owner, text):
    plain = text.replace("*", "").replace("`", "")
    try:
        await bot.send_message(owner, text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        try: await bot.send_message(owner, plain)
        except Exception as e: logger.warning(f"auto notify {owner}: {e}")
    for gid, info in list(shop.get("auto_groups", {}).items()):
        try:
            if not isinstance(info, dict): info = {}
            title = md_escape(info.get("name") or "MEDUSA AUTO LIKE GROUP")
            header = f"🐍 *𝗠𝗘𝗗𝗨𝗦𝗔 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗔𝗨𝗧𝗢 𝗟𝗜𝗞𝗘*\\n📢 *{title}*\\n{LINE}\\n"
            await bot.send_message(int(gid), header + text, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.warning(f"auto group notify {gid}: {e.__class__.__name__}")

async def _auto_one(context, key, today):
    v = shop["auto"].get(key)
    if not v or v.get("completed"): return
    uid, region, owner = v["uid"], v["region"], v["owner"]
    try:
        data = await call_all_four_apis(region, uid)
    except Exception as e:
        logger.error(f"auto like crashed {uid}: {e}", exc_info=True)
        data = {"error": "internal"}

    if not data or "error" in data or data.get("status") not in (1, 2):
        n = auto_tries.get((key, today), 0) + 1
        auto_tries[(key, today)] = n
        logger.warning(f"auto like failed uid={uid} try={n}: {(data or {}).get('error', data)}")
        if n >= AUTO_MAX_TRIES:
            await _auto_send(context.bot, owner,
                f"⚠️ *Auto Like* could not reach `{uid}` today.\n"
                f"No day was deducted — we will try again tomorrow at {AUTO_TIME_LABEL}.")
        return

    given = _to_int(data.get("LikesGivenByAPI"))
    ok = data.get("status") == 1 and given > 0
    if ok:
        v["total_likes"] = int(v.get("total_likes", 0)) + given
        v["last_liked"] = today
    v["last_auto_day"] = today
    v["days_remaining"] = int(v["days_remaining"]) - 1
    done = v["days_remaining"] <= 0
    if done: v["completed"] = True
    save_shop()

    tail = (f"\n⚡ *Auto Like* — {max(0, v['days_remaining'])} day(s) left"
            if not done else f"\n🏁 *Auto Like finished* — total `{v['total_likes']}` likes sent. Thank you!")
    if ok:
        msg = fmt_success(data.get("used_api", "?"), data.get("PlayerNickname", "Unknown"),
                          data.get("UID", uid), region, data.get("LikesbeforeCommand", 0), given,
                          data.get("LikesafterCommand", 0), data.get("per_api", {})) + tail
    else:
        msg = (f"⏭ *Auto Like* — no likes added to `{uid}` today (already maxed / limit reached)." + tail)
    await _auto_send(context.bot, owner, msg)

async def auto_tick(context):
    now = now_bd()
    if (now.hour, now.minute) < (AUTO_HOUR, AUTO_MINUTE): return
    if auto_lock.locked(): return
    today = today_str()
    pending = [k for k, v in shop["auto"].items()
               if not v.get("completed") and v.get("last_auto_day") != today
               and auto_tries.get((k, today), 0) < AUTO_MAX_TRIES]
    if not pending: return
    async with auto_lock:
        for k in pending:
            await _auto_one(context, k, today)
            await asyncio.sleep(0.5)
    for kk in [x for x in auto_tries if x[1] != today]: auto_tries.pop(kk, None)



@owner_only
async def auto_like_allow_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """মূল মালিকের অনুমতিতে বর্তমান গ্রুপে Auto Like ফলাফল পাঠানোর ব্যবস্থা।"""
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return
    if chat.type not in ("group", "supergroup"):
        await reply(update, "❌ এই কমান্ডটি যে গ্রুপে Auto Like ফলাফল চান, সেই গ্রুপে ব্যবহার করুন।")
        return
    if not isinstance(shop.get("auto_groups"), dict):
        shop["auto_groups"] = {}
    gid = str(chat.id)
    if gid in shop["auto_groups"]:
        await reply(update, "✅ এই গ্রুপে Auto Like ফলাফল পাঠানো আগে থেকেই চালু আছে।")
        return
    shop["auto_groups"][gid] = {"name": chat.title or "MEDUSA AUTO LIKE GROUP", "added_by": user.id}
    save_shop()
    await reply(update, "🐍 *MEDUSA AUTO LIKE*\n━━━━━━━━━━━━━━━━━━━━\n✅ এই গ্রুপে Auto Like ফলাফল পাঠানো চালু হয়েছে।", parse_mode=ParseMode.MARKDOWN)


USER_MENU = [
    ("myrefer", "🎁 Referral link, coins & MyShop"),
    ("myshop", "🛍 MyShop — spend your coins"),
    ("auto_like_allow", "Allow Auto Like results in this group"),
    ("bal", "💰 Coin balance (reply to someone to see theirs)"),
    ("leaderboard", "🏆 Referral leaderboard"),
    ("start", "Start the bot"),
    ("like", "Get free likes (BD)"),
    ("premium", "💎 Premium likes (BD)"),
    ("myinfo", "View my limit"),
    ("top", "Today's top users"),
    ("id", "Group / User ID"),
    ("help", "Guide to all commands"),
]
ADMIN_MENU = USER_MENU + [
    ("all_user_refer", "👑 সবার রেফার লিস্ট"),
    ("admin", "👑 এডমিন প্যানেল"),
    ("cancel", "কাজ বাতিল"),
]
OWNER_MENU = ADMIN_MENU + [("med_x", "👑 রেফার/কয়েন হিসাব পরিবর্তন")]

async def setup_command_menu(app):
    """'/' চাপলে যে মেনু আসে — /myrefer সবার উপরে"""
    try:
        await app.bot.set_my_commands([BotCommand(c, d) for c, d in USER_MENU])
    except Exception as e:
        logger.warning(f"set_my_commands: {e}")
    for aid in ADMIN_IDS:
        try:
            menu = OWNER_MENU if is_owner(aid) else USER_MENU + [("cancel", "কাজ বাতিল")]
            await app.bot.set_my_commands([BotCommand(c, d) for c, d in menu],
                                          scope=BotCommandScopeChat(chat_id=aid))
        except Exception as e:      # এডমিন আগে বটে /start না দিলে এটা ফেল করে — সমস্যা নেই
            logger.warning(f"admin menu {aid}: {e}")

# ══════════════════════════════════════════════════
#  POST_INIT
# ══════════════════════════════════════════════════
async def post_init(app):
    global BOT_USERNAME, _BOT_REF
    _BOT_REF = app.bot
    me = await app.bot.get_me()
    BOT_USERNAME = me.username or ""
    logger.info(f"Bot username: @{BOT_USERNAME}")
    await setup_command_menu(app)

# ══════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════
def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN missing in .env"); return
    load_data()
    term.set_clock(print_banner())
    term.start(); refresh_status()

    # বড় কানেকশন পুল: একসাথে অনেক ইউজারের মেসেজ/এডিট পাঠাতে "Pool timeout" হবে না
    req = HTTPXRequest(connection_pool_size=256, pool_timeout=10.0,
                       connect_timeout=15.0, read_timeout=20.0, write_timeout=20.0)
    bot = AddGroupBot(token=BOT_TOKEN, request=req)
    # concurrent_updates: আগে একজনের লাইক শেষ না হওয়া পর্যন্ত বাকি সবাই লাইনে দাঁড়িয়ে থাকত
    app = (Application.builder().bot(bot).post_init(post_init)
           .concurrent_updates(256).build())

    if app.job_queue:
        app.job_queue.run_daily(reset_midnight,
                                time=time(hour=0, minute=0, second=0, tzinfo=BD_TZ),
                                days=tuple(range(7)))
        app.job_queue.run_daily(daily_report,
                                time=time(hour=23, minute=59, second=0, tzinfo=BD_TZ),
                                days=tuple(range(7)))

    if app.job_queue:
        app.job_queue.run_repeating(auto_tick, interval=60, first=20,
                                    job_kwargs={"misfire_grace_time": 60, "coalesce": True})

    # muted গ্রুপ আগে ফিল্টার (সবার আগে চলে)
    app.add_handler(TypeHandler(Update, mute_gate), group=-1)

    # User commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("myinfo", myinfo_cmd))
    app.add_handler(CommandHandler("apistatus", apistatus_cmd))
    app.add_handler(CommandHandler("apireset", apireset_cmd))
    app.add_handler(CommandHandler("myrefer", myrefer_cmd))
    app.add_handler(CommandHandler("myshop", myshop_cmd))
    app.add_handler(CommandHandler("auto_like_allow", auto_like_allow_cmd))
    app.add_handler(CommandHandler("bal", bal_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gift_input), group=-2)   # আলাদা group: mute_gate (-1) ও বাকি হ্যান্ডলারের সঙ্গে ধাক্কা লাগে না
    app.add_handler(CallbackQueryHandler(bal_callback, pattern=r"^bal:"))
    app.add_handler(CommandHandler("leaderboard", leaderboard_cmd))
    app.add_handler(CommandHandler("all_user_refer", owner_only(all_user_refer_cmd)))
    app.add_handler(CommandHandler("med_x", owner_only(med_x_cmd)))
    app.add_handler(CommandHandler("premium", like100_cmd))
    app.add_handler(CommandHandler("like", like_cmd))
    app.add_handler(CommandHandler("max", max_like_cmd))
    app.add_handler(CommandHandler(["max_like_on", "max_on"], owner_only(max_like_on_cmd)))
    app.add_handler(CommandHandler(["max_like_off", "max_off"], owner_only(max_like_off_cmd)))
    app.add_handler(CommandHandler("tg_id", tg_id_cmd))
    app.add_handler(CommandHandler("id", id_cmd))

    # Photo
    app.add_handler(CommandHandler("set_photo_like_ms", owner_only(set_photo_cmd)))
    # ছবির caption-এ লেখা কমান্ডও কাজ করবে (CommandHandler caption দেখে না)
    app.add_handler(MessageHandler(filters.PHOTO & filters.CaptionRegex(r"(?i)^/set_photo_like_ms"), owner_only(set_photo_cmd)))
    app.add_handler(CommandHandler("remove_photo", owner_only(remove_photo_cmd)))

    # Block
    app.add_handler(CommandHandler("Bend_group", bend_group_cmd))
    app.add_handler(CommandHandler("Bend_group_id", bend_group_id_cmd))
    app.add_handler(CommandHandler("Unblock_group_id", unblock_group_id_cmd))
    app.add_handler(CommandHandler("blocked_groups", blocked_groups_cmd))

    # 100-Like
    app.add_handler(CommandHandler("premium_bot_open", owner_only(bot100_on)))
    app.add_handler(CommandHandler("premium_bot_off", owner_only(bot100_off)))
    app.add_handler(CommandHandler(["premium_allow", "100_like_allow"], owner_only(allow_100like_group)))

    # Public
    app.add_handler(CommandHandler("public_bot_on", owner_only(pub_on)))
    app.add_handler(CommandHandler("public_bot_off", owner_only(pub_off)))
    app.add_handler(CommandHandler("public_bot_allow", owner_only(pub_allow)))

    # VIP
    app.add_handler(CommandHandler("VIP", owner_only(vip_cmd)))
    app.add_handler(CommandHandler("banvip", owner_only(banvip_cmd)))
    app.add_handler(CommandHandler("vip_list", owner_only(vip_list_cmd)))

    # Force-Join
    app.add_handler(CommandHandler("add_group", owner_only(add_group_cmd)))
    app.add_handler(CommandHandler("ban_add_group", owner_only(ban_add_group_cmd)))
    app.add_handler(CommandHandler("add_channel", owner_only(add_channel_cmd)))
    app.add_handler(CommandHandler("ban_add_channel", owner_only(ban_add_channel_cmd)))

    # Shared
    app.add_handler(CommandHandler("admin", owner_only(admin_cmd)))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("user_like", user_like_cmd))
    app.add_handler(CommandHandler(["setlimit_premium", "setlimit100"], owner_only(setlimit100_cmd)))
    app.add_handler(CommandHandler("setlimitpub", owner_only(setlimitpub_cmd)))
    app.add_handler(CommandHandler("api", owner_only(api_info)))
    app.add_handler(CommandHandler("broadcast", owner_only(broadcast_cmd)))
    app.add_handler(CommandHandler("cancel", cancel_cmd))

    # Mute
    app.add_handler(CommandHandler("like_bot_mute", owner_only(like_bot_mute_cmd)))
    app.add_handler(CommandHandler("like_bot_unmute", owner_only(like_bot_unmute_cmd)))
    app.add_handler(CommandHandler("muted_groups", owner_only(muted_groups_cmd)))

    # New
    app.add_handler(CommandHandler(["ban_user", "public_like_ban"], ban_user_cmd))
    app.add_handler(CommandHandler(["unban_user", "public_like_unban"], unban_user_cmd))
    app.add_handler(CommandHandler("public_mode", owner_only(public_mode_cmd)))
    app.add_handler(CommandHandler("groups", owner_only(groups_cmd)))
    app.add_handler(CommandHandler("backup", owner_only(backup_cmd)))
    app.add_handler(CommandHandler("top", top_cmd))
    app.add_handler(CommandHandler("api_check", api_check_cmd))

    # Chat member
    app.add_handler(ChatMemberHandler(on_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(shop_callback, pattern=r"^shop:"))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, private_fallback))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler_auto))

    app.add_error_handler(global_error_handler)

    logger.info(f"🤖 Bot running — {len(APIS)} APIs")

    try:
        app.run_polling(allowed_updates=Update.ALL_TYPES, bootstrap_retries=-1)
    except KeyboardInterrupt:
        pass
    finally:
        term.stop()

if __name__ == "__main__":
    main()
