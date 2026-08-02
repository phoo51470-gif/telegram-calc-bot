import os
import re
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

user_data_store = {}

CATEGORIES = [
    "总进粉人数",
    "重粉人数",
    "不回复人数",
    "发链接不回复",
    "问电报不回复",
    "异国粉",
    "账户封锁数",
    "已经注册过人数",
    "注册人数",
    "推送电报人数"
]

# Render Free Web Service အလုပ်လုပ်ရန် Dummy Server
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data_store[user_id] = {cat: 0 for cat in CATEGORIES}
    
    msg = (
        "👋 **မင်္ဂလာပါ! စာရင်းတွက်ချက်ပေးမည့် Bot မှ ကြိုဆိုပါတယ်။**\n\n"
        "စာရင်းများကို Forward လုပ်၍ ပို့ပေးပါ။\n\n"
        "📌 **အသုံးပြုနိုင်သော Command များ:**\n"
        "• /recheck - လက်ရှိ ပေါင်းထားသော စာရင်းများကို ပြန်စစ်ရန်\n"
        "• /recalculate - စာရင်းဟောင်းများကို ဖျက်ပြီး အစမှ ပြန်တွက်ရန်\n"
        "• /total - လက်ရှိ ပေါင်းလဒ် စုစုပေါင်းကို ကြည့်ရန်\n"
        "• /help - ကူညီမည့် လမ်းညွှန်ချက်များ ကြည့်ရန်"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def recalculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data_store[user_id] = {cat: 0 for cat in CATEGORIES}
    await update.message.reply_text("🔄 **စာရင်း အားလုံးကို 0 သို့ ပြန်လည် စတင်လိုက်ပါပြီ။**", parse_mode='Markdown')

async def recheck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data_store:
        user_data_store[user_id] = {cat: 0 for cat in CATEGORIES}

    response_text = "📊 **လက်ရှိ စာရင်း စုစုပေါင်း စစ်ဆေးချက် (Recheck Summary)**\n\n"
    for cat in CATEGORIES:
        response_text += f"{cat}：{user_data_store[user_id][cat]}\n"
    
    await update.message.reply_text(response_text, parse_mode='Markdown')

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data_store:
        user_data_store[user_id] = {cat: 0 for cat in CATEGORIES}
    
    text = update.message.text
    if not text:
        return

    found_any = False
    lines = text.split('\n')
    
    for line in lines:
        for cat in CATEGORIES:
            if cat in line:
                numbers = re.findall(r'\d+', line)
                if numbers:
                    val = int(numbers[-1])
                    user_data_store[user_id][cat] += val
                    found_any = True

    if found_any:
        response_text = "✅ **ပေါင်းလဒ် စုစုပေါင်း (Total Summary)**\n\n"
        for cat in CATEGORIES:
            response_text += f"{cat}：{user_data_store[user_id][cat]}\n"
        
        await update.message.reply_text(response_text, parse_mode='Markdown')

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN မရှိပါ။")
        exit(1)

    # Dummy Web Server ကို Background တွင် Run ခိုင်းမည်
    Thread(target=run_dummy_server, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("recalculate", recalculate))
    app.add_handler(CommandHandler("reset", recalculate))
    app.add_handler(CommandHandler("recheck", recheck))
    app.add_handler(CommandHandler("total", recheck))
    
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), process_message))
    
    print("Bot 💡 စတင် အလုပ်လုပ်နေပါပြီ...")
    app.run_polling()
