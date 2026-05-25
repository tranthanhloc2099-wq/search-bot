"""
MIX DATA SEARCH BOT PRO - Tự động tìm kiếm đa nguồn
Chức năng:
- Tự động phát hiện loại từ khóa (email, phone, username, domain)
- Tìm kiếm trên nhiều engine (file, API, web)
- Mở rộng dễ dàng
"""

import subprocess
import sys
import importlib
import logging
import os
import re
from typing import List, Dict, Any

# ========== TỰ ĐỘNG CÀI MODULE ==========
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def check_and_install_modules():
    required_modules = ["telegram", "telegram.ext", "requests"]
    for module in required_modules:
        try:
            if module == "telegram.ext":
                importlib.import_module("telegram.ext")
            else:
                importlib.import_module(module)
            print(f"✅ Module {module} đã có sẵn")
        except ImportError:
            print(f"⚠️ Module {module} chưa được cài. Đang tự động cài...")
            try:
                install_package(module if module != "telegram.ext" else "python-telegram-bot==20.7")
                print(f"✅ Đã cài {module} thành công!")
            except Exception as e:
                print(f"❌ Lỗi: {e}")
                sys.exit(1)

print("🔍 Đang kiểm tra module...")
check_and_install_modules()
print("✅ Module sẵn sàng!\n")

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ========== CẤU HÌNH ==========
TOKEN = "8795044675:AAGRfrm-JCpQECIBr4orFy4KVbu-wW1-pmo"
logging.basicConfig(level=logging.INFO)

# ========== CÁC ENGINE TÌM KIẾM ==========

class SearchEngine:
    """Lớp cơ sở cho các engine tìm kiếm"""
    def __init__(self, name: str):
        self.name = name
    
    def search(self, keyword: str) -> List[str]:
        """Trả về list kết quả tìm kiếm"""
        return []

class FileSearchEngine(SearchEngine):
    """Tìm kiếm trong file data.txt"""
    def __init__(self, filepath: str = "data.txt"):
        super().__init__("File TXT")
        self.filepath = filepath
        self._ensure_file()
    
    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write("# data.txt - Mỗi dòng một bản ghi\n")
                f.write("example@gmail.com:password123\n")
                f.write("user@domain.com:pass456\n")
    
    def search(self, keyword: str) -> List[str]:
        if not os.path.exists(self.filepath):
            return []
        results = []
        keyword_lower = keyword.lower()
        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if keyword_lower in line.lower():
                    results.append(line.strip())
        return results

class EmailLookupEngine(SearchEngine):
    """Tìm kiếm thông tin email qua API công khai (ví dụ: Hunter, EmailHippo)"""
    def __init__(self, api_key: str = None):
        super().__init__("Email Lookup")
        self.api_key = api_key  # Cần đăng ký API key thật
    
    def search(self, keyword: str) -> List[str]:
        # Phát hiện email pattern
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', keyword):
            return []
        
        results = []
        # Ví dụ dùng EmailHippo API (cần key thật)
        if self.api_key:
            try:
                # Đây là API giả định, thay bằng endpoint thật
                url = f"https://api.emailhippo.com/v1/verify?email={keyword}&key={self.api_key}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    results.append(f"📧 Email: {keyword}")
                    results.append(f"   Status: {data.get('status', 'unknown')}")
            except:
                pass
        return results

class DomainSearchEngine(SearchEngine):
    """Tìm kiếm domain (whois, DNS)"""
    def __init__(self):
        super().__init__("Domain")
    
    def search(self, keyword: str) -> List[str]:
        # Phát hiện domain pattern
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', keyword):
            return []
        results = []
        # Thực hiện whois lookup (cần cài đặt whois)
        try:
            import subprocess
            result = subprocess.run(['whois', keyword], capture_output=True, text=True, timeout=5)
            lines = result.stdout.split('\n')[:10]  # Lấy 10 dòng đầu
            results.append(f"🌐 Domain: {keyword}")
            results.extend(lines[:5])
        except:
            results.append(f"🌐 Domain: {keyword} - (whois không khả dụng)")
        return results

class UsernameSearchEngine(SearchEngine):
    """Tìm kiếm username trên mạng xã hội công khai"""
    def __init__(self):
        super().__init__("Username")
        self.sites = [
            "https://github.com/{}",
            "https://twitter.com/{}",
            "https://www.instagram.com/{}",
            "https://www.reddit.com/user/{}"
        ]
    
    def search(self, keyword: str) -> List[str]:
        # Username thường không có @ hoặc khoảng trắng
        if ' ' in keyword or '@' in keyword:
            return []
        results = [f"👤 Tìm kiếm username: {keyword}"]
        for site in self.sites:
            url = site.format(keyword)
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    results.append(f"✅ Tồn tại: {url}")
                else:
                    results.append(f"❌ Không tồn tại: {url}")
            except:
                results.append(f"⚠️ Không kiểm tra được: {url}")
        return results

