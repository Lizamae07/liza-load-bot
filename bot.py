import os
import sqlite3

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes


TOKEN = os.environ.get("BOT_TOKEN")


# =========================
# DATABASE
# =========================

def init_db():
    conn = sqlite3.connect("members.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            telegram_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            branch TEXT,
            balance REAL DEFAULT 0,
            status TEXT DEFAULT 'Active'
        )
    """)

    conn.commit()
    conn.close()


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "🌐 GLOBE & TM PROMO",
                url="https://t.me/lizaloadpricelist"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Welcome to Liza's Load Bot!\n\n"
        "Use /create to register.\n"
        "Use /bank to check your account.\n"
        "Use /pl to view the pricelist.",
        reply_markup=reply_markup
    )


# =========================
# CREATE ACCOUNT
# =========================

async def create(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    conn = sqlite3.connect("members.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT telegram_id FROM members WHERE telegram_id = ?",
        (user.id,)
    )

    existing = cursor.fetchone()

    if existing:
        await update.message.reply_text(
            "✅ You are already registered."
        )
        conn.close()
        return

    cursor.execute("""
        INSERT INTO members
        (telegram_id, first_name, username, branch, balance, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user.id,
        user.first_name,
        user.username or "",
        "A",
        0,
        "Active"
    ))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        "✅ Account created successfully!\n\n"
        f"👤 Name: {user.first_name}\n"
        "🏢 Branch: A\n"
        "💰 Balance: ₱0.00\n"
        "📌 Status: Active"
    )


# =========================
# BANK
# =========================

async def bank(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    conn = sqlite3.connect("members.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT first_name, username, branch, balance, status
        FROM members
        WHERE telegram_id = ?
    """, (user.id,))

    member = cursor.fetchone()
    conn.close()

    if not member:
        await update.message.reply_text(
            "❌ You are not registered yet.\n\n"
            "Use /create first."
        )
        return

    first_name, username, branch, balance, status = member

    await update.message.reply_text(
        "🏦 YOUR BANK ACCOUNT\n\n"
        f"👤 Name: {first_name}\n"
        f"🔹 Username: @{username if username else 'none'}\n"
        f"🏢 Branch: {branch}\n"
        f"💰 Balance: ₱{balance:.2f}\n"
        f"📌 Status: {status}"
    )


# =========================
# ADD BALANCE
# =========================

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if not context.args:
        await update.message.reply_text(
            "Usage:\n/add 100"
        )
        return

    try:
        amount = float(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a valid amount."
        )
        return

    if amount <= 0:
        await update.message.reply_text(
            "❌ Amount must be greater than 0."
        )
        return

    conn = sqlite3.connect("members.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT balance FROM members WHERE telegram_id = ?",
        (user.id,)
    )

    member = cursor.fetchone()

    if not member:
        conn.close()
        await update.message.reply_text(
            "❌ Please use /create first."
        )
        return

    new_balance = member[0] + amount

    cursor.execute(
        "UPDATE members SET balance = ? WHERE telegram_id = ?",
        (new_balance, user.id)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"✅ Added ₱{amount:.2f}\n"
        f"💰 New Balance: ₱{new_balance:.2f}"
    )


# =========================
# DEDUCT BALANCE
# =========================

async def deduct(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if not context.args:
        await update.message.reply_text(
            "Usage:\n/deduct 100"
        )
        return

    try:
        amount = float(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a valid amount."
        )
        return

    if amount <= 0:
        await update.message.reply_text(
            "❌ Amount must be greater than 0."
        )
        return

    conn = sqlite3.connect("members.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT balance FROM members WHERE telegram_id = ?",
        (user.id,)
    )

    member = cursor.fetchone()

    if not member:
        conn.close()
        await update.message.reply_text(
            "❌ Please use /create first."
        )
        return

    balance = member[0]

    if amount > balance:
        conn.close()
        await update.message.reply_text(
            f"❌ Insufficient balance.\n"
            f"💰 Current Balance: ₱{balance:.2f}"
        )
        return

    new_balance = balance - amount

    cursor.execute(
        "UPDATE members SET balance = ? WHERE telegram_id = ?",
        (new_balance, user.id)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"✅ Deducted ₱{amount:.2f}\n"
        f"💰 New Balance: ₱{new_balance:.2f}"
    )


# =========================
# PRICELIST
# =========================


async def pl(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("🌐 GLOBE AND TM PROMO", url="https://t.me/lizaloadpricelist")],
        [InlineKeyboardButton("📱 SMART AND TNT PROMO", url="https://t.me/lizaloadpricelist")],
        [InlineKeyboardButton("📡 DITO PROMO", url="https://t.me/lizaloadpricelist")]
    ]

    await update.message.reply_text(
        "📋 LIZA'S LOAD PRICELIST\n\nChoose a network below:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# MAIN
# =========================

def main():

    init_db()

    if not TOKEN:
        print("❌ BOT_TOKEN is missing!")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("create", create))
    app.add_handler(CommandHandler("bank", bank))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("deduct", deduct))
    app.add_handler(CommandHandler("pl", pl))

    print("🤖 Bot is running...")

    port = int(os.environ.get("PORT", 10000))
    hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")

    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TOKEN,
        webhook_url=f"https://{hostname}/{TOKEN}"
    )


if __name__ == "__main__":
    main()
