import os
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

# User အလိုက် အပိုင်းအလိုက် စာရင်းများ သိမ်းဆည်းရန်
# Structure: { user_id: { 'batches': [ {cat: val}, {cat: val} ], 'current': {cat: val} } }
user_store = {}

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

def init_user(user_id):
    if user_id not in user_store:
        user_store[user_id] = {
            'batches': [],
            'current': {cat: 0 for cat in CATEGORIES}
        }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_store[user_id] = {
        'batches': [],
        'current': {cat: 0 for cat in CATEGORIES}
    }
    msg = (
        "👋 **စနစ်သစ်မှ ကြိုဆိုပါတယ်။**\n\n"
        "📌 **အသုံးပြုနည်း လမ်းညွှန်:**\n"
        "1. စာရင်းများ Forward လုပ်ပါ -> **/total** ရိုက်လျှင် လက်ရှိသုတ် စုစုပေါင်းကို ပြပါမည်။\n"
        "2. စာရင်းပိတ်ချင်လျှင် **`----`** (မျဉ်းတား) ပို့ပါ -> နောက်ထပ် အသစ်များကို သီးသန့် ပြန်ပေါင်းပါမည်။\n"
        "3. အပိုင်းအားလုံး၏ စုစုပေါင်း ပေါင်းလဒ် ကြည့်ချင်ပါက **/grand** (သို့) **/all** ဟု ရိုက်ပါ။\n"
        "4. စာရင်းအားလုံး အစမှ ပြန်ဖျက်လိုပါက **/clear** ဟု ရိုက်ပါ။"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def clear_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_store[user_id] = {
        'batches': [],
        'current': {cat: 0 for cat in CATEGORIES}
    }
    await update.message.reply_text("🔄 **စာရင်း အားလုံး (အဟောင်းရော အသစ်ပါ) ရှင်းထုတ်လိုက်ပါပြီ။**", parse_mode='Markdown')

# လက်ရှိ အပိုင်း (Current Batch) ရဲ့ Total ကို ပြရန်
async def show_total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    init_user(user_id)

    curr = user_store[user_id]['current']
    batch_num = len(user_store[user_id]['batches']) + 1

    response_text = f"📊 **အပိုင်း ({batch_num}) စုစုပေါင်း (TOTAL SUMMARY)**\n\n"
    for cat in CATEGORIES:
        response_text += f"{cat}：{curr[cat]}\n"
    
    await update.message.reply_text(response_text, parse_mode='Markdown')

# အပိုင်း အားလုံး (1 + 2 + ...) စုစုပေါင်း ပေါင်းလဒ် ကြည့်ရန်
async def show_grand_total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    init_user(user_id)

    # Batches အားလုံး + Current ကို ပေါင်းမည်
    grand_totals = {cat: 0 for cat in CATEGORIES}
    
    all_batches = user_store[user_id]['batches'] + [user_store[user_id]['current']]
    
    for b in all_batches:
        for cat in CATEGORIES:
            grand_totals[cat] += b[cat]

    total_sections = len(all_batches)
    response_text = f"🏆 **အပိုင်း (၁ မှ {total_sections} အထိ) စုစုပေါင်း ပေါင်းလဒ် (GRAND TOTAL)**\n\n"
    for cat in CATEGORIES:
        response_text += f"{cat}：{grand_totals[cat]}\n"
    
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
    init_user(user_id)

    text = update.message.text
    if not text:
        return

    # မင်း မျဉ်းတားလိုက်တာ (--- သို့မဟုတ် === ) စစ်ဆေးခြင်း
    if re.match(r'^[-=_]{3,}$', text.strip()):
        # လက်ရှိ အပိုင်းကို သိမ်းပြီး အသစ်ပြန်စမည်
        user_store[user_id]['batches'].append(user_store[user_id]['current'])
        user_store[user_id]['current'] = {cat: 0 for cat in CATEGORIES}
        
        batch_count = len(user_store[user_id]['batches'])
        await update.message.reply_text(
            f"🛑 **အပိုင်း ({batch_count}) စာရင်း ပိတ်လိုက်ပါပြီ!**\n"
            f"ယခုမှစ၍ ပို့သမျှ စာရင်းများကို အပိုင်း ({batch_count + 1}) အဖြစ် အသစ်သီးသန့် ပေါင်းပေးပါမည်။", 
            parse_mode='Markdown'
        )
        return

    # ပုံမှန် စာရင်းများ ဖတ်ရှု ပေါင်းထည့်ခြင်း
    found_any = False
    lines = text.split('\n')
    
    for line in lines:
        for cat in CATEGORIES:
            if cat in line:
                val = parse_line_value(line)
                user_store[user_id]['current'][cat] += val
                found_any = True

    if found_any:
        await update.message.reply_text("✅ ပေါင်းထည့်လိုက်ပါပြီ။", parse_mode='Markdown')

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN မရှိပါ။")
        exit(1)

    Thread(target=run_web_server, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear_data))
    app.add_handler(CommandHandler("reset", clear_data))
    app.add_handler(CommandHandler("total", show_total))
    app.add_handler(CommandHandler("grand", show_grand_total))
    app.add_handler(CommandHandler("all", show_grand_total))
    
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), process_message))
    
    print("Bot 💡 စတင် အလုပ်လုပ်နေပါပြီ...")
    app.run_polling()
