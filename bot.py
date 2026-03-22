# Kos Hack menu handler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters, ApplicationHandlerStop
from urllib.parse import quote_plus
import asyncio
import base64
import copy
import html
import json
import os
import threading
import logging
from datetime import datetime, timedelta
from telegram.ext import TypeHandler
from flask import Flask

try:
    import firebase_admin  # pyright: ignore[reportMissingImports]
    from firebase_admin import credentials, firestore  # pyright: ignore[reportMissingImports]
except Exception:
    firebase_admin = None
    credentials = None
    firestore = None

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ADMIN_ID = 7107553688
FIRESTORE_COLLECTION = os.getenv('FIRESTORE_COLLECTION', 'hsa_store')
FIRESTORE_DOCUMENT = os.getenv('FIRESTORE_DOCUMENT', 'main')

_firestore_db = None

# ⚠️ CRITICAL: Lock for thread-safe stock access
stock_lock = threading.Lock()

# -------------------------------
# Keep-alive server for Replit
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive ✅"

def run():
    app.run(host="0.0.0.0", port=3000)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()
# -------------------------------

# --- product & stock configuration ---
# Friendly hack information including images and display names
HACK_INFO = {
    'snake_engine': {
        'name': 'Snake Engine',
        'image': 'https://i.postimg.cc/ryWbNb41/IMG-20260301-211803.png'
    },
    'kos_mode': {
        'name': 'Kos Mode',
        'image': 'https://i.postimg.cc/ZnFwtGFT/IMG-20260301-214244.png'
    },
    'kos_virtual': {
        'name': 'Kos Virtual',
        'image': 'https://i.postimg.cc/ZnFwtGFT/IMG-20260301-214244.png'
    },
    'aim_x': {
        'name': 'Aim X Hack',
        'image': 'https://i.postimg.cc/7Zp09B07/IMG-20260301-212442.png'
    },
    'aim_king_nonroot': {
        'name': 'Aim King Non-Root',
        'image': 'https://i.postimg.cc/W1twXFK4/IMG-20260301-213329.png'
    },
    'ak_loader_root': {
        'name': 'AK Loader Root',
        'image': 'https://i.postimg.cc/W1twXFK4/IMG-20260301-213329.png'
    },
    'wolf_hack': {
        'name': 'Wolf Hack',
        'image': 'https://i.postimg.cc/4ySmdd1t/IMG-20260301-214113.png'
    },
    'wizard_ios': {
        'name': 'Wizard iOS',
        'image': 'https://i.postimg.cc/8ktv9kLf/IMG-20260301-212731.png'
    },
    'ninja_engine': {
        'name': 'Ninja Engine',
        'image': 'https://i.postimg.cc/q7tCKnZP/IMG-20260302-163756.png'
    },
    'carrom_se': {
        'name': 'Carrom SE',
        'image': 'https://i.postimg.cc/fytM8vxD/IMG-20260301-213641.png'
    },
    'carrom_ak': {
        'name': 'Carrom AK',
        'image': 'https://i.postimg.cc/5y0Rg3Q2/IMG-20260302-203112.png'
    },
    'score_se': {
        'name': 'Score SE',
        'image': 'https://i.postimg.cc/xd7wtfhB/file-000000006d287209b1015a9e2f45b99b.png'
    },
    'score_ak': {
        'name': 'Score AK',
        'image': 'https://i.postimg.cc/xd7wtfhB/file-000000006d287209b1015a9e2f45b99b.png'
    },
    'ff_android': {
        'name': 'Free Fire Android',
        'image': 'https://i.postimg.cc/3xJZnVh1/free-fire-banner.png'
    },
    'ff_ios': {
        'name': 'Killer AIM iOS',
        'image': 'https://i.postimg.cc/QC7bJwY1/IMG-20260302-165241.png'
    },
    'ff_android_drip': {
        'name': 'Free Fire Android - Drip Client',
        'image': 'https://i.postimg.cc/W3F6sxVc/IMG-20260302-164657.png'
    },
    'ff_android_kos': {
        'name': 'Free Fire Android - Kos Ffire',
        'image': 'https://i.postimg.cc/RhW1VyzB/IMG-20260302-204116.png'
    },
    'esign': {
        'name': 'E-Sign Certificate',
        'image': 'https://i.postimg.cc/qq6ndK84/IMG-20260302-203514.png'
    },
    'gbox': {
        'name': 'GBOX Certificate',
        'image': 'https://i.postimg.cc/cLSDX1Sd/IMG-20260302-170714.png'
    }
}

# product definitions used for purchasing
PRODUCTS = {
    # snake
    'buy_snake_3': {'price': 4.0, 'hack': 'snake_engine', 'duration': '3_days', 'label': '3 Days'},
    'buy_snake_10': {'price': 9.9, 'hack': 'snake_engine', 'duration': '10_days', 'label': '10 Days'},
    'buy_snake_30': {'price': 20.3, 'hack': 'snake_engine', 'duration': '30_days', 'label': '30 Days'},
    # aim x
    'buy_aimx_1': {'price': 0.9, 'hack': 'aim_x', 'duration': '1_day', 'label': '1 Day'},
    'buy_aimx_2': {'price': 1.7, 'hack': 'aim_x', 'duration': '2_days', 'label': '2 Days'},
    'buy_aimx_7': {'price': 2.6, 'hack': 'aim_x', 'duration': '7_days', 'label': '7 Days'},
    'buy_aimx_15': {'price': 3.6, 'hack': 'aim_x', 'duration': '15_days', 'label': '15 Days'},
    'buy_aimx_30': {'price': 5.6, 'hack': 'aim_x', 'duration': '30_days', 'label': '30 Days'},
    # aim king
    'buy_aimking_nonroot_7': {'price': 8.3, 'hack': 'aim_king_nonroot', 'duration': '7_days', 'label': '7 Days'},
    'buy_aimking_nonroot_30': {'price': 19.5, 'hack': 'aim_king_nonroot', 'duration': '30_days', 'label': '30 Days'},
    'buy_aimking_nonroot_90': {'price': 52.0, 'hack': 'aim_king_nonroot', 'duration': '90_days', 'label': '90 Days'},
    # ak loader
    'buy_akloader_7': {'price': 6.9, 'hack': 'ak_loader_root', 'duration': '7_days', 'label': '7 Days'},
    'buy_akloader_30': {'price': 16.4, 'hack': 'ak_loader_root', 'duration': '30_days', 'label': '30 Days'},
    'buy_akloader_90': {'price': 42.0, 'hack': 'ak_loader_root', 'duration': '90_days', 'label': '90 Days'},
    # kos mode & kos virtual
    'buy_kosmode_1': {'price': 0.9, 'hack': 'kos_mode', 'duration': '1_day', 'label': '1 Day'},
    'buy_kosmode_7': {'price': 2.9, 'hack': 'kos_mode', 'duration': '7_days', 'label': '7 Days'},
    'buy_kosmode_15': {'price': 4.4, 'hack': 'kos_mode', 'duration': '15_days', 'label': '15 Days'},
    'buy_kosmode_30': {'price': 7.4, 'hack': 'kos_mode', 'duration': '30_days', 'label': '30 Days'},
    'buy_kosvirt_1': {'price': 1.2, 'hack': 'kos_virtual', 'duration': '1_day', 'label': '1 Day'},
    'buy_kosvirt_7': {'price': 3.0, 'hack': 'kos_virtual', 'duration': '7_days', 'label': '7 Days'},
    'buy_kosvirt_15': {'price': 5.5, 'hack': 'kos_virtual', 'duration': '15_days', 'label': '15 Days'},
    'buy_kosvirt_30': {'price': 9.5, 'hack': 'kos_virtual', 'duration': '30_days', 'label': '30 Days'},
    # wolf, wizard, ninja
    'buy_wolf_1': {'price': 1.4, 'hack': 'wolf_hack', 'duration': '1_day', 'label': '1 Day'},
    'buy_wolf_7': {'price': 2.5, 'hack': 'wolf_hack', 'duration': '7_days', 'label': '7 Days'},
    'buy_wolf_30': {'price': 5.0, 'hack': 'wolf_hack', 'duration': '30_days', 'label': '30 Days'},
    'buy_wizard_1': {'price': 2.4, 'hack': 'wizard_ios', 'duration': '1_day', 'label': '1 Day'},
    'buy_wizard_7': {'price': 7.0, 'hack': 'wizard_ios', 'duration': '7_days', 'label': '7 Days'},
    'buy_wizard_30': {'price': 14.0, 'hack': 'wizard_ios', 'duration': '30_days', 'label': '30 Days'},
    'buy_ninja_3': {'price': 5.0, 'hack': 'ninja_engine', 'duration': '3_days', 'label': '3 Days'},
    'buy_ninja_7': {'price': 8.0, 'hack': 'ninja_engine', 'duration': '7_days', 'label': '7 Days'},
    'buy_ninja_30': {'price': 15.0, 'hack': 'ninja_engine', 'duration': '30_days', 'label': '30 Days'},
    'buy_carromse_3': {'price': 2.4, 'hack': 'carrom_se', 'duration': '3_days', 'label': '3 Days'},
    'buy_carromse_10': {'price': 4.4, 'hack': 'carrom_se', 'duration': '10_days', 'label': '10 Days'},
    'buy_carromse_30': {'price': 9.4, 'hack': 'carrom_se', 'duration': '30_days', 'label': '30 Days'},
    'buy_carromak_auto_7': {'price': 5.5, 'hack': 'carrom_ak', 'duration': 'auto_7_days', 'label': 'Auto 7 Days'},
    'buy_carromak_auto_30': {'price': 13.5, 'hack': 'carrom_ak', 'duration': 'auto_30_days', 'label': 'Auto 30 Days'},
    'buy_carromak_normal_7': {'price': 4.5, 'hack': 'carrom_ak', 'duration': 'normal_7_days', 'label': 'Normal 7 Days'},
    'buy_carromak_normal_30': {'price': 10.5, 'hack': 'carrom_ak', 'duration': 'normal_30_days', 'label': 'Normal 30 Days'},
    'buy_scorese_3': {'price': 3.5, 'hack': 'score_se', 'duration': '3_days', 'label': '3 Days'},
    'buy_scorese_10': {'price': 7.0, 'hack': 'score_se', 'duration': '10_days', 'label': '10 Days'},
    'buy_scorese_30': {'price': 14.0, 'hack': 'score_se', 'duration': '30_days', 'label': '30 Days'},
    'buy_scoreak_7': {'price': 6.0, 'hack': 'score_ak', 'duration': '7_days', 'label': '7 Days'},
    'buy_scoreak_30': {'price': 13.8, 'hack': 'score_ak', 'duration': '30_days', 'label': '30 Days'},
    'buy_scoreak_90': {'price': 32.0, 'hack': 'score_ak', 'duration': '90_days', 'label': '90 Days'},
    # free fire android - drip client
    'buy_ffandroid_drip_1': {'price': 1.9, 'hack': 'ff_android_drip', 'duration': '1_day', 'label': '1 Day'},
    'buy_ffandroid_drip_7': {'price': 5.4, 'hack': 'ff_android_drip', 'duration': '7_days', 'label': '7 Days'},
    'buy_ffandroid_drip_30': {'price': 9.5, 'hack': 'ff_android_drip', 'duration': '30_days', 'label': '30 Days'},
    # free fire android - kos ffire
    'buy_ffandroid_kos_1': {'price': 1.0, 'hack': 'ff_android_kos', 'duration': '1_day', 'label': '1 Day'},
    'buy_ffandroid_kos_7': {'price': 3.0, 'hack': 'ff_android_kos', 'duration': '7_days', 'label': '7 Days'},
    'buy_ffandroid_kos_15': {'price': 4.0, 'hack': 'ff_android_kos', 'duration': '15_days', 'label': '15 Days'},
    'buy_ffandroid_kos_30': {'price': 7.5, 'hack': 'ff_android_kos', 'duration': '30_days', 'label': '30 Days'},
    # free fire ios - Killer AIM iOS
    'buy_ffios_1': {'price': 1.6, 'hack': 'ff_ios', 'duration': '1_day', 'label': '1 Day'},
    'buy_ffios_7': {'price': 4.0, 'hack': 'ff_ios', 'duration': '7_days', 'label': '7 Days'},
    'buy_ffios_30': {'price': 7.0, 'hack': 'ff_ios', 'duration': '30_days', 'label': '30 Days'},
    # esign certificate
    'buy_esign_30_iphone': {'price': 4.6, 'hack': 'esign', 'duration': '30_days_iphone', 'label': '30 Days iPhone'},
    'buy_esign_90_iphone': {'price': 6.7, 'hack': 'esign', 'duration': '90_days_iphone', 'label': '90 Days iPhone'},
    'buy_esign_360_ipad': {'price': 7.0, 'hack': 'esign', 'duration': '360_days_ipad', 'label': '360 Days iPad'},
    # gbox certificate
    'buy_gbox_1year': {'price': 8.0, 'hack': 'gbox', 'duration': '1_year', 'label': '1 Year'},
}

API_TOKEN = '8673798950:AAFe8Iko5CVT5UzovpxRNcYg8qk3iP_RgQQ'

LANG_STRINGS = {
    'en': {
        'status_vip': '🌟 VIP',
        'status_active': '🔓 Active',
        'no_username': 'No username',
        'no_purchases': 'No purchases yet',
        'welcome': '<b>👋 Welcome {name}</b>',
        'label_user_id': '<b>🆔 User ID:</b> <code>{uid}</code>',
        'label_username': '<b>💻 Username:</b> {username}',
        'label_balance': '<b>💰 Balance:</b> ${balance}',
        'label_status': '<b>⭐ Status:</b> {status}',
        'label_last_purchase': '<b>🛍️ Last Purchase:</b> {last_purchase}',
        'menu_intro': '<b>🛒 Enjoy shopping from trusted sellers below ↓</b>',
        'btn_trusted_seller': '⭐ Trusted Seller',
        'btn_product': '🛍️ Product',
        'btn_add_balance': '💳 Add Balance',
        'btn_history': '📜 History',
        'btn_profile': '👤 My Profile',
        'btn_help': '🆘 Help & Support',
        'btn_choose_language': '🌐 Chose Language',
        'btn_terms': '📋 Terms',
        'btn_become_reseller': '💼 Become Reseller',
        'terms_message': '<b>📋 𝗢𝗳𝗳𝗶𝗰𝗶𝗮𝗹 𝗥𝗲𝘀𝘀𝗲𝗹𝗹𝗲𝗿 𝗧𝗲𝗿𝗺𝘀</b>\n\n<b>⚠️ Important: Contacting us without accepting these terms may result in messages being ignored or blocked.</b>\n<b>💼 Become a Top Reseller on HSA PANEL</b>\n<b>Step into the fast lane of sales and connect with thousands of customers &amp; stores.</b>\n\n<b>✨ Requirements to Join:</b>\n<b>• 🤝 Loyalty: Full loyalty to HSA PANEL is required.</b>\n<b>• 🌐 Support: Must have active channels to share purchase links and confirm payments.</b>\n<b>• 📱 Knowledge: Basic Android app skills to use tools &amp; handle sales efficiently.</b>\n<b>💰 Activation Fee: $10 🔑</b>\n<b>💡 Note: This amount is credited to your account balance and can be used for future transactions.</b>\n\n<b>🚀 After Activation:</b>\n<b>• 📋 Your name listed in the official Reseller list.</b>\n<b>• 👥 Sell to individual customers.</b>\n<b>• 🏪 Sell to stores.</b>\n<b>• 🤝 Collaborate with approved resellers.</b>\n\n<b>🔥 Activate now &amp; unlock premium reseller status!</b>',
        'choose_language_title': '<b>🌐 Choose Language</b>',
        'choose_language_desc': 'Select your preferred bot language.',
        'btn_english': '🇬🇧 English',
        'btn_arabic': '🇸🇦 Arabic',
        'language_set_en': '✅ English selected. (Default language)',
        'language_set_ar': '✅ Arabic selected. Bot messages will appear in Arabic.',
        'btn_back': '🔙 Back',
        'btn_back_to_menu': '🔙 Back to Menu',
        'btn_back_to_main_menu': '🏠 Back to Main Menu',
        'product_title': '<b>🛍️ What you want?</b>',
        'product_desc_1': '<b>Please select a category below 👇</b>',
        'product_desc_2': '🎮 <b>Account:</b> Buy game accounts',
        'product_desc_3': '🔧 <b>Hackes:</b> Browse premium tools & packages',
        'btn_account': '🎮 Account',
        'btn_hackes': '🔧 Hackes',
        'account_title': '<b>🎮 Game Accounts</b>',
        'account_desc': '<b>Choose your account type below 👇</b>\nBuy premium game accounts with coins and features.',
        'hackes_title': '<b>🔧 Hackes Categories</b>',
        'hackes_desc': '<b>Please select a category below 👇</b>\nChoose your game and explore available tools & premium packages.',
        'no_resellers': '❌ No reseller found.',
        'trusted_sellers_title': '⭐ <b>Trusted Sellers</b>',
        'trusted_sellers_footer': '📞 Contact any seller to purchase!',
        'help_title': '<b>🛠 Need Help?</b>',
        'help_purchase_error_title': '<b>⚠ Purchase Error</b>',
        'help_purchase_error_body': 'If you are facing any error during purchase.',
        'help_apk_title': '<b>📦 APK Link</b>',
        'help_apk_body': "If you purchased any hack but don't have APK link.",
        'help_any_title': '<b>🆘 Any Type of Help</b>',
        'help_any_body': 'Click the button below to connect with Admin Support.',
        'btn_help_short': '🆘 Help',
        'profile_title': '<b>👤 My Profile</b>',
        'profile_name': '<b>👤 Name:</b> {name}',
        'profile_username': '<b>💻 Username:</b> @{username}',
        'profile_member_since': '<b>📅 Member Since:</b> {date}',
        'btn_purchase_history': '📜 Purchase History',
        'add_balance_title': '<b>╔════════════════════╗</b>\n<b>   ADD BALANCE CENTER</b>\n<b>╚════════════════════╝</b>',
        'add_balance_1': '<b>Want to add balance 💰</b>',
        'add_balance_2': '<b>Copy your User ID, then tap the Deposit button below 👇</b>',
        'add_balance_3': '<b>Your ID:</b>',
        'add_balance_4': '<b>After payment, send your screenshot to admin.</b>',
        'btn_deposit_now': '💳 Deposit Now',
        'btn_contact_admin': '💬 Contact Admin',
        'btn_refresh': '🔄 Refresh',
        'history_empty': 'No purchase history found.',
        'history_title': '<b>🕓 Your Purchase History:</b>',
        'history_page': '<b>Page {page}/{total}</b>',
        'history_product': '<b>📦 Product:</b> {product}',
        'history_duration': '<b>⏳ Duration:</b> {duration}',
        'history_key': '<b>🔑 Key:</b> <code>{key}</code>',
        'history_status_expired': '<b>📅 Status:</b> Expired ❌',
        'history_status_active': '<b>📅 Status:</b> Active ✅',
        'history_expired_on': '<i>Expired on: {date}</i>',
        'history_expires_on': '<i>Expires on: {date}</i>',
        'btn_previous': '⬅️ Previous',
        'btn_next': 'Next ➡️',
        'confirm_sure': '<b>📝 Are you sure about buying? 🫆</b>',
        'confirm_separator': '<b>--------------------------------------</b>',
        'confirm_note': '<b>Please Note📣:</b>',
        'confirm_no_return': '<b>The key cannot be returned upon purchase!</b>',
        'confirm_your_balance': '<b>💰 Your Balance:</b> ${balance}',
        'confirm_price': '<b>💰 Price:</b> ${price}',
        'confirm_stock': '<b>📦 Stock:</b> {stock}',
        'confirm_stock_available': '<b>📦 Stock: Available</b>',
        'btn_confirm': '✅ Confirm',
        'btn_cancel': '❌ Cancel',
        'out_of_stock_title': '❌ Product Out of Stock',
        'out_of_stock_product': '🐍 Product: {product}',
        'out_of_stock_duration': '⏳ Duration: {duration}',
        'out_of_stock_footer': '📦 Stock Available: 0\n\nPlease try again later.',
        'not_vip_msg': '❌ You are not VIP. Prices are visible only to VIP users.',
        'unknown_product': 'Unknown product.',
        'out_of_stock_error': '❌ Sorry, the product went out of stock.',
        'insufficient_balance_title': '❌ Insufficient Balance',
        'insufficient_balance_body': 'Your balance is too low to complete this purchase.\n\nPlease add funds and try again.',
        'success_title': '<b>✅ Purchase Successful!</b>',
        'success_product': '<b>📦 Product:</b> {product}',
        'success_duration': '<b>⏳ Duration:</b> {duration}',
        'success_remaining': '<b>💰 Remaining Balance:</b> {balance}$',
        'success_key': '<b>🔑 Your Key:</b> <code>{key}</code>',
        'success_enjoy': '<b>Enjoy your premium access 🚀</b>',
        'account_not_available_title': '❌ Account Not Available',
        'account_not_available_body': 'Sorry, no accounts are available at the moment.\nPlease contact admin or try again later.',
        'success_8bp_product': '🎱 <b>Product:</b> {product}',
        'success_8bp_price': '💰 <b>Price:</b> ${price}',
        'success_8bp_remaining': '💳 <b>Remaining Balance:</b> ${balance}',
        'success_8bp_account_header': '          ✓ <b>Account Details</b>',
        'success_8bp_gmail': '📥 <b>Gmail:</b> {gmail}',
        'success_8bp_password': '🔐 <b>Password:</b> {password}',
        'insuf_price': '💰 <b>Price:</b> ${price}',
        'insuf_your_balance': '💳 <b>Your Balance:</b> ${balance}',
        'insuf_shortfall': '📊 <b>Shortfall:</b> ${shortfall}',
        'insuf_footer': 'Please add balance to your account.',
    },
    'ar': {
        'status_vip': '🌟 VIP',
        'status_active': '🔓 نشط',
        'no_username': 'بدون اسم مستخدم',
        'no_purchases': 'لا توجد عمليات شراء بعد',
        'welcome': '<b>👋 مرحبا {name}</b>',
        'label_user_id': '<b>🆔 معرف المستخدم:</b> <code>{uid}</code>',
        'label_username': '<b>💻 اسم المستخدم:</b> {username}',
        'label_balance': '<b>💰 الرصيد:</b> ${balance}',
        'label_status': '<b>⭐ الحالة:</b> {status}',
        'label_last_purchase': '<b>🛍️ اخر عملية شراء:</b> {last_purchase}',
        'menu_intro': '<b>🛒 تسوق من البائعين الموثوقين بالاسفل ↓</b>',
        'btn_trusted_seller': '⭐ بائع موثوق',
        'btn_product': '🛍️ المنتجات',
        'btn_add_balance': '💳 اضافة رصيد',
        'btn_history': '📜 السجل',
        'btn_profile': '👤 ملفي الشخصي',
        'btn_help': '🆘 المساعدة والدعم',
        'btn_choose_language': '🌐 اختيار اللغة',
        'btn_terms': '📋 الشروط',
        'btn_become_reseller': '💼 كن بائعا',
        'terms_message': '<b>📋 شروط الموزع الرسمي</b>\n\n<b>⚠️ مهم: التواصل معنا بدون قبول هذه الشروط قد يؤدي إلى تجاهل الرسائل أو حظرها.</b>\n<b>💼 كن موزعا مميزا في HSA PANEL</b>\n<b>ادخل طريق الربح السريع وتواصل مع آلاف العملاء والمتاجر.</b>\n\n<b>✨ متطلبات الانضمام:</b>\n<b>• 🤝 الولاء: الولاء الكامل لـ HSA PANEL مطلوب.</b>\n<b>• 🌐 الدعم: يجب امتلاك قنوات نشطة لمشاركة روابط الشراء وتأكيد الدفع.</b>\n<b>• 📱 المعرفة: خبرة أساسية في تطبيقات الأندرويد لاستخدام الأدوات وإدارة المبيعات بكفاءة.</b>\n<b>💰 رسوم التفعيل: $10 🔑</b>\n<b>💡 ملاحظة: هذا المبلغ يضاف إلى رصيد حسابك ويمكن استخدامه في المعاملات القادمة.</b>\n\n<b>🚀 بعد التفعيل:</b>\n<b>• 📋 إدراج اسمك في قائمة الموزعين الرسمية.</b>\n<b>• 👥 البيع للعملاء الأفراد.</b>\n<b>• 🏪 البيع للمتاجر.</b>\n<b>• 🤝 التعاون مع الموزعين المعتمدين.</b>\n\n<b>🔥 فعّل الآن وافتح حالة الموزع المميز!</b>',
        'choose_language_title': '<b>🌐 اختيار اللغة</b>',
        'choose_language_desc': 'اختر لغة البوت المفضلة لديك.',
        'btn_english': '🇬🇧 الانجليزية',
        'btn_arabic': '🇸🇦 العربية',
        'language_set_en': '✅ تم اختيار الانجليزية (اللغة الافتراضية)',
        'language_set_ar': '✅ تم اختيار العربية. ستظهر رسائل البوت بالعربية.',
        'btn_back': '🔙 رجوع',
        'btn_back_to_menu': '🔙 رجوع للقائمة',
        'btn_back_to_main_menu': '🏠 رجوع للقائمة الرئيسية',
        'product_title': '<b>🛍️ ماذا تريد؟</b>',
        'product_desc_1': '<b>اختر فئة من الاسفل 👇</b>',
        'product_desc_2': '🎮 <b>حسابات:</b> شراء حسابات العاب',
        'product_desc_3': '🔧 <b>هاكات:</b> تصفح الادوات والباقات المميزة',
        'btn_account': '🎮 حسابات',
        'btn_hackes': '🔧 هاكات',
        'account_title': '<b>🎮 حسابات الالعاب</b>',
        'account_desc': '<b>اختر نوع الحساب من الاسفل 👇</b>\nشراء حسابات العاب مميزة مع العملات والمميزات.',
        'hackes_title': '<b>🔧 فئات الهاكات</b>',
        'hackes_desc': '<b>اختر فئة من الاسفل 👇</b>\nاختر لعبتك واستكشف الادوات والباقات المتاحة.',
        'no_resellers': '❌ لا يوجد بائعون.',
        'trusted_sellers_title': '⭐ <b>البائعون الموثوقون</b>',
        'trusted_sellers_footer': '📞 تواصل مع اي بائع للشراء!',
        'help_title': '<b>🛠 تحتاج مساعدة؟</b>',
        'help_purchase_error_title': '<b>⚠ خطأ في الشراء</b>',
        'help_purchase_error_body': 'اذا واجهت اي خطأ اثناء الشراء.',
        'help_apk_title': '<b>📦 رابط APK</b>',
        'help_apk_body': 'اذا اشتريت اي هاك ولم تحصل على رابط APK.',
        'help_any_title': '<b>🆘 اي نوع من المساعدة</b>',
        'help_any_body': 'اضغط الزر بالاسفل للتواصل مع دعم الادمن.',
        'btn_help_short': '🆘 مساعدة',
        'profile_title': '<b>👤 ملفي الشخصي</b>',
        'profile_name': '<b>👤 الاسم:</b> {name}',
        'profile_username': '<b>💻 اسم المستخدم:</b> @{username}',
        'profile_member_since': '<b>📅 عضو منذ:</b> {date}',
        'btn_purchase_history': '📜 سجل المشتريات',
        'add_balance_title': '<b>╔════════════════════╗</b>\n<b>   مركز اضافة الرصيد</b>\n<b>╚════════════════════╝</b>',
        'add_balance_1': '<b>هل تريد اضافة رصيد 💰</b>',
        'add_balance_2': '<b>انسخ معرفك ثم اضغط زر الايداع بالاسفل 👇</b>',
        'add_balance_3': '<b>معرفك:</b>',
        'add_balance_4': '<b>بعد الدفع ارسل صورة التحويل للادمن.</b>',
        'btn_deposit_now': '💳 ايداع الان',
        'btn_contact_admin': '💬 تواصل مع الادمن',
        'btn_refresh': '🔄 تحديث',
        'history_empty': 'لا يوجد سجل مشتريات.',
        'history_title': '<b>🕓 سجل مشترياتك:</b>',
        'history_page': '<b>الصفحة {page}/{total}</b>',
        'history_product': '<b>📦 المنتج:</b> {product}',
        'history_duration': '<b>⏳ المدة:</b> {duration}',
        'history_key': '<b>🔑 المفتاح:</b> <code>{key}</code>',
        'history_status_expired': '<b>📅 الحالة:</b> منتهي ❌',
        'history_status_active': '<b>📅 الحالة:</b> فعال ✅',
        'history_expired_on': '<i>انتهى بتاريخ: {date}</i>',
        'history_expires_on': '<i>ينتهي بتاريخ: {date}</i>',
        'btn_previous': '⬅️ السابق',
        'btn_next': 'التالي ➡️',
        'confirm_sure': '<b>📝 هل أنت متأكد من الشراء؟ 🫆</b>',
        'confirm_separator': '<b>--------------------------------------</b>',
        'confirm_note': '<b>ملاحظة📣:</b>',
        'confirm_no_return': '<b>لا يمكن إرجاع المفتاح بعد الشراء!</b>',
        'confirm_your_balance': '<b>💰 رصيدك:</b> ${balance}',
        'confirm_price': '<b>💰 السعر:</b> ${price}',
        'confirm_stock': '<b>📦 المخزون:</b> {stock}',
        'confirm_stock_available': '<b>📦 المخزون: متاح</b>',
        'btn_confirm': '✅ تأكيد',
        'btn_cancel': '❌ إلغاء',
        'out_of_stock_title': '❌ المنتج غير متوفر',
        'out_of_stock_product': '🐍 المنتج: {product}',
        'out_of_stock_duration': '⏳ المدة: {duration}',
        'out_of_stock_footer': '📦 المخزون المتاح: 0\n\nالرجاء المحاولة لاحقاً.',
        'not_vip_msg': '❌ أنت لست VIP. الأسعار مرئية فقط لأعضاء VIP.',
        'unknown_product': 'منتج غير معروف.',
        'out_of_stock_error': '❌ عذراً، نفذ المنتج من المخزون.',
        'insufficient_balance_title': '❌ رصيد غير كافٍ',
        'insufficient_balance_body': 'رصيدك غير كافٍ لإتمام هذا الشراء.\n\nالرجاء إضافة رصيد والمحاولة مجدداً.',
        'success_title': '<b>✅ تم الشراء بنجاح!</b>',
        'success_product': '<b>📦 المنتج:</b> {product}',
        'success_duration': '<b>⏳ المدة:</b> {duration}',
        'success_remaining': '<b>💰 الرصيد المتبقي:</b> {balance}$',
        'success_key': '<b>🔑 مفتاحك:</b> <code>{key}</code>',
        'success_enjoy': '<b>استمتع بصلاحياتك المميزة 🚀</b>',
        'account_not_available_title': '❌ الحساب غير متاح',
        'account_not_available_body': 'عذراً، لا توجد حسابات متاحة في الوقت الحالي.\nالرجاء التواصل مع الادمن أو المحاولة لاحقاً.',
        'success_8bp_product': '🎱 <b>المنتج:</b> {product}',
        'success_8bp_price': '💰 <b>السعر:</b> ${price}',
        'success_8bp_remaining': '💳 <b>الرصيد المتبقي:</b> ${balance}',
        'success_8bp_account_header': '          ✓ <b>تفاصيل الحساب</b>',
        'success_8bp_gmail': '📥 <b>الجيميل:</b> {gmail}',
        'success_8bp_password': '🔐 <b>كلمة المرور:</b> {password}',
        'insuf_price': '💰 <b>السعر:</b> ${price}',
        'insuf_your_balance': '💳 <b>رصيدك:</b> ${balance}',
        'insuf_shortfall': '📊 <b>الفرق:</b> ${shortfall}',
        'insuf_footer': 'الرجاء إضافة رصيد إلى حسابك.',
    }
}


