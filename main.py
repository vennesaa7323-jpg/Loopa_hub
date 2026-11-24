import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- CONFIG ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = "@loopahub"  # Your channel
CHANNEL_URL = "https://t.me/loopahub"

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- HELPER: Check membership ---
async def is_user_member(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Return True if user is a member of the channel."""
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        # Statuses that mean "joined"
        if member.status in ["member", "administrator", "creator"]:
            return True
        # Also allow "restricted" if they are still a member (rare for channels)
        if member.status == "restricted" and member.is_member:
            return True
        return False
    except Exception as e:
        logger.error(f"Membership check error for {user_id}: {e}")
        return False

# --- KEYBOARD BUILDERS ---
def get_join_keyboard():
    """Keyboard shown when user has NOT joined."""
    keyboard = [
        [InlineKeyboardButton("📢 Join @loopahub", url=CHANNEL_URL)],
        [InlineKeyboardButton("✅ I've Joined – Check Again", callback_data="check_membership")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_main_menu_keyboard():
    """Keyboard shown when user HAS joined."""
    keyboard = [
        [InlineKeyboardButton("🔗 Loopa Hub", url=CHANNEL_URL)],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    joined = await is_user_member(context, user.id)

    if joined:
        await update.message.reply_text(
            f"✅ Welcome, {user.first_name}!\n\nYou are verified as a member of **@loopahub**.\n\nUse the buttons below.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"👋 Hello {user.first_name}!\n\n"
            "To use this bot, you must first join our official channel:\n"
            f"👉 {CHANNEL_URL}\n\n"
            "After joining, tap **Check Again** below.",
            reply_markup=get_join_keyboard(),
            parse_mode="Markdown"
        )

async def check_membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    joined = await is_user_member(context, user.id)
    if joined:
        await query.edit_message_text(
            f"✅ Verified! Welcome, {user.first_name}.\n\nYou now have access.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await query.edit_message_text(
            "❌ You are **not** a member yet.\n\n"
            f"Please join {CHANNEL_URL} first, then tap the button again.",
            reply_markup=get_join_keyboard(),
            parse_mode="Markdown"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    joined = await is_user_member(context, update.effective_user.id)
    if joined:
        await update.message.reply_text(
            "**Loopa Hub Access Bot**\n\n"
            "/start – Re-check membership\n"
            "/help – This message\n\n"
            f"Channel: {CHANNEL_URL}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"Please join {CHANNEL_URL} first.",
            reply_markup=get_join_keyboard()
        )

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "**Loopa Hub Access Bot**\n\n"
        "/start – Re-check membership\n"
        "/help – This message\n\n"
        f"Channel: {CHANNEL_URL}",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )

# --- MAIN ---
def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is not set!")

    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(check_membership_callback, pattern="^check_membership$"))
    app.add_handler(CallbackQueryHandler(help_callback, pattern="^help$"))

    logger.info("Bot starting with long polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
