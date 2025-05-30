import re
import io
from contextlib import redirect_stdout
import urllib.parse
from flask import Flask
import threading

from balethon import Client
import youtube_tools
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = Client(TOKEN)

app = Flask(__name__)

@app.route('/')
def index():
    return "ربات تلگرام فعال است."


YOUTUBE_URL_REGEX = re.compile(
    r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]+"
)

ANSI_LINK_RE = re.compile(
    r'\x1b\]8;;(?P<url>.*?)\x07(?P<text>.*?)\x1b\]8;;\x07'
)

def run_bot():
    bot.run()

def parse_sections(raw: str):
   
    parts = re.split(r'(?m)^(🎥 فقط ویدیو:|🔊 فقط صدا:|📜 زیرنویس‌ها:)$', raw)
    sections = {}
    for i in range(1, len(parts), 2):
        sections[parts[i].strip()] = parts[i+1].strip()
    return sections
    
def extract_buttons(section_text: str):
    buttons = []
    for m in ANSI_LINK_RE.finditer(section_text):
        text = m.group('text')
        url  = m.group('url')
        buttons.append([{"text": text, "url": url}])
    return buttons

@bot.on_message()
async def handle(message):
    txt = message.text or ""
    if not YOUTUBE_URL_REGEX.search(txt):
        return await message.reply("لطفاً یک لینک ویدیوی YouTube ارسال کن.")

    processing_message = await message.reply("⏳ در حال دریافت و پردازش اطلاعات ویدیو…")

    try:
        info = youtube_tools.get_video_info(txt)
        if not info:
            return await processing_message.edit_text("❌ اطلاعات ویدیوی معتبر یافت نشد.")

        title   = info.get("title","N/A")
        channel = info.get("channel") or info.get("uploader","N/A")
        dur_str = info.get("duration_string") or ""
        if not dur_str and isinstance(info.get("duration"), (int, float)):
            t = int(info["duration"])
            h, r = divmod(t, 3600)
            m, s = divmod(r, 60)
            dur_str = f"{h:02}:{m:02}:{s:02}"
        view = info.get("view_count",0)
        up   = info.get("upload_date","")
        header = (
            f"🎬 عنوان: {title}\n"
            f"📺 کانال: {channel}\n"
            f"⏱ مدت زمان: {dur_str or 'N/A'}\n"
            f"👁 تعداد بازدید: {view:,}\n"
            f"📅 تاریخ آپلود: {up[:4]+'/'+up[4:6]+'/'+up[6:] if len(up)==8 else 'N/A'}"
        )
        await processing_message.edit_text(header)

        buf = io.StringIO()
        with redirect_stdout(buf):
            youtube_tools.list_formats(info)
        raw = buf.getvalue().strip()
        
        if not raw:
            await message.reply("❌ فرمت‌های قابل دانلودی یافت نشد.")
            return

        sections = parse_sections(raw)
        order = ["🎥 فقط ویدیو:", "🔊 فقط صدا:"]

        any_button_sent = False
        for section_title in order:
            body = sections.get(section_title, "")
            if not body:
                continue
            buttons = extract_buttons(body)
            
            if not buttons:
                continue
            
            await bot.send_message(
                chat_id=message.chat.id,
                text=section_title,
                reply_markup={"inline_keyboard": buttons}
            )
            any_button_sent = True
        
        if not any_button_sent:
             await message.reply("هیچ لینک دانلودی (ویدیو/صدا) برای این ویدیو یافت نشد.")

    except Exception as e:
        error_message = f"❌ خطا در پردازش ویدیو"
        if processing_message:
            await processing_message.edit_text(error_message)
        else:
            await message.reply(error_message)
        print(f"Error: {e}")

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    app.run(host='0.0.0.0', port=8000)