def get_user_language(user_id: int, db=None) -> str:
    local_db = db if db is not None else load_db()
    user = local_db.get('users', {}).get(str(user_id), {})
    lang = user.get('language', 'en')
    return lang if lang in LANG_STRINGS else 'en'


def set_user_language(user_id: int, language: str) -> None:
    if language not in LANG_STRINGS:
        language = 'en'
    db = load_db()
    users = db.setdefault('users', {})
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            'balance': 0.0,
            'purchases': [],
            'member_since': datetime.now().strftime('%Y-%m-%d'),
            'language': language,
        }
    else:
        users[uid]['language'] = language
    save_db(db)


def t(user_id: int, key: str, lang: str | None = None, **kwargs) -> str:
    resolved_lang = lang if lang in LANG_STRINGS else get_user_language(user_id)
    template = LANG_STRINGS.get(resolved_lang, LANG_STRINGS['en']).get(key, LANG_STRINGS['en'].get(key, key))
    try:
        return template.format(**kwargs)
    except Exception:
        return template


def build_main_menu(user_id: int, lang: str | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(user_id, 'btn_trusted_seller', lang=lang), callback_data='trusted_seller')],
        [InlineKeyboardButton(t(user_id, 'btn_product', lang=lang), callback_data='product')],
        [InlineKeyboardButton(t(user_id, 'btn_add_balance', lang=lang), callback_data='add_balance'),
         InlineKeyboardButton(t(user_id, 'btn_history', lang=lang), callback_data='history')],
        [InlineKeyboardButton(t(user_id, 'btn_profile', lang=lang), callback_data='my_profile'),
         InlineKeyboardButton(t(user_id, 'btn_help', lang=lang), callback_data='help_support')],
        [InlineKeyboardButton(t(user_id, 'btn_choose_language', lang=lang), callback_data='choose_language'),
         InlineKeyboardButton(t(user_id, 'btn_terms', lang=lang), callback_data='terms')]
    ])


def build_main_profile_text(user_id: int, name_user: str, username: str, balance: float, status_text: str, last_purchase_text: str = '', show_last_purchase: bool = False, lang: str | None = None) -> str:
    lines = [
        t(user_id, 'welcome', lang=lang, name=name_user),
        '',
        t(user_id, 'label_user_id', lang=lang, uid=user_id),
        t(user_id, 'label_username', lang=lang, username=username),
        t(user_id, 'label_balance', lang=lang, balance=balance),
        t(user_id, 'label_status', lang=lang, status=status_text),
    ]
    if show_last_purchase:
        lines.append(t(user_id, 'label_last_purchase', lang=lang, last_purchase=last_purchase_text))
    lines.append('')
    lines.append(t(user_id, 'menu_intro', lang=lang))
    return '\n'.join(lines)

async def start(update: Update, context: CallbackContext) -> None:
    logger.info(f"START command received from user: {update.effective_user.id}")
    user = update.effective_user
    if not user or not update.message:
        return

    name_user = user.first_name
    username = user.username or "No username"
    user_id = user.id

    db = load_db()
    users = db.get('users', {})
    uid = str(user_id)

    if uid not in users:
        users[uid] = {
            'balance': 0.0, 
            'purchases': [], 
            'member_since': datetime.now().strftime("%Y-%m-%d"),
            'username': username,
            'first_name': name_user,
            'language': 'en'
        }
        save_db(db)
    else:
        # Update username and first_name if changed
        changed = False
        if users[uid].get('username') != username or users[uid].get('first_name') != name_user:
            users[uid]['username'] = username
            users[uid]['first_name'] = name_user
            changed = True
        if users[uid].get('language') not in LANG_STRINGS:
            users[uid]['language'] = 'en'
            changed = True
        if changed:
            save_db(db)

    lang = get_user_language(user_id, db)
    balance = users.get(uid, {}).get('balance', 0.0)
    safe_name_user = html.escape(name_user or 'User')
    display_username = user.username or t(user_id, 'no_username', lang=lang)
    safe_display_username = html.escape(display_username)

    # Check VIP status
    status_text = t(user_id, 'status_vip', lang=lang) if is_vip(user_id) else t(user_id, 'status_active', lang=lang)
    profile_text = build_main_profile_text(user_id, safe_name_user, safe_display_username, balance, status_text, lang=lang)
    menu = build_main_menu(user_id, lang=lang)

    try:
        await update.message.reply_photo(
            photo="https://i.postimg.cc/k4kRGdVK/file-00000000ca8c71faadd50d667e4a0509.png",
            caption=profile_text,
            reply_markup=menu,
            parse_mode=ParseMode.HTML
        )
    except Exception as exc:
        logger.warning(f"START photo send failed for user {user_id}: {exc}")
        await update.message.reply_text(
            text=profile_text,
            reply_markup=menu,
            parse_mode=ParseMode.HTML
        )
    logger.info(f"START message sent to user: {update.effective_user.id}")


def _other_menu_text() -> str:
    return (
        "<b>💼 Become Reseller</b>\n"
        "Start earning by selling premium products.\n\n"
        "<b>📱 Check Device</b>\n"
        "Verify if your device is compatible with our tools.\n\n"
        "<b>📘 User Guide</b>\n"
        "Step-by-step instructions for safe & effective use."
    )


def _other_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💼 Become Reseller", callback_data="other_become_reseller")],
        [InlineKeyboardButton("📱 Check Device", callback_data="other_check_device"),
         InlineKeyboardButton("📘 User Guide", callback_data="other_user_guide")],
        [InlineKeyboardButton("🌐 Open Site", callback_data="other_open_site")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
    ])


async def other_command(update: Update, context: CallbackContext) -> None:
    """Show reseller/device/user-guide menu for /other command."""
    if not update.message:
        return
    await update.message.reply_photo(
        photo="https://i.postimg.cc/pdtfG7LF/IMG-20260305-163542.png",
        caption=_other_menu_text(),
        reply_markup=_other_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )


async def other_become_reseller(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    text = (
        "👑 Become an Official Reseller\n\n"
        "💼 Start earning by selling our premium products and grow your business.\n\n"
        "1️⃣ Contact Admin: @Hayazi_Saheb\n"
        "2️⃣ Deposit: Minimum 10 USDT\n"
        "3️⃣ Activation: Get VIP Reseller Access\n\n"
        "💎 Reseller Benefits\n"
        "⚡ Access to Reseller Prices\n"
        "🔑 Instant Auto Key Delivery\n"
        "🚀 Sell Products & Earn Your Profit\n"
        "📦 24/7 Automated System\n"
        "🛡 Secure & Trusted Transactions\n"
        "📊 Easy product selling system\n\n"
        "🎮 Available Products\n"
        "🎱 8 Ball Pool Hack\n"
        "🎯 Carrom Pool Hack\n"
        "⚡ Score Star Hack\n"
        "🔥 Free Fire Hack\n"
        "📱 iOS Certificate\n\n"
        "📢 Important:\n"
        "• Prices are visible only to VIP users\n"
        "• Keys are delivered instantly after purchase\n"
        "• Perfect for Telegram channels, TikTok & Facebook sellers"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 Become Reseller", url="https://t.me/Hayazi_Saheb")],
        [InlineKeyboardButton("🔙 Back", callback_data="other_back_menu")]
    ])
    try:
        await query.edit_message_caption(caption=text, reply_markup=keyboard)
    except Exception:
        await query.edit_message_text(text=text, reply_markup=keyboard)


async def other_check_device(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    text = (
        "<b>📱 Device Verification Required\n\n"
        "🔍 Please check your device compatibility and than buy.\n\n"
        "⚙ Supported Device\n"
        "🟢 64-bit (arm64-v8a)\n\n"
        "🚫 Not Supported\n"
        "🔴 32-bit (armeabi-v7a)\n\n"
        "📥 Step 1: Download Device Info Tool\n"
        "📲 Step 2: Open the app and check ABI\n\n"
        "🟢 ABI: arm64-v8a ➜ Supported ✅\n"
        "🔴 ABI: armeabi-v7a ➜ Not Supported ❌\n\n"
        "⚠ If your device is 32-bit, the app cannot run on your device.</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Download", url="https://www.mediafire.com/file/91tl7ko41da8xh2/deviceinfo.apk/file")],
        [InlineKeyboardButton("🔙 Back", callback_data="other_back_menu")]
    ])
    try:
        await query.edit_message_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    except Exception:
        await query.edit_message_text(text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)


async def other_user_guide(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    text = (
        "<b>🧠 Power Without Fear — Use Our Products with Confidence\n\n"
        "⚡ Our tools are built to deliver power, safety & smooth performance.\n"
        "A pro-grade system designed for the best gaming experience.\n\n"
        "⚙️ Golden Rules for Safe Use:\n"
        "• 🏟 Start in Private/Training Matches to test settings\n"
        "• 🎯 In competitive modes, play smart & balanced\n"
        "• 📹 Avoid using tools during live streams or recordings\n"
        "• 💎 Buy keys only from trusted resellers\n"
        "• 🔄 Always use the latest updated version\n\n"
        "📱 Device & Version Support:\n"
        "• ✅ Works best on Android 64-bit devices\n"
        "• 📱 Compatible with Samsung, Xiaomi, Realme, Vivo, Oppo & Huawei\n"
        "• 🔓 Some tools require Root, while others work without Root\n\n"
        "🧩 Technical Support:\n"
        "• 💬 Support team available when you need help\n"
        "• 🔧 Regular updates for stability & performance\n"
        "• 📝 All user reports are reviewed carefully\n\n"
        "💡 Remember:\n"
        "Safety depends on how you use the tools.\n"
        "Our products are built with security, stability & performance in mind.</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Close", callback_data="other_back_menu")]
    ])
    try:
        await query.edit_message_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    except Exception:
        await query.edit_message_text(text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)


async def other_open_site(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    text = (
        "<b>🎮 INSTANT GAMING STORE 🎮</b>\n\n"
        "<b>💎 Want to Buy Game Items Instantly?</b>\n"
        "<b>⚡ Fast • Safe • Trusted Delivery</b>\n\n"
        "<b>🎯 Available Services:</b>\n\n"
        "<b>🎱 8 Ball Pool Hacks</b>\n"
        "<b>💰 Coin & Cash Top-Up</b>\n"
        "<b>🏆 Golden Shot / Golden Shop</b>\n"
        "<b>🔫 PUBG UC Top-Up</b>\n"
        "<b>🛒 Premium Gaming Items</b>\n\n"
        "<b>━━━━━━━━━━━━━━━━━━━━</b>\n\n"
        "<b>🚀 Click The Button Below</b>\n"
        "<b>🌐 Open The Website & Explore All Products</b>\n\n"
        "<b>💥 Instant Delivery</b>\n"
        "<b>🔐 Secure System</b>\n"
        "<b>⭐ Trusted Service</b>\n\n"
        "<b>👇 TAP BELOW TO OPEN SITE 👇</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Open Site", url="https://studio-5771407601-823f3.web.app")],
        [InlineKeyboardButton("🔙 Back", callback_data="other_back_menu")]
    ])
    try:
        await query.edit_message_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    except Exception:
        await query.edit_message_text(text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)


async def other_back_menu(update: Update, context: CallbackContext) -> None:
    """Return from /other sub-pages to the /other menu page."""
    query = update.callback_query
    await query.answer()
    try:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media="https://i.postimg.cc/pdtfG7LF/IMG-20260305-163542.png",
                caption=_other_menu_text(),
                parse_mode=ParseMode.HTML
            ),
            reply_markup=_other_menu_keyboard()
        )
    except Exception:
        await query.edit_message_text(
            text=_other_menu_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=_other_menu_keyboard()
        )

async def product(update: Update, context: CallbackContext) -> None:
    """Show intermediate menu: What you want - Account or Hackes"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    product_text = t(user_id, 'product_title') + "\n\n"
    product_text += t(user_id, 'product_desc_1') + "\n\n"
    product_text += t(user_id, 'product_desc_2') + "\n"
    product_text += t(user_id, 'product_desc_3')

    product_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(user_id, 'btn_account'), callback_data="product_accounts"),
         InlineKeyboardButton(t(user_id, 'btn_hackes'), callback_data="product_hackes")],
        [InlineKeyboardButton(t(user_id, 'btn_back'), callback_data="back_to_menu")]
    ])

    await query.edit_message_media(
        media=InputMediaPhoto(
            media="https://i.postimg.cc/63SX4GDG/IMG-20260301-213107.png",
            caption=product_text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=product_menu
    )

async def product_accounts(update: Update, context: CallbackContext) -> None:
    """Show account options (8BP Account)"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    account_text = t(user_id, 'account_title') + "\n\n"
    account_text += t(user_id, 'account_desc')

    account_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎱 8 Ball Pool Account", callback_data="product_8bp_account")],
        [InlineKeyboardButton(t(user_id, 'btn_back'), callback_data="product")]
    ])

    await query.edit_message_media(
        media=InputMediaPhoto(
            media="https://i.postimg.cc/63SX4GDG/IMG-20260301-213107.png",
            caption=account_text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=account_menu
    )

async def product_hackes(update: Update, context: CallbackContext) -> None:
    """Show hack/tool categories"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    product_text = t(user_id, 'hackes_title') + "\n\n"
    product_text += t(user_id, 'hackes_desc')

    product_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎱 8 Ball Pool", callback_data="product_8ball"),
         InlineKeyboardButton("🏏 Caroom Pool", callback_data="product_caroom")],
        [InlineKeyboardButton("⚽ Score Star", callback_data="product_scorestar"),
         InlineKeyboardButton("🔥 Free Fire", callback_data="product_freefire")],
        [InlineKeyboardButton("📗 Certificate iOS", callback_data="product_certificate_ios")],
        [InlineKeyboardButton(t(user_id, 'btn_back'), callback_data="product")]
    ])

    await query.edit_message_media(
        media=InputMediaPhoto(
            media="https://i.postimg.cc/63SX4GDG/IMG-20260301-213107.png",
            caption=product_text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=product_menu
    )

async def eight_ball_pool(update: Update, context: CallbackContext) -> None:


    query = update.callback_query
    await query.answer()

    pool_text = "<b>🎱 8 Ball Pool Category</b>\n\n"
    pool_text += "<b>The strongest hacks available right now 🚀</b>\n"
    pool_text += "Choose your desired product below 🎮\n\n"
    # fetch balance
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)
    pool_text += f"<b>💰 Your Balance:</b> {balance}$"

    pool_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton("🐍 Snake Engine", callback_data="item_snake") ,
         InlineKeyboardButton("🎯 Aim King", callback_data="item_aimking")],
        [InlineKeyboardButton("💀 Kos Hack", callback_data="item_kos"),
         InlineKeyboardButton("🎯 Aim X", callback_data="item_aimx")],
        [InlineKeyboardButton("🐺 Wolf Hack", callback_data="item_wolf"),
         InlineKeyboardButton("🧙 Wizard iOS", callback_data="item_wizard")],
        [InlineKeyboardButton("🥷 Ninja Engine", callback_data="item_ninja")],
        [InlineKeyboardButton("🔙 Back to Product Category", callback_data="product_hackes")]
    ])
    await query.edit_message_media(
        media=InputMediaPhoto(
            media="https://i.postimg.cc/63SX4GDG/IMG-20260301-213107.png",
            caption=pool_text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=pool_menu
    )

async def eight_bp_account(update: Update, context: CallbackContext) -> None:
    """8BP Account coin purchase menu."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db = load_db()
    users = db.setdefault('users', {})
    uid = str(user_id)
    if uid not in users:
        users[uid] = {'balance': 0.0, 'purchases': [], 'member_since': datetime.now().strftime("%Y-%m-%d")}
    
    balance = users[uid].get('balance', 0.0)

    text = (
        "<b>🎱 8 Ball Pool Accounts</b>\n\n"
        "<b>Choose your account if you want to buy:</b>\n\n"
        "💰 <b>3B Coin Account</b>\n"
        "💰 <b>2B Coin Account</b>\n"
        "💰 <b>1B Coin Account</b>\n"
        "💰 <b>100M Coin Account</b>\n\n"
        f"<b>💳 Your Balance:</b> ${balance}"
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("3B Coin", callback_data="buy_8bp_3b"),
         InlineKeyboardButton("2B Coin", callback_data="buy_8bp_2b")],
        [InlineKeyboardButton("1B Coin", callback_data="buy_8bp_1b"),
         InlineKeyboardButton("100M Coin", callback_data="buy_8bp_100m")],
        [InlineKeyboardButton("🔙 Back", callback_data="product_accounts")]
    ])

    await query.edit_message_media(
        media=InputMediaPhoto(
            media="https://i.postimg.cc/63SX4GDG/IMG-20260301-213107.png",
            caption=text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=buttons
    )

async def buy_8bp_1b(update: Update, context: CallbackContext) -> None:
    """Handle 1B Coin purchase - show confirmation first."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if not has_vip_access(user_id):
        await show_vip_required_screen(
            query,
            "https://i.postimg.cc/63SX4GDG/IMG-20260301-213107.png",
            "product_8bp_account"
        )
        return

    db = load_db()
    users = db.setdefault('users', {})
    uid = str(user_id)
    if uid not in users:
        users[uid] = {'balance': 0.0, 'purchases': [], 'member_since': datetime.now().strftime("%Y-%m-%d")}
    
    balance = users[uid].get('balance', 0.0)
    price = 2.8
    
    # Show confirmation message
    text = f"<b>🏷 1B Coin Account  →  ${price}</b>\n\n"
    text += f"{t(user_id, 'confirm_sure')}\n"
    text += f"{t(user_id, 'confirm_separator')}\n\n"
    text += f"{t(user_id, 'confirm_note')}\n"
    text += f"{t(user_id, 'confirm_no_return')}\n"
    text += f"{t(user_id, 'confirm_your_balance', balance=balance)}\n"
    text += f"{t(user_id, 'confirm_price', price=price)}\n"
    text += t(user_id, 'confirm_stock_available')

    await query.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(t(user_id, 'btn_confirm'), callback_data="confirm_buy_8bp_1b"),
             InlineKeyboardButton(t(user_id, 'btn_cancel'), callback_data="product_8bp_account")],
        ]),
        parse_mode=ParseMode.HTML
    )

async def buy_8bp_100m(update: Update, context: CallbackContext) -> None:
    """Handle 100M Coin purchase - show confirmation first."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if not has_vip_access(user_id):
        await show_vip_required_screen(
            query,
            "https://i.postimg.cc/63SX4GDG/IMG-20260301-213107.png",
            "product_8bp_account"
        )
        return

    db = load_db()
    users = db.setdefault('users', {})
    uid = str(user_id)
    if uid not in users:
        users[uid] = {'balance': 0.0, 'purchases': [], 'member_since': datetime.now().strftime("%Y-%m-%d")}
    
    balance = users[uid].get('balance', 0.0)
    price = 2.4
    
    # Show confirmation message
    text = f"<b>🏷 100M Coin Account  →  ${price}</b>\n\n"
    text += f"{t(user_id, 'confirm_sure')}\n"
    text += f"{t(user_id, 'confirm_separator')}\n\n"
    text += f"{t(user_id, 'confirm_note')}\n"
    text += f"{t(user_id, 'confirm_no_return')}\n"
    text += f"{t(user_id, 'confirm_your_balance', balance=balance)}\n"
    text += f"{t(user_id, 'confirm_price', price=price)}\n"
    text += t(user_id, 'confirm_stock_available')

    await query.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(t(user_id, 'btn_confirm'), callback_data="confirm_buy_8bp_100m"),
             InlineKeyboardButton(t(user_id, 'btn_cancel'), callback_data="product_8bp_account")],
        ]),
        parse_mode=ParseMode.HTML
    )


