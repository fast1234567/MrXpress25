import logging
import sqlite3
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(level=logging.INFO)

# Replace with your bot token
TOKEN = "7929962828:AAHhacl36aCYMYo4kKWnIfqw63jUgkOyAsk"  # ⚠️ Use your own token

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
bad_words = ["spam", "click here", "free", "deal", "girl", "boy", "fake", "scam", "weast", "dust", "no use"]
auto_replies = {
    "how to join": "🔗 Use the group link to join.",
    "admin": "👮‍♂️ Our admins will assist you shortly.",
    "rules": "📜 Type /rules to read group rules."
}

# Welcome message
def welcome(update: Update, context: CallbackContext):
    for user in update.message.new_chat_members:
        update.message.reply_text(
            f"🎉✨ வணக்கம் {user.full_name} ✨🎉\n\n"
            "💥 XPRESS குழுவிற்கு வரவேற்கிறோம்! 💥\n\n"
            "நான் MrXpress! உங்களுக்கு என்ன உதவி வேண்டும்? 😎✨"
        )

# Left message
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
            break

# Warn
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
        cursor.execute("INSERT INTO users (id, warns) VALUES (?, ?) ", (uid, warns))

    conn.commit()
    update.message.reply_text(f"⚠️ {user.full_name} warned ({warns}/3)")

    if warns >= 3:
        context.bot.kick_chat_member(chat_id, uid)
        update.message.reply_text(f"❌ {user.full_name} banned after 3 warnings.")
        cursor.execute("DELETE FROM users WHERE id = ?", (uid,))
        conn.commit()

# Ban
def ban(update: Update, context: CallbackContext):
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        context.bot.kick_chat_member(update.effective_chat.id, user.id)
        update.message.reply_text(f"❌ {user.full_name} has been banned.")

# Unban
def unban(update: Update, context: CallbackContext):
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        context.bot.unban_chat_member(update.effective_chat.id, user.id)
        update.message.reply_text(f"✅ {user.full_name} has been unbanned.")

# Rules
def rules(update: Update, context: CallbackContext):
    update.message.reply_text("📌 Group Rules:\n1. No spam\n2. No promotions\n3. Respect everyone\n4. Admins have final say.")

# Admin-only start
def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat_id = update.effective_chat.id

    try:
        admins = context.bot.get_chat_administrators(chat_id)
        is_admin = any(admin.user.id == user_id for admin in admins)

        if not is_admin:
            update.message.reply_text("❌ இந்த கட்டளையை admin-கள் மட்டுமே பயன்படுத்த முடியும்.")
            return

        keyboard = [[InlineKeyboardButton("Rules", callback_data='rules')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("🤖 MrXpress Bot ready to protect your group!", reply_markup=reply_markup)

    except Exception as e:
        update.message.reply_text(f"⚠️ பிழை ஏற்பட்டது: {e}")

# Main
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("rules", rules))
    dp.add_handler(CommandHandler("warn", warn))
    dp.add_handler(CommandHandler("ban", ban))
    dp.add_handler(CommandHandler("unban", unban))

    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome))
    dp.add_handler(MessageHandler(Filters.status_update.left_chat_member, left))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, filter_all))

    updater.start_polling()
    print("✅ Bot is running...")
    updater.idle()

if __name__ == '__main__':
    main()
