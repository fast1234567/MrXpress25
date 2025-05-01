import logging
import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,
)

# Enable logging
logging.basicConfig(level=logging.INFO)

# Replace with your bot token
TOKEN = "7929962828:AAHhacl36aCYMYo4kKWnIfqw63jUgkOyAsk"  # ⚠️ Replace with your own token

# SQLite setup
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        warns INTEGER DEFAULT 0
    )
""")
conn.commit()

# Bad words & filters
bad_words = [
    "spam", "click here", "free", "deal", "girl", "boy", "fake", "scam", "weast",
    "dust", "no use", "usdt", "Doller", "buy", "sell", "usd"
]

auto_replies = {
    "how to join": "🔗 Use the group link to join.",
    "admin": "👮‍♂️ Admin is currently offline. 💬 They will reply to you as soon as they're online.",
    "dm": "📩 Admin is offline now. 💬 Once online, they’ll respond immediately.",
    "rules": "📜 Type /rules to read group rules.",
    "hello": "👋 Hey there! 😊 How can I help you today?",
    "what's up": "🤖 I'm just here to keep the group safe and fun! 🎉"
}

fun_replies = [
    "😜 Let's get this party started!",
    "😂 Haha, you're funny!",
    "🤩 I can't stop laughing!",
    "🎉 This is the most fun I've had all day!"
]

# Welcome new members
def welcome(update: Update, context: CallbackContext):
    for user in update.message.new_chat_members:
        update.message.reply_text(
            f"🎉✨ வணக்கம் {user.full_name} ✨🎉\n\n"
            "💥 XPRESS குழுவிற்கு வரவேற்கிறோம்! 💥\n\n"
            "நான் MrXpress! உங்களுக்கு என்ன உதவி வேண்டும்? 😎✨"
        )

# Member left
def left(update: Update, context: CallbackContext):
    user = update.message.left_chat_member
    update.message.reply_text(f"👋 {user.full_name} குழுவிலிருந்து விலகினார்.")

# Message filter
def filter_all(update: Update, context: CallbackContext):
    msg = update.message
    text = msg.text.lower() if msg.text else ""

    is_admin = any(admin.user.id == msg.from_user.id for admin in context.bot.get_chat_administrators(update.effective_chat.id))

    if not is_admin:
        if msg.forward_date:
            msg.delete()
        if any(x in text for x in ["http", "www", "@"]):
            msg.delete()
        if any(word in text for word in bad_words):
            msg.delete()

    for key in auto_replies:
        if key in text:
            msg.reply_text(auto_replies[key])
            return

    if "fun" in text or "joke" in text:
        msg.reply_text(random.choice(fun_replies))

# Warn user
def warn(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        update.message.reply_text("⚠️ Reply to the user's message to warn.")
        return

    user = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    uid = user.id

    cursor.execute("SELECT warns FROM users WHERE id = ?", (uid,))
    row = cursor.fetchone()

    if row:
        warns = row[0] + 1
        cursor.execute("UPDATE users SET warns = ? WHERE id = ?", (warns, uid))
    else:
        warns = 1
        cursor.execute("INSERT INTO users (id, warns) VALUES (?, ?)", (uid, warns))

    conn.commit()
    update.message.reply_text(f"⚠️ {user.full_name} warned ({warns}/3)")

    if warns >= 3:
        context.bot.kick_chat_member(chat_id, uid)
        update.message.reply_text(f"❌ {user.full_name} banned after 3 warnings.")
        cursor.execute("DELETE FROM users WHERE id = ?", (uid,))
        conn.commit()

# Ban user
def ban(update: Update, context: CallbackContext):
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        context.bot.kick_chat_member(update.effective_chat.id, user.id)
        update.message.reply_text(f"❌ {user.full_name} has been banned.")

# Unban user
def unban(update: Update, context: CallbackContext):
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        context.bot.unban_chat_member(update.effective_chat.id, user.id)
        update.message.reply_text(f"✅ {user.full_name} has been unbanned.")

# Inline button callback (Rules)
def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == "rules":
        rules_text = (
            "📜 *XPRESS Airdrop Group Rules:*\n\n"
            "1. 🚫 *Spam Strictly Not Allowed* – No unwanted links or repeated messages.\n"
            "2. 📢 *No Promotions or Referral Links*\n"
            "3. 🧑‍⚖️ *Respect Everyone*\n"
            "4. 🛑 *No Forwarded Messages*\n"
            "5. 💸 *USDT Buy/Sell is BANNED*\n"
            "6. 🌐 *Language:* Only Tamil or English\n"
            "7. 🔍 *DYOR (Do Your Own Research)*\n"
            "8. 🛡 *Admins' Word is Final*\n\n"
            "📌 Type /rules anytime to see these rules again."
        )
        query.edit_message_text(rules_text, parse_mode="Markdown")

# /start command (admin only)
def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat_id = update.effective_chat.id

    try:
        admins = context.bot.get_chat_administrators(chat_id)
        is_admin = any(admin.user.id == user_id for admin in admins)

        if not is_admin:
            update.message.reply_text("❌ இந்த கட்டளையை admin-கள் மட்டுமே பயன்படுத்த முடியும்.")
            return

        keyboard = [
            [InlineKeyboardButton("📜 Rules", callback_data='rules')],
            [InlineKeyboardButton("👮‍♂️ Admin Chat", url="https://t.me/Xpress_Airdrop")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            "🤖 MrXpress Bot ready to protect your group!\n\nChoose an option below:",
            reply_markup=reply_markup
        )

    except Exception as e:
        update.message.reply_text(f"⚠️ பிழை ஏற்பட்டது: {e}")

# /rules command (text)
def rules(update: Update, context: CallbackContext):
    update.message.reply_text(
        "📜 Type /start and press 'Rules' button to see full group rules.",
        quote=True
    )

# Main function
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("rules", rules))
    dp.add_handler(CommandHandler("warn", warn))
    dp.add_handler(CommandHandler("ban", ban))
    dp.add_handler(CommandHandler("unban", unban))
    dp.add_handler(CallbackQueryHandler(button_callback))

    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome))
    dp.add_handler(MessageHandler(Filters.status_update.left_chat_member, left))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, filter_all))

    updater.start_polling()
    print("✅ Bot is running...")
    updater.idle()

if __name__ == '__main__':
    main()
