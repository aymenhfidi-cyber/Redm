import telebot
from telebot import types
import json
import os

# ── ⚙️ CONFIGURATION (Your Settings Configured) ───────────────────
BOT_TOKEN = "8660388819:AAHDNVSOCT5h7Ggn7lNXxPFi5lnPQgiEvGc"  
OWNER_IDS = [7367073412, 6676819684]  
# ──────────────────────────────────────────────────────────────────

bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = "database.json"

# تحميل قاعدة البيانات مع دعم نظام اليوزرات الجديد
def load_db():
    if not os.path.exists(DB_FILE):
        default_data = {
            "admins": [],
            "banned": [],
            "codes": {},      
            "winners": [],    
            "users": [],
            "usernames": {}  
        }
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            if "usernames" not in data:
                data["usernames"] = {}
            return data
        except:
            return {"admins": [], "banned": [], "codes": {}, "winners": [], "users": [], "usernames": {}}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def is_admin(user_id):
    db = load_db()
    return user_id in OWNER_IDS or user_id in db["admins"]

# دالة ذكية لتحويل اليوزر نيم أو النص إلى آيدي رقمي صحيح
def resolve_user_id(input_text, db):
    text = input_text.strip()
    if text.startswith('@'):
        username = text[1:].lower()
        if username in db.get("usernames", {}):
            return db["usernames"][username], f"@{username}"
        else:
            return None, "not_found"
    else:
        try:
            uid = int(text)
            name = f"`{uid}`"
            for u, i in db.get("usernames", {}).items():
                if i == uid:
                    name = f"@{u}"
                    break
            return uid, name
        except ValueError:
            return None, "invalid"

