import discord
from discord.ext import commands
import google.generativeai as genai
from flask import Flask
from threading import Thread
import os
import json

# Tạo web server để giữ cho Replit luôn hoạt động
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# API key và token từ biến môi trường Replit
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
AUTHORIZED_USER_ID = 1299386568712392765  # Chỉnh sửa ID người điều khiển bot

# Cấu hình Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash')

# Cấu hình Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Lưu trạng thái theo dõi kênh ---
STATE_FILE = "channels.json"

def load_channels():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_channels():
    with open(STATE_FILE, "w") as f:
        json.dump(monitored_channels, f)

# Danh sách các kênh đang được theo dõi
monitored_channels = load_channels()

@bot.event
async def on_ready():
    print(f"Bot đã đăng nhập với tên {bot.user.name}")

@bot.command()
async def start(ctx, channel_id: int):
    if ctx.author.id != AUTHORIZED_USER_ID:
        await ctx.send("Bạn không dùng được lệnh này.")
        return

    channel = bot.get_channel(channel_id)
    if channel is None:
        await ctx.send("Không tìm thấy kênh")
        return

    monitored_channels[str(channel_id)] = True
    save_channels()
    await ctx.send(f"AI start <#{channel_id}>.")

@bot.command()
async def stop(ctx, channel_id: int):
    if ctx.author.id != AUTHORIZED_USER_ID:
        await ctx.send("Bạn không có quyền sử dụng lệnh này")
        return

    if str(channel_id) in monitored_channels:
        del monitored_channels[str(channel_id)]
        save_channels()
        await ctx.send(f"Đã dừng theo dõi kênh <#{channel_id}>.")
    else:
        await ctx.send("Kênh không được theo dõi.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if str(message.channel.id) in monitored_channels:
        try:
            user_input = message.content
            prompt = f"Hãy trả lời bằng tiếng Việt nếu có thể.\nCâu hỏi: {user_input}"
            response = model.generate_content(prompt)
            if response.text:
                await message.channel.send(response.text)
            else:
                await message.channel.send("Gemini không trả lời được nội dung này.")
        except Exception as e:
            print(f"Lỗi: {e}")
            await message.channel.send("Đã có lỗi xảy ra khi tạo phản hồi.")

    await bot.process_commands(message)

# Giữ Replit luôn hoạt động
keep_alive()

# Khởi động bot
bot.run(DISCORD_TOKEN)