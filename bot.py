# telegram_tiktok_buff_bot_complete.py - Full bot with Vietnam proxies + Bot Token
import asyncio
import random
import time
import re
import json
import os
import requests
from typing import Optional, List, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ========== BOT TOKEN - THAY BẰNG TOKEN CỦA BẠN ==========
BOT_TOKEN = "8659787129:AAFPGVPn7SoXji3wLnrzBWxKyzaVPERAEgk"

# ========== PROXY VIỆT NAM ==========
PROXY_LIST = [
    "socks5://113.22.123.45:1080",
    "socks5://115.72.200.12:1080",
    "socks5://14.161.45.78:1080",
    "socks5://125.235.65.23:1080",
    "socks5://113.160.32.100:1080",
    "socks5://113.161.55.88:1080",
    "socks5://222.252.100.50:1080",
    "socks5://14.225.200.33:1080",
    "socks5://103.238.240.10:1080",
    "socks5://103.238.245.20:1080",
]

# ========== FILE LƯU TOKEN (để không mất khi reset bot) ==========
TOKEN_CONFIG_FILE = "bot_config.json"

def save_bot_token(token: str):
    """Lưu token vào file"""
    with open(TOKEN_CONFIG_FILE, "w") as f:
        json.dump({"bot_token": token}, f)
    print(f"✅ Đã lưu token vào {TOKEN_CONFIG_FILE}")

def load_bot_token() -> str:
    """Đọc token từ file"""
    if os.path.exists(TOKEN_CONFIG_FILE):
        with open(TOKEN_CONFIG_FILE, "r") as f:
            data = json.load(f)
            return data.get("bot_token", BOT_TOKEN)
    return BOT_TOKEN

# ========== PROXY MANAGER ==========
class ProxyManager:
    def __init__(self, proxy_list: List[str], max_failures: int = 3, cooldown_seconds: int = 30):
        self.proxies = []
        for proxy in proxy_list:
            self.proxies.append({
                'url': proxy,
                'failures': 0,
                'last_used': 0,
                'success_count': 0,
                'total_requests': 0
            })
        self.max_failures = max_failures
        self.cooldown = cooldown_seconds
    
    def get_proxy(self) -> Optional[str]:
        current_time = time.time()
        available = [p for p in self.proxies 
                    if p['failures'] < self.max_failures 
                    and (current_time - p['last_used']) >= self.cooldown]
        if not available:
            return None
        available.sort(key=lambda x: x['last_used'])
        chosen = available[0]
        chosen['last_used'] = current_time
        chosen['total_requests'] += 1
        return chosen['url']
    
    def report_result(self, proxy_url: str, success: bool):
        for p in self.proxies:
            if p['url'] == proxy_url:
                if success:
                    p['success_count'] += 1
                    p['failures'] = 0
                else:
                    p['failures'] += 1
                break
    
    def get_stats(self) -> Dict:
        alive = sum(1 for p in self.proxies if p['failures'] < self.max_failures)
        return {'total': len(self.proxies), 'alive': alive, 'dead': len(self.proxies) - alive}

# ========== TIKTOK API ==========
TIKTOK_VIEW_URL = "https://www.tiktok.com/api/v1/item/view"
TIKTOK_LIKE_URL = "https://www.tiktok.com/api/v1/commit/like"
TIKTOK_FOLLOW_URL = "https://www.tiktok.com/api/v1/commit/follow"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
]

def send_with_proxy(url: str, payload: dict, proxy_manager: ProxyManager) -> Optional[dict]:
    proxy_url = proxy_manager.get_proxy()
    if not proxy_url:
        return None
    try:
        clean_proxy = proxy_url.replace('socks5://', '')
        proxies = {'http': f'socks5://{clean_proxy}', 'https': f'socks5://{clean_proxy}'}
        headers = {"User-Agent": random.choice(USER_AGENTS), "Accept-Language": "en-US,en;q=0.9"}
        response = requests.post(url, headers=headers, json=payload, proxies=proxies, timeout=10)
        success = response.status_code == 200
        proxy_manager.report_result(proxy_url, success)
        return response.json() if success else None
    except Exception:
        proxy_manager.report_result(proxy_url, False)
        return None

def extract_video_id(url: str) -> str:
    match = re.search(r'/video/(\d+)', url)
    return match.group(1) if match else "0"

# ========== USER STATE MANAGEMENT ==========
user_states = {}  # {chat_id: {'action': str, 'quantity': int, 'target': str}}

