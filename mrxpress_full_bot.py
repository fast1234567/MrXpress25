from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackContext, CallbackQueryHandler
import logging
import sqlite3
from datetime import datetime

# Enable logging
logging.basicConfig(level=logging.INFO)

# 🔐 Replace this with your bot token
TOKEN = "7929962828:AAHH257wvSTjRinE5yQqQ9nMczQHm7Sb2pA"

# Create or connect to an SQLite database
conn = sqlite3.connect("user_data.db")
cursor = conn.cursor()

# Create necessary tables
cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT, warnings INTEGER, blocked INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS logs (log_id INTEGER PRIMARY KEY, action TEXT, user_id INTEGER, timestamp TEXT)''')
conn.commit()

# In-memory storage (use database for persistence)
warn_count = {}
blocklist = set()

# List of filters
filters = {
    "spam": "🚫 Spam not allowed!",
    "offer": "🚫 No promotional offers allowed."
}

# Auto replies
auto_replies = {
    "how to join": "🔗 Use the group link to join.",
    "admin": "👮‍♂️ Our admins will assist you shortly.",
    "rules": "📜 Type /rules to read group rules.",
    "subscriber": "📌 Please subscribe to our channel for updates."
}

spam_and_bad_words = ["spam", "click here", "free money", "offer", "deal", "join now", "fake", "scam", "waste", "girl", "boy"]

# 👋 Welcome message
def welcome(update: Update, context: CallbackContext):
    for user in update.message.new_chat_members:
        # Add user to database
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username, full_name, warnings, blocked) VALUES (?, ?, ?, ?, ?)",
                       (user.id, user.username, user.full_name, 0, 0))
        conn.commit()
        
        update.message.reply_text(
            f"🎉✨ வணக்கம் {user.full_name} ✨🎉\n\n"
            "💥 XPRESS குழுவிற்கு வரவேற்கிறோம்! 💥\n\n"
            "நான் MrXpress! உங்களுக்கு என்ன உதவி வேண்டும்? 😎✨"
        )

# 🏃‍♂️ Left message
def left(update: Update, context: CallbackContext):
    for user in update.message.left_chat_members:
        cursor.execute("UPDATE users SET blocked = 1 WHERE user_id = ?", (user.id,))
        conn.commit()
        update.message.reply_text(f"❌ {user.full_name} குழுவிலிருந்து விலகி விட்டது.")

# Admin panel to allow different admin roles
def admin_panel(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("📜 Group Rules", callback_data="rules")],
        [InlineKeyboardButton("⚠️ Warn User", callback_data="warn")],
        [InlineKeyboardButton("❌ Ban User", callback_data="ban")],
        [InlineKeyboardButton("💬 Get Help", callback_data="help")],
        [InlineKeyboardButton("🔒 Admin Panel", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("🤖 Welcome to MrXpress Bot! Choose an option below:", reply_markup=reply_markup)

# Handle button presses
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()  # To acknowledge the click

    if query.data == "rules":
        query.edit_message_text("📌 Group Rules:\n1. No spam\n2. No promotions\n3. Respect everyone\n4. Admins have final say.")
    
    elif query.data == "warn":
        query.edit_message_text("⚠️ Reply to a user's message to warn them.")
    
    elif query.data == "ban":
        query.edit_message_text("❌ Reply to a user's message to ban them.")
    
    elif query.data == "help":
        query.edit_message_text("🤖 MrXpress Bot can help you manage your group. You can use commands to warn, ban users, and much more!")
    
    elif query.data == "admin_panel":
        query.edit_message_text("🔒 Admin Panel:\n1. Ban User\n2. Warn User\n3. View Blocked Users\nUse commands directly.")

# Filter all messages for non-admins
def filter_all(update: Update, context: CallbackContext):
    message = update.message
    text = message.text.lower() if message.text else ""

    try:
        # Skip empty messages
        if not text:
            return

        # Check if user is admin
        is_admin = any(admin.user.id == message.from_user.id
                       for admin in context.bot.get_chat_administrators(update.effective_chat.id))

        # Block links, usernames, and spam for non-admins
        if any(x in text for x in ["http", "www", "@"]) and not is_admin:
            message.delete()
            return

        if any(word in text for word in spam_and_bad_words) and not is_admin:
            message.delete()
            return

        # Custom filter delete (for all)
        for word in filters:
            if word in text:
                message.delete()
                break

        # Auto reply (for all)
        for key in auto_replies:
            if key in text:
                message.reply_text(auto_replies[key])
                break

    except Exception as e:
        print(f"⚠️ Error in filter_all: {e}")

# Log activity in the database
def log_activity(action: str, user_id: int):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO logs (action, user_id, timestamp) VALUES (?, ?, ?)", (action, user_id, timestamp))
    conn.commit()

# ⚠️ Warn user
def warn(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        update.message.reply_text("⚠️ Reply to the user's message to warn.")
        return

    user = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id

    cursor.execute("SELECT warnings FROM users WHERE user_id = ?", (user.id,))
    user_data = cursor.fetchone()
    warnings = user_data[0] if user_data else 0
    warnings += 1
    cursor.execute("UPDATE users SET warnings = ? WHERE user_id = ?", (warnings, user.id))
    conn.commit()

    update.message.reply_text(f"⚠️ {user.full_name} warned ({warnings}/3)")

    if warnings >= 3:
        context.bot.kick_chat_member(chat_id, user.id)
        update.message.reply_text(f"❌ {user.full_name} banned after 3 warnings.")
        cursor.execute("UPDATE users SET blocked = 1 WHERE user_id = ?", (user.id,))
        conn.commit()

# 🔨 Ban user
def ban(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        update.message.reply_text("❌ Reply to a user’s message to ban them.")
        return

    user = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id

    try:
        context.bot.kick_chat_member(chat_id, user.id)
        update.message.reply_text(f"❌ {user.full_name} has been banned.")
        log_activity("Banned", user.id)
    except Exception as e:
        update.message.reply_text(f"❌ Failed to ban. Error: {e}")

# Main function
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", main_menu))
    dp.add_handler(CommandHandler("rules", rules))
    dp.add_handler(CommandHandler("warn", warn))
    dp.add_handler(CommandHandler("ban", ban))
    dp.add_handler(CommandHandler("unban", unban))
    dp.add_handler(CommandHandler("blockuser", block_user))
    dp.add_handler(CommandHandler("unblockuser", unblock_user))

    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome))
    dp.add_handler(MessageHandler(Filters.status_update.left_chat_members, left))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, filter_all))

    dp.add_handler(CallbackQueryHandler(button))  # Handle button press events

    updater.start_polling()
    print("✅ MrXpress Bot is running...")
    updater.idle()

if __name__ == '__main__':
    main()
