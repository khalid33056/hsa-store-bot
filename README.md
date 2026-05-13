# Lionx Chat Group Bot

A Telegram bot for managing group chat with warning system, spam detection, abuse filtering, and link blocking.

## Features

✅ **Warning System**: Users get warnings for violations (max 10, then ban)
✅ **Spam Detection**: Detects repeated characters and all-caps spam
✅ **Abuse Filter**: Blocks abusive language (Urdu/Hindustani words)
✅ **Link Blocking**: Removes external links and warns users
✅ **Welcome Messages**: Greets new members with group rules
✅ **Admin Commands**: Kick, clear warnings, check warnings

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Get your Telegram Bot Token:
   - Chat with BotFather on Telegram
   - Create a new bot and copy the token

3. Edit `bot.py` and replace `YOUR_BOT_TOKEN_HERE` with your actual token:
```python
TOKEN = "YOUR_BOT_TOKEN_HERE"
```

4. Run the bot:
```bash
python bot.py
```

## Commands

- `/start` - Start the bot
- `/warnings` - Check your warnings (or reply to a user's message)
- `/kick` - Remove a user (reply to their message)
- `/clear_warnings` - Reset warnings for a user (reply to their message)

## Violations & Warnings

- **Spam**: Repeated characters or all-caps messages → 1 Warning
- **Abusive Language**: Using offensive words → 1 Warning
- **External Links**: Posting URLs or links → 1 Warning + Message Deleted

**Ban Trigger**: 10 warnings = Auto-ban from group

## Database

Warnings are stored in `user_warnings.json` with timestamps and reasons.

## Requirements

- Python 3.8+
- telegram (python-telegram-bot library)
- Active Telegram bot token

Enjoy! 🚀