# ========== BOT COMMANDS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in user_states:
        user_states[chat_id] = {'action': None, 'quantity': 50, 'target': None}
    
    keyboard = [
        [InlineKeyboardButton("📊 Buff Views", callback_data='buff_views')],
        [InlineKeyboardButton("❤️ Buff Likes", callback_data='buff_likes')],
        [InlineKeyboardButton("👥 Buff Followers", callback_data='buff_followers')],
        [InlineKeyboardButton("🔢 Set Quantity", callback_data='set_quantity')],
        [InlineKeyboardButton("📡 Proxy Status", callback_data='proxy_status')]
    ]
    stats = proxy_mgr.get_stats()
    qty = user_states[chat_id]['quantity']
    await update.message.reply_text(
        f"🤖 TikTok Buff Bot (Proxy Việt Nam)\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 Proxy: {stats['alive']}/{stats['total']} hoạt động\n"
        f"🔢 Số lượng buff: {qty}\n"
        f"👤 User ID: {chat_id}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Chọn hành động:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    
    if chat_id not in user_states:
        user_states[chat_id] = {'action': None, 'quantity': 50, 'target': None}
    
    action = query.data
    
    if action == 'set_quantity':
        await query.edit_message_text("📝 Gửi số lượng (1-1000):")
        user_states[chat_id]['action'] = 'awaiting_quantity'
    
    elif action == 'proxy_status':
        stats = proxy_mgr.get_stats()
        await query.edit_message_text(
            f"📡 Proxy Status\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"✅ Alive: {stats['alive']}\n"
            f"❌ Dead: {stats['dead']}\n"
            f"📊 Total: {stats['total']}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🔄 Tự động xoay vòng mỗi 30 giây"
        )
        # Quay lại menu sau 3 giây
        await asyncio.sleep(3)
        keyboard = [
            [InlineKeyboardButton("📊 Buff Views", callback_data='buff_views')],
            [InlineKeyboardButton("❤️ Buff Likes", callback_data='buff_likes')],
            [InlineKeyboardButton("👥 Buff Followers", callback_data='buff_followers')],
            [InlineKeyboardButton("🔢 Set Quantity", callback_data='set_quantity')]
        ]
        await query.edit_message_text(
            f"🤖 TikTok Buff Bot\n📡 Proxy: {stats['alive']}/{stats['total']}\n🔢 Quantity: {user_states[chat_id]['quantity']}\nSelect action:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif action == 'buff_views':
        user_states[chat_id]['action'] = 'awaiting_views_url'
        await query.edit_message_text(f"📹 Gửi link TikTok để buff {user_states[chat_id]['quantity']} views:")
    
    elif action == 'buff_likes':
        user_states[chat_id]['action'] = 'awaiting_likes_url'
        await query.edit_message_text(f"❤️ Gửi link TikTok để buff {user_states[chat_id]['quantity']} likes:")
    
    elif action == 'buff_followers':
        user_states[chat_id]['action'] = 'awaiting_followers_username'
        await query.edit_message_text(f"👤 Gửi username (ví dụ: @username) để buff {user_states[chat_id]['quantity']} followers:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_input = update.message.text.strip()
    
    if chat_id not in user_states:
        user_states[chat_id] = {'action': None, 'quantity': 50, 'target': None}
    
    state = user_states[chat_id]
    
    # Xử lý nhập số lượng
    if state['action'] == 'awaiting_quantity':
        try:
            qty = int(user_input)
            if 1 <= qty <= 1000:
                state['quantity'] = qty
                state['action'] = None
                await update.message.reply_text(f"✅ Đã đặt số lượng thành {qty}")
                # Quay lại menu
                keyboard = [
                    [InlineKeyboardButton("📊 Buff Views", callback_data='buff_views')],
                    [InlineKeyboardButton("❤️ Buff Likes", callback_data='buff_likes')],
                    [InlineKeyboardButton("👥 Buff Followers", callback_data='buff_followers')],
                    [InlineKeyboardButton("🔢 Set Quantity", callback_data='set_quantity')]
                ]
                stats = proxy_mgr.get_stats()
                await update.message.reply_text(
                    f"🤖 TikTok Buff Bot\n📡 Proxy: {stats['alive']}/{stats['total']}\n🔢 Quantity: {state['quantity']}\nSelect action:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await update.message.reply_text("❌ Số lượng phải từ 1 đến 1000. Nhập lại:")
        except ValueError:
            await update.message.reply_text("❌ Vui lòng nhập số. Nhập lại:")
        return
    
    # Xử lý buff views
    elif state['action'] == 'awaiting_views_url':
        video_id = extract_video_id(user_input)
        if video_id == "0":
            await update.message.reply_text("❌ Link TikTok không hợp lệ. Gửi lại hoặc /start để hủy:")
            return
        
        count = state['quantity']
        await update.message.reply_text(f"🚀 Đang buff {count} views cho video {video_id}...")
        success_count = 0
        for i in range(count):
            payload = {"itemId": video_id, "source": "feed"}
            result = send_with_proxy(TIKTOK_VIEW_URL, payload, proxy_mgr)
            if result:
                success_count += 1
                if (i+1) % 10 == 0 or i+1 == count:
                    await update.message.reply_text(f"📊 Tiến độ: {i+1}/{count} views ({success_count} thành công)")
            else:
                await update.message.reply_text(f"⚠️ View {i+1} thất bại - proxy lỗi")
            time.sleep(random.uniform(0.8, 1.5))
        
        await update.message.reply_text(f"✅ Hoàn thành {success_count}/{count} views")
        state['action'] = None
    
    # Xử lý buff likes
    elif state['action'] == 'awaiting_likes_url':
        video_id = extract_video_id(user_input)
        if video_id == "0":
            await update.message.reply_text("❌ Link TikTok không hợp lệ. Gửi lại hoặc /start để hủy:")
            return
        
        count = state['quantity']
        await update.message.reply_text(f"❤️ Đang buff {count} likes cho video {video_id}...")
        success_count = 0
        for i in range(count):
            payload = {"itemId": video_id, "likeType": 1}
            result = send_with_proxy(TIKTOK_LIKE_URL, payload, proxy_mgr)
            if result:
                success_count += 1
                if (i+1) % 10 == 0 or i+1 == count:
                    await update.message.reply_text(f"📊 Tiến độ: {i+1}/{count} likes ({success_count} thành công)")
            else:
                await update.message.reply_text(f"⚠️ Like {i+1} thất bại")
            time.sleep(random.uniform(1.0, 1.8))
        
        await update.message.reply_text(f"✅ Hoàn thành {success_count}/{count} likes")
        state['action'] = None
    
    # Xử lý buff followers
    elif state['action'] == 'awaiting_followers_username':
        username = user_input.lstrip('@')
        if not username or len(username) < 2:
            await update.message.reply_text("❌ Username không hợp lệ. Gửi lại hoặc /start để hủy:")
            return
        
        count = state['quantity']
        await update.message.reply_text(f"👥 Đang buff {count} followers cho @{username}...")
        success_count = 0
        fake_user_id = str(random.randint(1000000000, 9999999999))
        for i in range(count):
            payload = {"userId": fake_user_id, "type": 1}
            result = send_with_proxy(TIKTOK_FOLLOW_URL, payload, proxy_mgr)
            if result:
                success_count += 1
                if (i+1) % 5 == 0 or i+1 == count:
                    await update.message.reply_text(f"📊 Tiến độ: {i+1}/{count} follow ({success_count} thành công)")
            else:
                await update.message.reply_text(f"⚠️ Follow {i+1} thất bại")
            time.sleep(random.uniform(2.0, 3.5))
        
        await update.message.reply_text(f"✅ Hoàn thành {success_count}/{count} followers")
        state['action'] = None

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in user_states:
        user_states[chat_id]['action'] = None
    await update.message.reply_text("❌ Đã hủy. Gửi /start để bắt đầu lại.")

# ========== KHỞI TẠO PROXY MANAGER TOÀN CỤC ==========
proxy_mgr = ProxyManager(PROXY_LIST)

# ========== MAIN ==========
def main():
    # Load token từ file hoặc dùng mặc định
    token = load_bot_token()
    
    if token == "YOUR_BOT_TOKEN_HERE":
        print("⚠️ CHƯA CẤU HÌNH TOKEN!")
        print("📝 Cách lấy token:")
        print("   1. Vào Telegram tìm @BotFather")
        print("   2. Gửi lệnh /newbot")
        print("   3. Đặt tên bot và username")
        print("   4. Copy token và thay vào BOT_TOKEN trong code")
        print("   Hoặc tạo file bot_config.json với nội dung:")
        print('   {"bot_token": "TOKEN_CUA_BAN"}')
        return
    
    print(f"🚀 Khởi động bot với token: {token[:20]}...")
    print(f"📡 Proxy Việt Nam: {len(PROXY_LIST)} proxy")
    
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Bot đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()