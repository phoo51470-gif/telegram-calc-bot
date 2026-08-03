import os
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

# အသုံးပြုသူတစ်ဦးချင်းစီ၏ စာရင်းပေါင်းများကို သိမ်းဆည်းထားရန် Memory
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

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

    def log_message(self, format, *args):
        return

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data_store[user_id] = {cat: 0 for cat in CATEGORIES}
    
    msg = (
        "👋 **မင်္ဂလာပါ! စာရင်းတွက်ချက်ပေးမည့် Bot မှ ကြိုဆိုပါတယ်။**\n\n"
        "စာရင်းများကို အများကြီး Forward လုပ်၍ ပို့ပေးပါ။\n\n"
        "📌 **အသုံးပြုနည်း:**\n"
        "1. စာရင်းများကို Forward လုပ်ပြီး ပို့ပါ။ (Bot က ပေါင်းထားပါလိမ့်မည်)\n"
        "2. ပို့ပြီးပါက စုစုပေါင်း အဖြေကြည့်ရန် **/total** ဟု ရိုက်ပါ။\n"
        "3. စာရင်းအသစ် ပြန်စလိုပါက **/clear** ဟု ရိုက်ပါ။"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

# စာရင်း အားလုံးကို ဖျက်ပြီး အသစ်ပြန်စရန် (/clear သို့မဟုတ် /reset)
async def clear_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data_store[user_id] = {cat: 0 for cat in CATEGORIES}
    await update.message.reply_text("🔄 **စာရင်း အားလုံးကို ဖျက်ပြီးပါပြီ။ စာရင်းအသစ်များ Forward စတင်လုပ်နိုင်ပါပြီ။**", parse_mode='Markdown')

# စုစုပေါင်း အဖြေထုတ်ပေးရန် (/total သို့မဟုတ် /recheck)
async def show_total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data_store:
        user_data_store[user_id] = {cat: 0 for cat in CATEGORIES}

    response_text = "📊 **စုစုပေါင်း စာရင်း ပေါင်းလဒ် (TOTAL SUMMARY)**\n\n"
    for cat in CATEGORIES:
        response_text += f"{cat}：{user_data_store[user_id][cat]}\n"
    
    await update.message.reply_text(response_text, parse_mode='Markdown')

def parse_line_value(line: str) -> int:
    if '=' in line:
        after_equal = line.split('=')[-1]
        numbers = re.findall(r'\d+', after_equal)
        if numbers:
            return int(numbers[0])
    
    minus_match = re.search(r'(\d+)\s*-\s*(\d+)', line)
    if minus_match:
        a, b = int(minus_match.group(1)), int(minus_match.group(2))
        return a - b

    numbers = re.findall(r'\d+', line)
    if numbers:
        return int(numbers[-1])
        
    return 0

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
                val = parse_line_value(line)
                user_data_store[user_id][cat] += val
                found_any = True

    if found_any:
        # Message များစွာ ပို့သည့်အခါ Chat ထဲ စာရှုပ်မနေစေရန် အောက်ပါအတိုင်း အသိပေးချက် သာပြမည်
        await update.message.reply_text("✅ ပေါင်းထည့်လိုက်ပါပြီ။ စာရင်းအားလုံး ပို့ပြီးပါက စုစုပေါင်းကြည့်ရန် **/total** ဟု ရိုက်ပါ။", parse_mode='Markdown')

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN မရှိပါ။")
        exit(1)

    Thread(target=run_web_server, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("clear", clear_data))
    app.add_handler(CommandHandler("reset", clear_data))
    app.add_handler(CommandHandler("total", show_total))
    app.add_handler(CommandHandler("recheck", show_total))
    
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), process_message))
    
    print("Bot 💡 စတင် အလုပ်လုပ်နေပါပြီ...")
    app.run_polling()
