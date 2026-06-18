import telebot
from telebot import types
import json
import os

# ── ⚙️ CONFIGURATION (Your Settings Configured) ───────────────────
BOT_TOKEN = "8603010807:AAG2NITIY4CwDZDzDvtZ1c1W7E7rVcor5Qg"  
OWNER_IDS = [7826341576, 6676819684]  
# ──────────────────────────────────────────────────────────────────

bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = "database.json"

# تحميل قاعدة البيانات بأمان
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

# تحويل اليوزر نيم أو النص إلى آيدي رقمي صحيح
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
            name = f"<code>{uid}</code>"
            for u, i in db.get("usernames", {}).items():
                if i == uid:
                    name = f"@{u}"
                    break
            return uid, name
        except ValueError:
            return None, "invalid"

# لوحة التحكم الاحترافية بنظام HTML المستقر
def get_owner_panel():
    db = load_db()
    stats_text = (
        "👑 <b>SYSTEM DASHBOARD</b>\n"
        "‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\n"
        "📊 <b>Current Statistics:</b>\n"
        f" ├ 🎁 Active Codes: <code>{len(db['codes'])}</code>\n"
        f" ├ 🏆 Total Winners: <code>{len(db['winners'])}</code>\n"
        f" ├ 👥 Total Users: <code>{len(db['users'])}</code>\n"
        f" └ 🚫 Banned Users: <code>{len(db['banned'])}</code>\n"
        "________________________\n"
        " <i>Select an action from the menu below:</i>"
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

# أمر التشغيل /start
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
        bot.reply_to(message, "🚫 <b>Access Denied:</b> You are permanently banned from this bot.", parse_mode="HTML")
        return

    if is_admin(user_id):
        text, markup = get_owner_panel()
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    else:
        bot.send_message(
            message.chat.id, 
            "👋 <b>Welcome!</b>\n\nPlease send the correct <b>Secret Code</b> to claim your prize instantly.",
            parse_mode="HTML"
        )

# معالجة الضغط التفاعلي على الأزرار ومنع التعليق
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "❌ Unauthorized Access.", show_alert=True)
        return

    db = load_db()

    if call.data == "btn_create_code":
        bot.answer_callback_query(call.id)
        msg = bot.edit_message_text(
            "📝 <b>Create New Reward</b>\n\nSend the code and prize using this format:\n<code>CODE REWARD_TEXT</code>\n\n<i>Example: VIP2026 Premium Account</i>\n\nType <code>/cancel</code> to abort.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_create_code)

    elif call.data == "btn_delete_code":
        bot.answer_callback_query(call.id)
        if not db["codes"]:
            bot.answer_callback_query(call.id, "There are no active codes available to delete.", show_alert=True)
            return
        msg = bot.edit_message_text("🗑 <b>Delete Code</b>\n\nSend the exact code you want to remove from the system:\n\nType <code>/cancel</code> to abort.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler(msg, process_delete_code)

    elif call.data == "btn_winners":
        # حل مشكلة قائمة الفائزين نهائياً عبر إنهاء عجلة التحميل فوراً وعرض النص الآمن
        bot.answer_callback_query(call.id)
        text = "🏆 <b>No winners recorded yet.</b>" if not db["winners"] else "🏆 <b>List of All Winners:</b>\n\n" + "\n".join(db["winners"])
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Dashboard", callback_data="btn_refresh_panel"))
        try:
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=markup)
        except Exception:
            bot.edit_message_text("🏆 <b>Winners List (Safe Mode):</b>\n\n" + "\n".join(db["winners"]), chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

    elif call.data == "btn_prizes":
        bot.answer_callback_query(call.id)
        if not db["codes"]:
            text = "🎁 <b>No active prizes available at the moment.</b>"
        else:
            text = "🎁 <b>Active Codes & Prizes:</b>\n\n"
            for code, prize in db["codes"].items():
                text += f" • <code>{code}</code> ➔ <i>{prize}</i>\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Dashboard", callback_data="btn_refresh_panel"))
        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=markup)

    elif call.data == "btn_ban":
        bot.answer_callback_query(call.id)
        msg = bot.edit_message_text("🚫 <b>Ban Management</b>\n\nSend the Telegram <b>@Username</b> or <b>User ID</b> you want to block:\n\nType <code>/cancel</code> to abort.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler(msg, process_ban_user)

    elif call.data == "btn_unban":
        bot.answer_callback_query(call.id)
        msg = bot.edit_message_text("✅ <b>Ban Management</b>\n\nSend the Telegram <b>@Username</b> or <b>User ID</b> you want to unban:\n\nType <code>/cancel</code> to abort.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler(msg, process_unban_user)

    elif call.data == "btn_manage_admins":
        bot.answer_callback_query(call.id)
        if user_id not in OWNER_IDS:
            bot.answer_callback_query(call.id, "❌ Access Restricted to Primary Owners.", show_alert=True)
            return
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ Add Admin", callback_data="admin_add"), types.InlineKeyboardButton("➖ Remove Admin", callback_data="admin_remove"))
        markup.add(types.InlineKeyboardButton("🔙 Back to Dashboard", callback_data="btn_refresh_panel"))
        bot.edit_message_text("👥 <b>Admin Management</b>\n\nSelect an action configuration from below:", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=markup)

    elif call.data == "admin_add":
        bot.answer_callback_query(call.id)
        msg = bot.edit_message_text("➕ <b>Promote User</b>\n\nSend the Telegram <b>@Username</b> or <b>User ID</b> to add as an Admin:\n\nType <code>/cancel</code> to abort.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler(msg, process_add_admin)

    elif call.data == "admin_remove":
        bot.answer_callback_query(call.id)
        msg = bot.edit_message_text("➖ <b>Demote User</b>\n\nSend the Telegram <b>@Username</b> or <b>User ID</b> to remove from Admins:\n\nType <code>/cancel</code> to abort.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler(msg, process_remove_admin)

    elif call.data in ["btn_refresh_panel"]:
        # حل مشكلة تعليق زر الـ Refresh نهائياً عبر إرسال إشعار علوي للمستخدم يوضح حالة التحديث
        try:
            text, markup = get_owner_panel()
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")
            bot.answer_callback_query(call.id, text="🔄 Dashboard updated!", show_alert=False)
        except telebot.apihelper.ApiTelegramException as e:
            if "message is not modified" in e.description.lower():
                bot.answer_callback_query(call.id, text="🔄 Dashboard is already up-to-date!", show_alert=False)
            else:
                bot.answer_callback_query(call.id, text="⚠️ Refresh Error.", show_alert=True)

# ── معالجة البيانات المدخلة خطوة بخطوة ─────────────────────────────

def process_create_code(message):
    if message.text == '/cancel': 
        bot.send_message(message.chat.id, "Action cancelled.")
    else:
        try:
            parts = message.text.split(' ', 1)
            if len(parts) < 2:
                bot.reply_to(message, "❌ <b>Syntax Error:</b> Please write the code, then a space, followed by the prize content.", parse_mode="HTML")
                return
            code, prize = parts[0], parts[1]
            db = load_db()
            db["codes"][code] = prize
            save_db(db)
            bot.send_message(message.chat.id, f"✅ <b>Success:</b> New item configuration saved.\n🔑 Code: <code>{code}</code>\n🎁 Prize: <i>{prize}</i>", parse_mode="HTML")
        except:
            bot.reply_to(message, "An unexpected error occurred.")
    text, markup = get_owner_panel()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

def process_delete_code(message):
    if message.text == '/cancel': 
        bot.send_message(message.chat.id, "Action cancelled.")
    else:
        db = load_db()
        code = message.text.strip()
        if code in db["codes"]:
            del db["codes"][code]
            save_db(db)
            bot.send_message(message.chat.id, f"🗑 <b>Deleted:</b> Code <code>{code}</code> was wiped successfully.", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "❌ <b>Error:</b> Code not found in the active pool.")
    text, markup = get_owner_panel()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

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
                bot.send_message(message.chat.id, f"🚫 <b>Banned:</b> User {name} restricted permanently.", parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, f"This user {name} is already banned.")
        else:
            bot.send_message(message.chat.id, "❌ <b>Error:</b> Username not found. User must start the bot first.")
    text, markup = get_owner_panel()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

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
                bot.send_message(message.chat.id, f"✅ <b>Restored:</b> User {name} unbanned successfully.", parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, f"Target user {name} is not currently banned.")
        else:
            bot.send_message(message.chat.id, "❌ <b>Error:</b> Username not found or input format is invalid.")
    text, markup = get_owner_panel()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

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
                bot.send_message(message.chat.id, f"👥 <b>Promotion:</b> User {name} granted Admin permissions.", parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, f"This user {name} is already an Admin.")
        else:
            bot.send_message(message.chat.id, "❌ <b>Error:</b> Username not found. User must start the bot first.")
    text, markup = get_owner_panel()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

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
                bot.send_message(message.chat.id, f"➖ <b>Demotion:</b> Admin permissions revoked for {name}.", parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, f"This user {name} is not an Admin.")
        else:
            bot.send_message(message.chat.id, "❌ <b>Error:</b> Username not found or input invalid.")
    text, markup = get_owner_panel()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")


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
        
        # حفظ الفائز بصيغة HTML آمنة ومقاومة للعلامات الغريبة
        db["winners"].append(f" • {user_mention} ➔ Code: <code>{incoming_text}</code>")
        del db["codes"][incoming_text]  
        save_db(db)
        
        bot.reply_to(
            message, 
            f"🎉 <b>Congratulations! You found a valid code!</b> 🎉\n\n🔑 Code: <code>{incoming_text}</code>\n🎁 Your Reward: <b>{prize}</b>",
            parse_mode="HTML"
        )
        
        for owner_id in OWNER_IDS:
            try:
                bot.send_message(
                    owner_id,
                    f"🔔 <b>New Key Claimed!</b>\n\n👤 Winner: {user_mention} (<code>{user_id}</code>)\n🔑 Code: <code>{incoming_text}</code>\n🎁 Reward Sent: <b>{prize}</b>",
                    parse_mode="HTML"
                )
            except:
                pass
    else:
        if not is_admin(user_id):
            bot.reply_to(message, "❌ <b>Invalid Code:</b> That answer is incorrect or has already been claimed.", parse_mode="HTML")

# إقلاع البوت
print("Dashboard system engine initialized smoothly in HTML mode...")
bot.infinity_polling()
