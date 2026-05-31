"""
MIX DATA SEARCH BOT - Cho Python 3.13+
"""

import os
import re
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ========== CẤU HÌNH ==========
TOKEN = "8659787129:AAFPGVPn7SoXji3wLnrzBWxKyzaVPERAEgk"
DATA_FILE = "data.txt"
logging.basicConfig(level=logging.INFO)

user_pending_search = {}

# ========== HÀM XỬ LÝ ==========
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.write("alice@gmail.com:password123\n")
            f.write("bob@yahoo.com:bob456\n")
            f.write("testuser:testpass\n")
        return []
    
    with open(DATA_FILE, "r", encoding="utf-8", errors="ignore") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return lines

def search_data(keyword: str):
    lines = load_data()
    keyword_lower = keyword.lower()
    results = [line for line in lines if keyword_lower in line.lower()]
    
    if results:
        return f"✅ Tìm thấy {len(results)} kết quả:\n\n" + "\n".join(results[:20])
    else:
        return f"❌ Không tìm thấy dữ liệu nào chứa: {keyword}"

# ========== HANDLERS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 TÌM KIẾM", callback_data="search")],
        [InlineKeyboardButton("📊 THỐNG KÊ", callback_data="stats")],
        [InlineKeyboardButton("📋 HƯỚNG DẪN", callback_data="help")]
    ]
    await update.message.reply_text(
        "🤖 *MIX DATA SEARCH BOT*\n\nBot tìm kiếm trong file data.txt\nBấm nút bên dưới để bắt đầu!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "search":
        msg = await query.edit_message_text(
            "🔍 *NHẬP TỪ KHÓA*\n\nReply tin nhắn này và nhập từ khóa cần tìm.\n\nVí dụ: `gmail.com`, `alice`",
            parse_mode="Markdown"
        )
        user_pending_search[update.effective_user.id] = msg.message_id
    
    elif query.data == "stats":
        lines = load_data()
        await query.edit_message_text(
            f"📊 *THỐNG KÊ*\n\n📁 Tổng số dòng: {len(lines)}\n✅ Bot đang chạy!",
            parse_mode="Markdown"
        )
    
    elif query.data == "help":
        await query.edit_message_text(
            "📋 *HƯỚNG DẪN*\n\n1. Bấm TÌM KIẾM\n2. Reply tin nhắn\n3. Nhập từ khóa\n4. Nhận kết quả",
            parse_mode="Markdown"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_pending_search:
        return
    if not update.message.reply_to_message:
        return
    if update.message.reply_to_message.message_id != user_pending_search[user_id]:
        return
    
    keyword = update.message.text.strip()
    if not keyword:
        await update.message.reply_text("❌ Vui lòng nhập từ khóa!")
        return
    
    del user_pending_search[user_id]
    result = search_data(keyword)
    await update.message.reply_text(result)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Gõ /start để xem menu")

# ========== MAIN ==========
def main():
    print("🚀 Bot đang khởi động...")
    load_data()
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    
    print("✅ Bot đã sẵn sàng!")
    app.run_polling()

if __name__ == "__main__":
    main()