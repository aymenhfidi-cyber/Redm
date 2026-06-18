import telebot
from telebot import types
import json
import os

# ── ⚙️ CONFIGURATION ──────────────────────────────────────────────
BOT_TOKEN = "8660388819:AAHDNVSOCT5h7Ggn7lNXxPFi5lnPQgiEvGc"  # Replace with your Bot Token from @BotFather

# Add the Telegram IDs of both owners here
OWNER_IDS = [7367073412, 6676819684]  
# ──────────────────────────────────────────────────────────────────

bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = "database.json"

# Load database settings cleanly
def load_db():
    if not os.path.exists(DB_FILE):
        default_data = {
            "admins": [],
            "banned": [],
            "codes": {},      
            "winners": [],    
            "users": []       
        }
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return {"admins": [], "banned": [], "codes": {}, "winners": [], "users": []}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def is_admin(user_id):
    db = load_db()
    return user_id in OWNER_IDS or user_id in db["admins"]

# Generate Dashboard Layout matching your exact structural needs
def get_owner_panel():
    db = load_db()
    stats_text = (
        "⚙️ *SYSTEM DASHBOARD*\n"
        "‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\n"
        "📊 *Current Statistics:*\n"
        f" • Active Codes: `{len(db['codes'])}`\n"
        f" • Total Winners: `{len(db['winners'])}`\n"
        f" • Total Users: `{len(db['users'])}`\n"
        f" • Banned Users: `{len(db['banned'])}`\n"
        "________________________\n"
        " _Select an action from the menu below:_"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_create = types.InlineKeyboardButton("Create Code", callback_data="btn_create_code")
    btn_delete = types.InlineKeyboardButton("Delete Code", callback_data="btn_delete_code")
    btn_winners = types.InlineKeyboardButton("Winners List", callback_data="btn_winners")
    btn_prizes = types.InlineKeyboardButton("Active Prizes", callback_data="btn_prizes")
    btn_ban = types.InlineKeyboardButton("Ban User", callback_data="btn_ban")
    btn_unban = types.InlineKeyboardButton("Unban User", callback_data="btn_unban")
    btn_manage_admins = types.InlineKeyboardButton("Manage Admins", callback_data="btn_manage_admins")
    btn_refresh = types.InlineKeyboardButton("Refresh Panel", callback_data="btn_refresh_panel")
    
    markup.add(btn_create, btn_delete)
    markup.add(btn_winners, btn_prizes)
    markup.add(btn_ban, btn_unban)
    markup.add(btn_manage_admins)
    markup.add(btn_refresh)
    
    return stats_text, markup

# Command /start handler
@bot.message_handler(commands=['start'])
def start_cmd(message):
    db = load_db()
    user_id = message.from_user.id
    
    if user_id in db["banned"]:
        bot.reply_to(message, "*Access Denied:* You are permanently banned from this bot.", parse_mode="Markdown")
        return

    if user_id not in db["users"]:
        db["users"].append(user_id)
        save_db(db)

    if is_admin(user_id):
        text, markup = get_owner_panel()
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(
            message.chat.id, 
            "👋 *Welcome!*\n\nPlease send the correct *Secret Code* to claim your prize instantly.",
            parse_mode="Markdown"
        )

# Intercepting button clicks
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "Unauthorized Access.", show_alert=True)
        return

    db = load_db()

    if call.data == "btn_create_code":
        msg = bot.edit_message_text(
            "📝 *Create New Reward*\n\nSend the code and prize using this format:\n`CODE REWARD_TEXT`\n\n_Example: VIP2026 Premium Account_\n\nType `/cancel` to abort.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, process_create_code)

    elif call.data == "btn_delete_code":
        if not db["codes"]:
            bot.answer_callback_query(call.id, "There are no active codes available to delete.", show_alert=True)
            return
        msg = bot.edit_message_text("🗑 *Delete Code*\n\nSend the exact code you want to remove from the system:\n\nType `/cancel` to abort.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_delete_code)

    elif call.data == "btn_winners":
        text = "🏆 *No winners recorded yet.*" if not db["winners"] else "🏆 *List of All Winners:*\n\n" + "\n".join(db["winners"])
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Back to Dashboard", callback_data="btn_refresh_panel"))
        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "btn_prizes":
        if not db["codes"]:
            text = "🎁 *No active prizes available at the moment.*"
        else:
            text = "🎁 *Active Codes & Prizes:*\n\n"
            for code, prize in db["codes"].items():
                text += f"• `{code}` ➔ _{prize}_\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Back to Dashboard", callback_data="btn_refresh_panel"))
        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "btn_ban":
        msg = bot.edit_message_text("🚫 *Ban Management*\n\nSend the Telegram User ID you want to block:\n\nType `/cancel` to abort.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_ban_user)

    elif call.data == "btn_unban":
        msg = bot.edit_message_text("✅ *Ban Management*\n\nSend the Telegram User ID you want to unban:\n\nType `/cancel` to abort.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_unban_user)

    elif call.data == "btn_manage_admins":
        if user_id not in OWNER_IDS:
            bot.answer_callback_query(call.id, "Access Restricted to Primary Owners.", show_alert=True)
            return
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Add Admin", callback_data="admin_add"), types.InlineKeyboardButton("Remove Admin", callback_data="admin_remove"))
        markup.add(types.InlineKeyboardButton("Back to Dashboard", callback_data="btn_refresh_panel"))
        bot.edit_message_text("👥 *Admin Management*\nSelect an action configuration:", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "admin_add":
        msg = bot.edit_message_text("📝 *Promote User*\n\nSend the Telegram User ID to add as an Admin:\n\nType `/cancel` to abort.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_add_admin)

    elif call.data == "admin_remove":
        msg = bot.edit_message_text("📝 *Demote User*\n\nSend the Telegram User ID to remove from Admins:\n\nType `/cancel` to abort.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_remove_admin)

    elif call.data in ["btn_refresh_panel"]:
        text, markup = get_owner_panel()
        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")

# ── SEQUENTIAL INPUT STEP HANDLERS ───────────────────────────────

def process_create_code(message):
    if message.text == '/cancel': 
        bot.send_message(message.chat.id, "Action cancelled.")
    else:
        try:
            parts = message.text.split(' ', 1)
            if len(parts) < 2:
                bot.reply_to(message, "❌ *Syntax Error:* Please write the code, then a space, followed by the prize content.", parse_mode="Markdown")
                return
            code, prize = parts[0], parts[1]
            db = load_db()
            db["codes"][code] = prize
            save_db(db)
            bot.send_message(message.chat.id, f"✅ *Success:* New item configuration saved.\n🔑 Code: `{code}`\n🎁 Prize: _{prize}_", parse_mode="Markdown")
        except:
            bot.reply_to(message, "An unexpected error occurred.")
    text, markup = get_owner_panel()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

def process_delete_code(message):
    if message.text == '/cancel': 
        bot.send_message(message.chat.id, "Action cancelled.")
    else:
        db = load_db()
        code = message.text.strip()
        if code in db["codes"]:
            del db["codes"][code]
            save_db(db)
            bot.send_message(message.chat.id, f"🗑 *Deleted:* Code `{code}` was wiped from the database successfully.", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ *Error:* Code not found in the active pool.")
    text, markup = get_owner_panel()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

def process_ban_user(message):
    if message.text == '/cancel': 
        bot.send_message(message.chat.id, "Action cancelled.")
    else:
        try:
            target_id = int(message.text.strip())
            db = load_db()
            if target_id not in db["banned"]:
                db["banned"].append(target_id)
                save_db(db)
                bot.send_message(message.chat.id, f"🚫 *Banned:* User ID `{target_id}` restricted permanently.", parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, "This user is already banned.")
        except:
            bot.send_message(message.chat.id, "❌ *Invalid Input:* Please provide a valid numerical User ID.")
    text, markup = get_owner_panel()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

def process_unban_user(message):
    if message.text == '/cancel': 
        bot.send_message(message.chat.id, "Action cancelled.")
    else:
        try:
            target_id = int(message.text.strip())
            db = load_db()
            if target_id in db["banned"]:
                db["banned"].remove(target_id)
                save_db(db)
                bot.send_message(message.chat.id, f"✅ *Restored:* User ID `{target_id}` unbanned successfully.", parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, "Target user is not currently banned.")
        except:
            bot.send_message(message.chat.id, "❌ *Invalid Input:* Please provide a valid numerical User ID.")
    text, markup = get_owner_panel()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

def process_add_admin(message):
    if message.text == '/cancel': 
        bot.send_message(message.chat.id, "Action cancelled.")
    else:
        try:
            target_id = int(message.text.strip())
            db = load_db()
            if target_id not in db["admins"]:
                db["admins"].append(target_id)
                save_db(db)
                bot.send_message(message.chat.id, f"👥 *Promotion:* User `{target_id}` granted Admin permissions.", parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, "This user is already an Admin.")
        except:
            bot.send_message(message.chat.id, "❌ *Invalid Input:* Please provide a valid numerical User ID.")
    text, markup = get_owner_panel()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

def process_remove_admin(message):
    if message.text == '/cancel': 
        bot.send_message(message.chat.id, "Action cancelled.")
    else:
        try:
            target_id = int(message.text.strip())
            db = load_db()
            if target_id in db["admins"]:
                db["admins"].remove(target_id)
                save_db(db)
                bot.send_message(message.chat.id, f"➖ *Demotion:* Admin permissions revoked for `{target_id}`.", parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, "This user is not an Admin.")
        except:
            bot.send_message(message.chat.id, "❌ *Invalid Input:* Please provide a valid numerical User ID.")
    text, markup = get_owner_panel()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")


# ── INCOMING MESSAGES HANDLER (REDEEM CODES) ─────────────────────

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    db = load_db()
    user_id = message.from_user.id
    
    if user_id in db["banned"]:
        return

    incoming_text = message.text.strip()
    
    # Check if text matches any active code
    if incoming_text in db["codes"]:
        prize = db["codes"][incoming_text]
        user_mention = f"@{message.from_user.username}" if message.from_user.username else str(user_id)
        
        # Save winner structure safely
        db["winners"].append(f"• {user_mention} ➔ Code: `{incoming_text}`")
        del db["codes"][incoming_text]  # Instantly delete to prevent duplication
        save_db(db)
        
        bot.reply_to(
            message, 
            f"🎉 *Congratulations! You found a valid code!* 🎉\n\n🔑 Code: `{incoming_text}`\n🎁 Your Reward: *{prize}*",
            parse_mode="Markdown"
        )
        
        # Notify all specified Owners immediately
        for owner_id in OWNER_IDS:
            try:
                bot.send_message(
                    owner_id,
                    f"🔔 *New Key Claimed!*\n\n👤 Winner: {user_mention} (`{user_id}`)\n🔑 Code: `{incoming_text}`\n🎁 Reward Sent: *{prize}*",
                    parse_mode="Markdown"
                )
            except:
                pass
    else:
        # Ignore input if text sent belongs to admins interacting with system commands
        if not is_admin(user_id):
            bot.reply_to(message, "❌ *Invalid Code:* That answer is incorrect or has already been claimed.")

# Polling loop initialization
print("Professional system engine initialized...")
bot.infinity_polling()
