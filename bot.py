"""
MIX DATA SEARCH BOT - Phiên bản ổn định cho python-telegram-bot 20.x
"""

import os
import re
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ========== CẤU HÌNH ==========
TOKEN = "8795044675:AAGRfrm-JCpQECIBr4orFy4KVbu-wW1-pmo"
DATA_FILE = "data.txt"
logging.basicConfig(level=logging.INFO)

# Lưu trạng thái user
user_pending_search = {}

# ========== HÀM XỬ LÝ DỮ LIỆU ==========
def load_data():
    """Đọc dữ liệu từ file"""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.write("alice@gmail.com:password123\n")
            f.write("bob@yahoo.com:bob456\n")
            f.write("carol@gmail.com:carol789\n")
        return []
    
    with open(DATA_FILE, "r", encoding="utf-8", errors="ignore") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return lines

def search_data(keyword: str):
    """Tìm kiếm từ khóa trong file"""
    lines = load_data()
    keyword_lower = keyword.lower()
    results = [line for line in lines if keyword_lower in line.lower()]
    
    if results:
        return f"✅ Tìm thấy {len(results)} kết quả:\n\n" + "\n".join(results)
    else:
        return f"❌ Không tìm thấy dữ liệu nào chứa: {keyword}"

# ========== TELEGRAM HANDLERS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /start"""
    keyboard = [
        [InlineKeyboardButton("🔍 TÌM KIẾM", callback_data="search")],
        [InlineKeyboardButton("📊 THỐNG KÊ", callback_data="stats")],
        [InlineKeyboardButton("📋 HƯỚNG DẪN", callback_data="help")]
    ]
    await update.message.reply_text(
        "🤖 *MIX DATA SEARCH BOT*\n\n"
        "Bot tìm kiếm dữ liệu trong file data.txt\n"
        "Gõ /start để xem menu\n\n"
        "Bấm nút TÌM KIẾM để bắt đầu!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý nút bấm"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "search":
        msg = await query.edit_message_text(
            "🔍 *NHẬP TỪ KHÓA*\n\n"
            "Hãy **reply** tin nhắn này và nhập từ khóa cần tìm.\n\n"
            "Ví dụ: `gmail.com`, `alice`, `password`",
            parse_mode="Markdown"
        )
        user_pending_search[update.effective_user.id] = msg.message_id
    
    elif query.data == "stats":
        lines = load_data()
        await query.edit_message_text(
            f"📊 *THỐNG KÊ*\n\n"
            f"📁 File: {DATA_FILE}\n"
            f"📝 Tổng số dòng: {len(lines)}\n"
            f"✅ Bot đang hoạt động tốt!",
            parse_mode="Markdown"
        )
    
    elif query.data == "help":
        await query.edit_message_text(
            "📋 *HƯỚNG DẪN*\n\n"
            "1️⃣ Bấm nút TÌM KIẾM\n"
            "2️⃣ **Reply** vào tin nhắn của bot\n"
            "3️⃣ Nhập từ khóa cần tìm\n"
            "4️⃣ Nhận kết quả ngay lập tức\n\n"
            "💡 *Mẹo:* Thêm dữ liệu vào file data.txt để tìm kiếm.",
            parse_mode="Markdown"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý tin nhắn thường (reply)"""
    user_id = update.effective_user.id
    
    # Kiểm tra có đang chờ tìm kiếm không
    if user_id not in user_pending_search:
        return
    
    # Kiểm tra có reply không
    if not update.message.reply_to_message:
        return
    
    # Kiểm tra có đúng tin nhắn không
    if update.message.reply_to_message.message_id != user_pending_search[user_id]:
        return
    
    # Lấy từ khóa
    keyword = update.message.text.strip()
    if not keyword:
        await update.message.reply_text("❌ Vui lòng nhập từ khóa!")
        return
    
    # Xóa trạng thái
    del user_pending_search[user_id]
    
    # Tìm kiếm
    result = search_data(keyword)
    
    # Gửi kết quả
    await update.message.reply_text(result)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh không xác định"""
    await update.message.reply_text(
        "❓ Không hiểu lệnh. Gõ /start để xem menu."
    )

# ========== MAIN ==========
def main():
    """Khởi chạy bot"""
    print("🚀 Bot đang khởi động...")
    
    # Tạo file nếu chưa có
    load_data()
    
    # Tạo app
    app = Application.builder().token(TOKEN).build()
    
    # Thêm handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    
    print("✅ Bot đã sẵn sàng!")
    print("💡 Bot đang chạy...")
    
    # Chạy polling
    app.run_polling()

if __name__ == "__main__":
    main()