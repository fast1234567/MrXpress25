from telegram import Update, ChatPermissions
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackContext
import logging

# Enable logging
logging.basicConfig(level=logging.INFO)

# 🔐 Replace this with your bot token
TOKEN = "7929962828:AAHH257wvSTjRinE5yQqQ9nMczQHm7Sb2pA"

# In-memory storage
warn_count = {}
filters = {
    "spam": "🚫 Spam not allowed!",
    "offer": "🚫 No promotional offers allowed."
}

auto_replies = {
    "how to join": "🔗 Use the group link to join.",
    "admin": "👮‍♂️ Our admins will assist you shortly.",
    "rules": "📜 Type /rules to read group rules."
}

spam_and_bad_words = ["spam", "click here", "free money", "offer", "deal", "join now", "fake", "scam", "waste", "girl", "boy"]

# 👋 Welcome message
def welcome(update: Update, context: CallbackContext):
    for user in update.message.new_chat_members:
        update.message.reply_text(
            f"🎉✨ வணக்கம் {user.full_name} ✨🎉\n\n"
            "💥 XPRESS குழுவிற்கு வரவேற்கிறோம்! 💥\n\n"
            "நான் MrXpress! உங்களுக்கு என்ன உதவி வேண்டும்? 😎✨"
        )

# 🚫 Filter all messages for non-admins
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

        # Forwarded messages blocked for users
        if message.forward_date and not is_admin:
            message.delete()
            return

        # Link and username restrictions for users only
        if any(x in text for x in ["http", "www", "@"]) and not is_admin:
            message.delete()
            return

        # Spam words filter
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

# ⚠️ Warn user
def warn(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        update.message.reply_text("⚠️ Reply to the user's message to warn.")
        return

    user = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    key = f"{chat_id}:{user.id}"

    warn_count[key] = warn_count.get(key, 0) + 1
    update.message.reply_text(f"⚠️ {user.full_name} warned ({warn_count[key]}/3)")

    if warn_count[key] >= 3:
        context.bot.kick_chat_member(chat_id, user.id)
        update.message.reply_text(f"❌ {user.full_name} banned after 3 warnings.")
        del warn_count[key]

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
    except Exception as e:
        update.message.reply_text(f"❌ Failed to ban. Error: {e}")

# ✅ Unban user
def unban(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        update.message.reply_text("Reply to a user to unban.")
        return
    user = update.message.reply_to_message.from_user
    try:
        context.bot.unban_chat_member(update.effective_chat.id, user.id)
        update.message.reply_text(f"✅ {user.full_name} has been unbanned.")
    except Exception as e:
        update.message.reply_text(f"❌ Failed to unban. Error: {e}")

# 🛠️ Add filter
def add_filter(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        update.message.reply_text("Usage: /addfilter <word> <response>")
        return
    word = context.args[0].lower()
    response = " ".join(context.args[1:])
    filters[word] = response
    update.message.reply_text(f"✅ Filter added for word: `{word}`", parse_mode="Markdown")

# ❌ Delete filter
def del_filter(update: Update, context: CallbackContext):
    word = context.args[0].lower()
    if word in filters:
        del filters[word]
        update.message.reply_text(f"🗑️ Filter removed: `{word}`", parse_mode="Markdown")
    else:
        update.message.reply_text("❌ No such filter found.")

# 📜 Rules command
def rules(update: Update, context: CallbackContext):
    update.message.reply_text("📌 Group Rules:\n1. No spam\n2. No promotions\n3. Respect everyone\n4. Admins have final say.")

# 🔘 Start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("🤖 MrXpress is online and protecting your group!")

# Main function
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("rules", rules))
    dp.add_handler(CommandHandler("warn", warn))
    dp.add_handler(CommandHandler("ban", ban))
    dp.add_handler(CommandHandler("unban", unban))
    dp.add_handler(CommandHandler("addfilter", add_filter))
    dp.add_handler(CommandHandler("delfilter", del_filter))

    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, filter_all))

    updater.start_polling()
    print("✅ MrXpress Bot is running...")
    updater.idle()

if __name__ == '__main__':
    main()
