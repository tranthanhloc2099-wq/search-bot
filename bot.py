"""
MIX DATA SEARCH BOT PRO - Phiên bản ổn định
Đã fix lỗi AttributeError, tương thích python-telegram-bot==20.7
"""

import subprocess
import sys
import importlib
import logging
import os
import re
from typing import List, Dict

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
                if module == "telegram" or module == "telegram.ext":
                    install_package("python-telegram-bot==20.7")
                else:
                    install_package(module)
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
DATA_FILE = "data.txt"
logging.basicConfig(level=logging.INFO)

# ========== LƯU TRẠNG THÁI USER ==========
user_pending_search = {}

# ========== HÀM ĐỌC DỮ LIỆU TỪ FILE ==========
def load_data():
    """Đọc file data.txt, mỗi dòng là một tài khoản"""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.write("# Mỗi dòng là một tài khoản - ví dụ:\n")
            f.write("alice@gmail.com:password123\n")
            f.write("bob@yahoo.com:bob456\n")
            f.write("carol@facebook.com:carol789\n")
            f.write("example@gmail.com:123456\n")
            f.write("admin@system.local:admin888\n")
        print(f"✅ Đã tạo file {DATA_FILE} mẫu")
        return []
    
    with open(DATA_FILE, "r", encoding="utf-8", errors="ignore") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    print(f"📂 Đã đọc {len(lines)} dòng dữ liệu từ {DATA_FILE}")
    return lines

def search_in_file(keyword: str, data_lines: list) -> list:
    """Tìm kiếm từ khóa trong dữ liệu file"""
    if not data_lines:
        return ["⚠️ Chưa có dữ liệu trong file data.txt"]
    
    keyword_lower = keyword.lower()
    results = []
    
    for line in data_lines:
        if keyword_lower in line.lower():
            results.append(line)
    
    if not results:
        results.append(f"❌ Không tìm thấy dữ liệu nào chứa: {keyword}")
    else:
        results.insert(0, f"✅ Tìm thấy {len(results)} kết quả:\n")
    
    return results

def search_email_online(email: str) -> list:
    """Tìm kiếm thông tin email qua API công khai (kiểm tra định dạng)"""
    results = []
    # Kiểm tra định dạng email hợp lệ
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, email):
        domain = email.split('@')[1]
        results.append(f"📧 Email: {email}")
        results.append(f"   Domain: {domain}")
        results.append(f"   🔍 Gợi ý: Kiểm tra tại https://haveibeenpwned.com")
    return results

def search_domain(domain: str) -> list:
    """Tìm kiếm thông tin domain"""
    domain_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(domain_pattern, domain):
        return [f"🌐 Domain: {domain}", f"   🔍 Tra cứu WHOIS: https://whois.domaintools.com/{domain}"]
    return []

# ========== HÀM TÌM KIẾM TỔNG HỢP ==========
def auto_search(keyword: str) -> Dict[str, list]:
    """Tự động tìm kiếm trên tất cả nguồn"""
    results = {}
    keyword_lower = keyword.lower()
    
    # 1. Tìm trong file data.txt
    data_lines = load_data()
    file_results = search_in_file(keyword_lower, data_lines)
    if file_results:
        results["📁 Dữ liệu từ file"] = file_results
    
    # 2. Kiểm tra nếu là email
    if '@' in keyword:
        email_results = search_email_online(keyword)
        if email_results:
            results["📧 Email lookup"] = email_results
    
    # 3. Kiểm tra nếu là domain
    if '.' in keyword and not '@' in keyword:
        domain_results = search_domain(keyword)
        if domain_results:
            results["🌐 Domain info"] = domain_results
    
    # 4. Nếu không có kết quả nào
    if not results:
        results["ℹ️ Thông báo"] = [f"❌ Không tìm thấy dữ liệu cho: {keyword}", 
                                   f"💡 Hãy thêm dữ liệu vào file {DATA_FILE}"]
    
    return results