async def buy_8bp_2b(update: Update, context: CallbackContext) -> None:
    """Handle 2B Coin purchase - show confirmation first."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if not has_vip_access(user_id):
        await show_vip_required_screen(
            query,
            "https://i.postimg.cc/63SX4GDG/IMG-20260301-213107.png",
            "product_8bp_account"
        )
        return

    db = load_db()
    users = db.setdefault('users', {})
    uid = str(user_id)
    if uid not in users:
        users[uid] = {'balance': 0.0, 'purchases': [], 'member_since': datetime.now().strftime("%Y-%m-%d")}

    balance = users[uid].get('balance', 0.0)
    price = 5.5

    text = f"<b>🏷 2B Coin Account  →  ${price}</b>\n\n"
    text += f"{t(user_id, 'confirm_sure')}\n"
    text += f"{t(user_id, 'confirm_separator')}\n\n"
    text += f"{t(user_id, 'confirm_note')}\n"
    text += f"{t(user_id, 'confirm_no_return')}\n"
    text += f"{t(user_id, 'confirm_your_balance', balance=balance)}\n"
    text += f"{t(user_id, 'confirm_price', price=price)}\n"
    text += t(user_id, 'confirm_stock_available')

    await query.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(t(user_id, 'btn_confirm'), callback_data="confirm_buy_8bp_2b"),
             InlineKeyboardButton(t(user_id, 'btn_cancel'), callback_data="product_8bp_account")],
        ]),
        parse_mode=ParseMode.HTML
    )


async def buy_8bp_3b(update: Update, context: CallbackContext) -> None:
    """Handle 3B Coin purchase - show confirmation first."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if not has_vip_access(user_id):
        await show_vip_required_screen(
            query,
            "https://i.postimg.cc/63SX4GDG/IMG-20260301-213107.png",
            "product_8bp_account"
        )
        return

    db = load_db()
    users = db.setdefault('users', {})
    uid = str(user_id)
    if uid not in users:
        users[uid] = {'balance': 0.0, 'purchases': [], 'member_since': datetime.now().strftime("%Y-%m-%d")}

    balance = users[uid].get('balance', 0.0)
    price = 8.0

    text = f"<b>🏷 3B Coin Account  →  ${price}</b>\n\n"
    text += f"{t(user_id, 'confirm_sure')}\n"
    text += f"{t(user_id, 'confirm_separator')}\n\n"
    text += f"{t(user_id, 'confirm_note')}\n"
    text += f"{t(user_id, 'confirm_no_return')}\n"
    text += f"{t(user_id, 'confirm_your_balance', balance=balance)}\n"
    text += f"{t(user_id, 'confirm_price', price=price)}\n"
    text += t(user_id, 'confirm_stock_available')

    await query.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(t(user_id, 'btn_confirm'), callback_data="confirm_buy_8bp_3b"),
             InlineKeyboardButton(t(user_id, 'btn_cancel'), callback_data="product_8bp_account")],
        ]),
        parse_mode=ParseMode.HTML
    )

async def confirm_buy_8bp_1b(update: Update, context: CallbackContext) -> None:
    """Confirm 1B Coin purchase."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db = load_db()
    users = db.setdefault('users', {})
    uid = str(user_id)
    if uid not in users:
        users[uid] = {'balance': 0.0, 'purchases': [], 'member_since': datetime.now().strftime("%Y-%m-%d")}
    
    balance = users[uid].get('balance', 0.0)
    price = 2.8

    if balance >= price:
        # Check if account is available
        accounts = db.get('8bp_accounts_1b', [])
        
        if not accounts:
            await query.message.reply_text(
                f"{t(user_id, 'account_not_available_title')}\n\n{t(user_id, 'account_not_available_body')}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(t(user_id, 'btn_contact_admin'), url="https://t.me/Hayazi_Saheb")],
                    [InlineKeyboardButton(t(user_id, 'btn_back'), callback_data="product_8bp_account")]
                ]),
                parse_mode=ParseMode.HTML
            )
            return
        
        # Get first available account
        account = accounts.pop(0)
        
        users[uid]['balance'] = round(balance - price, 8)
        entry = {
            'product': '1B Coin Account',
            'category': '8 Ball Pool',
            'price': price,
            'date': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }
        users[uid]['purchases'].append(entry)
        save_db(db)

        # Send admin notification
        db = load_db()
        admins_list = db.get('admins', [ADMIN_ID])
        user_name = query.from_user.username or "Unknown"
        if user_name != "Unknown":
            user_name = f"@{user_name}"
        
        admin_notification = f"🛒 <b>New Purchase Notification</b>\n\n"
        admin_notification += f"🆔 <b>User ID:</b> {user_id}\n"
        admin_notification += f"👤 <b>User name:</b> {user_name}\n"
        admin_notification += f"📦 <b>Product:</b> 1 Billion Coin Account\n"
        admin_notification += f"⏳ <b>Duration:</b> Lifetime\n"
        admin_notification += f"💰 <b>Price:</b> {price}$\n"
        admin_notification += f"📅 <b>Purchase Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        for admin_id in admins_list:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_notification,
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass  # Silently fail if admin notification doesn't send

        await query.message.reply_text(
            f"{t(user_id, 'success_title')}\n\n"
            f"{t(user_id, 'success_8bp_product', product='1 Billion Coin Account')}\n"
            f"{t(user_id, 'success_8bp_price', price=price)}\n"
            f"{t(user_id, 'success_8bp_remaining', balance=users[uid]['balance'])}\n\n"
            f"{t(user_id, 'success_8bp_account_header')}\n"
            f"{t(user_id, 'success_8bp_gmail', gmail=account['gmail'])}\n"
            f"{t(user_id, 'success_8bp_password', password=account['password'])}",
            parse_mode=ParseMode.HTML
        )
    else:
        await query.message.reply_text(
            f"{t(user_id, 'insufficient_balance_title')}\n\n"
            f"{t(user_id, 'insuf_price', price=price)}\n"
            f"{t(user_id, 'insuf_your_balance', balance=balance)}\n"
            f"{t(user_id, 'insuf_shortfall', shortfall=round(price - balance, 2))}\n\n"
            f"{t(user_id, 'insuf_footer')}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(t(user_id, 'btn_add_balance'), callback_data="add_balance")],
                [InlineKeyboardButton(t(user_id, 'btn_back'), callback_data="product_8bp_account")]
            ]),
            parse_mode=ParseMode.HTML
        )

async def confirm_buy_8bp_100m(update: Update, context: CallbackContext) -> None:
    """Confirm 100M Coin purchase."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db = load_db()
    users = db.setdefault('users', {})
    uid = str(user_id)
    if uid not in users:
        users[uid] = {'balance': 0.0, 'purchases': [], 'member_since': datetime.now().strftime("%Y-%m-%d")}
    
    balance = users[uid].get('balance', 0.0)
    price = 2.4

    if balance >= price:
        # Check if account is available
        accounts = db.get('8bp_accounts_100m', [])
        
        if not accounts:
            await query.message.reply_text(
                f"{t(user_id, 'account_not_available_title')}\n\n{t(user_id, 'account_not_available_body')}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(t(user_id, 'btn_contact_admin'), url="https://t.me/Hayazi_Saheb")],
                    [InlineKeyboardButton(t(user_id, 'btn_back'), callback_data="product_8bp_account")]
                ]),
                parse_mode=ParseMode.HTML
            )
            return
        
        # Get first available account
        account = accounts.pop(0)
        
        users[uid]['balance'] = round(balance - price, 8)
        entry = {
            'product': '100M Coin Account',
            'category': '8 Ball Pool',
            'price': price,
            'date': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }
        users[uid]['purchases'].append(entry)
        save_db(db)

        # Send admin notification
        db = load_db()
        admins_list = db.get('admins', [ADMIN_ID])
        user_name = query.from_user.username or "Unknown"
        if user_name != "Unknown":
            user_name = f"@{user_name}"
        
        admin_notification = f"🛒 <b>New Purchase Notification</b>\n\n"
        admin_notification += f"🆔 <b>User ID:</b> {user_id}\n"
        admin_notification += f"👤 <b>User name:</b> {user_name}\n"
        admin_notification += f"📦 <b>Product:</b> 100 Million Coin Account\n"
        admin_notification += f"⏳ <b>Duration:</b> Lifetime\n"
        admin_notification += f"💰 <b>Price:</b> {price}$\n"
        admin_notification += f"📅 <b>Purchase Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        for admin_id in admins_list:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_notification,
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass  # Silently fail if admin notification doesn't send

        await query.message.reply_text(
            f"{t(user_id, 'success_title')}\n\n"
            f"{t(user_id, 'success_8bp_product', product='100 Million Coin Account')}\n"
            f"{t(user_id, 'success_8bp_price', price=price)}\n"
            f"{t(user_id, 'success_8bp_remaining', balance=users[uid]['balance'])}\n\n"
            f"{t(user_id, 'success_8bp_account_header')}\n"
            f"{t(user_id, 'success_8bp_gmail', gmail=account['gmail'])}\n"
            f"{t(user_id, 'success_8bp_password', password=account['password'])}",
            parse_mode=ParseMode.HTML
        )
    else:
        await query.message.reply_text(
            f"{t(user_id, 'insufficient_balance_title')}\n\n"
            f"{t(user_id, 'insuf_price', price=price)}\n"
            f"{t(user_id, 'insuf_your_balance', balance=balance)}\n"
            f"{t(user_id, 'insuf_shortfall', shortfall=round(price - balance, 2))}\n\n"
            f"{t(user_id, 'insuf_footer')}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(t(user_id, 'btn_add_balance'), callback_data="add_balance")],
                [InlineKeyboardButton(t(user_id, 'btn_back'), callback_data="product_8bp_account")]
            ]),
            parse_mode=ParseMode.HTML
        )


async def confirm_buy_8bp_2b(update: Update, context: CallbackContext) -> None:
    """Confirm 2B Coin purchase."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db = load_db()
    users = db.setdefault('users', {})
    uid = str(user_id)
    if uid not in users:
        users[uid] = {'balance': 0.0, 'purchases': [], 'member_since': datetime.now().strftime("%Y-%m-%d")}

    balance = users[uid].get('balance', 0.0)
    price = 5.5

    if balance >= price:
        accounts = db.get('8bp_accounts_2b', [])

        if not accounts:
            await query.message.reply_text(
                f"{t(user_id, 'account_not_available_title')}\n\n{t(user_id, 'account_not_available_body')}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(t(user_id, 'btn_contact_admin'), url="https://t.me/Hayazi_Saheb")],
                    [InlineKeyboardButton(t(user_id, 'btn_back'), callback_data="product_8bp_account")]
                ]),
                parse_mode=ParseMode.HTML
            )
            return

        account = accounts.pop(0)

        users[uid]['balance'] = round(balance - price, 8)
        entry = {
            'product': '2B Coin Account',
            'category': '8 Ball Pool',
            'price': price,
            'date': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }
        users[uid]['purchases'].append(entry)
        save_db(db)

        db = load_db()
        admins_list = db.get('admins', [ADMIN_ID])
        user_name = query.from_user.username or "Unknown"
        if user_name != "Unknown":
            user_name = f"@{user_name}"

        admin_notification = f"🛒 <b>New Purchase Notification</b>\n\n"
        admin_notification += f"🆔 <b>User ID:</b> {user_id}\n"
        admin_notification += f"👤 <b>User name:</b> {user_name}\n"
        admin_notification += f"📦 <b>Product:</b> 2 Billion Coin Account\n"
        admin_notification += f"⏳ <b>Duration:</b> Lifetime\n"
        admin_notification += f"💰 <b>Price:</b> {price}$\n"
        admin_notification += f"📅 <b>Purchase Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        for admin_id in admins_list:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_notification,
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass

        await query.message.reply_text(
            f"{t(user_id, 'success_title')}\n\n"
            f"{t(user_id, 'success_8bp_product', product='2 Billion Coin Account')}\n"
            f"{t(user_id, 'success_8bp_price', price=price)}\n"
            f"{t(user_id, 'success_8bp_remaining', balance=users[uid]['balance'])}\n\n"
            f"{t(user_id, 'success_8bp_account_header')}\n"
            f"{t(user_id, 'success_8bp_gmail', gmail=account['gmail'])}\n"
            f"{t(user_id, 'success_8bp_password', password=account['password'])}",
            parse_mode=ParseMode.HTML
        )
    else:
        await query.message.reply_text(
            f"{t(user_id, 'insufficient_balance_title')}\n\n"
            f"{t(user_id, 'insuf_price', price=price)}\n"
            f"{t(user_id, 'insuf_your_balance', balance=balance)}\n"
            f"{t(user_id, 'insuf_shortfall', shortfall=round(price - balance, 2))}\n\n"
            f"{t(user_id, 'insuf_footer')}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(t(user_id, 'btn_add_balance'), callback_data="add_balance")],
                [InlineKeyboardButton(t(user_id, 'btn_back'), callback_data="product_8bp_account")]
            ]),
            parse_mode=ParseMode.HTML
        )


async def confirm_buy_8bp_3b(update: Update, context: CallbackContext) -> None:
    """Confirm 3B Coin purchase."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db = load_db()
    users = db.setdefault('users', {})
    uid = str(user_id)
    if uid not in users:
        users[uid] = {'balance': 0.0, 'purchases': [], 'member_since': datetime.now().strftime("%Y-%m-%d")}

    balance = users[uid].get('balance', 0.0)
    price = 8.0

    if balance >= price:
        accounts = db.get('8bp_accounts_3b', [])

        if not accounts:
            await query.message.reply_text(
                f"{t(user_id, 'account_not_available_title')}\n\n{t(user_id, 'account_not_available_body')}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(t(user_id, 'btn_contact_admin'), url="https://t.me/Hayazi_Saheb")],
                    [InlineKeyboardButton(t(user_id, 'btn_back'), callback_data="product_8bp_account")]
                ]),
                parse_mode=ParseMode.HTML
            )
            return

        account = accounts.pop(0)

        users[uid]['balance'] = round(balance - price, 8)
        entry = {
            'product': '3B Coin Account',
            'category': '8 Ball Pool',
            'price': price,
            'date': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }
        users[uid]['purchases'].append(entry)
        save_db(db)

        db = load_db()
        admins_list = db.get('admins', [ADMIN_ID])
        user_name = query.from_user.username or "Unknown"
        if user_name != "Unknown":
            user_name = f"@{user_name}"

        admin_notification = f"🛒 <b>New Purchase Notification</b>\n\n"
        admin_notification += f"🆔 <b>User ID:</b> {user_id}\n"
        admin_notification += f"👤 <b>User name:</b> {user_name}\n"
        admin_notification += f"📦 <b>Product:</b> 3 Billion Coin Account\n"
        admin_notification += f"⏳ <b>Duration:</b> Lifetime\n"
        admin_notification += f"💰 <b>Price:</b> {price}$\n"
        admin_notification += f"📅 <b>Purchase Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        for admin_id in admins_list:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_notification,
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass

        await query.message.reply_text(
            f"{t(user_id, 'success_title')}\n\n"
            f"{t(user_id, 'success_8bp_product', product='3 Billion Coin Account')}\n"
            f"{t(user_id, 'success_8bp_price', price=price)}\n"
            f"{t(user_id, 'success_8bp_remaining', balance=users[uid]['balance'])}\n\n"
            f"{t(user_id, 'success_8bp_account_header')}\n"
            f"{t(user_id, 'success_8bp_gmail', gmail=account['gmail'])}\n"
            f"{t(user_id, 'success_8bp_password', password=account['password'])}",
            parse_mode=ParseMode.HTML
        )
    else:
        await query.message.reply_text(
            f"{t(user_id, 'insufficient_balance_title')}\n\n"
            f"{t(user_id, 'insuf_price', price=price)}\n"
            f"{t(user_id, 'insuf_your_balance', balance=balance)}\n"
            f"{t(user_id, 'insuf_shortfall', shortfall=round(price - balance, 2))}\n\n"
            f"{t(user_id, 'insuf_footer')}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(t(user_id, 'btn_add_balance'), callback_data="add_balance")],
                [InlineKeyboardButton(t(user_id, 'btn_back'), callback_data="product_8bp_account")]
            ]),
            parse_mode=ParseMode.HTML
        )

async def caroom_pool(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    caroom_text = "<b>🏏 Caroom Pool Category</b>\n\n"
    caroom_text += "<b>Select your product below 👇</b>\n"
    caroom_text += "Choose Carrom SE or Carrom AK."

    caroom_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏏 Carrom SE", callback_data="carrom_se"),
         InlineKeyboardButton("🏏 Carrom AK", callback_data="carrom_ak")],
        [InlineKeyboardButton("🔙 Back", callback_data="product_hackes")]
    ])

    await query.edit_message_media(
        media=InputMediaPhoto(
            media="https://i.postimg.cc/63SX4GDG/IMG-20260301-213107.png",
            caption=caroom_text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=caroom_menu
    )

async def ninja_engine(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)
    text = "<b>🎱 DOMINATED THE TABLE</b>\nPrecision. Power. Perfect Shots.\n\n<b>💰 YOUR BALANCE:</b> {}$".format(balance)
    
    price_3 = get_price('ninja_engine', '3_days')
    price_7 = get_price('ninja_engine', '7_days')
    price_30 = get_price('ninja_engine', '30_days')
    
    menu = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"3 Days – ${price_3}", callback_data="buy_ninja_3"),
         InlineKeyboardButton(f"7 Days – ${price_7}", callback_data="buy_ninja_7")],
        [InlineKeyboardButton(f"30 Days – ${price_30}", callback_data="buy_ninja_30")],
        [InlineKeyboardButton("🔙 Back", callback_data="product_8ball")]
    ])
    await query.edit_message_media(
        media=InputMediaPhoto(
            media=HACK_INFO['ninja_engine']['image'],
            caption=text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=menu
    )

async def snake_engine(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    snake_text = "<b>🐍 Snake Engine – Premium Access</b>\n\n"
    snake_text += "Please choose your desired duration below ⏳\n\n"
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)
    snake_text += f"<b>💰 Your Balance:</b> {balance}$"

    price_3 = get_price('snake_engine', '3_days')
    price_10 = get_price('snake_engine', '10_days')
    price_30 = get_price('snake_engine', '30_days')

    # build durations
    snake_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"3 Days – ${price_3}", callback_data="buy_snake_3") ,
         InlineKeyboardButton(f"10 Days – ${price_10}", callback_data="buy_snake_10")],
        [InlineKeyboardButton(f"30 Days – ${price_30}", callback_data="buy_snake_30")],
        [InlineKeyboardButton("🔙 Back", callback_data="product_8ball")]
    ])

    await query.edit_message_media(
        media=InputMediaPhoto(
            media="https://i.postimg.cc/ryWbNb41/IMG-20260301-211803.png",
            caption=snake_text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=snake_menu
    )

async def aim_x_hack(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)

    ax_text = "<b>🎯 Aim X Hack – Premium Access</b>\n\n"
    ax_text += "Choose your desired duration below ⏳\n\n"
    ax_text += f"<b>💰 Your Balance:</b> {balance}$\n\n"

    price_1 = get_price('aim_x', '1_day')
    price_2 = get_price('aim_x', '2_days')
    price_7 = get_price('aim_x', '7_days')
    price_15 = get_price('aim_x', '15_days')
    price_30 = get_price('aim_x', '30_days')

    ax_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"1 Day – ${price_1}", callback_data="buy_aimx_1"),
         InlineKeyboardButton(f"2 Days – ${price_2}", callback_data="buy_aimx_2")],
        [InlineKeyboardButton(f"7 Days – ${price_7}", callback_data="buy_aimx_7"),
         InlineKeyboardButton(f"15 Days – ${price_15}", callback_data="buy_aimx_15")],
        [InlineKeyboardButton(f"30 Days – ${price_30}", callback_data="buy_aimx_30")],
        [InlineKeyboardButton("🔙 Back", callback_data="product_8ball")]
    ])

    await query.edit_message_media(
        media=InputMediaPhoto(
            media="https://i.postimg.cc/7Zp09B07/IMG-20260301-212442.png",
            caption=ax_text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=ax_menu
    )


# Add Balance button flow handler

async def kos_mode(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)

    mode_text = "<b>🔥 Kos Mode – Premium Packages</b>\n\n"
    mode_text += "Select your duration ⏳\n\n"
    mode_text += f"<b>💰 Your Balance:</b> {balance}$\n\n"

    price_1 = get_price('kos_mode', '1_day')
    price_7 = get_price('kos_mode', '7_days')
    price_15 = get_price('kos_mode', '15_days')
    price_30 = get_price('kos_mode', '30_days')

    mode_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"1 Day – ${price_1}", callback_data="buy_kosmode_1"),
         InlineKeyboardButton(f"7 Days – ${price_7}", callback_data="buy_kosmode_7")],
        [InlineKeyboardButton(f"15 Days – ${price_15}", callback_data="buy_kosmode_15"),
         InlineKeyboardButton(f"30 Days – ${price_30}", callback_data="buy_kosmode_30")],
        [InlineKeyboardButton("🔙 Back", callback_data="item_kos")]
    ])

    await query.edit_message_media(
        media=InputMediaPhoto(
            media="https://i.postimg.cc/ZnFwtGFT/IMG-20260301-214244.png",
            caption=mode_text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=mode_menu
    )

async def kos_virtual(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)

    virt_text = "<b>⚡ Kos Virtual – Premium Packages</b>\n\n"
    virt_text += "Select your duration ⏳\n\n"
    virt_text += f"<b>💰 Your Balance:</b> {balance}$\n\n"

    price_1 = get_price('kos_virtual', '1_day')
    price_7 = get_price('kos_virtual', '7_days')
    price_15 = get_price('kos_virtual', '15_days')
    price_30 = get_price('kos_virtual', '30_days')

    virt_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"1 Day – ${price_1}", callback_data="buy_kosvirt_1"),
         InlineKeyboardButton(f"7 Days – ${price_7}", callback_data="buy_kosvirt_7")],
        [InlineKeyboardButton(f"15 Days – ${price_15}", callback_data="buy_kosvirt_15"),
         InlineKeyboardButton(f"30 Days – ${price_30}", callback_data="buy_kosvirt_30")],
        [InlineKeyboardButton("🔙 Back", callback_data="item_kos")]
    ])

    await query.edit_message_media(
        media=InputMediaPhoto(
            media="https://i.postimg.cc/ZnFwtGFT/IMG-20260301-214244.png",
            caption=virt_text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=virt_menu
    )

# new hack menus
async def wolf_hack(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)

    text = "<b>🐺 Wolf Hack– Premium Access</b>\n\n"
    text += "<b>Select your desired package below</b>\n\n"
    text += f"<b>💰 Your Balance:</b> {balance}$\n\n"

    price_1 = get_price('wolf_hack', '1_day')
    price_7 = get_price('wolf_hack', '7_days')
    price_30 = get_price('wolf_hack', '30_days')

    menu = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"1 day – ${price_1}", callback_data="buy_wolf_1"),
         InlineKeyboardButton(f"7 Days – ${price_7}", callback_data="buy_wolf_7")],
        [InlineKeyboardButton(f"30 Days – ${price_30}", callback_data="buy_wolf_30")],
        [InlineKeyboardButton("🔙 Back", callback_data="product_8ball")]
    ])

    await query.edit_message_media(
        media=InputMediaPhoto(
            media=HACK_INFO['wolf_hack']['image'],
            caption=text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=menu
    )

async def wizard_hack(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)

    text = "<b>👨‍🔧 Wizard Hack– Premium Access</b>\n\n"
    text += "<b>Note:</b> This only works on iPhone & iPad\n\n"
    text += "<b>Select your desired package below</b>\n\n"
    text += f"<b>💰 Your Balance:</b> {balance}$\n\n"

    price_1 = get_price('wizard_ios', '1_day')
    price_7 = get_price('wizard_ios', '7_days')
    price_30 = get_price('wizard_ios', '30_days')

    menu = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"1 day – ${price_1}", callback_data="buy_wizard_1"),
         InlineKeyboardButton(f"7 Days – ${price_7}", callback_data="buy_wizard_7")],
        [InlineKeyboardButton(f"30 Days – ${price_30}", callback_data="buy_wizard_30")],
        [InlineKeyboardButton("🔙 Back", callback_data="product_8ball")]
    ])

    await query.edit_message_media(
        media=InputMediaPhoto(
            media=HACK_INFO['wizard_ios']['image'],
            caption=text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=menu
    )

# --- database helpers ---

def _default_db_structure() -> dict:
    return {"users": {}, "keys": {}}


def _ensure_db_structure(db: dict) -> dict:
    if not isinstance(db, dict):
        db = _default_db_structure()
    if 'users' not in db or not isinstance(db['users'], dict):
        db['users'] = {}
    if 'keys' not in db or not isinstance(db['keys'], dict):
        db['keys'] = {}
    for user_data in db.get('users', {}).values():
        if isinstance(user_data, dict) and 'purchases' not in user_data:
            user_data['purchases'] = []
    return db


def _init_firestore_client():
    global _firestore_db
    if _firestore_db is not None:
        return _firestore_db
    if firebase_admin is None or firestore is None:
        raise RuntimeError("Firestore SDK is not available. Install firebase-admin.")
    try:
        if not firebase_admin._apps:
            cred_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
            cred_json_b64 = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON_B64')
            cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or os.getenv('FIREBASE_CREDENTIALS_PATH')

            if cred_json:
                firebase_admin.initialize_app(credentials.Certificate(json.loads(cred_json)))
            elif cred_json_b64:
                decoded = base64.b64decode(cred_json_b64).decode('utf-8')
                firebase_admin.initialize_app(credentials.Certificate(json.loads(decoded)))
            elif cred_path:
                # Railway users often paste raw JSON into GOOGLE_APPLICATION_CREDENTIALS.
                # Support both a file path and inline JSON for reliability.
                trimmed = cred_path.strip()
                if trimmed.startswith('{') and trimmed.endswith('}'):
                    firebase_admin.initialize_app(credentials.Certificate(json.loads(trimmed)))
                elif os.path.exists(cred_path):
                    firebase_admin.initialize_app(credentials.Certificate(cred_path))
                else:
                    raise RuntimeError(
                        "GOOGLE_APPLICATION_CREDENTIALS is set but not valid. "
                        "Provide a valid file path or use FIREBASE_SERVICE_ACCOUNT_JSON."
                    )
            else:
                firebase_admin.initialize_app()
        _firestore_db = firestore.client()
        return _firestore_db
    except Exception as exc:
        raise RuntimeError(f"Firestore initialization failed: {exc}") from exc


def _firestore_doc_ref():
    db_client = _init_firestore_client()
    return db_client.collection(FIRESTORE_COLLECTION).document(FIRESTORE_DOCUMENT)

def load_db():
    doc_ref = _firestore_doc_ref()
    snapshot = doc_ref.get()
    if snapshot.exists:
        db = snapshot.to_dict() or _default_db_structure()
    else:
        db = _default_db_structure()
        doc_ref.set(db)
    return _ensure_db_structure(db)

async def kos_hack(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)
    kos_text = "<b>💀 Kos Hack – Premium Access</b>\n\n"
    kos_text += "Choose your desired product below 👇\n\n"
    kos_text += f"<b>💰 Your Balance:</b> {balance}$"
    kos_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Kos Mode", callback_data="kos_mode")],
        [InlineKeyboardButton("⚡ Kos Virtual", callback_data="kos_virtual")],
        [InlineKeyboardButton("🔙 Back to 8 Ball Pool", callback_data="product_8ball")]
    ])
    await query.edit_message_media(
        media=InputMediaPhoto(
            media="https://i.postimg.cc/ZnFwtGFT/IMG-20260301-214244.png",
            caption=kos_text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=kos_menu
    )

# --- key and stock helpers ---

def get_stock(hack: str, duration: str) -> int:
    db = load_db()
    return len(db.get('keys', {}).get(hack, {}).get(duration, []))


def peek_first_key(hack: str, duration: str) -> str | None:
    db = load_db()
    keys = db.get('keys', {}).get(hack, {}).get(duration, [])
    if keys:
        return keys[0]
    return None


def consume_key(hack: str, duration: str) -> str | None:
    """Consume (remove) first key from stock. Thread-safe. Returns key or None."""
    with stock_lock:
        db = load_db()  # Fresh load inside lock
        keys = db.get('keys', {}).get(hack, {}).get(duration, [])
        if not keys:
            return None
        key = keys.pop(0)  # ✅ CRITICAL: Must use .pop(0), not indexing
        save_db(db)  # ✅ CRITICAL: Save immediately after removal
        return key


def add_key(hack: str, duration: str, value: str) -> None:
    """Add key to stock. Thread-safe. Ensures strict product + duration mapping."""
    clean_value = value.strip()
    if not clean_value:
        return
    with stock_lock:
        db = load_db()  # Fresh load inside lock
        # Strict structure validation: keys[product][duration]
        if 'keys' not in db:
            db['keys'] = {}
        if hack not in db['keys']:
            db['keys'][hack] = {}
        if duration not in db['keys'][hack]:
            db['keys'][hack][duration] = []
        db['keys'][hack][duration].append(clean_value)
        save_db(db)


def remove_key(hack: str, duration: str, value: str | None = None, clear_all: bool = False) -> bool:
    """Remove key from stock. Thread-safe. Strict product + duration."""
    with stock_lock:
        db = load_db()  # Fresh load inside lock
        keys = db.get('keys', {}).get(hack, {}).get(duration, [])
        if not keys:
            return False
        if clear_all:
            db['keys'][hack][duration] = []
            save_db(db)
            return True
        if value and value in keys:
            keys.remove(value)
            save_db(db)
            return True
        return False


def save_db(data):
    payload = _ensure_db_structure(copy.deepcopy(data))
    doc_ref = _firestore_doc_ref()
    doc_ref.set(payload)

# --- price management functions ---
def get_price(hack: str, duration: str) -> float:
    """Get price from Firestore, fallback to PRODUCTS if not found."""
    db = load_db()
    prices = db.get('prices', {})
    price_key = f"{hack}_{duration}"
    if price_key in prices:
        return float(prices[price_key])
    # Fallback to hardcoded PRODUCTS dictionary
    for product_id, product_info in PRODUCTS.items():
        if product_info.get('hack') == hack and product_info.get('duration') == duration:
            return product_info.get('price', 0.0)
    return 0.0

def set_price(hack: str, duration: str, price: float) -> None:
    """Set price in Firestore. Thread-safe."""
    with stock_lock:
        db = load_db()
        if 'prices' not in db:
            db['prices'] = {}
        price_key = f"{hack}_{duration}"
        db['prices'][price_key] = float(price)
        save_db(db)

# --- admin related functions ---

def is_admin(user_id: int) -> bool:
    """Check if a user is an admin."""
    db = load_db()
    admins_list = db.get('admins', [ADMIN_ID])
    return user_id in admins_list

def is_vip(user_id: int) -> bool:
    """Check if a user is VIP."""
    db = load_db()
    vip_users = db.get('vip_users', {})
    return str(user_id) in vip_users

def has_vip_access(user_id: int) -> bool:
    """VIP access includes VIP users and admins."""
    return is_admin(user_id) or is_vip(user_id)

def _vip_contact_url(user_id: int) -> str:
    prefill = f"🚨 VIP Activation Request\n\n👤 User ID: {user_id}\n\n❗ Admin, please activate VIP access for my account."
    return f"https://t.me/Hayazi_Saheb?text={quote_plus(prefill)}"

async def show_vip_required_screen(query, image_url: str, back_callback: str) -> None:
    """Show VIP required screen with Become VIP and Back buttons."""
    user_id = query.from_user.id
    text = (
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "          <b>🔐 VIP ACCESS ONLY</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ <b><i>ACCESS DENIED</i></b> ⚠️\n\n"
        "╔═══════════════════╗\n"
        "║  <b>💎 VIP EXCLUSIVE 💎</b>  ║\n"
        "╚═══════════════════╝\n\n"
        "🔒 <i>This content is available</i>\n"
        "   <i>only for VIP members</i>\n\n"
        "✨ <b>Unlock Premium Features:</b>\n"
        "   • View all prices\n"
        "   • Purchase any product\n"
        "   • Priority support\n"
        "   • Exclusive deals\n\n"
        "💫 <b><i>Ready to upgrade?</i></b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Become VIP Member ✨", url=_vip_contact_url(user_id))],
        [InlineKeyboardButton("🔙 Back", callback_data=back_callback)],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]
    ])

    try:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=image_url,
                caption=text,
                parse_mode=ParseMode.HTML
            ),
            reply_markup=buttons
        )
    except Exception:
        try:
            await query.edit_message_caption(
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=buttons
            )
        except Exception:
            await query.edit_message_text(
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=buttons
            )

