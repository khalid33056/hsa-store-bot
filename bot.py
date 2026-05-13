import logging
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler, ConversationHandler
from telegram.error import TelegramError
import json
import os
from datetime import datetime, timedelta
import re
import random
from functools import wraps

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database file for tracking warnings
DB_FILE = "user_warnings.json"

class WarningSystem:
    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        self.load_data()
    
    def load_data(self):
        """Load warnings from database"""
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {}
    
    def save_data(self):
        """Save warnings to database"""
        with open(self.db_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add_warning(self, user_id: int, reason: str):
        """Add warning to user"""
        user_id_str = str(user_id)
        if user_id_str not in self.data:
            self.data[user_id_str] = {"warnings": 0, "reasons": []}
        
        self.data[user_id_str]["warnings"] += 1
        self.data[user_id_str]["reasons"].append({
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        self.save_data()
        return self.data[user_id_str]["warnings"]
    
    def get_warnings(self, user_id: int):
        """Get warning count for user"""
        user_id_str = str(user_id)
        if user_id_str in self.data:
            return self.data[user_id_str]["warnings"]
        return 0
    
    def reset_warnings(self, user_id: int):
        """Reset warnings for user"""
        user_id_str = str(user_id)
        if user_id_str in self.data:
            self.data[user_id_str]["warnings"] = 0
            self.data[user_id_str]["reasons"] = []
            self.save_data()

    def update_stats(self, user_id: int, username: str):
        """Update message count and user info"""
        user_id_str = str(user_id)
        if user_id_str not in self.data:
            self.data[user_id_str] = {
                "warnings": 0, 
                "reasons": [],
                "total_messages": 0,
                "first_seen": datetime.now().isoformat()
            }
        
        # Ensure new fields exist for old users
        if "total_messages" not in self.data[user_id_str]:
            self.data[user_id_str]["total_messages"] = 0
        if "first_seen" not in self.data[user_id_str]:
            self.data[user_id_str]["first_seen"] = datetime.now().isoformat()
            
        self.data[user_id_str]["total_messages"] += 1
        self.data[user_id_str]["username"] = username
        self.save_data()

# Database file for keys
KEY_FILE = "keys.json"

class KeySystem:
    def __init__(self, file_path=KEY_FILE):
        self.file_path = file_path
        self.last_reply_time = None
        self.load_data()
    
    def load_data(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {}
            
    def save_data(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=2)
            
    def add_key(self, key, days):
        expiry = datetime.now() + timedelta(days=days)
        self.data[key] = {
            "expiry": expiry.isoformat(),
            "duration": f"{days} days"
        }
        self.save_data()
        
    def get_valid_key(self):
        now = datetime.now()
        valid = None
        expired = []
        
        for k, v in self.data.items():
            exp = datetime.fromisoformat(v["expiry"])
            if exp > now:
                valid = (k, exp)
                break
            else:
                expired.append(k)
        
        # Cleanup expired
        for k in expired:
            del self.data[k]
        if expired:
            self.save_data()
            
        return valid

class SpamTracker:
    def __init__(self):
        self.user_messages = {} # user_id -> [timestamps]
        self.last_messages = {} # user_id -> last_text
        self.FLOOD_THRESHOLD = 5 # 5 messages
        self.FLOOD_WINDOW = 10   # in 10 seconds
        
    def is_flooding(self, user_id: int):
        """Check if user is sending messages too fast"""
        now = datetime.now()
        if user_id not in self.user_messages:
            self.user_messages[user_id] = []
        
        # Add current timestamp
        self.user_messages[user_id].append(now)
        
        # Clean up old timestamps
        cutoff = now - timedelta(seconds=self.FLOOD_WINDOW)
        self.user_messages[user_id] = [t for t in self.user_messages[user_id] if t > cutoff]
        
        return len(self.user_messages[user_id]) > self.FLOOD_THRESHOLD

    def is_duplicate(self, user_id: int, text: str):
        """Check if user is sending the same message repeatedly"""
        if not text or len(text) < 3: return False
        
        is_dup = (user_id in self.last_messages and self.last_messages[user_id] == text)
        self.last_messages[user_id] = text
        return is_dup

# Initialize all systems
warning_system = WarningSystem()
spam_tracker = SpamTracker()
key_system = KeySystem()

# States for /lionxkey conversation
CHOOSING_DURATION, ENTERING_KEY = range(2)

def admin_only(func):
    """Decorator to restrict commands to admins only"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.effective_message or not update.effective_user:
            return
            
        # In groups, check if user is admin
        if update.effective_chat.type in ["group", "supergroup"]:
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            
            try:
                member = await context.bot.get_chat_member(chat_id, user_id)
                if member.status not in ['administrator', 'creator']:
                    # Delete the unauthorized command message
                    try:
                        await update.effective_message.delete()
                    except Exception:
                        pass
                        
                    msg = await context.bot.send_message(
                        chat_id=chat_id,
                        text=(
                            "❌ <b>ACCESS DENIED!</b> ❌\n\n"
                            "⚠️ Only <b>Admins</b> can use this command."
                        ),
                        parse_mode="HTML"
                    )
                    await auto_delete(msg, context)
                    return
            except TelegramError:
                # Fallback if member info can't be fetched
                return

        return await func(update, context, *args, **kwargs)
    return wrapper

async def delete_msg_job(context: ContextTypes.DEFAULT_TYPE):
    """Background job to delete a message"""
    job_data = context.job.data
    try:
        await context.bot.delete_message(
            chat_id=job_data['chat_id'], 
            message_id=job_data['message_id']
        )
    except Exception:
        pass # Message already deleted or bot lacks permission

async def auto_delete(message, context: ContextTypes.DEFAULT_TYPE, delay=180):
    """Helper to schedule message deletion"""
    if message and context.job_queue:
        context.job_queue.run_once(
            delete_msg_job, 
            delay, 
            data={'chat_id': message.chat_id, 'message_id': message.message_id}
        )

@admin_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    msg = await update.message.reply_text(
        "🤖 <b>Lionx Chat Group Bot Started!</b>\n\n"
        "✨ I will help manage the group with style! ✨",
        parse_mode="HTML"
    )
    await auto_delete(msg, context)

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome new members to the group"""
    for member in update.message.new_chat_members:
        if not member.is_bot:
            welcome_text = (
                f"👋 <b>Welcome {member.first_name}!</b>\n\n"
                f"✨ Enjoy your stay in <b>Lionx Chat Group</b>!\n"
                f"📌 Please follow the group rules."
            )
            try:
                msg = await update.message.reply_text(welcome_text, parse_mode="HTML")
                await auto_delete(msg, context)
            except TelegramError as e:
                logger.error(f"Error sending welcome message: {e}")

def check_spam(update: Update):
    """Check for spam patterns in text"""
    if not update.message or not update.message.text:
        return False
    
    original_text = update.message.text
    text = original_text.lower()
    user_id = update.message.from_user.id
    
    # 1. Check for flood (too many messages)
    if spam_tracker.is_flooding(user_id):
        return "flood"
    
    # 2. Check for duplicate messages
    if spam_tracker.is_duplicate(user_id, text):
        return "duplicate message"
    
    # 3. Check for repeated characters (e.g. aaaaaaaaaaaaaa)
    spam_pattern = r'(.)\1{14,}'  # 15+ repeated characters
    if re.search(spam_pattern, text):
        return "repeated characters"
    
    # 4. Check for all caps (likely screaming/spam)
    if len(original_text) > 10 and original_text.isupper():
        return "all caps"
    
    # 5. Check for too many emojis
    emoji_pattern = r'[^\w\s,.]'
    emojis = re.findall(emoji_pattern, original_text)
    if len(emojis) > 20:
        return "emoji spam"
    
    return None

def check_abuse(update: Update):
    """Check for abusive language"""
    if not update.message or not update.message.text:
        return False
    
    text = update.message.text.lower()
    
    # Urdu/Hindustani abuse words + English
    abuse_words = [
        "gali", "gaali", "saala", "bekar", "chal", "chakka", 
        "badmash", "harami", "suar", "kutta", "kutya",
        "fuck", "shit", "damn", "ass", "bastard", "bitch",
        "chutiya", "madarchod", "bhenchod", "bhosdike"
    ]
    
    for word in abuse_words:
        if word in text:
            return True
    
    return False

def check_links(update: Update):
    """Check for external links"""
    if not update.message or not update.message.text:
        return False
    
    text = update.message.text
    
    # Check for URLs with http/https
    url_pattern = r'https?://\S+'
    if re.search(url_pattern, text, re.IGNORECASE):
        return True
    
    # Check for www links
    if re.search(r'www\.\S+', text, re.IGNORECASE):
        return True
    
    # Check for common domain patterns
    domain_pattern = r'[a-zA-Z0-9-]+\.(com|io|org|net|co|in|pk|de|fr|ru|uk|us|edu|gov|info|biz|cc|tv|xyz|app|dev|online|site|web|store|shop)\b'
    if re.search(domain_pattern, text, re.IGNORECASE):
        return True
    
    return False

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    if not update.message or not update.message.from_user:
        return
    
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name or "User"
    username = update.message.from_user.username or user_name
    
    # Update user statistics
    warning_system.update_stats(user_id, username)
    
    # Check if user is admin - admins are exempt from all warnings
    is_admin_user = False
    if update.effective_chat.type in ["group", "supergroup"]:
        try:
            member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
            is_admin_user = member.status in ['administrator', 'creator']
        except Exception:
            pass

    violation_reason = None
    
    # Only check for violations if the user is NOT an admin
    if not is_admin_user:
        # Check for spam
        spam_type = check_spam(update)
        if spam_type:
            violation_reason = f"spam ({spam_type})"
        
        # Check for abuse
        elif check_abuse(update):
            violation_reason = "abusive language"
        
        # Check for links
        elif check_links(update):
            violation_reason = "posting links"
    
    # Check for free key triggers
    text = update.message.text.lower()
    triggers = ["free key", "key expired", "key available", "free key do", "key expire"]
    if any(trigger in text for trigger in triggers):
        # 5-minute global cooldown
        now = datetime.now()
        if key_system.last_reply_time and (now - key_system.last_reply_time).seconds < 300:
            return
            
        key_info = key_system.get_valid_key()
        if key_info:
            key, expiry = key_info
            remaining = expiry - now
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            
            response = (
                f"🔑 <b>FREE KEY AVAILABLE!</b> 🔓\n\n"
                f"📝 <b>Copy here:</b>\n<code>{key}</code>\n\n"
                f"⏳ <b>Expires in:</b> {hours}h {minutes}m\n"
                f"✨ <i>Free for all group members!</i>"
            )
            key_system.last_reply_time = now
        else:
            no_key_msgs = [
                "Currently no free key available, check back later!",
                "All keys are used up! Wait for admin to add more.",
                "No keys left! Try again after some time.",
                "The shelf is empty! No free keys for now.",
                "Oops! No keys found. Keep an eye on the group.",
                "Wait for the next drop! No keys available currently.",
                "Admin hasn't added any keys yet. Patience!",
                "No valid keys at the moment. Stay tuned!",
                "Free keys are exhausted. Wait for the update.",
                "Nothing here! No keys available this time."
            ]
            response = f"❌ {random.choice(no_key_msgs)}"
            key_system.last_reply_time = now # Cooldown applies to "no key" too to avoid spam
            
        msg = await update.message.reply_text(response, parse_mode="HTML")
        await auto_delete(msg, context)
        return

    # Check for update triggers
    update_triggers = ["new update", "update kab", "release kab", "apk update", "next update"]
    if any(trigger in text for trigger in update_triggers):
        response = (
            "🚀 <b>New Updates & APK Files!</b>\n\n"
            "For the latest APK files and update news, please join our "
            "<a href='https://t.me/Lion_X_Engine'>Main Channel</a>.\n\n"
            "📢 <i>Don't miss the next release!</i>"
        )
        msg = await update.message.reply_text(response, parse_mode="HTML", disable_web_page_preview=True)
        await auto_delete(msg, context)
        return

    # If violation detected, issue warning
    if violation_reason:
        warning_count = warning_system.add_warning(user_id, violation_reason)
        
        # 1. Delete the violating message (Always try to delete violations)
        try:
            await update.message.delete()
        except TelegramError as e:
            logger.error(f"Error deleting message: {e}")

        # 2. Check for warning cooldown (don't spam warnings)
        now = datetime.now()
        cooldown_key = f"warn_cd_{user_id}"
        last_warn = context.user_data.get(cooldown_key)
        
        if last_warn and (now - last_warn).seconds < 10:
            return # Don't send another warning so soon

        context.user_data[cooldown_key] = now
        
        if warning_count >= 10:
            # Ban the user
            try:
                await context.bot.ban_chat_member(
                    chat_id=update.message.chat_id,
                    user_id=user_id
                )
                msg = await context.bot.send_message(
                    chat_id=update.message.chat_id,
                    text=(
                        f"🚫 <b>USER BANNED!</b> 🚫\n\n"
                        f"👤 <b>@{username}</b> has been <b>removed</b> from the group.\n"
                        f"⚠️ <b>Reason:</b> Reached 10 warnings\n"
                        f"🔴 <b>Last Violation:</b> {violation_reason.capitalize()}\n\n"
                        f"⛔ This user exceeded the warning limit."
                    ),
                    parse_mode="HTML"
                )
                await auto_delete(msg, context)
                warning_system.reset_warnings(user_id)
            except TelegramError as e:
                logger.error(f"Error banning user: {e}")
                msg = await context.bot.send_message(
                    chat_id=update.message.chat_id,
                    text=f"⚠️ <b>Could not ban @{username}</b>\n🔧 Admin permissions needed.",
                    parse_mode="HTML"
                )
                await auto_delete(msg, context)
        else:
            # Send warning
            remaining = 10 - warning_count
            msg = await context.bot.send_message(
                chat_id=update.message.chat_id,
                text=(
                    f"⚠️ <b>VIOLATION DETECTED!</b> ⚠️\n\n"
                    f"👤 <b>@{username}</b>\n"
                    f"📌 <b>Violation:</b> {violation_reason.capitalize()}\n"
                    f"📊 <b>Warnings:</b> {warning_count}/<b>10</b>\n"
                    f"⏳ <b>Remaining:</b> <b>{remaining}</b>\n\n"
                    f"🗑️ <i>Your message was deleted.</i>\n"
                    f"🔴 <b>Be careful!</b> Ban at 10 warnings!"
                ),
                parse_mode="HTML"
            )
            await auto_delete(msg, context)

@admin_only
async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kick command - remove user from group"""
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ <b>Please reply to a user's message to kick them!</b>",
            parse_mode="HTML"
        )
        return
    
    user_id = update.message.reply_to_message.from_user.id
    user_name = update.message.reply_to_message.from_user.first_name
    
    try:
        await context.bot.ban_chat_member(
            chat_id=update.message.chat_id,
            user_id=user_id
        )
        msg = await update.message.reply_text(
            f"🚫 <b>{user_name} has been kicked from the group!</b> 👋\n"
            f"⛔ <b>Status:</b> Removed",
            parse_mode="HTML"
        )
        await auto_delete(msg, context)
        warning_system.reset_warnings(user_id)
    except TelegramError as e:
        logger.error(f"Error kicking user: {e}")
        msg = await update.message.reply_text(
            "❌ <b>Could not kick user.</b> Admin permissions needed.",
            parse_mode="HTML"
        )
        await auto_delete(msg, context)

@admin_only
async def clear_warnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear warnings for a user - Admin only"""
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ <b>Please reply to a user's message to clear their warnings!</b>",
            parse_mode="HTML"
        )
        return
    
    user_id = update.message.reply_to_message.from_user.id
    user_name = update.message.reply_to_message.from_user.first_name
    
    warning_system.reset_warnings(user_id)
    msg = await update.message.reply_text(
        f"✅ <b>Warnings cleared!</b> ✨\n\n"
        f"👤 <b>{user_name}</b>'s warnings have been <b>reset to 0</b>.\n"
        f"🟢 <b>Status:</b> Fresh start!",
        parse_mode="HTML"
    )
    await auto_delete(msg, context)

@admin_only
async def check_warnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check warnings for a user"""
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        user_name = update.message.reply_to_message.from_user.first_name
    else:
        user_id = update.message.from_user.id
        user_name = update.message.from_user.first_name
    
    warnings = warning_system.get_warnings(user_id)
    msg = await update.message.reply_text(
        f"📊 <b>WARNING STATUS</b> 📊\n\n"
        f"👤 <b>User:</b> {user_name}\n"
        f"⚠️ <b>Warnings:</b> {warnings}/<b>10</b>\n"
        f"📈 <b>Progress:</b> {'🔴' * warnings}{'⚪' * (10 - warnings)}\n\n"
        f"{'✅ <b>Good standing!</b>' if warnings < 5 else '⚠️ <b>Be careful!</b>' if warnings < 10 else '❌ <b>BANNED!</b>'}",
        parse_mode="HTML"
    )
    await auto_delete(msg, context)

@admin_only
async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get detailed user info - /info"""
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    else:
        target_user = update.message.from_user
        
    user_id = target_user.id
    user_data = warning_system.data.get(str(user_id), {})
    
    warnings = user_data.get("warnings", 0)
    total_msgs = user_data.get("total_messages", 0)
    first_seen = user_data.get("first_seen", "N/A")
    
    if first_seen != "N/A":
        try:
            date_obj = datetime.fromisoformat(first_seen)
            first_seen = date_obj.strftime("%d %b %Y")
        except:
            pass

    info_text = (
        f"👤 <b>USER PROFILE</b> 👤\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>Name:</b> {target_user.first_name}\n"
        f"🏷️ <b>Username:</b> @{target_user.username or 'N/A'}\n"
        f"🔢 <b>User ID:</b> <code>{user_id}</code>\n\n"
        f"💬 <b>Total Messages:</b> {total_msgs}\n"
        f"📅 <b>Member Since:</b> {first_seen}\n"
        f"⚠️ <b>Warnings:</b> {warnings}/10\n"
        f"📊 <b>History:</b> {'🔴' * warnings}{'⚪' * (10 - warnings)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ <i>Lionx Management Bot</i>"
    )
    
    msg = await update.message.reply_text(info_text, parse_mode="HTML")
    await auto_delete(msg, context)

@admin_only
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mute a user for a specific duration - /mute <time> <reason>"""
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ <b>Reply to a user to mute them!</b>", parse_mode="HTML")
        return
    
    target_user = update.message.reply_to_message.from_user
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "❌ <b>Usage:</b> /mute <time><m/h/d> [reason]\n"
            "Example: <code>/mute 1h spam</code>",
            parse_mode="HTML"
        )
        return
    
    time_str = args[0]
    reason = " ".join(args[1:]) if len(args) > 1 else "No reason provided"
    
    # Parse time (e.g., 10m, 1h, 2d)
    match = re.match(r"(\d+)([mhd])", time_str.lower())
    if not match:
        await update.message.reply_text(
            "❌ <b>Invalid time format!</b>\n"
            "Use: <b>m</b> (min), <b>h</b> (hour), <b>d</b> (day)\n"
            "Example: <code>10m</code>, <code>1h</code>, <code>1d</code>",
            parse_mode="HTML"
        )
        return
    
    amount = int(match.group(1))
    unit = match.group(2)
    
    now = datetime.now()
    if unit == 'm':
        until_date = now + timedelta(minutes=amount)
        duration_text = f"{amount} minutes"
    elif unit == 'h':
        until_date = now + timedelta(hours=amount)
        duration_text = f"{amount} hours"
    else: # 'd'
        until_date = now + timedelta(days=amount)
        duration_text = f"{amount} days"
        
    try:
        # Restrict member permissions
        await context.bot.restrict_chat_member(
            chat_id=update.message.chat_id,
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        
        msg = await update.message.reply_text(
            f"🔇 <b>USER MUTED!</b> 🔇\n\n"
            f"👤 <b>User:</b> {target_user.first_name} (@{target_user.username or 'N/A'})\n"
            f"⏳ <b>Duration:</b> {duration_text}\n"
            f"📝 <b>Reason:</b> {reason}\n\n"
            f"🚫 <i>You cannot send messages until the timer ends.</i>",
            parse_mode="HTML"
        )
        await auto_delete(msg, context)
    except TelegramError as e:
        logger.error(f"Error muting: {e}")
        msg = await update.message.reply_text(
            "❌ <b>Failed to mute user.</b>\n"
            "🔧 Bot must be admin with 'Restrict Members' permission.",
            parse_mode="HTML"
        )
        await auto_delete(msg, context)

@admin_only
async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unmute a user - /unmute"""
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ <b>Reply to a user to unmute them!</b>", parse_mode="HTML")
        return
    
    target_user = update.message.reply_to_message.from_user
    
    try:
        # Restore all common permissions
        await context.bot.restrict_chat_member(
            chat_id=update.message.chat_id,
            user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        msg = await update.message.reply_text(
            f"🔊 <b>USER UNMUTED!</b> 🔊\n\n"
            f"👤 <b>User:</b> {target_user.first_name}\n"
            f"✅ <i>Access to send messages has been restored!</i>",
            parse_mode="HTML"
        )
        await auto_delete(msg, context)
    except TelegramError as e:
        logger.error(f"Error unmuting: {e}")
        msg = await update.message.reply_text("❌ <b>Failed to unmute user.</b>", parse_mode="HTML")
        await auto_delete(msg, context)

@admin_only
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to ban user - /ban"""
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ <b>Reply to a user's message to ban them with /ban!</b>",
            parse_mode="HTML"
        )
        return
    
    user_id = update.message.reply_to_message.from_user.id
    user_name = update.message.reply_to_message.from_user.first_name
    username = update.message.reply_to_message.from_user.username or user_name
    
    try:
        await context.bot.ban_chat_member(
            chat_id=update.message.chat_id,
            user_id=user_id
        )
        msg = await update.message.reply_text(
            f"🌬️ <b>ANOTHER ONE BITES THE DUST!</b> 🌬️\n\n"
            f"👤 <b>{user_name}</b> (@{username})\n\n"
            f"💨 <b>Dust settled! Goodbye!</b> 👋",
            parse_mode="HTML"
        )
        await auto_delete(msg, context)
        warning_system.reset_warnings(user_id)
    except TelegramError as e:
        logger.error(f"Error banning user: {e}")
        msg = await update.message.reply_text(
            f"❌ <b>Could not ban @{username}</b>\n"
            f"🔧 Admin permissions needed.",
            parse_mode="HTML"
        )
        await auto_delete(msg, context)

@admin_only
async def dban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to ban user AND delete message - /dban"""
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ <b>Reply to a user's message to ban them with /dban!</b>",
            parse_mode="HTML"
        )
        return
    
    user_id = update.message.reply_to_message.from_user.id
    user_name = update.message.reply_to_message.from_user.first_name
    username = update.message.reply_to_message.from_user.username or user_name
    
    try:
        # Delete the user's message
        await update.message.reply_to_message.delete()
        
        # Ban the user
        await context.bot.ban_chat_member(
            chat_id=update.message.chat_id,
            user_id=user_id
        )
        msg = await update.message.reply_text(
            f"🔥 <b>ANOTHER ONE BITES THE DUST!</b> 🔥\n\n"
            f"👤 <b>{user_name}</b> (@{username})\n"
            f"🗑️ <b>Evidence:</b> Message Deleted\n\n"
            f"💨 <b>Dust settled! Goodbye!</b> 👋",
            parse_mode="HTML"
        )
        await auto_delete(msg, context)
        warning_system.reset_warnings(user_id)
    except TelegramError as e:
        logger.error(f"Error in dban: {e}")
        msg = await update.message.reply_text(
            f"❌ <b>Action failed.</b>\n"
            f"🔧 Admin permissions (Ban & Delete) needed.",
            parse_mode="HTML"
        )
        await auto_delete(msg, context)

@admin_only
async def dwarn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to warn user - /dwarn"""
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ <b>Reply to a user's message to warn them with /dwarn!</b>",
            parse_mode="HTML"
        )
        return
    
    user_id = update.message.reply_to_message.from_user.id
    user_name = update.message.reply_to_message.from_user.first_name
    username = update.message.reply_to_message.from_user.username or user_name
    
    warning_count = warning_system.add_warning(user_id, "admin warning")
    remaining = 10 - warning_count
    
    msg = await update.message.reply_text(
        f"⚠️ <b>BE CAREFUL USER {user_name.upper()}!</b> ⚠️\n\n"
        f"👤 <b>@{username}</b>\n"
        f"📌 <b>Type:</b> Admin Warning\n"
        f"📊 <b>Warnings:</b> {warning_count}/<b>10</b>\n"
        f"⏳ <b>Remaining:</b> <b>{remaining}</b>\n\n"
        f"🔴 <b>Watch your step! Ban at 10 warnings!</b>",
        parse_mode="HTML"
    )
    await auto_delete(msg, context)

@admin_only
async def lionxkey_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the key adding process"""
    keyboard = [
        [
            InlineKeyboardButton("1 Day", callback_data='1'),
            InlineKeyboardButton("3 Days", callback_data='3'),
            InlineKeyboardButton("7 Days", callback_data='7')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = await update.message.reply_text(
        "🛠️ <b>KEY GENERATOR</b>\n\n"
        "Select the duration for the new key:",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    await auto_delete(msg, context)
    return CHOOSING_DURATION

async def duration_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle duration selection"""
    query = update.callback_query
    await query.answer()
    
    days = int(query.data)
    context.user_data['key_days'] = days
    
    await query.edit_message_text(
        f"✅ <b>{days} Day(s) selected.</b>\n\n"
        f"⌨️ Now please <b>send the key</b> you want to add:",
        parse_mode="HTML"
    )
    return ENTERING_KEY

async def key_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the received key"""
    key = update.message.text.strip()
    days = context.user_data.get('key_days', 1)
    
    key_system.add_key(key, days)
    
    msg = await update.message.reply_text(
        f"🎉 <b>KEY SAVED!</b> 🎉\n\n"
        f"🔑 <b>Key:</b> <code>{key}</code>\n"
        f"📅 <b>Duration:</b> {days} Days\n"
        f"✅ Added to database successfully!",
        parse_mode="HTML"
    )
    await auto_delete(msg, context)
    return ConversationHandler.END

async def cancel_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel process"""
    await update.message.reply_text("❌ Key generation cancelled.")
    return ConversationHandler.END

@admin_only
async def secret_lionxkeys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Specific command /lionxkeys for user ID 7107553688"""
    user_id = update.effective_user.id
    if user_id == 7107553688:
        msg = await update.message.reply_text(
            "👑 <b>Welcome Boss!</b>\n\n"
            "The system is running perfectly. Your command is recognized.",
            parse_mode="HTML"
        )
        await auto_delete(msg, context)
    else:
        msg = await update.message.reply_text("❌ <b>Unknown command.</b>", parse_mode="HTML")
        await auto_delete(msg, context)

@admin_only
async def delete_active_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete the current active key - /delkey"""
    # Force a check/cleanup first
    key_info = key_system.get_valid_key()
    
    if key_info:
        key, _ = key_info
        if key in key_system.data:
            del key_system.data[key]
            key_system.save_data()
            msg = await update.message.reply_text(
                f"🗑️ <b>KEY DELETED!</b>\n\n"
                f"🔑 The active key <code>{key}</code> has been removed manually.\n"
                f"✅ Users will no longer receive this key.",
                parse_mode="HTML"
            )
            await auto_delete(msg, context)
        else:
            msg = await update.message.reply_text("❌ <b>Error:</b> Could not find key in database.")
            await auto_delete(msg, context)
    else:
        msg = await update.message.reply_text("❌ <b>No active keys</b> found to delete.")
        await auto_delete(msg, context)

@admin_only
async def clear_all_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all keys from database - /clearkeys"""
    key_system.data = {}
    key_system.save_data()
    msg = await update.message.reply_text("💥 <b>DATABASE WIPED!</b>\n\nAll keys have been removed successfully.")
    await auto_delete(msg, context)

def main():
    """Start the bot"""
    # Replace with your actual bot token
    TOKEN = "8903751626:AAF35x8I-OZzNlMk3YOODiMEHKzwqCdWz8k"
    
    # Create application with longer timeouts
    app = Application.builder().token(TOKEN).connect_timeout(30).read_timeout(30).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("dban", dban))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("dwarn", dwarn))
    app.add_handler(CommandHandler("info", user_info))
    app.add_handler(CommandHandler("delkey", delete_active_key))
    app.add_handler(CommandHandler("clearkeys", clear_all_keys))
    app.add_handler(CommandHandler("lionxkeys", secret_lionxkeys))
    
    # Key Conversation Handler
    key_conv = ConversationHandler(
        entry_points=[CommandHandler("lionxkey", lionxkey_start)],
        states={
            CHOOSING_DURATION: [CallbackQueryHandler(duration_selected)],
            ENTERING_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, key_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel_key)],
    )
    app.add_handler(key_conv)
    
    app.add_handler(CommandHandler("clear_warnings", clear_warnings))
    app.add_handler(CommandHandler("warnings", check_warnings))
    
    # Welcome new members
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    
    # Handle all messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start bot
    logger.info("Bot started polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
