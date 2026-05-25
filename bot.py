"""
MIX DATA SEARCH BOT - Hoàn chỉnh
Chức năng:
- Yêu cầu user reply vào tin nhắn để nhập từ khóa
- Tìm kiếm trên nhiều nguồn dữ liệu (user, product, document, domain)
- Dễ dàng mở rộng thêm nguồn dữ liệu
"""

import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ========== CẤU HÌNH ==========
TOKEN = "8795044675:AAGRfrm-JCpQECIBr4orFy4KVbu-wW1-pmo"  # <--- ĐÃ THAY TOKEN CỦA BẠN
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ========== DỮ LIỆU MẪU ==========
# Bạn có thể thay thế bằng database, API, file, v.v.
MIX_DATA = {
    "user": {
        "alice": "👤 Alice - 25 tuổi - alice@example.com - SĐT: 0901234567",
        "bob": "👤 Bob - 30 tuổi - bob@example.com - SĐT: 0912345678",
        "carol": "👤 Carol - 22 tuổi - carol@example.com - SĐT: 0923456789",
    },
    "product": {
        "laptop": "💻 Laptop Dell XPS - 25,000,000 VND",
        "mouse": "🖱️ Chuột Logitech - 500,000 VND",
        "keyboard": "⌨️ Bàn phím cơ - 1,200,000 VND",
        "gmail.com": "📧 Dịch vụ Gmail của Google - Miễn phí",
        "google.com": "🔍 Google Search Engine",
        "facebook.com": "📱 Facebook - Mạng xã hội",
    },
    "document": {
        "hopdong": "📄 Hợp đồng mẫu số 001 - Tải tại: https://example.com/hopdong.pdf",
        "baogia": "📊 Báo giá dịch vụ 2025 - Xem file đính kèm",
    },
    "domain": {
        "gmail.com": "📧 Email service",
        "google.com": "🔍 Search engine",
        "facebook.com": "📱 Social network",
        "yahoo.com": "📧 Email + News",
        "github.com": "💻 Code hosting",
    }
}

# Lưu message_id của tin nhắn "reply vào đây" theo từng user
user_pending_search = {}

# ========== HÀM HỖ TRỢ ==========
def search_all(keyword: str) -> list:
    """Tìm kiếm từ khóa trong tất cả danh mục, trả về list kết quả"""
    keyword_lower = keyword.lower()
    results = []
    
    for category, data in MIX_DATA.items():
        if keyword_lower in data:
            results.append(f"📁 *{category.upper()}*: {data[keyword_lower]}")
    
    # Tìm kiếm gần đúng (chứa từ khóa, không cần khớp chính xác key)
    for category, data in MIX_DATA.items():
        for key, value in data.items():
            if keyword_lower in key.lower() or keyword_lower in value.lower():
                if f"📁 *{category.upper()}*: {value}" not in results:
                    results.append(f"🔍 *{category.upper()}* (gần đúng): {value}")
    
    if not results:
        results.append(f"❌ Không tìm thấy kết quả nào cho: *{keyword}*")
    
    return results