# ========== KHỞI TẠO CÁC ENGINE ==========
engines = [
    FileSearchEngine("data.txt"),
    EmailLookupEngine(),  # Thêm API key nếu có
    DomainSearchEngine(),
    UsernameSearchEngine(),
]

# ========== HÀM TÌM KIẾM CHÍNH ==========
def auto_search(keyword: str) -> Dict[str, List[str]]:
    """Tự động chọn engine phù hợp và tìm kiếm"""
    results = {}
    
    # Phân loại từ khóa
    keyword_lower = keyword.lower()
    
    for engine in engines:
        # Chạy tất cả engine hoặc chỉ engine phù hợp
        engine_results = engine.search(keyword)
        if engine_results:
            results[engine.name] = engine_results
    
    # Nếu không engine nào có kết quả, thử tìm trong file data.txt (luôn có)
    if not results:
        file_engine = FileSearchEngine("data.txt")
        file_results = file_engine.search(keyword)
        if file_results:
            results["File TXT"] = file_results
        else:
            results["Thông báo"] = [f"❌ Không tìm thấy dữ liệu nào cho: {keyword}"]
    
    return results

# ========== TELEGRAM BOT HANDLER ==========
user_pending_search = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 TÌM KIẾM (Reply)", callback_data="search_reply")],
        [InlineKeyboardButton("📊 Danh sách engine", callback_data="engines")],
        [InlineKeyboardButton("ℹ️ Hướng dẫn", callback_data="help")]
    ]
    await update.message.reply_text(
        "🤖 *MIX DATA SEARCH PRO*\n\n"
        "Bot tự động tìm kiếm dữ liệu từ nhiều nguồn:\n"
        "📁 File TXT | 📧 Email | 🌐 Domain | 👤 Username\n\n"
        "Hãy bấm nút bên dưới!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "search_reply":
        msg = await query.edit_message_text(
            "🔍 *NHẬP TỪ KHÓA TÌM KIẾM*\n\n"
            "Reply tin nhắn này và nhập từ khóa.\n"
            "Bot sẽ tự động phát hiện loại dữ liệu và tìm kiếm.\n\n"
            "Ví dụ: `gmail.com`, `alice@gmail.com`, `@username`, `facebook`",
            parse_mode="Markdown"
        )
        user_pending_search[update.effective_user.id] = msg.message_id
    
    elif data == "engines":
        engine_list = "\n".join([f"🔹 {e.name}" for e in engines])
        await query.edit_message_text(
            f"📊 *CÁC ENGINE TÌM KIẾM*\n\n{engine_list}\n\n"
            "Bot sẽ tự động chọn engine phù hợp với từ khóa.",
            parse_mode="Markdown"
        )
    
    elif data == "help":
        await query.edit_message_text(
            "📋 *HƯỚNG DẪN*\n\n"
            "1️⃣ Bấm 'TÌM KIẾM (Reply)'\n"
            "2️⃣ Reply tin nhắn đó và nhập từ khóa\n"
            "3️⃣ Bot tự động tìm kiếm và trả về kết quả\n\n"
            "*Dữ liệu mẫu:*\n"
            "- Email: example@gmail.com\n"
            "- Domain: google.com\n"
            "- Username: githubuser\n\n"
            "💾 File data.txt lưu thủ công để tìm kiếm offline.",
            parse_mode="Markdown"
        )

async def handle_reply_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_pending_search:
        return
    if not update.message.reply_to_message:
        return
    if update.message.reply_to_message.message_id != user_pending_search[user_id]:
        return
    
    keyword = update.message.text.strip()
    if not keyword:
        await update.message.reply_text("❌ Từ khóa không được để trống.")
        return
    
    del user_pending_search[user_id]
    
    status_msg = await update.message.reply_text(f"🔍 Đang tìm kiếm '{keyword}' trên tất cả engine...")
    
    # Thực hiện tìm kiếm
    results_dict = auto_search(keyword)
    
    await status_msg.delete()
    
    # Gửi kết quả
    if not results_dict:
        await update.message.reply_text(f"❌ Không tìm thấy kết quả cho: {keyword}")
        return
    
    for engine_name, engine_results in results_dict.items():
        if engine_results:
            msg = f"📌 *{engine_name}*:\n" + "\n".join(engine_results[:20])  # Giới hạn 20 dòng
            if len(msg) > 4000:
                msg = msg[:4000] + "..."
            await update.message.reply_text(msg, parse_mode="Markdown")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Dùng /start để xem menu.")

# ========== MAIN ==========
def main():
    print("🚀 MIX DATA SEARCH PRO đang khởi động...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply_search))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    print("✅ Bot đã sẵn sàng! Nhấn Ctrl+C để dừng.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()