# ========== TELEGRAM HANDLERS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /start"""
    keyboard = [
        [InlineKeyboardButton("🔍 TÌM KIẾM (Reply)", callback_data="search_reply")],
        [InlineKeyboardButton("📊 Thống kê data", callback_data="stats")],
        [InlineKeyboardButton("📋 Hướng dẫn", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🤖 *MIX DATA SEARCH BOT*\n\n"
        "Bot tìm kiếm dữ liệu trong file data.txt\n"
        "Hỗ trợ tìm kiếm email, domain, username\n\n"
        "Hãy bấm nút bên dưới để bắt đầu!",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý nút bấm"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "search_reply":
        msg = await query.edit_message_text(
            "🔍 *NHẬP TỪ KHÓA TÌM KIẾM*\n\n"
            "📝 Reply tin nhắn này và nhập từ khóa cần tìm.\n\n"
            "Ví dụ: `gmail.com`, `alice@gmail.com`, `facebook`\n\n"
            "⚠️ Mẹo: Reply tin nhắn này rồi mới ghi keyword",
            parse_mode="Markdown"
        )
        user_pending_search[update.effective_user.id] = msg.message_id
    
    elif query.data == "stats":
        data_lines = load_data()
        await query.edit_message_text(
            f"📊 *THỐNG KÊ DỮ LIỆU*\n\n"
            f"📁 File: {DATA_FILE}\n"
            f"📝 Tổng số dòng: {len(data_lines)}\n\n"
            f"💡 Gợi ý: Thêm dữ liệu vào file data.txt để tìm kiếm.",
            parse_mode="Markdown"
        )
    
    elif query.data == "help":
        await query.edit_message_text(
            "📋 *HƯỚNG DẪN SỬ DỤNG*\n\n"
            "1️⃣ Bấm nút 'TÌM KIẾM (Reply)'\n"
            "2️⃣ Bot gửi tin nhắn mẫu\n"
            "3️⃣ *REPLY* vào tin nhắn đó và nhập từ khóa\n"
            "4️⃣ Bot trả về kết quả tìm kiếm\n\n"
            "🔎 *Các từ khóa mẫu:*\n"
            "- Tìm email: alice@gmail.com\n"
            "- Tìm tên miền: google.com\n"
            "- Tìm thông thường: password, admin\n\n"
            "📝 Để thêm dữ liệu, sửa file data.txt cùng thư mục với bot.",
            parse_mode="Markdown"
        )

async def handle_reply_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý khi user reply để tìm kiếm"""
    user_id = update.effective_user.id
    
    # Kiểm tra user có đang chờ tìm kiếm không
    if user_id not in user_pending_search:
        return
    
    # Kiểm tra có reply không
    if not update.message.reply_to_message:
        return
    
    # Kiểm tra đúng tin nhắn không
    if update.message.reply_to_message.message_id != user_pending_search[user_id]:
        return
    
    keyword = update.message.text.strip()
    if not keyword:
        await update.message.reply_text("❌ Từ khóa không được để trống.")
        return
    
    # Xóa trạng thái chờ
    del user_pending_search[user_id]
    
    # Thông báo đang tìm kiếm
    status_msg = await update.message.reply_text(f"🔍 Đang tìm kiếm: *{keyword}*...", parse_mode="Markdown")
    
    # Thực hiện tìm kiếm
    results_dict = auto_search(keyword)
    
    # Xóa tin nhắn trạng thái
    await status_msg.delete()
    
    # Gửi kết quả
    for source, results in results_dict.items():
        result_text = f"*{source}*\n" + "\n".join(results)
        # Giới hạn độ dài tin nhắn
        if len(result_text) > 4000:
            result_text = result_text[:4000] + "..."
        await update.message.reply_text(result_text, parse_mode="Markdown")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh không xác định"""
    await update.message.reply_text(
        "❓ Tôi không hiểu lệnh đó.\n"
        "Hãy gõ /start để xem menu hướng dẫn."
    )

# ========== MAIN ==========
def main():
    """Khởi chạy bot"""
    print("🚀 MIX DATA SEARCH BOT đang khởi động...")
    print(f"📁 Sử dụng file dữ liệu: {DATA_FILE}")
    
    # Tạo file data.txt nếu chưa có
    load_data()
    
    # Khởi tạo ứng dụng
    app = Application.builder().token(TOKEN).build()
    
    # Thêm handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply_search))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    
    print("✅ Bot đã sẵn sàng!")
    print("💡 Bot đang chạy... Nhấn Ctrl+C để dừng.")
    
    # Chạy bot
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()