async def vip_tool_gatekeeper(update: Update, context: CallbackContext) -> None:
    """Block non-VIP users from tool pages that show prices."""
    query = update.callback_query
    if not query:
        return

    data = query.data or ""
    tool_map = {
        'item_snake': ('snake_engine', 'product_8ball'),
        'item_aimx': ('aim_x', 'product_8ball'),
        'kos_mode': ('kos_mode', 'item_kos'),
        'kos_virtual': ('kos_virtual', 'item_kos'),
        'item_ninja': ('ninja_engine', 'product_8ball'),
        'item_wolf': ('wolf_hack', 'product_8ball'),
        'item_wizard': ('wizard_ios', 'product_8ball'),
        'aimking_nonroot': ('aim_king_nonroot', 'item_aimking'),
        'ak_loader_root': ('ak_loader_root', 'item_aimking'),
        'carrom_se': ('carrom_se', 'product_caroom'),
        'carrom_ak': ('carrom_ak', 'product_caroom'),
        'score_se': ('score_se', 'product_scorestar'),
        'score_ak': ('score_ak', 'product_scorestar'),
        'ff_android_drip_select': ('ff_android_drip', 'ff_android'),
        'ff_android_kos_select': ('ff_android_kos', 'ff_android'),
        'ff_ios': ('ff_ios', 'product_freefire'),
        'esign': ('esign', 'product_certificate_ios'),
        'gbox': ('gbox', 'product_certificate_ios'),
    }

    if data not in tool_map:
        return

    user_id = query.from_user.id
    if has_vip_access(user_id):
        return

    await query.answer("VIP only", show_alert=False)
    hack_key, back_callback = tool_map[data]
    image_url = HACK_INFO.get(hack_key, {}).get('image', 'https://i.postimg.cc/k4kRGdVK/file-00000000ca8c71faadd50d667e4a0509.png')
    await show_vip_required_screen(query, image_url, back_callback)
    raise ApplicationHandlerStop

async def admin_edit_or_reply(query, text: str, reply_markup=None, parse_mode=None) -> None:
    try:
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        try:
            await query.edit_message_caption(caption=text, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception:
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)

async def admin_manage_keys(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    # Check if user is admin
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Key", callback_data="admin_key_add"),
         InlineKeyboardButton("➖ Remove Key", callback_data="admin_key_remove")],
        [InlineKeyboardButton("💲 Edit Price", callback_data="admin_edit_price")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_key_back")]
    ])
    await admin_edit_or_reply(
        query,
        "🔐 Key Management Panel\n\nHere you can manage product keys & stock.\n\nSelect an option below 👇",
        reply_markup=buttons
    )

async def admin_key_action(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    action = 'add' if query.data == 'admin_key_add' else 'remove'
    context.user_data['key_flow'] = {'action': action}
    
    # Show product categories
    categories = [
        ("8_ball_pool", "🎱 8 Ball Pool"),
        ("carrom_pool", "🥏 Carrom Pool"),
        ("score_star", "⚽ Score Star"),
        ("special", "🔥 Special Tools"),
        ("free_fire", "🔥 Free Fire Tools"),
        ("certificate_ios", "📗 Certificate iOS")
    ]
    
    kb = []
    for i in range(0, len(categories), 2):
        row = []
        for cat_id, label in categories[i:i+2]:
            row.append(InlineKeyboardButton(label, callback_data=f"admin_category_{cat_id}"))
        kb.append(row)
    kb.append([InlineKeyboardButton("🔙 Back", callback_data="admin_key_back")])
    
    await admin_edit_or_reply(
        query,
        "📂 Select a category to {} keys:".format("add" if action=='add' else "remove"),
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def admin_select_category(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    category = query.data.replace("admin_category_", "")
    context.user_data['key_flow']['category'] = category
    
    # Map categories to hacks
    category_map = {
        '8_ball_pool': [
            ("snake_engine", "🐍 Snake Engine"),
            ("aim_x", "🎯 Aim X"),
            ("aim_king_nonroot", "🎯 Aim King"),
            ("ak_loader_root", "🔓 AK Loader"),
            ("ninja_engine", "🥷 Ninja Engine")
        ],
        'carrom_pool': [
            ("carrom_se", "🥏 Carrom SE"),
            ("carrom_ak", "👑 Carrom AK")
        ],
        'score_star': [
            ("score_se", "⚽ Score SE"),
            ("score_ak", "⚽ Score AK")
        ],
        'special': [
            ("kos_mode", "🔥 Kos Mode"),
            ("kos_virtual", "⚡ Kos Virtual"),
            ("wolf_hack", "🐺 Wolf Hack"),
            ("wizard_ios", "🧙 Wizard iOS")
        ],
        'free_fire': [
            ("ff_ios", "🍎 FF iOS - Killer AIM"),
            ("ff_android_drip", "💧 FF Android - Drip"),
            ("ff_android_kos", "🔥 FF Android - Kos")
        ],
        'certificate_ios': [
            ("esign", "📘 E-Sign Certificate"),
            ("gbox", "🗳️ GBOX Certificate")
        ]
    }
    
    hacks = category_map.get(category, [])
    kb = []
    for i in range(0, len(hacks), 2):
        row = []
        for hack_id, label in hacks[i:i+2]:
            row.append(InlineKeyboardButton(label, callback_data=f"admin_hack_{hack_id}"))
        kb.append(row)
    kb.append([InlineKeyboardButton("🔙 Back", callback_data=f"admin_key_add" if context.user_data['key_flow']['action']=='add' else "admin_key_remove")])
    
    await admin_edit_or_reply(
        query,
        "🛠️ Select a tool to {} keys:".format("add" if context.user_data['key_flow']['action']=='add' else "remove"),
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def admin_select_hack(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    hack = query.data.replace("admin_hack_", "")
    context.user_data['key_flow']['hack'] = hack
    # display durations according to hack
    durations_map = {
        'snake_engine': [('3_days', '3 Days'), ('10_days', '10 Days'), ('30_days', '30 Days')],
        'ninja_engine': [('3_days', '3 Days'), ('7_days', '7 Days'), ('30_days', '30 Days')],
        'aim_x': [('1_day','1 Day'),('2_days','2 Days'),('7_days','7 Days'),('15_days','15 Days'),('30_days','30 Days')],
        'aim_king_nonroot': [('7_days','7 Days'),('30_days','30 Days'),('90_days','90 Days')],
        'ak_loader_root': [('7_days','7 Days'),('30_days','30 Days'),('90_days','90 Days')],
        'carrom_se': [('3_days', '3 Days'), ('10_days', '10 Days'), ('30_days', '30 Days')],
        'carrom_ak': [
            ('auto_7_days', 'Auto 7 Days'),
            ('auto_30_days', 'Auto 30 Days'),
            ('normal_7_days', 'Normal 7 Days'),
            ('normal_30_days', 'Normal 30 Days')
        ],
        'score_se': [('3_days', '3 Days'), ('10_days', '10 Days'), ('30_days', '30 Days')],
        'score_ak': [('7_days', '7 Days'), ('30_days', '30 Days'), ('90_days', '90 Days')],
        'kos_mode': [('1_day', '1 Day'), ('7_days', '7 Days'), ('15_days', '15 Days'), ('30_days', '30 Days')],
        'kos_virtual': [('1_day', '1 Day'), ('7_days', '7 Days'), ('15_days', '15 Days'), ('30_days', '30 Days')],
        'wolf_hack': [('1_day','1 Day'),('7_days','7 Days'),('30_days','30 Days')],
        'wizard_ios': [('1_day','1 Day'),('7_days','7 Days'),('30_days','30 Days')],
        'esign': [('30_days_iphone', '30 Days iPhone'), ('90_days_iphone', '90 Days iPhone'), ('360_days_ipad', '360 Days iPad')],
        'gbox': [('1_year', '1 Year')]
    }
    options = durations_map.get(hack, [])
    kb = []
    for i in range(0, len(options), 2):
        row = []
        for dur, label in options[i:i+2]:
            row.append(InlineKeyboardButton(label, callback_data=f"admin_dur_{hack}_{dur}"))
        kb.append(row)
    kb.append([InlineKeyboardButton("🔙 Back", callback_data="admin_key_add" if context.user_data['key_flow']['action']=='add' else "admin_key_remove")])
    await admin_edit_or_reply(
        query,
        "Select duration to {} key:".format("add" if context.user_data['key_flow']['action']=='add' else "remove"),
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def admin_select_duration(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    # Get hack from stored context state (already set in admin_select_hack)
    hack = context.user_data.get('key_flow', {}).get('hack')
    # Extract duration from callback: admin_dur_{hack}_{duration}
    data = query.data  # e.g., admin_dur_snake_engine_3_days
    prefix = f"admin_dur_{hack}_"
    if data.startswith(prefix):
        duration = data[len(prefix):]
    else:
        await admin_edit_or_reply(query, "Error parsing duration. Please try again.")
        return
    context.user_data['key_flow']['duration'] = duration
    action = context.user_data['key_flow']['action']
    friendly = HACK_INFO.get(hack, {}).get('name', hack)
    dur_label = duration.replace('_', ' ')
    if action == 'add':
        init_msg = (
            f"<b>🔑 Add Key</b>\n\n"
            f"<b>Product:</b> {friendly}\n"
            f"<b>Duration:</b> {dur_label}\n\n"
            f"Send the key to add:"
        )
        await admin_edit_or_reply(query, init_msg, parse_mode=ParseMode.HTML)
    else:
        stock = get_stock(hack, duration)
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🧼 Clear All", callback_data="key_clear_all")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_key_back")]
        ])
        await admin_edit_or_reply(
            query,
            f"Current stock for {friendly} – {dur_label}: {stock}\n\nSend the key you want to remove (or type CLEAR to delete all)",
            reply_markup=buttons
        )

async def key_add_again(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    flow = context.user_data.get('key_flow', {})
    hack = flow.get('hack')
    duration = flow.get('duration')
    if not hack or not duration:
        await admin_edit_or_reply(query, "Error: Invalid state. Please restart.")
        context.user_data.pop('key_flow', None)
        return
    friendly = HACK_INFO.get(hack, {}).get('name', hack)
    dur_label = duration.replace('_', ' ')
    msg_text = (
        f"<b>📝 Add Another Key</b>\n\n"
        f"<b>Product:</b> {friendly}\n"
        f"<b>Duration:</b> {dur_label}\n\n"
        f"Send the key to add:"
    )
    await admin_edit_or_reply(query, msg_text, parse_mode=ParseMode.HTML)

async def key_clear_all(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    flow = context.user_data.get('key_flow', {})
    hack = flow.get('hack')
    duration = flow.get('duration')
    if not hack or not duration:
        await admin_edit_or_reply(query, "Error: Invalid state. Please restart.")
        context.user_data.pop('key_flow', None)
        return
    remove_key(hack, duration, clear_all=True)
    stock = get_stock(hack, duration)
    await admin_edit_or_reply(query, f"All keys cleared. New stock: {stock}")
    context.user_data.pop('key_flow', None)

async def cancel_admin_key(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    flow = context.user_data.get('key_flow', {})
    action = flow.get('action')
    
    # Clear only hack and duration, keep action
    if 'key_flow' in context.user_data:
        context.user_data['key_flow'].pop('hack', None)
        context.user_data['key_flow'].pop('duration', None)
        context.user_data['key_flow'].pop('category', None)
    
    # Show category selection again
    categories = [
        ("8_ball_pool", "🎱 8 Ball Pool"),
        ("carrom_pool", "🥏 Carrom Pool"),
        ("score_star", "⚽ Score Star"),
        ("special", "🔥 Special Tools"),
        ("free_fire", "🔥 Free Fire Tools"),
        ("certificate_ios", "📗 Certificate iOS")
    ]
    
    kb = []
    for i in range(0, len(categories), 2):
        row = []
        for cat_id, label in categories[i:i+2]:
            row.append(InlineKeyboardButton(label, callback_data=f"admin_category_{cat_id}"))
        kb.append(row)
    kb.append([InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_keys")])
    
    await admin_edit_or_reply(
        query,
        "📂 Select a category to {} keys:".format("add" if action=='add' else "remove"),
        reply_markup=InlineKeyboardMarkup(kb)
    )


# --- price editing functions ---
async def admin_edit_price(update: Update, context: CallbackContext) -> None:
    """Start price editing flow: show categories."""
    query = update.callback_query
    await query.answer()
    context.user_data['price_flow'] = {}
    
    categories = [
        ("8_ball_pool", "🎱 8 Ball Pool"),
        ("carrom_pool", "🥏 Carrom Pool"),
        ("score_star", "⚽ Score Star"),
        ("special", "🔥 Special Tools"),
        ("free_fire", "🔥 Free Fire Tools"),
        ("certificate_ios", "📗 Certificate iOS")
    ]
    
    kb = []
    for i in range(0, len(categories), 2):
        row = []
        for cat_id, label in categories[i:i+2]:
            row.append(InlineKeyboardButton(label, callback_data=f"price_category_{cat_id}"))
        kb.append(row)
    kb.append([InlineKeyboardButton("🔙 Back", callback_data="admin_keys")])
    
    await admin_edit_or_reply(
        query,
        "📂 Select category to edit prices:\n\n",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def admin_price_select_category(update: Update, context: CallbackContext) -> None:
    """Show tools for selected category."""
    query = update.callback_query
    await query.answer()
    category = query.data.replace("price_category_", "")
    context.user_data['price_flow']['category'] = category
    
    category_map = {
        '8_ball_pool': [
            ("snake_engine", "🐍 Snake Engine"),
            ("aim_x", "🎯 Aim X"),
            ("aim_king_nonroot", "🎯 Aim King"),
            ("ak_loader_root", "🔓 AK Loader"),
            ("ninja_engine", "🥷 Ninja Engine")
        ],
        'carrom_pool': [
            ("carrom_se", "🥏 Carrom SE"),
            ("carrom_ak", "👑 Carrom AK")
        ],
        'score_star': [
            ("score_se", "⚽ Score SE"),
            ("score_ak", "⚽ Score AK")
        ],
        'special': [
            ("kos_mode", "🔥 Kos Mode"),
            ("kos_virtual", "⚡ Kos Virtual"),
            ("wolf_hack", "🐺 Wolf Hack"),
            ("wizard_ios", "🧙 Wizard iOS")
        ],
        'free_fire': [
            ("ff_ios", "🍎 FF iOS - Killer AIM"),
            ("ff_android_drip", "💧 FF Android - Drip"),
            ("ff_android_kos", "🔥 FF Android - Kos")
        ],
        'certificate_ios': [
            ("esign", "📘 E-Sign Certificate"),
            ("gbox", "🗳️ GBOX Certificate")
        ]
    }
    
    hacks = category_map.get(category, [])
    kb = []
    for i in range(0, len(hacks), 2):
        row = []
        for hack_id, label in hacks[i:i+2]:
            row.append(InlineKeyboardButton(label, callback_data=f"price_hack_{hack_id}"))
        kb.append(row)
    kb.append([InlineKeyboardButton("🔙 Back", callback_data="admin_edit_price")])
    
    await admin_edit_or_reply(
        query,
        "🛠️ Select a tool to edit prices:",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def admin_price_select_hack(update: Update, context: CallbackContext) -> None:
    """Show durations for selected hack with current prices."""
    query = update.callback_query
    await query.answer()
    hack = query.data.replace("price_hack_", "")
    context.user_data['price_flow']['hack'] = hack
    
    durations_map = {
        'snake_engine': [('3_days', '3 Days'), ('10_days', '10 Days'), ('30_days', '30 Days')],
        'ninja_engine': [('3_days', '3 Days'), ('7_days', '7 Days'), ('30_days', '30 Days')],
        'aim_x': [('1_day','1 Day'),('2_days','2 Days'),('7_days','7 Days'),('15_days','15 Days'),('30_days','30 Days')],
        'aim_king_nonroot': [('7_days','7 Days'),('30_days','30 Days'),('90_days','90 Days')],
        'ak_loader_root': [('7_days','7 Days'),('30_days','30 Days'),('90_days','90 Days')],
        'carrom_se': [('3_days', '3 Days'), ('10_days', '10 Days'), ('30_days', '30 Days')],
        'carrom_ak': [
            ('auto_7_days', 'Auto 7 Days'),
            ('auto_30_days', 'Auto 30 Days'),
            ('normal_7_days', 'Normal 7 Days'),
            ('normal_30_days', 'Normal 30 Days')
        ],
        'score_se': [('3_days', '3 Days'), ('10_days', '10 Days'), ('30_days', '30 Days')],
        'score_ak': [('7_days', '7 Days'), ('30_days', '30 Days'), ('90_days', '90 Days')],
        'kos_mode': [('1_day', '1 Day'), ('7_days', '7 Days'), ('15_days', '15 Days'), ('30_days', '30 Days')],
        'kos_virtual': [('1_day', '1 Day'), ('7_days', '7 Days'), ('15_days', '15 Days'), ('30_days', '30 Days')],
        'wolf_hack': [('1_day','1 Day'),('7_days','7 Days'),('30_days','30 Days')],
        'wizard_ios': [('1_day','1 Day'),('7_days','7 Days'),('30_days','30 Days')],
        'ff_ios': [('1_day', '1 Day'), ('3_days', '3 Days'), ('7_days', '7 Days'), ('30_days', '30 Days')],
        'ff_android_drip': [('1_day', '1 Day'), ('7_days', '7 Days'), ('30_days', '30 Days')],
        'ff_android_kos': [('1_day', '1 Day'), ('3_days', '3 Days'), ('7_days', '7 Days'), ('30_days', '30 Days')],
        'esign': [('30_days_iphone', '30 Days iPhone'), ('90_days_iphone', '90 Days iPhone'), ('360_days_ipad', '360 Days iPad')],
        'gbox': [('1_year', '1 Year')]
    }
    
    options = durations_map.get(hack, [])
    kb = []
    for dur, label in options:
        price = get_price(hack, dur)
        kb.append([InlineKeyboardButton(f"{label} - ${price}", callback_data=f"price_dur_{hack}_{dur}")])
    kb.append([InlineKeyboardButton("🔙 Back", callback_data=f"price_category_{context.user_data['price_flow'].get('category', 'special')}")])
    
    friendly = HACK_INFO.get(hack, {}).get('name', hack)
    await admin_edit_or_reply(
        query,
        f"📊 Edit prices for <b>{friendly}</b>\n\nSelect duration to edit:",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode=ParseMode.HTML
    )

async def admin_price_select_duration(update: Update, context: CallbackContext) -> None:
    """Prompt for new price input."""
    query = update.callback_query
    await query.answer()
    
    hack = context.user_data.get('price_flow', {}).get('hack')
    data = query.data
    prefix = f"price_dur_{hack}_"
    if data.startswith(prefix):
        duration = data[len(prefix):]
    else:
        await admin_edit_or_reply(query, "Error parsing duration. Please try again.")
        return
    
    context.user_data['price_flow']['duration'] = duration
    
    friendly = HACK_INFO.get(hack, {}).get('name', hack)
    dur_label = duration.replace('_', ' ')
    current_price = get_price(hack, duration)
    
    init_msg = (
        f"<b>💰 Edit Price</b>\n\n"
        f"<b>Tool:</b> {friendly}\n"
        f"<b>Duration:</b> {dur_label}\n"
        f"<b>Current Price:</b> ${current_price}\n\n"
        f"Send the new price (e.g., 4.99):"
    )
    await admin_edit_or_reply(query, init_msg, parse_mode=ParseMode.HTML)

async def aimking_nonroot(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)

    text = "<b>🎯 Aim King Non-Root</b>\n\n"
    text += "Choose your duration ⏳\n\n"
    text += f"<b>💰 Your Balance:</b> {balance}$\n\n"

    # Fetch dynamic prices from Firestore
    price_7 = get_price('aim_king_nonroot', '7_days')
    price_30 = get_price('aim_king_nonroot', '30_days')
    price_90 = get_price('aim_king_nonroot', '90_days')

    menu = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⏳ 7 Days – ${price_7}", callback_data="buy_aimking_nonroot_7"),
         InlineKeyboardButton(f"⏳ 30 Days – ${price_30}", callback_data="buy_aimking_nonroot_30")],
        [InlineKeyboardButton(f"⏳ 90 Days – ${price_90}", callback_data="buy_aimking_nonroot_90")],
        [InlineKeyboardButton("🔙 Back", callback_data="item_aimking")]
    ])

    await query.message.reply_photo(
        photo="https://i.postimg.cc/W1twXFK4/IMG-20260301-213329.png",
        caption=text,
        reply_markup=menu,
        parse_mode=ParseMode.HTML
    )

async def aim_king(update: Update, context: CallbackContext) -> None:
    """Show Aim King subcategories."""
    query = update.callback_query
    await query.answer()
    
    text = "<b>🎯 Aim King Category</b>\n\n"
    text += "Choose your preferred version 👇\n\n"
    
    menu = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Aim King Non-Root", callback_data="aimking_nonroot"),
         InlineKeyboardButton("🔓 AK Loader Root", callback_data="ak_loader_root")],
        [InlineKeyboardButton("🔙 Back", callback_data="product_8ball")]
    ])
    
    await query.edit_message_media(
        media=InputMediaPhoto(
            media="https://i.postimg.cc/W1twXFK4/IMG-20260301-213329.png",
            caption=text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=menu
    )

async def ak_loader_root(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)

    text = "<b>🔓 AK Loader Root</b>\n\n"
    text += "Choose your duration ⏳\n\n"
    text += f"<b>💰 Your Balance:</b> {balance}$\n\n"

    price_7 = get_price('ak_loader_root', '7_days')
    price_30 = get_price('ak_loader_root', '30_days')
    price_90 = get_price('ak_loader_root', '90_days')

    menu = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⏳ 7 Days – ${price_7}", callback_data="buy_akloader_7"),
         InlineKeyboardButton(f"⏳ 30 Days – ${price_30}", callback_data="buy_akloader_30")],
        [InlineKeyboardButton(f"⏳ 90 Days – ${price_90}", callback_data="buy_akloader_90")],
        [InlineKeyboardButton("🔙 Back", callback_data="item_aimking")]
    ])

    await query.message.reply_photo(
        photo="https://i.postimg.cc/W1twXFK4/IMG-20260301-213329.png",
        caption=text,
        reply_markup=menu,
        parse_mode=ParseMode.HTML
    )

async def carrom_se(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)

    text = "<b>🥏 Carrom SE – Premium Access</b>\n\n"
    text += "Select your desired package below\n"
    text += f"<b>💰 Your Balance:</b> {balance}$\n\n"

    price_3 = get_price('carrom_se', '3_days')
    price_10 = get_price('carrom_se', '10_days')
    price_30 = get_price('carrom_se', '30_days')

    menu = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⏳ 3 Days – ${price_3}", callback_data="buy_carromse_3"),
         InlineKeyboardButton(f"⏳ 10 Days – ${price_10}", callback_data="buy_carromse_10")],
        [InlineKeyboardButton(f"⏳ 30 Days – ${price_30}", callback_data="buy_carromse_30")],
        [InlineKeyboardButton("🔙 Back", callback_data="product_caroom")]
    ])

    await query.edit_message_media(
        media=InputMediaPhoto(
            media="https://i.postimg.cc/fytM8vxD/IMG-20260301-213641.png",
            caption=text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=menu
    )

async def carrom_ak(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)

    text = "👑Carrom AK– Premium Access\n\n"
    text += "Select your desired package below\n"
    text += f"💰 Your Balance: {balance}$\n\n"

    price_auto_7 = get_price('carrom_ak', 'auto_7_days')
    price_auto_30 = get_price('carrom_ak', 'auto_30_days')
    price_normal_7 = get_price('carrom_ak', 'normal_7_days')
    price_normal_30 = get_price('carrom_ak', 'normal_30_days')

    menu = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Auto 7 days {price_auto_7}$", callback_data="buy_carromak_auto_7"),
         InlineKeyboardButton(f"Auto 30 days {price_auto_30}$", callback_data="buy_carromak_auto_30")],
        [InlineKeyboardButton(f"Normal 7 days {price_normal_7}$", callback_data="buy_carromak_normal_7"),
         InlineKeyboardButton(f"Normal 30 days {price_normal_30}$", callback_data="buy_carromak_normal_30")],
        [InlineKeyboardButton("🔙 Back", callback_data="product_caroom")]
    ])

    await query.edit_message_media(
        media=InputMediaPhoto(
            media="https://i.postimg.cc/5y0Rg3Q2/IMG-20260302-203112.png",
            caption=text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=menu
    )

async def score_star(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    score_text = "<b>⚽ Score Star Category</b>\n\n"
    score_text += "<b>Select your product below 👇</b>\n"
    score_text += "Choose Score SE or Score AK."

    score_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚽ Score SE", callback_data="score_se"),
         InlineKeyboardButton("⚽ Score AK", callback_data="score_ak")],
        [InlineKeyboardButton("🔙 Back", callback_data="product_hackes")]
    ])

    await query.edit_message_media(
        media=InputMediaPhoto(
            media="https://i.postimg.cc/63SX4GDG/IMG-20260301-213107.png",
            caption=score_text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=score_menu
    )

async def score_se(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)

    text = "<b>⚽ Score Star SE– Premium Access</b>\n\n"
    text += "Select your desired package below\n"
    text += f"<b>💰 Your Balance:</b> {balance}$\n\n"

    price_3 = get_price('score_se', '3_days')
    price_10 = get_price('score_se', '10_days')
    price_30 = get_price('score_se', '30_days')

    menu = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⏳ 3 Days – ${price_3}", callback_data="buy_scorese_3"),
         InlineKeyboardButton(f"⏳ 10 Days – ${price_10}", callback_data="buy_scorese_10")],
        [InlineKeyboardButton(f"⏳ 30 Days – ${price_30}", callback_data="buy_scorese_30")],
        [InlineKeyboardButton("🔙 Back", callback_data="product_scorestar")]
    ])

    await query.edit_message_media(
        media=InputMediaPhoto(
            media="https://i.postimg.cc/qMWNHNqB/IMG-20260301-211110.png",
            caption=text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=menu
    )

async def score_ak(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)

    text = "<b>⚽ Score Star AK– Premium Access</b>\n\n"
    text += "Select your desired package below\n"
    text += f"<b>💰 Your Balance:</b> {balance}$\n\n"

    price_7 = get_price('score_ak', '7_days')
    price_30 = get_price('score_ak', '30_days')
    price_90 = get_price('score_ak', '90_days')

    menu = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⏳ 7 Days – ${price_7}", callback_data="buy_scoreak_7")],
        [InlineKeyboardButton(f"⏳ 30 Days – ${price_30}", callback_data="buy_scoreak_30")],
        [InlineKeyboardButton(f"⏳ 90 Days – ${price_90}", callback_data="buy_scoreak_90")],
        [InlineKeyboardButton("🔙 Back", callback_data="product_scorestar")]
    ])

    await query.edit_message_media(
        media=InputMediaPhoto(
            media="https://i.postimg.cc/hPBTRjPC/IMG-20260303-161958.png",
            caption=text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=menu
    )

async def free_fire(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    ff_text = "<b>🔥 Free Fire Category</b>\n\n"
    ff_text += "<b>Select your product below 👇</b>\n"
    ff_text += "Choose Free Fire Android or iOS."

    ff_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 FF Android", callback_data="ff_android"),
         InlineKeyboardButton("🍎 FF iOS", callback_data="ff_ios")],
        [InlineKeyboardButton("🔙 Back", callback_data="product_hackes")]
    ])

    try:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media="https://i.postimg.cc/63SX4GDG/IMG-20260301-213107.png",
                caption=ff_text,
                parse_mode=ParseMode.HTML
            ),
            reply_markup=ff_menu
        )
    except Exception:
        try:
            await query.edit_message_caption(
                caption=ff_text,
                parse_mode=ParseMode.HTML,
                reply_markup=ff_menu
            )
        except Exception:
            try:
                await query.edit_message_text(
                    text=ff_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=ff_menu
                )
            except Exception:
                await query.message.reply_text(ff_text, parse_mode=ParseMode.HTML, reply_markup=ff_menu)

