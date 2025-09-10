import os
import json
import threading
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# -----------------------------
# Flask Keep-Alive
# -----------------------------
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "✅ Pancono Airdrop Bot is Alive!"

def run():
    PORT = int(os.environ.get("PORT", 8080))  # Replit port
    app_flask.run(host="0.0.0.0", port=PORT)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# -----------------------------
# Database Setup
# -----------------------------
DB_FILE = "database.json"
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({"users": {}}, f)

def load_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# -----------------------------
# Global Receiver / Admin
# -----------------------------
GLOBAL_RECEIVER_ID = 7194082974  # 🔴 Replace with your Telegram ID

# -----------------------------
# Inline Keyboard (visible for all users)
# -----------------------------
def get_keyboard(user_id: str):
    app_url = f"https://{os.getenv('REPLIT_DEV_DOMAIN', 'localhost:8080')}/"
    keyboard = [
        [InlineKeyboardButton("📊 Account", callback_data="account")],
        [InlineKeyboardButton("🌐 Open App", url=app_url)],
        [InlineKeyboardButton("🛠 Admin Panel", callback_data="admin")]  # 👈 Always visible now
    ]
    return InlineKeyboardMarkup(keyboard)

# -----------------------------
# Auto Show Message + Buttons
# -----------------------------
async def show_main_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db = load_db()

    # Ensure user exists in DB
    if user_id not in db["users"]:
        db["users"][user_id] = {"balance": 0, "referred_by": None, "referrals": 0}
        save_db(db)

    # Message to display
    message = (
        "⚠️ Sometimes the Panno App or Wallet Bot may go offline. This is intentional.\n\n"
        "We periodically close and reopen access to ensure that the private keys of "
        "Pancono Coins remain limited to only a few users."
    )

    await update.effective_chat.send_message(
        text=message,
        reply_markup=get_keyboard(user_id)
    )

# -----------------------------
# Handle Inline Buttons
# -----------------------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    db = load_db()

    if query.data == "account":
        balance = db["users"][user_id]["balance"]
        referrals = db["users"][user_id]["referrals"]
        referral_link = f"https://t.me/{context.bot.username}?start={user_id}"
        text = (
            f"👤 *Your Account*\n\n"
            f"💰 Balance: {balance} PANNO\n"
            f"👥 Referrals: {referrals}\n"
            f"🔗 Referral Link: {referral_link}"
        )
        await query.answer()
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_keyboard(user_id))

    elif query.data == "admin":  # 👈 Now anyone can access
        admin_balance = db[str(GLOBAL_RECEIVER_ID)]["balance"] if str(GLOBAL_RECEIVER_ID) in db["users"] else 0
        total_users = len(db["users"])
        text = (
            f"🛠 *Admin Panel*\n\n"
            f"👑 Global Earnings (Mr A): {admin_balance} PANNO\n"
            f"👥 Total Registered Users: {total_users}"
        )
        await query.answer()
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_keyboard(user_id))

# -----------------------------
# Main
# -----------------------------
def main():
    keep_alive()  # Start Flask server in background

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not found in Replit Secrets!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # Catch all messages (no need for /start)
    app.add_handler(MessageHandler(filters.ALL, show_main_message))
    app.add_handler(CallbackQueryHandler(button))

    print("✅ Bot started, polling for updates...")
    app.run_polling()

if __name__ == "__main__":
    main()
