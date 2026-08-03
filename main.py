import os
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

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
    msg = (
        "👋 **မင်္ဂလာပါ! စာရင်းတွက်ချက်ပေးမည့် Bot မှ ကြိုဆိုပါတယ်။**\n\n"
        "စာရင်းများကို Forward လုပ်၍ ပို့ပေးပါ။\n"
        "• Message တစ်ခုချင်းစီကို သီးသန့် ပေါင်းပေးမည်ဖြစ်ပါသည်။\n"
        "• မျဉ်းတား (`---`) ပါပါက မျဉ်းအထက်နှင့် အောက်ကို သီးသန့် ခွဲတွက်ပေးပါမည်။"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

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
    text = update.message.text
    if not text:
        return

    blocks = re.split(r'[-=_]{3,}', text)
    results_summary = []

    for idx, block in enumerate(blocks):
        block_totals = {cat: 0 for cat in CATEGORIES}
        found_any = False
        lines = block.split('\n')
        
        for line in lines:
            for cat in CATEGORIES:
                if cat in line:
                    val = parse_line_value(line)
                    block_totals[cat] += val
                    found_any = True

        if found_any:
            summary_str = ""
            if len(blocks) > 1:
                summary_str += f"📍 **အပိုင်း ({idx + 1}) ပေါင်းလဒ်**\n"
            else:
                summary_str += "✅ **ပေါင်းလဒ် စုစုပေါင်း (Total Summary)**\n"
                
            for cat in CATEGORIES:
                summary_str += f"{cat}：{block_totals[cat]}\n"
            
            results_summary.append(summary_str)

    if results_summary:
        final_response = "\n-----------------------\n".join(results_summary)
        await update.message.reply_text(final_response, parse_mode='Markdown')

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN မရှိပါ။")
        exit(1)

    Thread(target=run_web_server, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), process_message))
    
    print("Bot 💡 စတင် အလုပ်လုပ်နေပါပြီ...")
    app.run_polling()