async def ff_android(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    text = "<b>🔥 Free Fire – Android Variants</b>\n\n"
    text += "Select your preferred client:\n"

    menu = InlineKeyboardMarkup([
        [InlineKeyboardButton("💧 Drip Client", callback_data="ff_android_drip_select"),
         InlineKeyboardButton("🔥 Kos Ffire", callback_data="ff_android_kos_select")],
        [InlineKeyboardButton("🔙 Back", callback_data="product_freefire")]
    ])

    try:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media="https://i.postimg.cc/3xJZnVh1/free-fire-banner.png",
                caption=text,
                parse_mode=ParseMode.HTML
            ),
            reply_markup=menu
        )
    except Exception:
        try:
            await query.edit_message_caption(
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=menu
            )
        except Exception:
            try:
                await query.edit_message_text(
                    text=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=menu
                )
            except Exception:
                await query.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=menu)

async def ff_android_drip(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)

    text = "<b>� Drip client– Premium Access</b>\n"
    text += "<b>free fire</b>\n\n"
    text += "Select your desired package below\n\n"
    text += f"<b>💰 Your Balance:</b> {balance}$\n\n"

    price_1 = get_price('ff_android_drip', '1_day')
    price_7 = get_price('ff_android_drip', '7_days')
    price_30 = get_price('ff_android_drip', '30_days')

    menu = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⏳ 1 Day – ${price_1}", callback_data="buy_ffandroid_drip_1"),
         InlineKeyboardButton(f"⏳ 7 Days – ${price_7}", callback_data="buy_ffandroid_drip_7")],
        [InlineKeyboardButton(f"⏳ 30 Days – ${price_30}", callback_data="buy_ffandroid_drip_30")],
        [InlineKeyboardButton("🔙 Back", callback_data="ff_android")]
    ])

    try:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media="https://i.postimg.cc/W3F6sxVc/IMG-20260302-164657.png",
                caption=text,
                parse_mode=ParseMode.HTML
            ),
            reply_markup=menu
        )
    except Exception:
        try:
            await query.edit_message_caption(
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=menu
            )
        except Exception:
            try:
                await query.edit_message_text(
                    text=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=menu
                )
            except Exception:
                await query.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=menu)

async def ff_android_kos(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)

    text = "<b>💧 Kos Free Fire– Premium Access</b>\n"
    text += "<b>✅ONLY WORK ROOT DEVICE</b>\n\n"
    text += "Select your desired package below\n\n"
    text += f"<b>💰 Your Balance:</b> {balance}$\n\n"

    price_1 = get_price('ff_android_kos', '1_day')
    price_7 = get_price('ff_android_kos', '7_days')
    price_15 = get_price('ff_android_kos', '15_days')
    price_30 = get_price('ff_android_kos', '30_days')

    menu = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"👍 1 DAY {price_1}$", callback_data="buy_ffandroid_kos_1"),
         InlineKeyboardButton(f"👍 7 DAY {price_7}$", callback_data="buy_ffandroid_kos_7")],
        [InlineKeyboardButton(f"👍 15 DAY {price_15}$", callback_data="buy_ffandroid_kos_15"),
         InlineKeyboardButton(f"👍 30 DAY {price_30}$", callback_data="buy_ffandroid_kos_30")],
        [InlineKeyboardButton("🔙 Back", callback_data="ff_android")]
    ])

    try:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media="https://i.postimg.cc/RhW1VyzB/IMG-20260302-204116.png",
                caption=text,
                parse_mode=ParseMode.HTML
            ),
            reply_markup=menu
        )
    except Exception:
        try:
            await query.edit_message_caption(
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=menu
            )
        except Exception:
            try:
                await query.edit_message_text(
                    text=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=menu
                )
            except Exception:
                await query.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=menu)

async def ff_ios(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)

    text = "<b>� Killer AIM iOS– Premium Access</b>\n\n"
    text += "<b>Select your desired package below</b>\n\n"
    text += f"<b>💰 Your Balance:</b> {balance}$\n\n"

    price_1 = get_price('ff_ios', '1_day')
    price_7 = get_price('ff_ios', '7_days')
    price_30 = get_price('ff_ios', '30_days')

    menu = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⏳ 1 Day – ${price_1}", callback_data="buy_ffios_1"),
         InlineKeyboardButton(f"⏳ 7 Days – ${price_7}", callback_data="buy_ffios_7")],
        [InlineKeyboardButton(f"⏳ 30 Days – ${price_30}", callback_data="buy_ffios_30")],
        [InlineKeyboardButton("🔙 Back", callback_data="product_freefire")]
    ])

    try:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media="https://i.postimg.cc/QC7bJwY1/IMG-20260302-165241.png",
                caption=text,
                parse_mode=ParseMode.HTML
            ),
            reply_markup=menu
        )
    except Exception:
        try:
            await query.edit_message_caption(
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=menu
            )
        except Exception:
            try:
                await query.edit_message_text(
                    text=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=menu
                )
            except Exception:
                await query.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=menu)

async def certificate_ios(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    cert_text = "<b>📗 Certificate iOS Category</b>\n\n"
    cert_text += "<b>Select your certificate service below 👇</b>\n"
    cert_text += "Choose E-Sign or GBOX for iOS certificate management."

    cert_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton("📘 E-Sign", callback_data="esign"),
         InlineKeyboardButton("🗳️ GBOX", callback_data="gbox")],
        [InlineKeyboardButton("🔙 Back", callback_data="product_hackes")]
    ])

    try:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media="https://i.postimg.cc/63SX4GDG/IMG-20260301-213107.png",
                caption=cert_text,
                parse_mode=ParseMode.HTML
            ),
            reply_markup=cert_menu
        )
    except Exception:
        try:
            await query.edit_message_caption(
                caption=cert_text,
                parse_mode=ParseMode.HTML,
                reply_markup=cert_menu
            )
        except Exception:
            try:
                await query.edit_message_text(
                    text=cert_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=cert_menu
                )
            except Exception:
                await query.message.reply_text(cert_text, parse_mode=ParseMode.HTML, reply_markup=cert_menu)

async def esign(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)

    esign_text = "<b>📘 E-Sign– Premium Access</b>\n\n"
    esign_text += "<b>Select your desired package below</b>\n\n"
    esign_text += f"<b>💰 Your Balance:</b> {balance}$\n\n"

    price_30_iphone = get_price('esign', '30_days_iphone')
    price_90_iphone = get_price('esign', '90_days_iphone')
    price_360_ipad = get_price('esign', '360_days_ipad')

    esign_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📱 30 Days – ${price_30_iphone} iPhone", callback_data="buy_esign_30_iphone"),
         InlineKeyboardButton(f"📱 90 Days – ${price_90_iphone} iPhone", callback_data="buy_esign_90_iphone")],
        [InlineKeyboardButton(f"📱 360 Days – ${price_360_ipad} iPad", callback_data="buy_esign_360_ipad")],
        [InlineKeyboardButton("🔙 Back", callback_data="product_certificate_ios")]
    ])

    try:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media="https://i.postimg.cc/qq6ndK84/IMG-20260302-203514.png",
                caption=esign_text,
                parse_mode=ParseMode.HTML
            ),
            reply_markup=esign_menu
        )
    except Exception:
        try:
            await query.edit_message_caption(
                caption=esign_text,
                parse_mode=ParseMode.HTML,
                reply_markup=esign_menu
            )
        except Exception:
            try:
                await query.edit_message_text(
                    text=esign_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=esign_menu
                )
            except Exception:
                await query.message.reply_text(esign_text, parse_mode=ParseMode.HTML, reply_markup=esign_menu)

async def gbox(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)

    gbox_text = "<b>🗳️ GBOX– Premium Access</b>\n\n"
    gbox_text += "<b>Select your desired package below</b>\n\n"
    gbox_text += f"<b>💰 Your Balance:</b> {balance}$\n\n"

    price_1year = get_price('gbox', '1_year')

    gbox_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📅 1 Year – ${price_1year}", callback_data="buy_gbox_1year")],
        [InlineKeyboardButton("🔙 Back", callback_data="product_certificate_ios")]
    ])

    try:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media="https://i.postimg.cc/cLSDX1Sd/IMG-20260302-170714.png",
                caption=gbox_text,
                parse_mode=ParseMode.HTML
            ),
            reply_markup=gbox_menu
        )
    except Exception:
        try:
            await query.edit_message_caption(
                caption=gbox_text,
                parse_mode=ParseMode.HTML,
                reply_markup=gbox_menu
            )
        except Exception:
            try:
                await query.edit_message_text(
                    text=gbox_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=gbox_menu
                )
            except Exception:
                await query.message.reply_text(gbox_text, parse_mode=ParseMode.HTML, reply_markup=gbox_menu)

async def buy_item(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if not has_vip_access(user_id):
        await query.message.reply_text(t(user_id, 'not_vip_msg'))
        return
    data = query.data  # like buy_snake_3
    product = PRODUCTS.get(data)
    if not product:
        await query.message.reply_text(t(user_id, 'unknown_product'))
        return

    hack = product['hack']
    duration = product['duration']
    price = get_price(hack, duration)  # 💰 Fetch price from Firestore (with fallback)
    db = load_db()
    balance = db.get('users', {}).get(str(user_id), {}).get('balance', 0.0)
    stock = get_stock(hack, duration)

    if stock <= 0:
        # out of stock message
        text = f"{t(user_id, 'out_of_stock_title')}\n\n"
        text += f"{t(user_id, 'out_of_stock_product', product=HACK_INFO.get(hack, {}).get('name', hack))}\n"
        text += f"{t(user_id, 'out_of_stock_duration', duration=product['label'])}\n"
        text += t(user_id, 'out_of_stock_footer')
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton(t(user_id, 'btn_back'), callback_data=f"cancel_{data}")]])
        await query.message.reply_text(text, reply_markup=buttons)
        return

    # show confirmation (without key - will show after confirm)
    product_name = HACK_INFO.get(hack, {}).get('name', hack)
    duration_label = product['label']
    
    text = f"<b>🏷 {duration_label}  →  ${price}</b>\n\n"
    text += f"{t(user_id, 'confirm_sure')}\n"
    text += f"{t(user_id, 'confirm_separator')}\n\n"
    text += f"{t(user_id, 'confirm_note')}\n"
    text += f"{t(user_id, 'confirm_no_return')}\n"
    text += f"{t(user_id, 'confirm_your_balance', balance=balance)}\n"
    text += f"{t(user_id, 'confirm_price', price=price)}\n"
    text += t(user_id, 'confirm_stock', stock=stock)

    buttons = InlineKeyboardMarkup([
           [InlineKeyboardButton(t(user_id, 'btn_confirm'), callback_data=f"confirm_{data}"),
            InlineKeyboardButton(t(user_id, 'btn_cancel'), callback_data=f"cancel_{data}")]
    ])

    await query.message.reply_photo(
        photo=HACK_INFO.get(hack, {}).get('image'),
        caption=text,
        reply_markup=buttons,
        parse_mode=ParseMode.HTML
    )

def save_purchase_history(user_id, product, key_value, duration, expire_date=None):
    """
    Save purchase to user's purchases array following the specification.
    Each purchase includes: product, duration, key, buy_date, expire_date, status
    """
    db = load_db()
    users = db.setdefault('users', {})
    uid = str(user_id)
    
    # Ensure user exists and has purchases array
    if uid not in users:
        users[uid] = {"balance": 0.0, "purchases": [], "member_since": datetime.now().strftime('%Y-%m-%d')}
    if 'purchases' not in users[uid]:
        users[uid]['purchases'] = []
    if 'member_since' not in users[uid]:
        users[uid]['member_since'] = datetime.now().strftime('%Y-%m-%d')
    
    # Create purchase entry
    entry = {
        'product': product['hack'],
        'duration': product['duration'],
        'key': key_value or '',
        'buy_date': datetime.now().strftime('%Y-%m-%d'),
        'expire_date': expire_date or '',
        'status': 'active'  # Default status is active
    }
    
    users[uid]['purchases'].append(entry)
    save_db(db)

async def history_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    if query:
        await query.answer()

    user_id = update.effective_user.id if update.effective_user else update.from_user.id
    db = load_db()
    
    # Get user purchases from the new structure
    purchases = db.get('users', {}).get(str(user_id), {}).get('purchases', [])
    
    if not purchases:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(t(user_id, 'btn_back_to_main_menu'), callback_data="back_to_menu")]])
        if hasattr(update, 'callback_query') and update.callback_query:
            try:
                await update.callback_query.edit_message_text(t(user_id, 'history_empty'), reply_markup=keyboard)
            except Exception:
                try:
                    await update.callback_query.edit_message_caption(caption=t(user_id, 'history_empty'), reply_markup=keyboard)
                except Exception:
                    await update.callback_query.message.reply_text(t(user_id, 'history_empty'), reply_markup=keyboard)
        else:
            await update.message.reply_text(t(user_id, 'history_empty'), reply_markup=keyboard)
        return
    
    # Reset to page 0 when viewing history
    context.user_data['history_page'] = 0
    await display_history_page(update, context, db, purchases)

async def display_history_page(update: Update, context: CallbackContext, db, purchases) -> None:
    """Display a page of purchase history with pagination."""
    items_per_page = 5
    current_page = context.user_data.get('history_page', 0)
    
    # Reverse purchases (newest first)
    reversed_purchases = list(reversed(purchases))
    
    # Calculate pagination
    total_items = len(reversed_purchases)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    
    # Ensure page is within bounds
    if current_page >= total_pages:
        current_page = total_pages - 1
    if current_page < 0:
        current_page = 0
    
    context.user_data['history_page'] = current_page
    
    # Get items for current page
    start_idx = current_page * items_per_page
    end_idx = start_idx + items_per_page
    page_items = reversed_purchases[start_idx:end_idx]
    
    user_id = update.effective_user.id
    msg = f"{t(user_id, 'history_title')}\n"
    msg += f"{t(user_id, 'history_page', page=current_page + 1, total=total_pages)}\n\n"
    
    now = datetime.now()
    
    # Process each purchase on this page
    for item in page_items:
        product_key = item.get("product", "unknown")
        product_name = html.escape(str(HACK_INFO.get(product_key, {}).get('name', product_key)))
        key = html.escape(str(item.get("key", "N/A")))
        duration_key = item.get("duration", "N/A")
        
        # Extract duration display label
        duration_label = html.escape(str(duration_key).replace('_', ' ').title())
        
        expire_date = str(item.get("expire_date", ""))
        status = item.get("status", "active")
        
        # Check if purchase is expired
        if expire_date and status != "expired":
            try:
                expire_dt = datetime.strptime(expire_date, "%Y-%m-%d")
                if now > expire_dt:
                    status = "expired"
                    item['status'] = "expired"  # Update status in db
            except Exception:
                pass
        
        # Format the history message
        msg += f"{t(user_id, 'history_product', product=product_name)}\n"
        msg += f"{t(user_id, 'history_duration', duration=duration_label)}\n"
        msg += f"{t(user_id, 'history_key', key=key)}\n"
        
        if status == "expired":
            msg += f"{t(user_id, 'history_status_expired')}\n"
            if expire_date:
                msg += f"{t(user_id, 'history_expired_on', date=expire_date)}\n"
        else:
            msg += f"{t(user_id, 'history_status_active')}\n"
            if expire_date:
                msg += f"{t(user_id, 'history_expires_on', date=expire_date)}\n"
        
        msg += "\n"
    
    # Save updated statuses
    save_db(db)
    
    # Create pagination buttons
    buttons = []
    nav_buttons = []
    
    # Add Previous button if not on first page
    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton(t(user_id, 'btn_previous'), callback_data="prev_history"))
    
    # Add Next button if not on last page
    if current_page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(t(user_id, 'btn_next'), callback_data="next_history"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    # Add Back to Main Menu button
    buttons.append([InlineKeyboardButton(t(user_id, 'btn_back_to_main_menu'), callback_data="back_to_menu")])
    
    keyboard = InlineKeyboardMarkup(buttons)
    
    if hasattr(update, 'callback_query') and update.callback_query:
        try:
            await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        except Exception:
            try:
                await update.callback_query.edit_message_caption(caption=msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            except Exception:
                await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    else:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def next_history(update: Update, context: CallbackContext) -> None:
    """Show next page of history."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    db = load_db()
    purchases = db.get('users', {}).get(str(user_id), {}).get('purchases', [])
    
    if not purchases:
        return
    
    # Increment page
    current_page = context.user_data.get('history_page', 0)
    context.user_data['history_page'] = current_page + 1
    
    await display_history_page(update, context, db, purchases)

async def prev_history(update: Update, context: CallbackContext) -> None:
    """Show previous page of history."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    db = load_db()
    purchases = db.get('users', {}).get(str(user_id), {}).get('purchases', [])
    
    if not purchases:
        return
    
    # Decrement page
    current_page = context.user_data.get('history_page', 0)
    context.user_data['history_page'] = max(0, current_page - 1)
    
    await display_history_page(update, context, db, purchases)

async def manage_reseller(update: Update, context: CallbackContext) -> None:
    """Seller management menu for admin."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    db = load_db()
    admins_list = db.get('admins', [ADMIN_ID])
    if user_id not in admins_list:
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Sellers", callback_data="seller_add"),
         InlineKeyboardButton("❌ Remove Sellers", callback_data="seller_remove")],
        [InlineKeyboardButton("📋 View List", callback_data="seller_view")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
    ])
    
    text = (
        "<b>🌟 SELLER MANAGEMENT</b>\n\n"
        "Manage the trusted seller/reseller list here:\n\n"
        "➕ <b>Add Sellers:</b> Add new seller(s) to the list\n"
        "❌ <b>Remove Sellers:</b> Remove seller(s) from the list\n"
        "📋 <b>View List:</b> View current seller list"
    )
    
    await admin_edit_or_reply(query, text, reply_markup=buttons, parse_mode=ParseMode.HTML)

async def seller_add_flow(update: Update, context: CallbackContext) -> None:
    """Prompt admin to add multiple sellers at once."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    context.user_data['admin_flow'] = 'add_sellers_bulk'
    text = (
        "📝 <b>Add Multiple Sellers</b>\n\n"
        "Send all seller entries at once, one per line:\n\n"
        "Format:\n"
        "Name: @username or link\n\n"
        "Example:\n"
        "Ali Khan: https://t.me/seller1\n"
        "Ahmed: https://t.me/seller2\n"
        "Sara: @seller3\n\n"
        "<i>All entries will be added to the list once.</i>"
    )
    await admin_edit_or_reply(query, text, parse_mode=ParseMode.HTML)

async def seller_list_view(update: Update, context: CallbackContext) -> None:
    """Show current seller list."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    db = load_db()
    reseller_list = db.get('reseller_list', '')
    
    if not reseller_list:
        text = "📋 <b>Seller List</b>\n\n❌ No sellers added yet."
    else:
        text = "📋 <b>Current Seller List</b>\n\n" + reseller_list
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="manage_reseller")]
    ])
    
    await admin_edit_or_reply(query, text, reply_markup=buttons, parse_mode=ParseMode.HTML)

async def seller_remove_flow(update: Update, context: CallbackContext) -> None:
    """Prompt admin to confirm bulk removal of all sellers."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    db = load_db()
    reseller_list = db.get('reseller_list', '')
    
    if not reseller_list:
        text = "❌ <b>No Sellers</b>\n\nThere are no sellers to remove."
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="manage_reseller")]
        ])
        await admin_edit_or_reply(query, text, reply_markup=buttons, parse_mode=ParseMode.HTML)
        return
    
    text = (
        "❌ <b>Remove All Sellers</b>\n\n"
        "<b>Current Seller List:</b>\n" + reseller_list + "\n\n"
        "⚠️ <b>Confirm:</b> This will remove ALL sellers from the list!\n"
        "This action cannot be undone."
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm - Remove All", callback_data="seller_remove_confirm"),
         InlineKeyboardButton("❌ Cancel", callback_data="manage_reseller")]
    ])
    
    await admin_edit_or_reply(query, text, reply_markup=buttons, parse_mode=ParseMode.HTML)