# اللوحة الاحترافية مع الإيموجيات وتنسيق الخطوط العريض والمائل
def get_owner_panel():
    db = load_db()
    stats_text = (
        "👑 *SYSTEM DASHBOARD*\n"
        "‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\n"
        "📊 *Current Statistics:*\n"
        f" ├ 🎁 Active Codes: `{len(db['codes'])}`\n"
        f" ├ 🏆 Total Winners: `{len(db['winners'])}`\n"
        f" ├ 👥 Total Users: `{len(db['users'])}`\n"
        f" └ 🚫 Banned Users: `{len(db['banned'])}`\n"
        "________________________\n"
        " _Select an action from the menu below:_"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_create = types.InlineKeyboardButton("➕ Create Code", callback_data="btn_create_code")
    btn_delete = types.InlineKeyboardButton("🗑️ Delete Code", callback_data="btn_delete_code")
    btn_winners = types.InlineKeyboardButton("🏆 Winners List", callback_data="btn_winners")
    btn_prizes = types.InlineKeyboardButton("🎁 Active Prizes", callback_data="btn_prizes")
    btn_ban = types.InlineKeyboardButton("🚫 Ban User", callback_data="btn_ban")
    btn_unban = types.InlineKeyboardButton("✅ Unban User", callback_data="btn_unban")
    btn_manage_admins = types.InlineKeyboardButton("👥 Manage Admins", callback_data="btn_manage_admins")
    btn_refresh = types.InlineKeyboardButton("🔄 Refresh Panel", callback_data="btn_refresh_panel")
    
    markup.add(btn_create, btn_delete)
    markup.add(btn_winners, btn_prizes)
    markup.add(btn_ban, btn_unban)
    markup.add(btn_manage_admins)
    markup.add(btn_refresh)
    
    return stats_text, markup

# أمر البدء /start
@bot.message_handler(commands=['start'])
def start_cmd(message):
    db = load_db()
    user_id = message.from_user.id
    username = message.from_user.username
    
    if username:
        db["usernames"][username.lower()] = user_id
    if user_id not in db["users"]:
        db["users"].append(user_id)
    save_db(db)
    
    if user_id in db["banned"]:
        bot.reply_to(message, "🚫 *Access Denied:* You are permanently banned from this bot.", parse_mode="Markdown")
        return

    if is_admin(user_id):
        text, markup = get_owner_panel()
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(
            message.chat.id, 
            "👋 *Welcome!*\n\nPlease send the correct *Secret Code* to claim your prize instantly.",
            parse_mode="Markdown"
        )

# معالجة الضغط على الأزرار تفاعلياً
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "❌ Unauthorized Access.", show_alert=True)
        return

    # [إصلاح] تصفير عجلة التحميل فوراً لكل الأزرار لمنع التعليق
    bot.answer_callback_query(call.id)
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
        # [إصلاح زر الفائزين] حماية الرسالة من الانكسار بسبب علامات الأندرسكور فاليوزرات
        text = "🏆 *No winners recorded yet.*" if not db["winners"] else "🏆 *List of All Winners:*\n\n" + "\n".join(db["winners"])
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Dashboard", callback_data="btn_refresh_panel"))
        try:
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            # حل بديل نقي في حال فشل الـ Markdown
            clean_text = text.replace("*", "").replace("`", "")
            bot.edit_message_text(clean_text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

    elif call.data == "btn_prizes":
        if not db["codes"]:
            text = "🎁 *No active prizes available at the moment.*"
        else:
            text = "🎁 *Active Codes & Prizes:*\n\n"
            for code, prize in db["codes"].items():
                text += f" • `{code}` ➔ _{prize}_\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Dashboard", callback_data="btn_refresh_panel"))
        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "btn_ban":
        msg = bot.edit_message_text("🚫 *Ban Management*\n\nSend the Telegram *@Username* or *User ID* you want to block:\n\nType `/cancel` to abort.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_ban_user)

    elif call.data == "btn_unban":
        msg = bot.edit_message_text("✅ *Ban Management*\n\nSend the Telegram *@Username* or *User ID* you want to unban:\n\nType `/cancel` to abort.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_unban_user)

    elif call.data == "btn_manage_admins":
        if user_id not in OWNER_IDS:
            bot.answer_callback_query(call.id, "❌ Access Restricted to Primary Owners.", show_alert=True)
            return
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ Add Admin", callback_data="admin_add"), types.InlineKeyboardButton("➖ Remove Admin", callback_data="admin_remove"))
        markup.add(types.InlineKeyboardButton("🔙 Back to Dashboard", callback_data="btn_refresh_panel"))
        bot.edit_message_text("👥 *Admin Management*\n\nSelect an action configuration from below:", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "admin_add":
        msg = bot.edit_message_text("➕ *Promote User*\n\nSend the Telegram *@Username* or *User ID* to add as an Admin:\n\nType `/cancel` to abort.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_add_admin)

    elif call.data == "admin_remove":
        msg = bot.edit_message_text("➖ *Demote User*\n\nSend the Telegram *@Username* or *User ID* to remove from Admins:\n\nType `/cancel` to abort.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_remove_admin)

    elif call.data in ["btn_refresh_panel"]:
        # [إصلاح زر الـ Refresh] منع توقف البوت أو إظهار خطأ إذا لم تتغير الإحصائيات
        try:
            text, markup = get_owner_panel()
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        except Exception:
            pass

# ── معالجة البيانات المدخلة خطوة بخطوة ─────────────────────────────

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
            bot.send_message(message.chat.id, f"🗑 *Deleted:* Code `{code}` was wiped successfully.", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ *Error:* Code not found in the active pool.")
    text, markup = get_owner_panel()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

def process_ban_user(message):
    if message.text == '/cancel': 
        bot.send_message(message.chat.id, "Action cancelled.")
    else:
        db = load_db()
        target_id, name = resolve_user_id(message.text, db)
        if target_id:
            if target_id not in db["banned"]:
                db["banned"].append(target_id)
                save_db(db)
                bot.send_message(message.chat.id, f"🚫 *Banned:* User {name} restricted permanently.", parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, f"This user {name} is already banned.")
        else:
            bot.send_message(message.chat.id, "❌ *Error:* Username not found or input format is invalid. User must start the bot first.")
    text, markup = get_owner_panel()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

def process_unban_user(message):
    if message.text == '/cancel': 
        bot.send_message(message.chat.id, "Action cancelled.")
    else:
        db = load_db()
        target_id, name = resolve_user_id(message.text, db)
        if target_id:
            if target_id in db["banned"]:
                db["banned"].remove(target_id)
                save_db(db)
                bot.send_message(message.chat.id, f"✅ *Restored:* User {name} unbanned successfully.", parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, f"Target user {name} is not currently banned.")
        else:
            bot.send_message(message.chat.id, "❌ *Error:* Username not found or input format is invalid.")
    text, markup = get_owner_panel()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

def process_add_admin(message):
    if message.text == '/cancel': 
        bot.send_message(message.chat.id, "Action cancelled.")
    else:
        db = load_db()
        target_id, name = resolve_user_id(message.text, db)
        if target_id:
            if target_id not in db["admins"]:
                db["admins"].append(target_id)
                save_db(db)
                bot.send_message(message.chat.id, f"👥 *Promotion:* User {name} granted Admin permissions.", parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, f"This user {name} is already an Admin.")
        else:
            bot.send_message(message.chat.id, "❌ *Error:* Username not found. User must start the bot first.")
    text, markup = get_owner_panel()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

def process_remove_admin(message):
    if message.text == '/cancel': 
        bot.send_message(message.chat.id, "Action cancelled.")
    else:
        db = load_db()
        target_id, name = resolve_user_id(message.text, db)
        if target_id:
            if target_id in db["admins"]:
                db["admins"].remove(target_id)
                save_db(db)
                bot.send_message(message.chat.id, f"➖ *Demotion:* Admin permissions revoked for {name}.", parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, f"This user {name} is not an Admin.")
        else:
            bot.send_message(message.chat.id, "❌ *Error:* Username not found or input invalid.")
    text, markup = get_owner_panel()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")


# ── فحص رسائل المستخدمين ومطابقة الأكواد ──────────────────────────

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    db = load_db()
    user_id = message.from_user.id
    username = message.from_user.username
    
    if username:
        db["usernames"][username.lower()] = user_id
        save_db(db)
    
    if user_id in db["banned"]:
        return

    incoming_text = message.text.strip()
    
    if incoming_text in db["codes"]:
        prize = db["codes"][incoming_text]
        user_mention = f"@{username}" if username else str(user_id)
        
        db["winners"].append(f" • {user_mention} ➔ Code: `{incoming_text}`")
        del db["codes"][incoming_text]  
        save_db(db)
        
        bot.reply_to(
            message, 
            f"🎉 *Congratulations! You found a valid code!* 🎉\n\n🔑 Code: `{incoming_text}`\n🎁 Your Reward: *{prize}*",
            parse_mode="Markdown"
        )
        
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
        if not is_admin(user_id):
            bot.reply_to(message, "❌ *Invalid Code:* That answer is incorrect or has already been claimed.", parse_mode="Markdown")

# إقلاع البوت
print("Dashboard system engine initialized with multi-input username resolution...")
bot.infinity_polling()