# ========== HANDLER ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /start - Hiển thị menu chính"""
    keyboard = [
        [InlineKeyboardButton("🔍 TÌM KIẾM (Reply)", callback_data="search_reply")],
        [InlineKeyboardButton("📋 Hướng dẫn", callback_data="help")],
        [InlineKeyboardButton("ℹ️ Thông tin bot", callback_data="info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🤖 *MIX DATA SEARCH BOT*\n\n"
        "Tôi có thể tìm kiếm dữ liệu về:\n"
        "👤 Người dùng | 💻 Sản phẩm | 📄 Tài liệu | 🌐 Domain\n\n"
        "Hãy bấm nút bên dưới để bắt đầu!",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý các nút bấm inline"""
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "search_reply":
        # Gửi tin nhắn yêu cầu reply để nhập keyword
        msg = await query.edit_message_text(
            "🔍 *NHẬP TỪ KHÓA TÌM KIẾM*\n\n"
            "📝 Vui lòng nhập từ khóa cần tìm:\n"
            "Ví dụ: `gmail.com`, `google.com`, `facebook.com`, `laptop`, `alice`\n\n"
            "⚠️ *Mẹo:* Reply tin nhắn này rồi mới ghi keyword",
            parse_mode="Markdown"
        )
        user_pending_search[update.effective_user.id] = msg.message_id
    
    elif data == "help":
        await query.edit_message_text(
            "📋 *HƯỚNG DẪN SỬ DỤNG*\n\n"
            "1️⃣ Bấm nút *'TÌM KIẾM (Reply)'*\n"
            "2️⃣ Bot sẽ gửi tin nhắn mẫu\n"
            "3️⃣ *REPLY* vào tin nhắn đó và nhập từ khóa\n"
            "4️⃣ Bot trả về kết quả tìm kiếm\n\n"
            "🔎 *Từ khóa mẫu:* alice, laptop, gmail.com, hopdong\n\n"
            "📌 Bạn có thể dùng lệnh /search bất cứ lúc nào.",
            parse_mode="Markdown"
        )
    
    elif data == "info":
        await query.edit_message_text(
            "ℹ️ *THÔNG TIN BOT*\n\n"
            "🤖 Tên: MIX DATA SEARCH BOT\n"
            "📦 Phiên bản: 1.0\n"
            "💡 Tính năng: Tìm kiếm hỗn hợp trên nhiều nguồn dữ liệu\n"
            "🛠️ Công nghệ: python-telegram-bot v20\n\n"
            "Gõ /start để quay lại menu.",
            parse_mode="Markdown"
        )

async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /search - Gửi tin nhắn yêu cầu reply (dùng khi không có menu)"""
    msg = await update.message.reply_text(
        "🔍 *NHẬP TỪ KHÓA TÌM KIẾM*\n\n"
        "📝 Vui lòng nhập từ khóa cần tìm:\n"
        "Ví dụ: gmail.com, google.com, facebook.com\n\n"
        "⚠️ *Mẹo:* Reply tin nhắn này rồi mới ghi keyword",
        parse_mode="Markdown"
    )
    user_pending_search[update.effective_user.id] = msg.message_id

async def handle_reply_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý khi user reply vào tin nhắn tìm kiếm"""
    user_id = update.effective_user.id
    
    # Kiểm tra user có đang trong trạng thái chờ tìm kiếm không
    if user_id not in user_pending_search:
        return
    
    # Kiểm tra có reply không và đúng message_id không
    if not update.message.reply_to_message:
        return
    
    replied_msg_id = update.message.reply_to_message.message_id
    if replied_msg_id != user_pending_search[user_id]:
        return
    
    # Lấy từ khóa
    keyword = update.message.text.strip()
    if not keyword:
        await update.message.reply_text("❌ Từ khóa không được để trống. Hãy reply lại tin nhắn và nhập keyword.")
        return
    
    # Xóa trạng thái chờ để tránh xử lý lại
    del user_pending_search[user_id]
    
    # Thông báo đang tìm kiếm
    status_msg = await update.message.reply_text(f"🔍 Đang tìm kiếm từ khóa: *{keyword}*...", parse_mode="Markdown")
    
    # Thực hiện tìm kiếm
    results = search_all(keyword)
    
    # Xóa tin nhắn trạng thái và gửi kết quả
    await status_msg.delete()
    
    if len("\n".join(results)) > 4000:
        # Nếu kết quả quá dài, chia nhỏ
        for i in range(0, len(results), 5):
            chunk = "\n".join(results[i:i+5])
            await update.message.reply_text(chunk, parse_mode="Markdown")
    else:
        await update.message.reply_text("\n\n".join(results), parse_mode="Markdown")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý tin nhắn không xác định"""
    await update.message.reply_text(
        "❓ Tôi không hiểu lệnh đó.\n"
        "Hãy gõ /start để xem menu hoặc /search để tìm kiếm."
    )

# ========== MAIN ==========
def main():
    """Khởi chạy bot"""
    print("🚀 MIX DATA SEARCH BOT đang khởi động...")
    
    app = Application.builder().token(TOKEN).build()
    
    # Thêm handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", cmd_search))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply_search))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))  # bắt lệnh không hợp lệ
    
    print("✅ Bot đã sẵn sàng! Nhấn Ctrl+C để dừng.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()