async def seller_remove_confirm(update: Update, context: CallbackContext) -> None:
    """Confirm and remove all sellers."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    db = load_db()
    old_list = db.get('reseller_list', '')
    
    # Remove all sellers
    db['reseller_list'] = ''
    save_db(db)
    
    text = (
        "✅ <b>All Sellers Removed Successfully!</b>\n\n"
        "<b>Removed List:</b>\n" + old_list + "\n\n"
        "The seller list is now empty."
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="manage_reseller")]
    ])
    
    await admin_edit_or_reply(query, text, reply_markup=buttons, parse_mode=ParseMode.HTML)

async def trusted_seller(update: Update, context: CallbackContext) -> None:
    """Show trusted seller list to user."""
    query = update.callback_query
    await query.answer()
    
    db = load_db()
    reseller_list = db.get('reseller_list', '')
    
    user_id = query.from_user.id

    if not reseller_list:
        text = t(user_id, 'no_resellers')
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(t(user_id, 'btn_back_to_menu'), callback_data="back_to_menu")]
        ])
        await query.message.reply_text(text, reply_markup=keyboard)
        return
    
    text = reseller_list
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(user_id, 'btn_back_to_menu'), callback_data="back_to_menu")]
    ])
    
    try:
        await query.edit_message_text(text=text, reply_markup=keyboard)
    except Exception:
        try:
            await query.edit_message_caption(caption=text, reply_markup=keyboard)
        except Exception:
            await query.message.reply_text(text, reply_markup=keyboard)

async def manage_8bp_accounts(update: Update, context: CallbackContext) -> None:
    """Show 8BP account management options."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    db = load_db()
    accounts_3b = db.get('8bp_accounts_3b', [])
    accounts_2b = db.get('8bp_accounts_2b', [])
    accounts_1b = db.get('8bp_accounts_1b', [])
    accounts_100m = db.get('8bp_accounts_100m', [])
    
    text = (
        "<b>🎱 8BP Account Management</b>\n\n"
        f"📊 <b>Available Accounts:</b>\n"
        f"💰 <b>3B Coin:</b> {len(accounts_3b)} accounts\n"
        f"💰 <b>2B Coin:</b> {len(accounts_2b)} accounts\n"
        f"💰 <b>1B Coin:</b> {len(accounts_1b)} accounts\n"
        f"💰 <b>100M Coin:</b> {len(accounts_100m)} accounts\n\n"
        "Choose an action:"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Account", callback_data="8bp_add_account")],
        [InlineKeyboardButton("📋 View Accounts", callback_data="8bp_view_accounts")],
        [InlineKeyboardButton("❌ Remove Account", callback_data="8bp_remove_account")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
    ])
    
    await admin_edit_or_reply(query, text, reply_markup=buttons, parse_mode=ParseMode.HTML)

async def add_8bp_account_flow(update: Update, context: CallbackContext) -> None:
    """Start account addition flow."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    text = (
        "<b>➕ Add 8BP Account</b>\n\n"
        "Select account type:"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 3B Coin Account", callback_data="8bp_add_3b")],
        [InlineKeyboardButton("💰 2B Coin Account", callback_data="8bp_add_2b")],
        [InlineKeyboardButton("💰 1B Coin Account", callback_data="8bp_add_1b")],
        [InlineKeyboardButton("💰 100M Coin Account", callback_data="8bp_add_100m")],
        [InlineKeyboardButton("🔙 Back", callback_data="manage_8bp_accounts")]
    ])
    
    await admin_edit_or_reply(query, text, reply_markup=buttons, parse_mode=ParseMode.HTML)

async def add_8bp_1b_start(update: Update, context: CallbackContext) -> None:
    """Start adding 1B account."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    context.user_data['admin_flow'] = 'add_8bp_1b_gmail'
    
    text = (
        "<b>➕ Add 1B Coin Account</b>\n\n"
        "📧 Send the Gmail address:\n\n"
        "Example: account@gmail.com"
    )
    
    await admin_edit_or_reply(query, text, parse_mode=ParseMode.HTML)


async def add_8bp_2b_start(update: Update, context: CallbackContext) -> None:
    """Start adding 2B account."""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return

    context.user_data['admin_flow'] = 'add_8bp_2b_gmail'

    text = (
        "<b>➕ Add 2B Coin Account</b>\n\n"
        "📧 Send the Gmail address:\n\n"
        "Example: account@gmail.com"
    )

    await admin_edit_or_reply(query, text, parse_mode=ParseMode.HTML)


async def add_8bp_3b_start(update: Update, context: CallbackContext) -> None:
    """Start adding 3B account."""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return

    context.user_data['admin_flow'] = 'add_8bp_3b_gmail'

    text = (
        "<b>➕ Add 3B Coin Account</b>\n\n"
        "📧 Send the Gmail address:\n\n"
        "Example: account@gmail.com"
    )

    await admin_edit_or_reply(query, text, parse_mode=ParseMode.HTML)

async def add_8bp_100m_start(update: Update, context: CallbackContext) -> None:
    """Start adding 100M account."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    context.user_data['admin_flow'] = 'add_8bp_100m_gmail'
    
    text = (
        "<b>➕ Add 100M Coin Account</b>\n\n"
        "📧 Send the Gmail address:\n\n"
        "Example: account@gmail.com"
    )
    
    await admin_edit_or_reply(query, text, parse_mode=ParseMode.HTML)

async def view_8bp_accounts(update: Update, context: CallbackContext) -> None:
    """View all available accounts."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    db = load_db()
    accounts_3b = db.get('8bp_accounts_3b', [])
    accounts_2b = db.get('8bp_accounts_2b', [])
    accounts_1b = db.get('8bp_accounts_1b', [])
    accounts_100m = db.get('8bp_accounts_100m', [])
    
    text = "<b>📋 8BP Account List</b>\n\n"

    if accounts_3b:
        text += "<b>💰 3B Coin Accounts:</b>\n"
        for i, acc in enumerate(accounts_3b, 1):
            text += f"{i}. {acc['gmail']} | {acc['password'][:3]}***\n"
        text += "\n"
    else:
        text += "<b>💰 3B Coin:</b> No accounts\n\n"

    if accounts_2b:
        text += "<b>💰 2B Coin Accounts:</b>\n"
        for i, acc in enumerate(accounts_2b, 1):
            text += f"{i}. {acc['gmail']} | {acc['password'][:3]}***\n"
        text += "\n"
    else:
        text += "<b>💰 2B Coin:</b> No accounts\n\n"
    
    if accounts_1b:
        text += "<b>💰 1B Coin Accounts:</b>\n"
        for i, acc in enumerate(accounts_1b, 1):
            text += f"{i}. {acc['gmail']} | {acc['password'][:3]}***\n"
        text += "\n"
    else:
        text += "<b>💰 1B Coin:</b> No accounts\n\n"
    
    if accounts_100m:
        text += "<b>💰 100M Coin Accounts:</b>\n"
        for i, acc in enumerate(accounts_100m, 1):
            text += f"{i}. {acc['gmail']} | {acc['password'][:3]}***\n"
    else:
        text += "<b>💰 100M Coin:</b> No accounts"
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="manage_8bp_accounts")]
    ])
    
    await admin_edit_or_reply(query, text, reply_markup=buttons, parse_mode=ParseMode.HTML)

async def remove_8bp_account_flow(update: Update, context: CallbackContext) -> None:
    """Start account removal flow."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    db = load_db()
    accounts_3b = db.get('8bp_accounts_3b', [])
    accounts_2b = db.get('8bp_accounts_2b', [])
    accounts_1b = db.get('8bp_accounts_1b', [])
    accounts_100m = db.get('8bp_accounts_100m', [])
    
    if not accounts_3b and not accounts_2b and not accounts_1b and not accounts_100m:
        text = "❌ <b>No Accounts Available</b>\n\nThere are no accounts to remove."
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="manage_8bp_accounts")]
        ])
        await admin_edit_or_reply(query, text, reply_markup=buttons, parse_mode=ParseMode.HTML)
        return
    
    text = (
        "<b>❌ Remove 8BP Account</b>\n\n"
        "Select account type:"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 3B Coin Account", callback_data="8bp_remove_3b")],
        [InlineKeyboardButton("💰 2B Coin Account", callback_data="8bp_remove_2b")],
        [InlineKeyboardButton("💰 1B Coin Account", callback_data="8bp_remove_1b")],
        [InlineKeyboardButton("💰 100M Coin Account", callback_data="8bp_remove_100m")],
        [InlineKeyboardButton("🔙 Back", callback_data="manage_8bp_accounts")]
    ])
    
    await admin_edit_or_reply(query, text, reply_markup=buttons, parse_mode=ParseMode.HTML)

async def remove_8bp_1b_start(update: Update, context: CallbackContext) -> None:
    """Start removing 1B account."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    db = load_db()
    accounts = db.get('8bp_accounts_1b', [])
    
    if not accounts:
        await query.answer("No 1B accounts available!", show_alert=True)
        return
    
    context.user_data['admin_flow'] = 'remove_8bp_1b'
    
    text = "<b>❌ Remove 1B Account</b>\n\n<b>Current Accounts:</b>\n"
    for i, acc in enumerate(accounts, 1):
        text += f"{i}. {acc['gmail']}\n"
    text += "\nSend the account number to remove (e.g., 1)"
    
    await admin_edit_or_reply(query, text, parse_mode=ParseMode.HTML)


async def remove_8bp_2b_start(update: Update, context: CallbackContext) -> None:
    """Start removing 2B account."""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return

    db = load_db()
    accounts = db.get('8bp_accounts_2b', [])

    if not accounts:
        await query.answer("No 2B accounts available!", show_alert=True)
        return

    context.user_data['admin_flow'] = 'remove_8bp_2b'

    text = "<b>❌ Remove 2B Account</b>\n\n<b>Current Accounts:</b>\n"
    for i, acc in enumerate(accounts, 1):
        text += f"{i}. {acc['gmail']}\n"
    text += "\nSend the account number to remove (e.g., 1)"

    await admin_edit_or_reply(query, text, parse_mode=ParseMode.HTML)


async def remove_8bp_3b_start(update: Update, context: CallbackContext) -> None:
    """Start removing 3B account."""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return

    db = load_db()
    accounts = db.get('8bp_accounts_3b', [])

    if not accounts:
        await query.answer("No 3B accounts available!", show_alert=True)
        return

    context.user_data['admin_flow'] = 'remove_8bp_3b'

    text = "<b>❌ Remove 3B Account</b>\n\n<b>Current Accounts:</b>\n"
    for i, acc in enumerate(accounts, 1):
        text += f"{i}. {acc['gmail']}\n"
    text += "\nSend the account number to remove (e.g., 1)"

    await admin_edit_or_reply(query, text, parse_mode=ParseMode.HTML)

async def remove_8bp_100m_start(update: Update, context: CallbackContext) -> None:
    """Start removing 100M account."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    db = load_db()
    accounts = db.get('8bp_accounts_100m', [])
    
    if not accounts:
        await query.answer("No 100M accounts available!", show_alert=True)
        return
    
    context.user_data['admin_flow'] = 'remove_8bp_100m'
    
    text = "<b>❌ Remove 100M Account</b>\n\n<b>Current Accounts:</b>\n"
    for i, acc in enumerate(accounts, 1):
        text += f"{i}. {acc['gmail']}\n"
    text += "\nSend the account number to remove (e.g., 1)"
    
    await admin_edit_or_reply(query, text, parse_mode=ParseMode.HTML)

async def help_support(update: Update, context: CallbackContext) -> None:
    """Show help and support information to user."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    text = (
        f"{t(user_id, 'help_title')}\n\n"
        f"{t(user_id, 'help_purchase_error_title')}\n"
        f"{t(user_id, 'help_purchase_error_body')}\n\n"
        f"{t(user_id, 'help_apk_title')}\n"
        f"{t(user_id, 'help_apk_body')}\n\n"
        f"{t(user_id, 'help_any_title')}\n"
        f"{t(user_id, 'help_any_body')}"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(user_id, 'btn_help_short'), url="https://t.me/Hayazi_Saheb")],
        [InlineKeyboardButton(t(user_id, 'btn_back'), callback_data="help_support_back")]
    ])
    
    try:
        await query.edit_message_caption(
            caption=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        try:
            await query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        except Exception:
            await query.message.reply_text(
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )

async def help_support_back(update: Update, context: CallbackContext) -> None:
    """Handle back button from help & support screen."""
    await back_to_menu(update, context)

async def my_profile(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    username = query.from_user.username or "No username"
    first_name = query.from_user.first_name or "User"
    
    db = load_db()
    users = db.get('users', {})
    uid = str(user_id)
    
    # Ensure user exists
    if uid not in users:
        users[uid] = {"balance": 0.0, "purchases": [], "member_since": datetime.now().strftime('%Y-%m-%d')}
        db['users'] = users
        save_db(db)
    
    user_data = users.get(uid, {})
    balance = user_data.get('balance', 0.0)
    member_since = user_data.get('member_since', datetime.now().strftime('%Y-%m-%d'))
    purchases = user_data.get('purchases', [])
    
    # Get last purchase info
    last_purchase_text = "No purchases yet"
    if purchases:
        last_purchase = purchases[-1]  # Get the most recent purchase
        product_name = HACK_INFO.get(last_purchase.get('product', ''), {}).get('name', last_purchase.get('product', 'Unknown'))
        last_purchase_text = f"{product_name}"
    
    safe_first_name = html.escape(first_name)
    safe_username = html.escape(username)
    safe_last_purchase = html.escape(last_purchase_text)

    # Build profile message
    profile_text = f"{t(user_id, 'profile_title')}\n\n"
    profile_text += f"{t(user_id, 'profile_name', name=safe_first_name)}\n"
    profile_text += f"{t(user_id, 'profile_username', username=safe_username)}\n"
    profile_text += f"{t(user_id, 'label_user_id', uid=user_id)}\n"
    profile_text += f"{t(user_id, 'profile_member_since', date=member_since)}\n"
    profile_text += f"{t(user_id, 'label_balance', balance=balance)}\n"
    profile_text += f"{t(user_id, 'label_last_purchase', last_purchase=safe_last_purchase)}\n"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(user_id, 'btn_add_balance'), callback_data="add_balance"),
         InlineKeyboardButton(t(user_id, 'btn_purchase_history'), callback_data="history")],
        [InlineKeyboardButton(t(user_id, 'btn_back_to_menu'), callback_data="back_to_menu")]
    ])
    
    try:
        # Try to edit with media (if message has photo)
        await query.edit_message_caption(caption=profile_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    except Exception as e:
        try:
            # If that fails, try to edit as text
            await query.edit_message_text(text=profile_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        except Exception as e2:
            # If both fail, reply with new message
            logger.error(f"Error editing profile message: {e2}")
            await query.message.reply_text(profile_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def confirm_buy(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    orig = query.data.replace("confirm_", "")
    product = PRODUCTS.get(orig)
    if not product:
        await query.message.reply_text(t(query.from_user.id, 'unknown_product'))
        return
    hack = product['hack']
    duration = product['duration']
    price = get_price(hack, duration)  # 💰 Fetch price from Firestore (with fallback)
    user_id = query.from_user.id
    uid = str(user_id)
    
    error_msg = None
    insufficient_balance = False
    
    # ATOMIC BLOCK - ALL database operations inside lock
    with stock_lock:
        db = load_db()
        users = db.setdefault('users', {})
        keys = db.setdefault('keys', {})
        
        # Ensure user structure
        if uid not in users:
            users[uid] = {"balance": 0.0, "purchases": [], "member_since": datetime.now().strftime('%Y-%m-%d')}
        if 'purchases' not in users[uid]:
            users[uid]['purchases'] = []
        if 'member_since' not in users[uid]:
            users[uid]['member_since'] = datetime.now().strftime('%Y-%m-%d')
        
        # Check stock FRESH inside lock
        if hack not in keys or duration not in keys[hack]:
            error_msg = t(user_id, 'out_of_stock_error')
        elif not keys[hack][duration]:
            error_msg = t(user_id, 'out_of_stock_error')
        else:
            # Check balance inside lock
            balance = users[uid].get('balance', 0.0)
            if balance < price:
                insufficient_balance = True
                error_msg = t(user_id, 'insufficient_balance_title')
            else:
                # ALL transaction operations inside lock - ATOMICALLY
                key_value = keys[hack][duration].pop(0)  # REMOVE KEY PERMANENTLY
                users[uid]['balance'] = round(balance - price, 8)  # DEDUCT BALANCE
                
                # Record purchase in purchases array
                expire_date = None
                try:
                    if 'day' in duration:
                        parts = duration.split('_')
                        days = next((int(part) for part in parts if part.isdigit()), None)
                        if days is not None:
                            expire_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
                except Exception:
                    pass
                
                entry = {
                    'product': hack,
                    'duration': duration,
                    'key': key_value,
                    'buy_date': datetime.now().strftime('%Y-%m-%d'),
                    'expire_date': expire_date or '',
                    'status': 'active'
                }
                users[uid]['purchases'].append(entry)
                
                # SAVE ONCE inside lock - persistence guaranteed
                save_db(db)
                error_msg = None  # Success - no error
    
    # Handle errors OUTSIDE lock
    if error_msg:
        if insufficient_balance:
            text = f"{t(user_id, 'insufficient_balance_title')}\n\n{t(user_id, 'insufficient_balance_body')}"
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton(t(user_id, 'btn_add_balance'), callback_data="add_balance")],
                [InlineKeyboardButton(t(user_id, 'btn_back'), callback_data=f"cancel_{orig}")]
            ])
            await query.message.reply_text(text, reply_markup=buttons)
        else:
            await query.message.reply_text(error_msg)
        return
    
    # Notify all admins of the purchase
    db = load_db()
    admins_list = db.get('admins', [ADMIN_ID])
    product_name = HACK_INFO.get(hack, {}).get('name', hack)
    duration_label = product['label']
    user_name = query.from_user.username or "Unknown"
    if user_name != "Unknown":
        user_name = f"@{user_name}"
    
    admin_notification = f"🛒 <b>New Purchase Notification</b>\n\n"
    admin_notification += f"🆔 <b>User ID:</b> {user_id}\n"
    admin_notification += f"👤 <b>User name:</b> {user_name}\n"
    admin_notification += f"📦 <b>Product:</b> {product_name}\n"
    admin_notification += f"⏳ <b>Duration:</b> {duration_label}\n"
    admin_notification += f"🔑 <b>Key:</b> <code>{key_value}</code>\n"
    admin_notification += f"💰 <b>Price:</b> {price}$\n"
    admin_notification += f"📅 <b>Purchase Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Send notification to all admins
    for admin_id in admins_list:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_notification,
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass  # Silently fail if admin notification doesn't send
    
    # Only reach here if transaction succeeded - display success message
    success_text = f"{t(user_id, 'success_title')}\n\n"
    success_text += f"{t(user_id, 'success_product', product=HACK_INFO.get(hack, {}).get('name', hack))}\n"
    success_text += f"{t(user_id, 'success_duration', duration=product['label'])}\n"
    success_text += f"{t(user_id, 'success_remaining', balance=users[uid]['balance'])}\n"
    success_text += f"{t(user_id, 'success_key', key=key_value)}\n\n"
    success_text += t(user_id, 'success_enjoy')
    
    back_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(user_id, 'btn_back_to_main_menu'), callback_data="back_to_menu")]
    ])
    
    try:
        # Try to edit the existing photo message caption
        await query.edit_message_caption(
            caption=success_text,
            parse_mode=ParseMode.HTML,
            reply_markup=back_buttons
        )
    except Exception:
        try:
            # If editing caption fails, try editing as text (if message is text-only)
            await query.edit_message_text(
                text=success_text,
                parse_mode=ParseMode.HTML,
                reply_markup=back_buttons
            )
        except Exception:
            # If both fail, reply with new message
            await query.message.reply_text(success_text, parse_mode=ParseMode.HTML, reply_markup=back_buttons)

async def cancel_buy(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    orig = query.data.replace("cancel_", "")
    product = PRODUCTS.get(orig)
    if not product:
        return
    hack = product['hack']
    # route back to hack duration menu
    if hack == 'snake_engine':
        await snake_engine(update, context)
    elif hack == 'carrom_se':
        await carrom_se(update, context)
    elif hack == 'carrom_ak':
        await carrom_ak(update, context)
    elif hack == 'score_se':
        await score_se(update, context)
    elif hack == 'score_ak':
        await score_ak(update, context)
    elif hack == 'aim_x':
        await aim_x_hack(update, context)
    elif hack == 'aim_king_nonroot':
        await aimking_nonroot(update, context)
    elif hack == 'ak_loader_root':
        await ak_loader_root(update, context)
    elif hack == 'kos_mode':
        await kos_mode(update, context)
    elif hack == 'kos_virtual':
        await kos_virtual(update, context)
    elif hack == 'wolf_hack':
        await wolf_hack(update, context)
    elif hack == 'wizard_ios':
        await wizard_hack(update, context)

async def admin_command(update: Update, context: CallbackContext) -> None:
    """Main admin panel with all management options."""
    # Get user ID from either callback query or message
    user_id = update.callback_query.from_user.id if update.callback_query else update.message.from_user.id
    
    # Check if user is admin
    if not is_admin(user_id):
        error_text = "❌ <b>Access Denied</b>\n\nYou are not authorized to access the admin panel.\nOnly admins can use this command."
        if update.callback_query:
            await update.callback_query.answer("Access Denied!", show_alert=True)
            return
        else:
            await update.message.reply_text(error_text, parse_mode=ParseMode.HTML)
            return
    
    query = update.callback_query if update.callback_query else None
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 Manage Keys", callback_data="admin_keys"),
         InlineKeyboardButton("💰 Manage Balance", callback_data="admin_manage_balance")],
        [InlineKeyboardButton("📊 Bot Stats", callback_data="admin_bot_stats"),
         InlineKeyboardButton("👥 Manage Admins", callback_data="admin_manage_admins")],
        [InlineKeyboardButton("💳 Balance Users", callback_data="admin_balance_users")],
        [InlineKeyboardButton("📢 Mailing", callback_data="admin_mailing"),
         InlineKeyboardButton("💎 Manage VIP", callback_data="admin_manage_vips")],
        [InlineKeyboardButton("🌟 Manage Sellers", callback_data="manage_reseller"),
         InlineKeyboardButton("📦 See Stock", callback_data="admin_see_stock")],
        [InlineKeyboardButton("🎱 Manage 8BP Account", callback_data="manage_8bp_accounts")],
        [InlineKeyboardButton("❌ Close", callback_data="admin_close")]
    ])
    
    text = (
        "<b>🔐 ADMIN CONTROL PANEL</b>\n\n"
        "Welcome to the admin dashboard. Choose an option:\n\n"
        "🔑 <b>Manage Keys:</b> Add/Remove product keys\n"
        "💰 <b>Balance:</b> Add/Remove user balance\n"
        "📊 <b>Stats:</b> View bot statistics\n"
        "👥 <b>Admins:</b> Manage admin users\n"
        "💳 <b>Balance Users:</b> View user balances and deposits\n"
        "💎 <b>VIP:</b> Add/Remove/List VIP users\n"
        "📢 <b>Mailing:</b> Send messages to all users\n"
        "🌟 <b>Sellers:</b> Manage seller/reseller list\n"
        "🎱 <b>8BP Account:</b> Manage game accounts\n"
        "📦 <b>Stock:</b> View available keys stock"
    )
    
    if query:
        await admin_edit_or_reply(query, text, reply_markup=buttons, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=buttons, parse_mode=ParseMode.HTML)

async def admin_manage_balance(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    # Check if user is admin
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    # show balance management options
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Balance", callback_data="admin_add_balance"),
         InlineKeyboardButton("➖ Remove Balance", callback_data="admin_remove_balance")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
    ])
    await admin_edit_or_reply(query, "💰 Balance Management\n\nHere you can add or remove user balance.\nChoose an action below.", reply_markup=buttons)


def _user_display_name(user_record: dict) -> str:
    """Build a readable username for admin lists."""
    username = user_record.get('username', '')
    first_name = user_record.get('first_name', '')
    name = user_record.get('name', '')

    if username and username != 'No username':
        return username if username.startswith('@') else f"@{username}"
    if first_name:
        return first_name
    if name:
        return name
    return 'Unknown'


def _get_total_deposit(user_record: dict) -> float:
    """Get cumulative total deposit with backward-compatible fallbacks."""
    # Primary source (new tracking)
    total_deposit = float(user_record.get('total_deposit', 0.0) or 0.0)

    # Secondary source: explicit deposit history list
    if total_deposit <= 0:
        deposit_history = user_record.get('deposit_history', [])
        if isinstance(deposit_history, list) and deposit_history:
            try:
                total_deposit = sum(float(item.get('amount', 0.0) or 0.0) for item in deposit_history if isinstance(item, dict))
            except Exception:
                total_deposit = 0.0

    # Backward-compatible estimate for old users without deposit tracking.
    # Estimate: current balance + total spent from purchases that include a price.
    if total_deposit <= 0:
        balance = float(user_record.get('balance', 0.0) or 0.0)
        purchases = user_record.get('purchases', [])
        spent = 0.0
        if isinstance(purchases, list):
            for p in purchases:
                if isinstance(p, dict):
                    spent += float(p.get('price', 0.0) or 0.0)
        total_deposit = max(0.0, balance + spent)

    return round(total_deposit, 2)


def _get_ledger_deposit_totals(db: dict) -> dict:
    """Return cumulative deposit totals by user_id from global deposit ledger."""
    totals = {}
    ledger = db.get('deposit_ledger', [])
    if not isinstance(ledger, list):
        return totals

    for item in ledger:
        if not isinstance(item, dict):
            continue
        uid = str(item.get('user_id', '')).strip()
        if not uid:
            continue
        amount = float(item.get('amount', 0.0) or 0.0)
        totals[uid] = round(float(totals.get(uid, 0.0)) + amount, 2)

    return totals


async def admin_balance_users(update: Update, context: CallbackContext) -> None:
    """Show paginated list of users with total deposit and current balance."""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return

    db = load_db()
    users = db.get('users', {})
    ledger_totals = _get_ledger_deposit_totals(db)

    page = 1
    if query.data.startswith('admin_balance_users_page_'):
        try:
            page = int(query.data.split('_')[-1])
        except Exception:
            page = 1

    if not users:
        text = "💳 <b>Balance Users</b>\n\n❌ No users found."
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
        ])
        await admin_edit_or_reply(query, text, reply_markup=buttons, parse_mode=ParseMode.HTML)
        return

    # Show only users who currently have balance > 0
    user_items = [
        (uid, rec)
        for uid, rec in users.items()
        if float(rec.get('balance', 0.0) or 0.0) > 0
    ]

    if not user_items:
        text = "💳 <b>Balance Users</b>\n\n❌ No users with balance found."
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
        ])
        await admin_edit_or_reply(query, text, reply_markup=buttons, parse_mode=ParseMode.HTML)
        return

    user_items = sorted(user_items, key=lambda item: int(item[0]) if str(item[0]).isdigit() else 0)
    users_per_page = 5
    total_pages = (len(user_items) + users_per_page - 1) // users_per_page

    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    start_idx = (page - 1) * users_per_page
    end_idx = start_idx + users_per_page
    page_users = user_items[start_idx:end_idx]

    total_deposit_all = sum(float(ledger_totals.get(uid, _get_total_deposit(rec))) for uid, rec in user_items)
    total_balance_all = sum(float(rec.get('balance', 0.0) or 0.0) for _, rec in user_items)

    lines = [
        f"💳 <b>Balance Users (Page {page}/{total_pages})</b>",
        f"📥 <b>Total Deposit (Users With Balance):</b> {total_deposit_all:.2f} USDT",
        f"💰 <b>Total Current Balance:</b> {total_balance_all:.2f} USDT",
        ""
    ]

    for idx, (uid, user_rec) in enumerate(page_users, 1):
        balance = float(user_rec.get('balance', 0.0) or 0.0)
        total_deposit = float(ledger_totals.get(uid, _get_total_deposit(user_rec)))
        username = _user_display_name(user_rec)

        lines.append(f"{start_idx + idx}. 🆔 <b>ID:</b> {uid}")
        lines.append(f"   👤 <b>User:</b> {username}")
        lines.append(f"   📥 <b>Total Deposit:</b> {total_deposit:.2f} USDT")
        lines.append(f"   💰 <b>Current Balance:</b> {balance:.2f} USDT")
        lines.append("")

    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"admin_balance_users_page_{page-1}"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"admin_balance_users_page_{page+1}"))

    buttons_rows = []
    if nav_row:
        buttons_rows.append(nav_row)
    buttons_rows.append([InlineKeyboardButton("🔙 Back", callback_data="admin_back")])

    await admin_edit_or_reply(
        query,
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(buttons_rows),
        parse_mode=ParseMode.HTML
    )

async def admin_back(update: Update, context: CallbackContext) -> None:
    # return to admin panel
    await admin_command(update, context)


async def admin_close(update: Update, context: CallbackContext) -> None:
    # close admin panel and return to main menu
    context.user_data.pop('admin_flow', None)
    await back_to_menu(update, context)


async def admin_add_flow(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data['admin_flow'] = 'add_balance_user'
    await admin_edit_or_reply(query, "Please send the user's Telegram ID.")

async def admin_remove_flow(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data['admin_flow'] = 'remove_balance_user'
    await admin_edit_or_reply(query, "Please send the user's Telegram ID.")

async def admin_manage_admins(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    # Check if user is admin
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Admin", callback_data="admin_add_admin"),
         InlineKeyboardButton("➖ Remove Admin", callback_data="admin_remove_admin")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
    ])
    await admin_edit_or_reply(
        query,
        "🛡️ <b>Admin Management</b>\n\nHere you can add or remove admins.\nChoose an action below.",
        reply_markup=buttons,
        parse_mode=ParseMode.HTML
    )

async def admin_add_admin_flow(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data['admin_flow'] = 'add_admin_user'
    await admin_edit_or_reply(query, "Please send the user's Telegram ID to add as admin:")

async def admin_remove_admin_flow(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data['admin_flow'] = 'remove_admin_user'
    await admin_edit_or_reply(query, "Please send the admin's Telegram ID to remove:")

async def admin_bot_stats(update: Update, context: CallbackContext) -> None:
    """Show bot statistics."""
    query = update.callback_query
    await query.answer()
    
    # Check if user is admin
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    db = load_db()
    users = db.get('users', {})
    keys_db = db.get('keys', {})
    admins = db.get('admins', [ADMIN_ID])
    
    total_users = len(users)
    total_revenue = sum(u.get('spent', 0) for u in users.values())
    
    # Count keys
    total_keys = 0
    for hack_keys in keys_db.values():
        for dur_keys in hack_keys.values():
            if isinstance(dur_keys, list):
                total_keys += len(dur_keys)
    
    stats_text = (
        f"<b>📊 BOT STATISTICS</b>\n\n"
        f"👥 <b>Total Users:</b> {total_users}\n"
        f"💰 <b>Total Revenue:</b> ${total_revenue:.2f}\n"
        f"🔑 <b>Total Keys:</b> {total_keys}\n"
        f"🛡️ <b>Total Admins:</b> {len(admins)}"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
    ])
    
    await admin_edit_or_reply(query, stats_text, reply_markup=buttons, parse_mode=ParseMode.HTML)

async def admin_mailing(update: Update, context: CallbackContext) -> None:
    """Start mailing flow."""
    query = update.callback_query
    await query.answer()
    
    # Check if user is admin
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    context.user_data['admin_flow'] = 'send_mailing'
    await admin_edit_or_reply(query, "📢 <b>Mailing Campaign</b>\n\nEnter the message to send to all users:", parse_mode=ParseMode.HTML)

async def admin_see_stock(update: Update, context: CallbackContext) -> None:
    """Show list of all hack tools for stock viewing."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    # Get unique hack tools from PRODUCTS
    hacks = {}
    for product_key, product_data in PRODUCTS.items():
        hack = product_data['hack']
        if hack not in hacks:
            label = HACK_INFO.get(hack, {}).get('name', hack)
            hacks[hack] = label
    
    # Create buttons in 2-column grid
    buttons_list = []
    stock_buttons = [
        InlineKeyboardButton(f"📦 {label}", callback_data=f"admin_tool_stock_{hack}")
        for hack, label in sorted(hacks.items())
    ]

    for i in range(0, len(stock_buttons), 2):
        buttons_list.append(stock_buttons[i:i + 2])
    
    buttons_list.append([InlineKeyboardButton("🔙 Back", callback_data="admin_back")])
    
    text = "<b>📦 Stock Overview</b>\n\n"
    text += "Select a hack tool to view available stock:\n\n"
    
    await admin_edit_or_reply(
        query,
        text,
        reply_markup=InlineKeyboardMarkup(buttons_list),
        parse_mode=ParseMode.HTML
    )

async def admin_view_tool_stock(update: Update, context: CallbackContext) -> None:
    """Show stock details for selected hack tool with all durations."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    # Extract hack from callback data (admin_tool_stock_snake_engine)
    hack = query.data.replace("admin_tool_stock_", "")
    
    # Get tool name
    tool_name = HACK_INFO.get(hack, {}).get('name', hack)
    
    # Get all products for this hack and their stock
    db = load_db()
    keys_db = db.get('keys', {})
    tool_keys = keys_db.get(hack, {})
    
    # Build stock info for all durations
    text = f"<b>📦 Stock for {tool_name}</b>\n\n"
    
    # Get all durations for this hack from PRODUCTS
    durations_for_hack = {}
    for product_key, product_data in PRODUCTS.items():
        if product_data['hack'] == hack:
            duration = product_data['duration']
            label = product_data['label']
            if duration not in durations_for_hack:
                durations_for_hack[duration] = label
    
    if not durations_for_hack:
        text += "No products available for this tool."
    else:
        # Sort durations and display stock + all keys under each duration
        for duration, label in sorted(durations_for_hack.items()):
            keys_list = tool_keys.get(duration, [])
            stock = len(keys_list)
            text += f"<b>⏳ {label}</b>\n"
            text += f"   📝 Available Keys: <b>{stock}</b>\n\n"

            if stock > 0:
                for idx, key_code in enumerate(keys_list, 1):
                    safe_key = str(key_code).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    text += f"   {idx}. <code>{safe_key}</code>\n"
            else:
                text += "   <i>No keys available</i>\n"

            text += "\n"
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="admin_see_stock")]
    ])
    
    await admin_edit_or_reply(
        query,
        text,
        reply_markup=buttons,
        parse_mode=ParseMode.HTML
    )

async def admin_manage_vips(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add VIP", callback_data="admin_add_vip"),
         InlineKeyboardButton("➖ Remove VIP", callback_data="admin_remove_vip")],
        [InlineKeyboardButton("📋 VIP List", callback_data="admin_vip_list")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
    ])
    await admin_edit_or_reply(
        query,
        "💎 <b>VIP Management</b>\n\nManage VIP users here.",
        reply_markup=buttons,
        parse_mode=ParseMode.HTML
    )

async def admin_add_vip_flow(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    context.user_data['admin_flow'] = 'add_vip_user'
    text = (
        "➕ <b>Add User to VIP</b>\n\n"
        "Send the user ID to add to VIP list:\n\n"
        "Example: 123456789"
    )
    await admin_edit_or_reply(query, text, parse_mode=ParseMode.HTML)

async def admin_remove_vip_flow(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    context.user_data['admin_flow'] = 'remove_vip_user'
    await admin_edit_or_reply(query, "Send user ID to remove VIP:")

async def admin_vip_list(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("❌ Access Denied!", show_alert=True)
        return

    db = load_db()
    vip_users = db.get('vip_users', {})
    
    # Get page number from callback data (default to 1)
    page = 1
    if query.data.startswith('vip_list_page_'):
        try:
            page = int(query.data.split('_')[-1])
        except:
            page = 1
    
    if not vip_users:
        text = "📋 <b>VIP List</b>\n\n❌ No VIP users yet."
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="admin_manage_vips")]
        ])
        await admin_edit_or_reply(query, text, reply_markup=buttons, parse_mode=ParseMode.HTML)
        return
    
    # Pagination settings
    users_per_page = 5
    vip_list = list(vip_users.items())
    total_pages = (len(vip_list) + users_per_page - 1) // users_per_page
    
    # Validate page number
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
    
    # Get users for current page
    start_idx = (page - 1) * users_per_page
    end_idx = start_idx + users_per_page
    page_users = vip_list[start_idx:end_idx]
    
    # Get users database for username lookup
    users = db.get('users', {})
    
    # Build the list text
    lines = [f"📋 <b>VIP Users List (Page {page}/{total_pages})</b>", ""]
    
    for idx, (user_id, vip_data) in enumerate(page_users, 1):
        # Handle both old format (just string) and new format (dict with username and date)
        if isinstance(vip_data, dict):
            username = vip_data.get('username', 'Unknown')
            joined_date = vip_data.get('joined_date', 'N/A')
        else:
            # Old format, migration
            username = 'Unknown'
            joined_date = str(vip_data)
        
        logging.info(f"VIP List - Processing user_id={user_id}, current username={username}")
        
        # If username is Unknown, try multiple sources
        if username == 'Unknown':
            # First try users database
            if user_id in users:
                stored_username = users[user_id].get('username', 'No username')
                stored_first_name = users[user_id].get('first_name', '')
                
                if stored_username and stored_username != 'No username':
                    username = stored_username
                    logging.info(f"VIP List - Found username in users DB: {username}")
                    # Update VIP data
                    if isinstance(vip_data, dict):
                        vip_users[user_id]['username'] = username
                        save_db(db)
                elif stored_first_name:
                    username = stored_first_name
                    logging.info(f"VIP List - Using first_name from users DB: {username}")
                    # Update VIP data
                    if isinstance(vip_data, dict):
                        vip_users[user_id]['username'] = username
                        save_db(db)
            
            # If still Unknown, try Telegram API
            if username == 'Unknown':
                try:
                    logging.info(f"VIP List - Attempting to fetch info from Telegram API for user_id={user_id}")
                    chat_info = await context.bot.get_chat(int(user_id))
                    logging.info(f"VIP List - Got chat_info for {user_id}: username={chat_info.username}, first_name={chat_info.first_name}")
                    if chat_info.username:
                        username = chat_info.username
                        # Update database with fetched username
                        if isinstance(vip_data, dict):
                            vip_users[user_id]['username'] = username
                            save_db(db)
                        # Add @ prefix for actual usernames
                        username = f"@{username}"
                    elif chat_info.first_name:
                        username = chat_info.first_name
                        # Update database with fetched name
                        if isinstance(vip_data, dict):
                            vip_users[user_id]['username'] = username
                            save_db(db)
                        # Don't add @ for first names
                except Exception as e:
                    logging.warning(f"Could not fetch username for VIP {user_id}: {e}")
        else:
            # Format existing username (only add @ if it's an actual username, not a first name)
            if username and username != 'Unknown':
                # If it doesn't start with @ and looks like a username (no spaces), add @
                if not username.startswith('@') and ' ' not in username:
                    username = f"@{username}"
        
        # Fallback if still Unknown
        if not username or username == 'Unknown':
            username = 'Unknown'
        
        lines.append(f"{start_idx + idx}. 🆔 <b>ID:</b> {user_id}")
        lines.append(f"   👤 <b>Name:</b> {username}")
        lines.append(f"   📅 <b>Joined:</b> {joined_date}")
        lines.append("")
    
    text = "\n".join(lines)
    
    # Build pagination buttons
    buttons_list = []
    
    # Previous and Next buttons
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"vip_list_page_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"vip_list_page_{page+1}"))
    
    if nav_buttons:
        buttons_list.append(nav_buttons)
    
    # Back button
    buttons_list.append([InlineKeyboardButton("🔙 Back", callback_data="admin_manage_vips")])
    
    buttons = InlineKeyboardMarkup(buttons_list)
    await admin_edit_or_reply(query, text, reply_markup=buttons, parse_mode=ParseMode.HTML)

async def admin_message_handler(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    # Block non-admin users from any active admin text flow (price/balance/keys/mailing)
    if any(k in context.user_data for k in ('admin_flow', 'price_flow', 'key_flow')) and not is_admin(user_id):
        context.user_data.pop('admin_flow', None)
        context.user_data.pop('price_flow', None)
        context.user_data.pop('key_flow', None)
        logger.warning(f"Unauthorized admin flow attempt by user_id={user_id}")
        await update.message.reply_text(
            f"❌ <b>Not an Admin</b>\n\n"
            f"You are not allowed to enter admin price/management values.\n"
            f"👤 <b>User ID:</b> {user_id}",
            parse_mode=ParseMode.HTML
        )
        return

    # handle text during admin flows (balance & key management)
    if 'admin_flow' in context.user_data:
        flow = context.user_data['admin_flow']
        text = update.message.text.strip()

        db = load_db()
        users = db.setdefault('users', {})
        admins = db.setdefault('admins', [ADMIN_ID])

        if flow == 'add_admin_user':
            try:
                admin_id = int(text)
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID. Please send a valid number.")
                return
            if admin_id in admins:
                await update.message.reply_text(f"❌ User ID {admin_id} is already an admin.")
            else:
                admins.append(admin_id)
                save_db(db)
                await update.message.reply_text(
                    f"✅ Admin Added Successfully!\n\n👤 New Admin ID: {admin_id}\n✓ Total Admins: {len(admins)}"
                )
                context.user_data.pop('admin_flow', None)
            return
        if flow == 'remove_admin_user':
            try:
                admin_id = int(text)
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID. Please send a valid number.")
                return
            if admin_id == ADMIN_ID:
                await update.message.reply_text("❌ Cannot remove the main admin.")
            elif admin_id not in admins:
                await update.message.reply_text(f"❌ User ID {admin_id} is not an admin.")
            else:
                admins.remove(admin_id)
                save_db(db)
                await update.message.reply_text(
                    f"✅ Admin Removed Successfully!\n\n👤 Removed Admin ID: {admin_id}\n✓ Remaining Admins: {len(admins)}"
                )
                context.user_data.pop('admin_flow', None)
            return
        if flow == 'add_vip_user':
            try:
                vip_id = int(text)
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID. Please send a valid number.")
                return
            vip_key = str(vip_id)
            vip_users = db.setdefault('vip_users', {})
            if vip_key in vip_users:
                await update.message.reply_text(f"❌ User ID {vip_id} is already VIP.")
            else:
                joined_date = datetime.utcnow().strftime('%Y-%m-%d')
                
                # Get username from Telegram API or users database
                username = 'Unknown'
                is_actual_username = False
                
                # First try users database
                users = db.get('users', {})
                if vip_key in users:
                    stored_username = users[vip_key].get('username', 'No username')
                    stored_first_name = users[vip_key].get('first_name', '')
                    
                    if stored_username and stored_username != 'No username':
                        username = stored_username
                        is_actual_username = True
                    elif stored_first_name:
                        username = stored_first_name
                        is_actual_username = False
                
                # If still Unknown, try Telegram API
                if username == 'Unknown':
                    try:
                        chat_info = await context.bot.get_chat(vip_id)
                        if chat_info.username:
                            username = chat_info.username
                            is_actual_username = True
                        elif chat_info.first_name:
                            username = chat_info.first_name
                            is_actual_username = False
                    except Exception as e:
                        logging.warning(f"Could not fetch username for {vip_id}: {e}")
                
                # Store as dict with username and joined_date
                vip_users[vip_key] = {
                    'username': username,
                    'joined_date': joined_date
                }
                save_db(db)
                
                # Only add @ for actual usernames, not first names
                display_username = f"@{username}" if (username != 'Unknown' and is_actual_username) else username
                await update.message.reply_text(
                    f"✅ <b>VIP Added Successfully!</b>\n\n"
                    f"🆔 <b>User ID:</b> {vip_id}\n"
                    f"👤 <b>Username:</b> {display_username}\n"
                    f"📅 <b>Joined:</b> {joined_date}",
                    parse_mode=ParseMode.HTML
                )
                # Send notification to the user
                try:
                    user_name = username if username != 'Unknown' else "User"
                    notification = f"🎉 <b>Welcome to VIP!</b>\n\nHello {user_name},\n\nYou are now a VIP member in HSA Store Panel!\n\n💎 Enjoy exclusive access to all premium tools and features!"
                    await context.bot.send_message(
                        chat_id=vip_id,
                        text=notification,
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    logging.warning(f"Could not notify user {vip_id}: {e}")
                context.user_data.pop('admin_flow', None)
            return
        if flow == 'remove_vip_user':
            try:
                vip_id = int(text)
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID. Please send a valid number.")
                return
            vip_key = str(vip_id)
            vip_users = db.setdefault('vip_users', {})
            if vip_key not in vip_users:
                await update.message.reply_text(f"❌ User ID {vip_id} is not in VIP list.")
            else:
                joined_at = vip_users.pop(vip_key, '')
                save_db(db)
                await update.message.reply_text(
                    f"✅ VIP Removed Successfully!\n\n👤 User ID: {vip_id}\n📅 Joined Date: {joined_at}"
                )
                # Send notification to the user
                try:
                    notification = f"ℹ️ Hello,\n\nYour VIP membership in HSA Store Panel has been removed.\n\nJoined: {joined_at}"
                    await context.bot.send_message(
                        chat_id=vip_id,
                        text=notification,
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    logging.warning(f"Could not notify user {vip_id}: {e}")
                context.user_data.pop('admin_flow', None)
            return
        if flow == 'add_balance_user':
            context.user_data['target_id'] = text
            context.user_data['admin_flow'] = 'add_balance_amount'
            await update.message.reply_text("Enter the USDT amount to add:")
            return
        if flow == 'add_balance_amount':
            try:
                amount = float(text)
            except ValueError:
                await update.message.reply_text("Please send a valid number for amount.")
                return
            tid = context.user_data.get('target_id')
            if tid not in users:
                users[tid] = {"balance": 0.0, "purchases": []}
            if 'purchases' not in users[tid]:
                users[tid]['purchases'] = []

            # Ensure cumulative deposit starts from best-known value for old records
            users[tid]['total_deposit'] = _get_total_deposit(users[tid])
            if 'deposit_history' not in users[tid] or not isinstance(users[tid].get('deposit_history'), list):
                users[tid]['deposit_history'] = []

            users[tid]['balance'] = users[tid].get('balance', 0.0) + amount
            users[tid]['total_deposit'] = float(users[tid].get('total_deposit', 0.0) or 0.0) + amount
            users[tid]['deposit_history'].append({
                'amount': amount,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

            # Global ledger keeps all-time deposits even if per-user structure changes later.
            deposit_ledger = db.setdefault('deposit_ledger', [])
            if not isinstance(deposit_ledger, list):
                deposit_ledger = []
                db['deposit_ledger'] = deposit_ledger
            deposit_ledger.append({
                'user_id': str(tid),
                'amount': amount,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            save_db(db)
            await update.message.reply_text(
                f"✅ Balance Updated Successfully!\n\n👤 User ID: {tid}\n💰 Added Amount: {amount} USDT\n💵 New Balance: {users[tid]['balance']} USDT"
            )
            # notify the user
            try:
                await context.bot.send_message(
                    chat_id=int(tid),
                    text=f"Hello {users[tid].get('name','User')}, your deposit of {amount} USDT has been added!"
                )
            except Exception:
                pass
            context.user_data.pop('admin_flow', None)
            return
        if flow == 'remove_balance_user':
            context.user_data['target_id'] = text
            context.user_data['admin_flow'] = 'remove_balance_amount'
            await update.message.reply_text("Enter the USDT amount to remove:")
            return
        if flow == 'remove_balance_amount':
            try:
                amount = float(text)
            except ValueError:
                await update.message.reply_text("Please send a valid number for amount.")
                return
            tid = context.user_data.get('target_id')
            if tid not in users:
                users[tid] = {"balance": 0.0, "purchases": []}
            if 'purchases' not in users[tid]:
                users[tid]['purchases'] = []
            users[tid]['balance'] = users[tid].get('balance', 0.0) - amount
            save_db(db)
            await update.message.reply_text(
                f"✅ Balance Updated Successfully!\n\n👤 User ID: {tid}\n💰 Removed Amount: {amount} USDT\n💵 New Balance: {users[tid]['balance']} USDT"
            )
            # notify the user
            try:
                await context.bot.send_message(
                    chat_id=int(tid),
                    text=f"Hello {users[tid].get('name','User')}, your balance of {amount} USDT has been removed."
                )
            except Exception:
                pass
            context.user_data.pop('admin_flow', None)
            return
        if flow == 'send_mailing':
            mailing_msg = text
            sent_count = 0
            failed_count = 0
            
            # Send message to all users
            for user_id_key in users.keys():
                try:
                    await context.bot.send_message(
                        chat_id=int(user_id_key),
                        text=mailing_msg
                    )
                    sent_count += 1
                except Exception:
                    failed_count += 1
            
            await update.message.reply_text(
                f"✅ <b>Mailing Campaign Completed!</b>\n\n"
                f"📤 Sent: {sent_count} users\n"
                f"❌ Failed: {failed_count}\n\n"
                f"Total Users Targeted: {sent_count + failed_count}",
                parse_mode=ParseMode.HTML
            )
            context.user_data.pop('admin_flow', None)
            return
        if flow == 'add_sellers_bulk':
            seller_text = text
            db = load_db()
            current_list = db.get('reseller_list', '')
            if current_list:
                new_list = current_list + "\n" + seller_text
            else:
                new_list = seller_text
            db['reseller_list'] = new_list
            save_db(db)
            await update.message.reply_text(
                f"✅ <b>All Sellers Added Successfully!</b>\n\n"
                f"📝 New Entries:\n{seller_text}\n\n"
                f"<b>Complete List:</b>\n{new_list}",
                parse_mode=ParseMode.HTML
            )
            context.user_data.pop('admin_flow', None)
            return
        
        # Handle 8BP account addition flows
        if flow == 'add_8bp_1b_gmail':
            gmail = text
            context.user_data['8bp_gmail'] = gmail
            context.user_data['admin_flow'] = 'add_8bp_1b_password'
            await update.message.reply_text(
                f"📧 <b>Gmail:</b> {gmail}\n\n"
                f"🔐 Now send the password:",
                parse_mode=ParseMode.HTML
            )
            return
        
        if flow == 'add_8bp_1b_password':
            password = text
            gmail = context.user_data.get('8bp_gmail', '')
            
            db = load_db()
            accounts = db.setdefault('8bp_accounts_1b', [])
            accounts.append({'gmail': gmail, 'password': password})
            save_db(db)
            
            await update.message.reply_text(
                f"✅ <b>1B Account Added!</b>\n\n"
                f"📧 <b>Gmail:</b> {gmail}\n"
                f"🔐 <b>Password:</b> {password}\n\n"
                f"Total 1B accounts: {len(accounts)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Another", callback_data="8bp_add_1b")],
                    [InlineKeyboardButton("🔙 Back", callback_data="manage_8bp_accounts")]
                ]),
                parse_mode=ParseMode.HTML
            )
            context.user_data.pop('admin_flow', None)
            context.user_data.pop('8bp_gmail', None)
            return

        if flow == 'add_8bp_2b_gmail':
            gmail = text
            context.user_data['8bp_gmail'] = gmail
            context.user_data['admin_flow'] = 'add_8bp_2b_password'
            await update.message.reply_text(
                f"📧 <b>Gmail:</b> {gmail}\n\n"
                f"🔐 Now send the password:",
                parse_mode=ParseMode.HTML
            )
            return

        if flow == 'add_8bp_2b_password':
            password = text
            gmail = context.user_data.get('8bp_gmail', '')

            db = load_db()
            accounts = db.setdefault('8bp_accounts_2b', [])
            accounts.append({'gmail': gmail, 'password': password})
            save_db(db)

            await update.message.reply_text(
                f"✅ <b>2B Account Added!</b>\n\n"
                f"📧 <b>Gmail:</b> {gmail}\n"
                f"🔐 <b>Password:</b> {password}\n\n"
                f"Total 2B accounts: {len(accounts)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Another", callback_data="8bp_add_2b")],
                    [InlineKeyboardButton("🔙 Back", callback_data="manage_8bp_accounts")]
                ]),
                parse_mode=ParseMode.HTML
            )
            context.user_data.pop('admin_flow', None)
            context.user_data.pop('8bp_gmail', None)
            return

        if flow == 'add_8bp_3b_gmail':
            gmail = text
            context.user_data['8bp_gmail'] = gmail
            context.user_data['admin_flow'] = 'add_8bp_3b_password'
            await update.message.reply_text(
                f"📧 <b>Gmail:</b> {gmail}\n\n"
                f"🔐 Now send the password:",
                parse_mode=ParseMode.HTML
            )
            return

        if flow == 'add_8bp_3b_password':
            password = text
            gmail = context.user_data.get('8bp_gmail', '')

            db = load_db()
            accounts = db.setdefault('8bp_accounts_3b', [])
            accounts.append({'gmail': gmail, 'password': password})
            save_db(db)

            await update.message.reply_text(
                f"✅ <b>3B Account Added!</b>\n\n"
                f"📧 <b>Gmail:</b> {gmail}\n"
                f"🔐 <b>Password:</b> {password}\n\n"
                f"Total 3B accounts: {len(accounts)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Another", callback_data="8bp_add_3b")],
                    [InlineKeyboardButton("🔙 Back", callback_data="manage_8bp_accounts")]
                ]),
                parse_mode=ParseMode.HTML
            )
            context.user_data.pop('admin_flow', None)
            context.user_data.pop('8bp_gmail', None)
            return
        
        if flow == 'add_8bp_100m_gmail':
            gmail = text
            context.user_data['8bp_gmail'] = gmail
            context.user_data['admin_flow'] = 'add_8bp_100m_password'
            await update.message.reply_text(
                f"📧 <b>Gmail:</b> {gmail}\n\n"
                f"🔐 Now send the password:",
                parse_mode=ParseMode.HTML
            )
            return
        
        if flow == 'add_8bp_100m_password':
            password = text
            gmail = context.user_data.get('8bp_gmail', '')
            
            db = load_db()
            accounts = db.setdefault('8bp_accounts_100m', [])
            accounts.append({'gmail': gmail, 'password': password})
            save_db(db)
            
            await update.message.reply_text(
                f"✅ <b>100M Account Added!</b>\n\n"
                f"📧 <b>Gmail:</b> {gmail}\n"
                f"🔐 <b>Password:</b> {password}\n\n"
                f"Total 100M accounts: {len(accounts)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Another", callback_data="8bp_add_100m")],
                    [InlineKeyboardButton("🔙 Back", callback_data="manage_8bp_accounts")]
                ]),
                parse_mode=ParseMode.HTML
            )
            context.user_data.pop('admin_flow', None)
            context.user_data.pop('8bp_gmail', None)
            return
        
        if flow == 'remove_8bp_1b':
            try:
                index = int(text) - 1
                db = load_db()
                accounts = db.get('8bp_accounts_1b', [])
                
                if index < 0 or index >= len(accounts):
                    await update.message.reply_text("❌ Invalid account number!")
                    return
                
                removed = accounts.pop(index)
                save_db(db)
                
                await update.message.reply_text(
                    f"✅ <b>Account Removed!</b>\n\n"
                    f"📧 {removed['gmail']}\n"
                    f"Remaining: {len(accounts)} accounts",
                    parse_mode=ParseMode.HTML
                )
                context.user_data.pop('admin_flow', None)
            except ValueError:
                await update.message.reply_text("❌ Please send a valid number!")
            return

        if flow == 'remove_8bp_2b':
            try:
                index = int(text) - 1
                db = load_db()
                accounts = db.get('8bp_accounts_2b', [])

                if index < 0 or index >= len(accounts):
                    await update.message.reply_text("❌ Invalid account number!")
                    return

                removed = accounts.pop(index)
                save_db(db)

                await update.message.reply_text(
                    f"✅ <b>Account Removed!</b>\n\n"
                    f"📧 {removed['gmail']}\n"
                    f"Remaining: {len(accounts)} accounts",
                    parse_mode=ParseMode.HTML
                )
                context.user_data.pop('admin_flow', None)
            except ValueError:
                await update.message.reply_text("❌ Please send a valid number!")
            return

        if flow == 'remove_8bp_3b':
            try:
                index = int(text) - 1
                db = load_db()
                accounts = db.get('8bp_accounts_3b', [])

                if index < 0 or index >= len(accounts):
                    await update.message.reply_text("❌ Invalid account number!")
                    return

                removed = accounts.pop(index)
                save_db(db)

                await update.message.reply_text(
                    f"✅ <b>Account Removed!</b>\n\n"
                    f"📧 {removed['gmail']}\n"
                    f"Remaining: {len(accounts)} accounts",
                    parse_mode=ParseMode.HTML
                )
                context.user_data.pop('admin_flow', None)
            except ValueError:
                await update.message.reply_text("❌ Please send a valid number!")
            return
        
        if flow == 'remove_8bp_100m':
            try:
                index = int(text) - 1
                db = load_db()
                accounts = db.get('8bp_accounts_100m', [])
                
                if index < 0 or index >= len(accounts):
                    await update.message.reply_text("❌ Invalid account number!")
                    return
                
                removed = accounts.pop(index)
                save_db(db)
                
                await update.message.reply_text(
                    f"✅ <b>Account Removed!</b>\n\n"
                    f"📧 {removed['gmail']}\n"
                    f"Remaining: {len(accounts)} accounts",
                    parse_mode=ParseMode.HTML
                )
                context.user_data.pop('admin_flow', None)
            except ValueError:
                await update.message.reply_text("❌ Please send a valid number!")
            return
    
    # handle price editing flow
    if 'price_flow' in context.user_data:
        flow = context.user_data['price_flow']
        hack = flow.get('hack')
        duration = flow.get('duration')
        if hack and duration:
            msg = update.message.text.strip()
            try:
                new_price = float(msg)
                if new_price < 0:
                    await update.message.reply_text("❌ Price cannot be negative.")
                    return
                set_price(hack, duration, new_price)
                
                # Get friendly product name
                product_name = HACK_INFO.get(hack, {}).get('name', hack)
                # Format duration nicely
                duration_label = duration.replace('_', ' ').title()
                
                await update.message.reply_text(
                    f"✅ <b>Price Updated Successfully!</b>\n\n"
                    f"📦 <b>Product:</b> {product_name}\n"
                    f"⏱️ <b>Duration:</b> {duration_label}\n"
                    f"💰 <b>New Price:</b> ${new_price}\n\n"
                    f"The updated price will be shown to users immediately.",
                    parse_mode=ParseMode.HTML
                )
                context.user_data.pop('price_flow', None)
                return
            except ValueError:
                await update.message.reply_text("❌ Invalid price. Please send a number (e.g., 4.99)")
                return
        else:
            # Price flow started but hack or duration not set - restart flow
            context.user_data.pop('price_flow', None)
            await update.message.reply_text("❌ Price edit session expired. Please use /admin to start again.")
            return
    
    # key management message handling
    if 'key_flow' not in context.user_data:
        return
    flow = context.user_data['key_flow']
    action = flow.get('action')
    hack = flow.get('hack')
    duration = flow.get('duration')
    if not hack or not duration:
        return
    msg = update.message.text.strip()
    if action == 'add':
        key_lines = [line.strip() for line in msg.splitlines() if line.strip()]
        if not key_lines:
            await update.message.reply_text("❌ Please send at least one valid key.")
            return
        for key_line in key_lines:
            add_key(hack, duration, key_line)
        stock = get_stock(hack, duration)
        friendly = HACK_INFO.get(hack, {}).get('name', hack)
        dur_label = duration.replace('_', ' ')
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Another", callback_data="key_add_again")],
            [InlineKeyboardButton("❌ Close", callback_data="admin_key_back")]
        ])
        
        confirmation_text = (
            f"✅ <b>Key Added Successfully</b>\n\n"
            f"<b>Product:</b> {friendly}\n"
            f"<b>Duration:</b> {dur_label}\n"
            f"<b>Added:</b> {len(key_lines)} key(s)\n"
            f"📦 <b>Stock Available:</b> {stock}"
        )
        await update.message.reply_text(confirmation_text, reply_markup=buttons, parse_mode=ParseMode.HTML)
        return
    else:  # remove
        if msg.upper() == 'CLEAR':
            remove_key(hack, duration, clear_all=True)
            stock = get_stock(hack, duration)
            await update.message.reply_text(f"✅ All keys cleared. Stock now: {stock}")
            return
        key_lines = [line.strip() for line in msg.splitlines() if line.strip()]
        if not key_lines:
            await update.message.reply_text("❌ Please send at least one key to remove.")
            return
        removed_count = 0
        for key_line in key_lines:
            if remove_key(hack, duration, value=key_line):
                removed_count += 1
        if removed_count > 0:
            stock = get_stock(hack, duration)
            await update.message.reply_text(f"✅ Removed {removed_count} key(s). Stock now: {stock}")
        else:
            await update.message.reply_text("❌ Key not found in stock.")
        return


async def back_to_menu(update: Update, context: CallbackContext) -> None:
    # Reuse verify logic for returning to main profile menu
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass

    name_user = query.from_user.first_name
    username = query.from_user.username or t(query.from_user.id, 'no_username')
    user_id = query.from_user.id
    db = load_db()
    users = db.get('users', {})
    uid = str(user_id)
    balance = users.get(uid, {}).get('balance', 0.0)
    purchases = users.get(uid, {}).get('purchases', [])

    lang = get_user_language(user_id, db)
    last_purchase_text = t(user_id, 'no_purchases', lang=lang)
    if purchases:
        last_purchase = purchases[-1]
        product_name = HACK_INFO.get(last_purchase.get('product', ''), {}).get('name', last_purchase.get('product', 'Unknown'))
        last_purchase_text = product_name

    # Check VIP status
    status_text = t(user_id, 'status_vip', lang=lang) if is_vip(user_id) else t(user_id, 'status_active', lang=lang)

    safe_name_user = html.escape(name_user or 'User')
    safe_username = html.escape(username)
    safe_last_purchase = html.escape(last_purchase_text)

    profile_text = build_main_profile_text(
        user_id,
        safe_name_user,
        safe_username,
        balance,
        status_text,
        last_purchase_text=safe_last_purchase,
        show_last_purchase=True,
        lang=lang,
    )

    menu = build_main_menu(user_id, lang=lang)

    await query.edit_message_media(
        media=InputMediaPhoto(
            media="https://i.postimg.cc/k4kRGdVK/file-00000000ca8c71faadd50d667e4a0509.png",
            caption=profile_text,
            parse_mode=ParseMode.HTML
        ),
        reply_markup=menu
    )

async def add_balance(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    deposit_username = "Hayazi_Saheb"
    prefill = f"Hello Admin, I want to add balance in my account.\nMy user ID is {user_id}\nPlease guide further."
    encoded_text = quote_plus(prefill)
    deposit_url = f"https://t.me/{deposit_username}?text={encoded_text}"
    text = (
        f"{t(user_id, 'add_balance_title')}\n\n"
        f"{t(user_id, 'add_balance_1')}\n"
        f"{t(user_id, 'add_balance_2')}\n\n"
        f"{t(user_id, 'add_balance_3')}\n"
        f"<code>{user_id}</code>\n\n"
        f"{t(user_id, 'add_balance_4')}"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(user_id, 'btn_deposit_now'), url=deposit_url),
         InlineKeyboardButton(t(user_id, 'btn_contact_admin'), url="https://t.me/Hayazi_Saheb")],
        [InlineKeyboardButton(t(user_id, 'btn_refresh'), callback_data="add_balance"),
         InlineKeyboardButton(t(user_id, 'btn_back'), callback_data="add_balance_back")]
    ])
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=buttons,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        await query.edit_message_caption(
            caption=text,
            reply_markup=buttons,
            parse_mode=ParseMode.HTML
        )

async def add_balance_back(update: Update, context: CallbackContext) -> None:
    await back_to_menu(update, context)


async def choose_language(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    text = f"{t(user_id, 'choose_language_title')}\n\n{t(user_id, 'choose_language_desc')}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(user_id, 'btn_english'), callback_data='set_lang_en'),
         InlineKeyboardButton(t(user_id, 'btn_arabic'), callback_data='set_lang_ar')],
        [InlineKeyboardButton(t(user_id, 'btn_back'), callback_data='back_to_menu')],
    ])

    try:
        await query.edit_message_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    except Exception:
        await query.edit_message_text(text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)


async def terms_menu(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    text = t(user_id, 'terms_message')

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(user_id, 'btn_back'), callback_data='back_to_menu'),
         InlineKeyboardButton(t(user_id, 'btn_become_reseller'), url='https://t.me/Hayazi_Saheb')]
    ])

    try:
        await query.edit_message_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    except Exception:
        await query.edit_message_text(text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)


async def set_language_english(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    set_user_language(query.from_user.id, 'en')
    await query.answer(t(query.from_user.id, 'language_set_en'), show_alert=False)
    await back_to_menu(update, context)


async def set_language_arabic(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    set_user_language(query.from_user.id, 'ar')
    await query.answer(t(query.from_user.id, 'language_set_ar'), show_alert=False)
    await back_to_menu(update, context)
async def pre_handle_update(update: Update, context) -> None:
    """Log all incoming updates before handler processing."""
    user_id = update.effective_user.id if update.effective_user else "unknown"
    if update.message:
        text = update.message.text[:50] if update.message.text else "(no text)"
        logger.info(f"📨 Message received from {user_id}: {text}")
    elif update.callback_query:
        data = update.callback_query.data or "(no data)"
        logger.info(f"🔘 Callback from {user_id}: {data}")
    else:
        logger.info(f"📦 Other update type from {user_id}: {update.update_id}")


async def error_handler(update, context):
    """Handle errors from Telegram API."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=True)

    # Log the error details
    if hasattr(context.error, '__class__'):
        error_type = context.error.__class__.__name__
        logger.error(f"Error type: {error_type}")
        
        # Handle specific errors gracefully
        if "Conflict" in error_type:
            logger.warning("Conflict: Another bot instance is running. Will retry in 30 seconds...")
            await asyncio.sleep(30)
        elif "Unauthorized" in error_type:
            logger.error("Unauthorized: Invalid token. Check API_TOKEN in bot.py")

def main() -> None:
    # Start keep-alive server for Replit
    keep_alive()
    
    _firestore_doc_ref()
    application = (
        Application.builder()
        .token(API_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .get_updates_connect_timeout(30)
        .get_updates_read_timeout(30)
        .get_updates_write_timeout(30)
        .get_updates_pool_timeout(30)
        .build()
    )

    vip_tool_pattern = r"^(item_snake|item_aimx|kos_mode|kos_virtual|item_ninja|item_wolf|item_wizard|aimking_nonroot|ak_loader_root|carrom_se|carrom_ak|score_se|score_ak|ff_android_drip_select|ff_android_kos_select|ff_ios|esign|gbox)$"
    application.add_handler(CallbackQueryHandler(vip_tool_gatekeeper, pattern=vip_tool_pattern), group=-2)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("other", other_command))
    application.add_handler(CallbackQueryHandler(product, pattern="^product$"))
    application.add_handler(CallbackQueryHandler(product_accounts, pattern="^product_accounts$"))
    application.add_handler(CallbackQueryHandler(product_hackes, pattern="^product_hackes$"))
    application.add_handler(CallbackQueryHandler(eight_ball_pool, pattern="^product_8ball$"))
    application.add_handler(CallbackQueryHandler(eight_bp_account, pattern="^product_8bp_account$"))
    application.add_handler(CallbackQueryHandler(buy_8bp_3b, pattern="^buy_8bp_3b$"))
    application.add_handler(CallbackQueryHandler(buy_8bp_2b, pattern="^buy_8bp_2b$"))
    application.add_handler(CallbackQueryHandler(buy_8bp_1b, pattern="^buy_8bp_1b$"))
    application.add_handler(CallbackQueryHandler(buy_8bp_100m, pattern="^buy_8bp_100m$"))
    application.add_handler(CallbackQueryHandler(confirm_buy_8bp_3b, pattern="^confirm_buy_8bp_3b$"))
    application.add_handler(CallbackQueryHandler(confirm_buy_8bp_2b, pattern="^confirm_buy_8bp_2b$"))
    application.add_handler(CallbackQueryHandler(confirm_buy_8bp_1b, pattern="^confirm_buy_8bp_1b$"))
    application.add_handler(CallbackQueryHandler(confirm_buy_8bp_100m, pattern="^confirm_buy_8bp_100m$"))
    application.add_handler(CallbackQueryHandler(caroom_pool, pattern="^product_caroom$"))
    application.add_handler(CallbackQueryHandler(carrom_se, pattern="^carrom_se$"))
    application.add_handler(CallbackQueryHandler(carrom_ak, pattern="^carrom_ak$"))
    application.add_handler(CallbackQueryHandler(score_star, pattern="^product_scorestar$"))
    application.add_handler(CallbackQueryHandler(score_se, pattern="^score_se$"))
    application.add_handler(CallbackQueryHandler(score_ak, pattern="^score_ak$"))
    application.add_handler(CallbackQueryHandler(free_fire, pattern="^product_freefire$"))
    application.add_handler(CallbackQueryHandler(ff_android, pattern="^ff_android$"))
    application.add_handler(CallbackQueryHandler(ff_android_drip, pattern="^ff_android_drip_select$"))
    application.add_handler(CallbackQueryHandler(ff_android_kos, pattern="^ff_android_kos_select$"))
    application.add_handler(CallbackQueryHandler(ff_ios, pattern="^ff_ios$"))
    application.add_handler(CallbackQueryHandler(certificate_ios, pattern="^product_certificate_ios$"))
    application.add_handler(CallbackQueryHandler(esign, pattern="^esign$"))
    application.add_handler(CallbackQueryHandler(gbox, pattern="^gbox$"))
    application.add_handler(CallbackQueryHandler(snake_engine, pattern="^item_snake$"))
    application.add_handler(CallbackQueryHandler(aim_x_hack, pattern="^item_aimx$"))
    application.add_handler(CallbackQueryHandler(kos_hack, pattern="^item_kos$"))
    application.add_handler(CallbackQueryHandler(kos_mode, pattern="^kos_mode$"))
    application.add_handler(CallbackQueryHandler(kos_virtual, pattern="^kos_virtual$"))
    application.add_handler(CallbackQueryHandler(aim_king, pattern="^item_aimking$"))
    application.add_handler(CallbackQueryHandler(aimking_nonroot, pattern="^aimking_nonroot$"))
    application.add_handler(CallbackQueryHandler(ak_loader_root, pattern="^ak_loader_root$"))
    application.add_handler(CallbackQueryHandler(ninja_engine, pattern="^item_ninja$"))
    application.add_handler(CallbackQueryHandler(buy_item, pattern="^buy_"))
    application.add_handler(CallbackQueryHandler(admin_manage_balance, pattern="^admin_manage_balance$"))
    application.add_handler(CallbackQueryHandler(admin_balance_users, pattern=r"^(admin_balance_users|admin_balance_users_page_\d+)$"))
    application.add_handler(CallbackQueryHandler(admin_add_flow, pattern="^admin_add_balance$"))
    application.add_handler(CallbackQueryHandler(admin_remove_flow, pattern="^admin_remove_balance$"))
    application.add_handler(CallbackQueryHandler(admin_manage_admins, pattern="^admin_manage_admins$"))
    application.add_handler(CallbackQueryHandler(admin_add_admin_flow, pattern="^admin_add_admin$"))
    application.add_handler(CallbackQueryHandler(admin_remove_admin_flow, pattern="^admin_remove_admin$"))
    application.add_handler(CallbackQueryHandler(admin_manage_vips, pattern="^admin_manage_vips$"))
    application.add_handler(CallbackQueryHandler(admin_add_vip_flow, pattern="^admin_add_vip$"))
    application.add_handler(CallbackQueryHandler(admin_remove_vip_flow, pattern="^admin_remove_vip$"))
    application.add_handler(CallbackQueryHandler(admin_vip_list, pattern=r"^(admin_vip_list|vip_list_page_\d+)$"))
    application.add_handler(CallbackQueryHandler(admin_bot_stats, pattern="^admin_bot_stats$"))
    application.add_handler(CallbackQueryHandler(admin_mailing, pattern="^admin_mailing$"))
    application.add_handler(CallbackQueryHandler(admin_see_stock, pattern="^admin_see_stock$"))
    application.add_handler(CallbackQueryHandler(admin_view_tool_stock, pattern=r"^admin_tool_stock_.*$"))
    application.add_handler(CallbackQueryHandler(admin_close, pattern="^admin_close$"))
    application.add_handler(CallbackQueryHandler(admin_back, pattern="^admin_back$"))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"))
    application.add_handler(CallbackQueryHandler(trusted_seller, pattern="^trusted_seller$"))
    application.add_handler(CallbackQueryHandler(help_support, pattern="^help_support$"))
    application.add_handler(CallbackQueryHandler(help_support_back, pattern="^help_support_back$"))
    application.add_handler(CallbackQueryHandler(other_become_reseller, pattern="^other_become_reseller$"))
    application.add_handler(CallbackQueryHandler(other_check_device, pattern="^other_check_device$"))
    application.add_handler(CallbackQueryHandler(other_user_guide, pattern="^other_user_guide$"))
    application.add_handler(CallbackQueryHandler(other_open_site, pattern="^other_open_site$"))
    application.add_handler(CallbackQueryHandler(other_back_menu, pattern="^other_back_menu$"))
    application.add_handler(CallbackQueryHandler(manage_reseller, pattern="^manage_reseller$"))
    application.add_handler(CallbackQueryHandler(seller_add_flow, pattern="^seller_add$"))
    application.add_handler(CallbackQueryHandler(seller_list_view, pattern="^seller_view$"))
    application.add_handler(CallbackQueryHandler(seller_remove_flow, pattern="^seller_remove$"))
    application.add_handler(CallbackQueryHandler(seller_remove_confirm, pattern="^seller_remove_confirm$"))
    # 8BP account management handlers
    application.add_handler(CallbackQueryHandler(manage_8bp_accounts, pattern="^manage_8bp_accounts$"))
    application.add_handler(CallbackQueryHandler(add_8bp_account_flow, pattern="^8bp_add_account$"))
    application.add_handler(CallbackQueryHandler(view_8bp_accounts, pattern="^8bp_view_accounts$"))
    application.add_handler(CallbackQueryHandler(remove_8bp_account_flow, pattern="^8bp_remove_account$"))
    application.add_handler(CallbackQueryHandler(add_8bp_3b_start, pattern="^8bp_add_3b$"))
    application.add_handler(CallbackQueryHandler(add_8bp_2b_start, pattern="^8bp_add_2b$"))
    application.add_handler(CallbackQueryHandler(add_8bp_1b_start, pattern="^8bp_add_1b$"))
    application.add_handler(CallbackQueryHandler(add_8bp_100m_start, pattern="^8bp_add_100m$"))
    application.add_handler(CallbackQueryHandler(remove_8bp_3b_start, pattern="^8bp_remove_3b$"))
    application.add_handler(CallbackQueryHandler(remove_8bp_2b_start, pattern="^8bp_remove_2b$"))
    application.add_handler(CallbackQueryHandler(remove_8bp_1b_start, pattern="^8bp_remove_1b$"))
    application.add_handler(CallbackQueryHandler(remove_8bp_100m_start, pattern="^8bp_remove_100m$"))
    application.add_handler(CallbackQueryHandler(choose_language, pattern="^choose_language$"))
    application.add_handler(CallbackQueryHandler(terms_menu, pattern="^terms$"))
    application.add_handler(CallbackQueryHandler(set_language_english, pattern="^set_lang_en$"))
    application.add_handler(CallbackQueryHandler(set_language_arabic, pattern="^set_lang_ar$"))
    # purchase confirmation/cancel
    application.add_handler(CallbackQueryHandler(confirm_buy, pattern="^confirm_buy_"))
    application.add_handler(CallbackQueryHandler(cancel_buy, pattern="^cancel_buy_"))
    application.add_handler(CallbackQueryHandler(history_handler, pattern="^history$"))
    application.add_handler(CallbackQueryHandler(next_history, pattern="^next_history$"))
    application.add_handler(CallbackQueryHandler(prev_history, pattern="^prev_history$"))
    application.add_handler(CallbackQueryHandler(my_profile, pattern="^my_profile$"))

    # admin key management handlers
    application.add_handler(CallbackQueryHandler(admin_manage_keys, pattern="^admin_keys$"))
    application.add_handler(CallbackQueryHandler(admin_key_action, pattern="^admin_key_(add|remove)$"))
    application.add_handler(CallbackQueryHandler(admin_select_category, pattern="^admin_category_"))
    application.add_handler(CallbackQueryHandler(admin_select_hack, pattern="^admin_hack_"))
    application.add_handler(CallbackQueryHandler(admin_select_duration, pattern="^admin_dur_"))
    application.add_handler(CallbackQueryHandler(key_add_again, pattern="^key_add_again$"))
    application.add_handler(CallbackQueryHandler(key_clear_all, pattern="^key_clear_all$"))
    application.add_handler(CallbackQueryHandler(cancel_admin_key, pattern="^admin_key_back$"))

    # admin price editing handlers
    application.add_handler(CallbackQueryHandler(admin_edit_price, pattern="^admin_edit_price$"))
    application.add_handler(CallbackQueryHandler(admin_price_select_category, pattern="^price_category_"))
    application.add_handler(CallbackQueryHandler(admin_price_select_hack, pattern="^price_hack_"))
    application.add_handler(CallbackQueryHandler(admin_price_select_duration, pattern="^price_dur_"))

    # new hack menu handlers
    application.add_handler(CallbackQueryHandler(wolf_hack, pattern="^item_wolf$"))
    application.add_handler(CallbackQueryHandler(wizard_hack, pattern="^item_wizard$"))
    # Add Balance button handlers
    application.add_handler(CallbackQueryHandler(add_balance, pattern="^add_balance$"))
    application.add_handler(CallbackQueryHandler(add_balance_back, pattern="^add_balance_back$"))

    # message handler for admin flows (balance & keys)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_message_handler))

    # Add error handler
    application.add_error_handler(error_handler)

    # Add pre-processor to log all updates (must be first handler)
    application.add_handler(TypeHandler(Update, pre_handle_update), group=-1)
    # Start bot with improved polling
    logger.info("Starting HSA Store Bot...")
    logger.info(f"Admin ID: {ADMIN_ID}")
    logger.info("Bot is running. Press Ctrl+C to stop.")
    
    try:
        application.run_polling(
            allowed_updates=None,
            drop_pending_updates=False,
            timeout=30,
            bootstrap_retries=-1,
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.exception(f"Unexpected error: {e!r}")
        logger.info("Waiting 60 seconds before exit...")
        import time
        time.sleep(60)

if __name__ == "__main__":
    main()
