import telebot
import asyncio
import json
import libsql_client
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo

# الإعدادات الرئيسية للمتجر
TOKEN = '8949634245:AAHdbmUjeaLFxYE3Evr6wfu6Kk8hfW4Henk'
ADMIN_ID = 7339897843
CONTACT_LINK = 'https://t.me/RAMD3'
CHANNEL_LINK = 'https://t.me/RAMD02I'

# 🌐 بيانات قاعدة البيانات السحابية (Turso)
TURSO_URL = "libsql://store-db-YOUR_USERNAME.turso.io"
TURSO_TOKEN = "ey...YOUR_TURSO_AUTH_TOKEN"

bot = telebot.TeleBot(TOKEN)
user_states = {}

# دالة إنشاء العميل للاتصال بقاعدة البيانات السحابية
async def get_db():
    return libsql_client.create_client_async(url=TURSO_URL, auth_token=TURSO_TOKEN)

def init_db():
    try:
        async def create_table():
            async with await get_db() as db:
                await db.execute('''CREATE TABLE IF NOT EXISTS accounts 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, desc TEXT, price TEXT, 
                     media_ids TEXT, media_types TEXT, is_sold INTEGER DEFAULT 0)''')
                await db.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
                await db.execute('''CREATE TABLE IF NOT EXISTS pending_orders 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, type TEXT, desc TEXT, price TEXT, 
                     media_ids TEXT, media_types TEXT)''')
        asyncio.run(create_table())
        print("✅ [قاعدة البيانات]: تم الاتصال وتحديث الجداول بنجاح.")
    except Exception as e:
        print(f"❌ [خطأ في قاعدة البيانات]: {e}")

init_db()

# دالة إرسال إشعار تلقائي للجميع عند قبول أو نشر سلعة
def notify_all_users(acc_type, price, desc):
    type_names = {
        'ff': '🎮 فري فاير',
        'tt_beta': '🎵 تيك توك بيطا',
        'tt_normal': '🎵 تيك توك عادي',
        'fb_group': '📘 فيسبوك (مجموعة)',
        'fb_page': '📘 فيسبوك (صفحة)'
    }
    category_name = type_names.get(acc_type, "سلعة جديدة")
    
    async def broadcast_new_item():
        async with await get_db() as db:
            res = await db.execute("SELECT user_id FROM users")
            users = res.rows
            
        notification_text = (
            f"📢 **تم إضافة سلعة جديدة في المتجر!**\n\n"
            f"📁 **القسم:** {category_name}\n"
            f"💵 **السعر:** {price}\n"
            f"📝 **الوصف:** {desc[:100]}...\n\n"
            f"💡 *ادخل إلى البوت الآن لتصفح التفاصيل والصور!*"
        )
        
        for u in users:
            try:
                bot.send_message(u[0], notification_text, parse_mode="Markdown")
            except Exception:
                continue

    asyncio.run(broadcast_new_item())

# بناء أزرار التحكم بالحسابات
def get_acc_markup(acc_id, acc_type, index, total, img_index=0, img_total=1):
    markup = InlineKeyboardMarkup()
    
    if img_total > 1:
        img_nav = []
        prev_img = img_index - 1 if img_index > 0 else img_total - 1
        img_nav.append(InlineKeyboardButton("▶️ الصورة السابقة", callback_data=f"media_{acc_type}_{index}_{prev_img}"))
        img_nav.append(InlineKeyboardButton(f"📷 {img_index+1}/{img_total}", callback_data="ignore"))
        next_img = img_index + 1 if img_index < img_total - 1 else 0
        img_nav.append(InlineKeyboardButton("الصورة التالية ◀️", callback_data=f"media_{acc_type}_{index}_{next_img}"))
        markup.row(*img_nav)

    nav_buttons = []
    if index > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"page_{acc_type}_{index-1}"))
    nav_buttons.append(InlineKeyboardButton(f"📦 {index+1}/{total}", callback_data="ignore"))
    if index < total - 1:
        nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"page_{acc_type}_{index+1}"))
    markup.row(*nav_buttons)
    
    markup.row(InlineKeyboardButton("🛒 شراء هذا الحساب", callback_data=f"buy_{acc_id}"))
    markup.row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu_back"))
    return markup

# القائمة الرئيسية
def main_menu(user_id):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🎮 فري فاير", callback_data="page_ff_0"))
    markup.row(InlineKeyboardButton("🎵 تيك توك", callback_data="menu_tt"), InlineKeyboardButton("📘 فيسبوك", callback_data="menu_fb"))
    markup.row(InlineKeyboardButton("📋 الحسابات المتوفرة حالياً", callback_data="show_all_available"))
    markup.row(InlineKeyboardButton("➕ إرسال سلعة للبيع", callback_data="user_add_acc"))
    markup.row(InlineKeyboardButton("📦 المبيعات السابقة (داخل البوت)", callback_data="sold_accs"))
    markup.row(InlineKeyboardButton("📢 طلبات تم إنجازها (القناة)", url=CHANNEL_LINK))
    markup.row(InlineKeyboardButton("📞 تواصل معي للإستفسار أو الشراء", url=CONTACT_LINK))
    if user_id == ADMIN_ID:
        markup.row(InlineKeyboardButton("🛠 لوحة التحكم", callback_data="admin_panel"))
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    async def save_user():
        async with await get_db() as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", [message.chat.id])
    asyncio.run(save_user())
    bot.send_message(message.chat.id, "👋 أهلاً بك في متجر الحسابات الرقمية! \n\nاختر القسم الذي تريد تصفحه من الأسفل ملاحظة‼️ يرجى التعامل بوسيط لضمان كفاءة البيع والثقة 💰:", reply_markup=main_menu(message.from_user.id))

# القوائم الفرعية (تيك توك - فيسبوك)
@bot.callback_query_handler(func=lambda call: call.data == "menu_tt")
def sub_menu_tt(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("⚡ تيك توك بيطا", callback_data="page_tt_beta_0"))
    markup.row(InlineKeyboardButton("🎵 تيك توك عادي", callback_data="page_tt_normal_0"))
    markup.row(InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu_back"))
    bot.edit_message_text("🎵 اختر نوع حساب التيك توك:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "menu_fb")
def sub_menu_fb(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("👥 مجموعات فيسبوك", callback_data="page_fb_group_0"))
    markup.row(InlineKeyboardButton("📄 صفحات فيسبوك", callback_data="page_fb_page_0"))
    markup.row(InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu_back"))
    bot.edit_message_text("📘 اختر نوع خدمات الفيسبوك:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "show_all_available")
def show_all_available_accs(call):
    async def fetch_available():
        async with await get_db() as db:
            res = await db.execute("SELECT id, type, price FROM accounts WHERE is_sold=0")
            return res.rows
            
    rows = asyncio.run(fetch_available())
    if not rows:
        bot.answer_callback_query(call.id, "🛒 المتجر فارغ حالياً، لا توجد حسابات معروضة للبيع!", show_alert=True)
        return
        
    type_names = {
        'ff': '🎮 فري فاير',
        'tt_beta': '🎵 تيك توك بيطا',
        'tt_normal': '🎵 تيك توك عادي',
        'fb_group': '📘 مجموعة فيسبوك',
        'fb_page': '📘 صفحة فيسبوك'
    }
    
    text = "📋 قائمة الحسابات المتوفرة حالياً للبيع:\n\n"
    for r in rows:
        name = type_names.get(r[1], 'سلعة')
        text += f"🔹 {name} | الرقم المعرف: {r[0]} | السعر: {r[2]}\n"
    
    text += "\n💡 *لتصفح تفاصيل أي حساب ورؤية صوره، اضغط على القسم الخاص به من القائمة الرئيسية مباشرة.*"
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel(call):
    if call.from_user.id != ADMIN_ID: return
    
    async def get_pending_count():
        async with await get_db() as db:
            res = await db.execute("SELECT COUNT(*) FROM pending_orders")
            return res.rows[0][0] if res.rows else 0
            
    count = asyncio.run(get_pending_count())
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("➕ إضافة حساب جديد", callback_data="add_acc"))
    markup.row(InlineKeyboardButton(f"📥 مراجعة طلبات السلع ({count})", callback_data="review_pending_0"))
    markup.row(InlineKeyboardButton("✅ تحويل حساب إلى (مباع)", callback_data="set_sold"))
    markup.row(InlineKeyboardButton("❌ حذف حساب نهائياً", callback_data="del_acc"))
    markup.row(InlineKeyboardButton("📢 إرسال إعلان للجميع", callback_data="broadcast"))
    markup.row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu_back"))
    bot.edit_message_text(f"🛠 لوحة التحكم الخاصة بالأدمن:\nاختر العملية التي تريد القيام بها:\n\n📥 يوجد حالياً {count} منشورات معلقة بانتظار المراجعة.", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "main_menu_back")
def back_to_menu(call):
    try: 
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception: 
        pass
    bot.send_message(call.message.chat.id, "اختر القسم الذي تريد تصفحه من الأسفل:", reply_markup=main_menu(call.from_user.id))

# إختيار نوع السلعة عند الإضافة
@bot.callback_query_handler(func=lambda call: call.data in ["add_acc", "user_add_acc"])
def add_account_start(call):
    if call.data == "add_acc" and call.from_user.id != ADMIN_ID: return
    is_admin = "1" if call.from_user.id == ADMIN_ID and call.data == "add_acc" else "0"
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🎮 فري فاير", callback_data=f"settype_ff_{is_admin}"))
    markup.row(InlineKeyboardButton("🎵 تيك توك بيطا", callback_data=f"settype_tt_beta_{is_admin}"), InlineKeyboardButton("🎵 تيك توك عادي", callback_data=f"settype_tt_normal_{is_admin}"))
    markup.row(InlineKeyboardButton("👥 مجموعة فيسبوك", callback_data=f"settype_fb_group_{is_admin}"), InlineKeyboardButton("📄 صفحة فيسبوك", callback_data=f"settype_fb_page_{is_admin}"))
    bot.edit_message_text("📁 اختر القسم الذي تريد إضافة السلعة أو المنشور إليه:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("settype_"))
def process_type(call):
    parts = call.data.split("_")
    is_admin = parts[-1]
    acc_type = "_".join(parts[1:-1])
    
    user_states[call.from_user.id] = {'type': acc_type, 'is_admin': is_admin, 'step': 'desc', 'media_ids': [], 'media_types': []}
    bot.edit_message_text("📝 الآن أرسل (تفاصيل المنشور أو وصف السلعة) بالتفصيل:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get('step') == 'desc')
def process_desc(message):
    user_states[message.from_user.id]['desc'] = message.text
    user_states[message.from_user.id]['step'] = 'price'
    bot.send_message(message.chat.id, "💵 كم السعر المطلوب؟ (مثال: 1500 DA):")

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get('step') == 'price')
def process_price(message):
    user_states[message.from_user.id]['price'] = message.text
    user_states[message.from_user.id]['step'] = 'media'
    bot.send_message(message.chat.id, "🖼️ الآن أرسل (الصورة الأولى أو الفيديو الأول) الخاصة بالسلعة:")

@bot.message_handler(content_types=['photo', 'video'], func=lambda msg: user_states.get(msg.from_user.id, {}).get('step') == 'media')
def process_media(message):
    state_data = user_states.get(message.from_user.id)
    if not state_data: return
    
    if message.photo:
        media_id = message.photo[-1].file_id
        media_type = 'photo'
    else:
        media_id = message.video.file_id
        media_type = 'video'
        
    state_data['media_ids'].append(media_id)
    state_data['media_types'].append(media_type)
    
    if len(state_data['media_ids']) >= 10:
        finish_adding_media(message.chat.id, message.from_user.id)
        return

    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("➕ إضافة صورة/فيديو آخر", callback_data="add_more_media"))
    markup.row(InlineKeyboardButton("✅ إنهاء وحفظ المنشور رسمياً", callback_data="finish_media"))
    bot.send_message(message.chat.id, f"📸 تم استلام الوسيط رقم ({len(state_data['media_ids'])}). هل تريد إضافة المزيد من الصور التوضيحية لهذا الحساب أم تكتفي بهذا؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "add_more_media")
def ask_more_media(call):
    bot.edit_message_text("🖼️ أرسل الآن الصورة التالية أو الفيديو التالي مباشرة:", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "finish_media")
def finish_media_callback(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    finish_adding_media(call.message.chat.id, call.from_user.id)

def finish_adding_media(chat_id, user_id):
    state_data = user_states.get(user_id)
    if not state_data: return
    
    media_ids_json = json.dumps(state_data['media_ids'])
    media_types_json = json.dumps(state_data['media_types'])
    
    if state_data['is_admin'] == "1":
        async def save_to_db():
            async with await get_db() as db:
                await db.execute(
                    "INSERT INTO accounts (type, desc, price, media_ids, media_types) VALUES (?, ?, ?, ?, ?)",
                    [state_data['type'], state_data['desc'], state_data['price'], media_ids_json, media_types_json]
                )
        try:
            asyncio.run(save_to_db())
            bot.send_message(chat_id, "✅ تم حفظ المنشور مع كامل ألبومه وإضافته للمتجر بنجاح!")
            # 🔔 إرسال إشعار تلقائي للجميع
            notify_all_users(state_data['type'], state_data['price'], state_data['desc'])
        except Exception as e:
            bot.send_message(chat_id, "❌ حدث خطأ أثناء الحفظ في قاعدة البيانات.")
    else:
        async def save_to_pending():
            async with await get_db() as db:
                await db.execute(
                    "INSERT INTO pending_orders (user_id, type, desc, price, media_ids, media_types) VALUES (?, ?, ?, ?, ?, ?)",
                    [user_id, state_data['type'], state_data['desc'], state_data['price'], media_ids_json, media_types_json]
                )
        try:
            asyncio.run(save_to_pending())
            bot.send_message(chat_id, "📥 تم إرسال منشورك مع ألبومه بنجاح للأدمن للمراجعة!\nسيتم فحصه ونشره في البوت فوراً إذا كان موافقاً للشروط.")
            bot.send_message(ADMIN_ID, "🔔 إشعار: زبون جديد قام بتقديم سلعة للبيع، ادخل للوحة التحكم لمراجعتها.")
        except Exception as e:
            bot.send_message(chat_id, "❌ فشل إرسال الطلب، يرجى إعادة المحاولة.")
            
    user_states.pop(user_id, None)

@bot.callback_query_handler(func=lambda call: call.data.startswith("page_") or call.data.startswith("media_"))
def show_accounts(call):
    is_media_click = call.data.startswith("media_")
    parts = call.data.split("_")
    
    if is_media_click:
        img_index = int(parts[-1])
        index = int(parts[-2])
        acc_type = "_".join(parts[1:-2])
    else:
        img_index = 0
        index = int(parts[-1])
        acc_type = "_".join(parts[1:-1])
    
    async def get_accs():
        async with await get_db() as db:
            res = await db.execute("SELECT * FROM accounts WHERE type=? AND is_sold=0", [acc_type])
            return res.rows
            
    accs = asyncio.run(get_accs())
    if not accs:
        bot.answer_callback_query(call.id, "🚫 لا توجد منشورات متوفرة حالياً في هذا القسم!", show_alert=True)
        return
        
    acc = accs[index]
    
    try:
        media_ids = json.loads(acc[4])
        media_types = json.loads(acc[5])
    except Exception:
        media_ids = [acc[4]]
        media_types = [acc[5]]
        
    if img_index >= len(media_ids): img_index = 0
    
    current_media_id = media_ids[img_index]
    current_media_type = media_types[img_index]
    
    type_names = {
        'ff': 'فري فاير',
        'tt_beta': 'تيك توك بيطا',
        'tt_normal': 'تيك توك عادي',
        'fb_group': 'مجموعة فيسبوك',
        'fb_page': 'صفحة فيسبوك'
    }
    name_ar = type_names.get(acc_type, "السلعة")
    caption = f"📦 حساب {name_ar} متوفر حالياً:\n\n🆔 رقم الحساب (ID): {acc[0]}\n📝 الوصف:\n{acc[2]}\n\n💵 السعر: {acc[3]}"
    
    markup = get_acc_markup(acc[0], acc_type, index, len(accs), img_index, len(media_ids))
    
    try:
        if current_media_type == 'photo':
            bot.edit_message_media(InputMediaPhoto(current_media_id, caption=caption, parse_mode="Markdown"), call.message.chat.id, call.message.message_id, reply_markup=markup)
        else:
            bot.edit_message_media(InputMediaVideo(current_media_id, caption=caption, parse_mode="Markdown"), call.message.chat.id, call.message.message_id, reply_markup=markup)
    except Exception:
        try: 
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception: 
            pass
        if current_media_type == 'photo':
            bot.send_photo(call.message.chat.id, photo=current_media_id, caption=caption, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_video(call.message.chat.id, video=current_media_id, caption=caption, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("review_pending_") or call.data.startswith("revmed_"))
def review_pending(call):
    if call.from_user.id != ADMIN_ID: return
    
    is_media_click = call.data.startswith("revmed_")
    parts = call.data.split("_")
    index = int(parts[1]) if not is_media_click else int(parts[2])
    img_index = int(parts[3]) if is_media_click else 0
    
    async def get_pending():
        async with await get_db() as db:
            res = await db.execute("SELECT * FROM pending_orders")
            return res.rows
            
    rows = asyncio.run(get_pending())
    if not rows:
        try: 
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception: 
            pass
        bot.send_message(call.message.chat.id, "📥 لا توجد أي سلع أو منشورات معلقة حالياً لمراجعتها!", reply_markup=main_menu(ADMIN_ID))
        return
        
    if index >= len(rows): index = 0
    
    row = rows[index]
    order_id, user_id, acc_type, desc, price, media_ids_raw, media_types_raw = row
    
    try:
        media_ids = json.loads(media_ids_raw)
        media_types = json.loads(media_types_raw)
    except Exception:
        media_ids = [media_ids_raw]
        media_types = [media_types_raw]
        
    if img_index >= len(media_ids): img_index = 0
    
    current_media_id = media_ids[img_index]
    current_media_type = media_types[img_index]
    
    type_names = {
        'ff': 'فري فاير',
        'tt_beta': 'تيك توك بيطا',
        'tt_normal': 'تيك توك عادي',
        'fb_group': 'مجموعة فيسبوك',
        'fb_page': 'صفحة فيسبوك'
    }
    name_ar = type_names.get(acc_type, "السلعة")
    caption = f"📥 مراجعة منشور معلق من زبون:\n\n👤 المرسل: tg://user?id={user_id}\n📁 القسم: {name_ar}\n📝 الوصف:\n{desc}\n\n💵 السعر المقترح: {price}\n\n⚙️ اختر قبول المنشور لإضافته رسمياً أو رفضه لحذفه:"
    
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ قبول ونشر", callback_data=f"accept_{order_id}"),
        InlineKeyboardButton("❌ رفض وحذف", callback_data=f"reject_{order_id}")
    )
    
    if len(media_ids) > 1:
        img_nav = []
        prev_img = img_index - 1 if img_index > 0 else len(media_ids) - 1
        img_nav.append(InlineKeyboardButton("▶️ صورة الطلب السابقة", callback_data=f"revmed_pending_{index}_{prev_img}"))
        img_nav.append(InlineKeyboardButton(f"📷 {img_index+1}/{len(media_ids)}", callback_data="ignore"))
        next_img = img_index + 1 if img_index < len(media_ids) - 1 else 0
        img_nav.append(InlineKeyboardButton("صورة الطلب التالية ◀️", callback_data=f"revmed_pending_{index}_{next_img}"))
        markup.row(*img_nav)

    nav_buttons = []
    if index > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"review_pending_{index-1}"))
    nav_buttons.append(InlineKeyboardButton(f"الطلبات: {index+1}/{len(rows)}", callback_data="ignore"))
    if index < len(rows) - 1:
        nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"review_pending_{index+1}"))
    markup.row(*nav_buttons)
    markup.row(InlineKeyboardButton("🛠 العودة للوحة التحكم", callback_data="admin_panel"))
    
    try:
        if current_media_type == 'photo':
            bot.edit_message_media(InputMediaPhoto(current_media_id, caption=caption), call.message.chat.id, call.message.message_id, reply_markup=markup)
        else:
            bot.edit_message_media(InputMediaVideo(current_media_id, caption=caption), call.message.chat.id, call.message.message_id, reply_markup=markup)
    except Exception:
        try: 
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception: 
            pass
        if current_media_type == 'photo':
            bot.send_photo(call.message.chat.id, photo=current_media_id, caption=caption, reply_markup=markup)
        else:
            bot.send_video(call.message.chat.id, video=current_media_id, caption=caption, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_"))
def accept_order(call):
    if call.from_user.id != ADMIN_ID: return
    order_id = int(call.data.split("_")[1])
    
    async def db_accept():
        async with await get_db() as db:
            cursor = await db.execute("SELECT * FROM pending_orders WHERE id=?", [order_id])
            rows = cursor.rows
            if rows:
                row = rows[0]
                await db.execute(
                    "INSERT INTO accounts (type, desc, price, media_ids, media_types) VALUES (?, ?, ?, ?, ?)",
                    [row[2], row[3], row[4], row[5], row[6]]
                )
                await db.execute("DELETE FROM pending_orders WHERE id=?", [order_id])
                return row
            return None

    row_data = asyncio.run(db_accept())
    if row_data:
        bot.answer_callback_query(call.id, "✅ تم قبول السلعة ونشرها في المتجر بنجاح!", show_alert=True)
        try: 
            bot.send_message(row_data[1], "🎉 أخبار سارة! تم مراجعة منشورك وقبوله من طرف الأدمن، وهو الآن معروض للبيع مع كامل صوره داخل البوت.")
        except Exception: 
            pass
            
        # 🔔 إرسال إشعارات لجميع المستخدمين الذين ضغطوا /start عند قبول السلعة
        notify_all_users(row_data[2], row_data[4], row_data[3])
    else:
        bot.answer_callback_query(call.id, "❌ تعذر العثور على البيانات.")
        
    review_pending(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject_order(call):
    if call.from_user.id != ADMIN_ID: return
    order_id = int(call.data.split("_")[1])
    
    async def db_reject():
        async with await get_db() as db:
            cursor = await db.execute("SELECT user_id FROM pending_orders WHERE id=?", [order_id])
            rows = cursor.rows
            user_id = rows[0][0] if rows else None
            await db.execute("DELETE FROM pending_orders WHERE id=?", [order_id])
            return user_id

    user_id = asyncio.run(db_reject())
    bot.answer_callback_query(call.id, "❌ تم رفض السلعة وحذفها نهائياً.", show_alert=True)
    if user_id:
        try: 
            bot.send_message(user_id, "⚠️ للاسف، تم رفض منشور السلعة الذي أرسلته من طرف الإدارة.")
        except Exception: 
            pass
    
    review_pending(call)

@bot.callback_query_handler(func=lambda call: call.data == "set_sold")
def set_sold_step(call):
    if call.from_user.id != ADMIN_ID: return
    user_states[call.from_user.id] = {'step': 'sell_id'}
    bot.edit_message_text("🔄 أرسل لي الآن (رقم ID الحساب) الذي قمت ببيعه ليتم إخفاؤه من المتجر:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get('step') == 'sell_id')
def process_sell_id(message):
    if message.from_user.id != ADMIN_ID: return
    acc_id = message.text.strip()
    
    if not acc_id.isdigit():
        bot.send_message(message.chat.id, "⚠️ يرجى إرسال رقم الـ ID صحيح (أرقام فقط):")
        return
    
    async def db_sell():
        async with await get_db() as db:
            cursor = await db.execute("SELECT * FROM accounts WHERE id=?", [acc_id])
            rows = cursor.rows
            if rows:
                await db.execute("UPDATE accounts SET is_sold=1 WHERE id=?", [acc_id])
                return rows[0]
            return None

    try:
        acc_data = asyncio.run(db_sell())
        if acc_data:
            bot.send_message(message.chat.id, f"✅ تم نقل الحساب رقم {acc_id} إلى المبيعات السابقة بنجاح!")
        else:
            bot.send_message(message.chat.id, f"❌ لم يتم العثور على حساب يحمل الرقم {acc_id} في القاعدة.")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ فشلت العملية بسبب خطأ داخلي.")
    user_states.pop(message.from_user.id, None)

@bot.callback_query_handler(func=lambda call: call.data == "del_acc")
def del_acc_step(call):
    if call.from_user.id != ADMIN_ID: return
    user_states[call.from_user.id] = {'step': 'delete_id'}
    bot.edit_message_text("❌ أرسل لي (رقم ID الحساب) لحذفه نهائياً من المتجر والقاعدة:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get('step') == 'delete_id')
def process_delete_id(message):
    if message.from_user.id != ADMIN_ID: return
    acc_id = message.text.strip()

    if not acc_id.isdigit():
        bot.send_message(message.chat.id, "⚠️ يرجى إرسال رقم الـ ID صحيح (أرقام فقط):")
        return

    async def db_delete():
        async with await get_db() as db:
            cursor = await db.execute("SELECT * FROM accounts WHERE id=?", [acc_id])
            if cursor.rows:
                await db.execute("DELETE FROM accounts WHERE id=?", [acc_id])
                return True
            return False

    try:
        success = asyncio.run(db_delete())
        if success:
            bot.send_message(message.chat.id, f"🗑️ تم حذف الحساب رقم {acc_id} نهائياً!")
        else:
            bot.send_message(message.chat.id, f"❌ لم يتم العثور على حساب يحمل الرقم {acc_id} في القاعدة.")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ فشل الحذف بسبب خطأ داخلي.")
    user_states.pop(message.from_user.id, None)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_callback(call):
    acc_id = call.data.split("_")[1]
    user = call.from_user
    username = f"@{user.username}" if user.username else "لا يملك معرف"
    admin_alert = f"🔔 طلب شراء جديد داخل البوت!\n\n👤 الزبون: {user.first_name} ({username})\n🆔 آيدي الزبون: {user.id}\n\n🆔 رقم الحساب المطلوب (ID): {acc_id}\n\n👉 [اضغط هنا لمراسلة الزبون مباشرة](tg://user?id={user.id})"
    bot.send_message(ADMIN_ID, admin_alert, parse_mode="Markdown")
    bot.answer_callback_query(call.id, "✅ تم إرسال طلب الشراء للأدمن بنجاح! سيتواصل معك في أقرب وقت لتسليم الحساب.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "broadcast")
def broadcast_step(call):
    if call.from_user.id != ADMIN_ID: return
    user_states[call.from_user.id] = {'step': 'broadcast_msg'}
    bot.edit_message_text("📢 أرسل الآن نص الإعلان الذي تريد تعميمه لجميع مستخدمي البوت:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get('step') == 'broadcast_msg')
def send_broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    async def get_users():
        async with await get_db() as db:
            res = await db.execute("SELECT user_id FROM users")
            return res.rows
            
    users = asyncio.run(get_users())
    count = 0
    bot.send_message(message.chat.id, f"⏳ جاري بدء إرسال الإعلان إلى {len(users)} مستخدم...")
    for user in users:
        try:
            bot.send_message(user[0], message.text)
            count += 1
        except Exception: 
            continue
    bot.send_message(message.chat.id, f"✅ تم انتهاء الإرسال بنجاح وتعميم المنشور على {count} زبون بنجاح.")
    user_states.pop(message.from_user.id, None)

@bot.callback_query_handler(func=lambda call: call.data == "sold_accs")
def show_sold(call):
    async def get_sold():
        async with await get_db() as db:
            res = await db.execute("SELECT * FROM accounts WHERE is_sold=1")
            return res.rows
            
    accs = asyncio.run(get_sold())
    if not accs:
        bot.answer_callback_query(call.id, "لا توجد مبيعات مؤرشفة بعد داخل البوت!", show_alert=True)
        return
    bot.send_message(call.message.chat.id, "📦 هذه قائمة بالحسابات التي تم بيعها سابقاً ومؤرشفة:")
    for acc in accs:
        bot.send_message(call.message.chat.id, f"✅ تم بيع حساب رقم: {acc[0]} \n📝 الوصف: {acc[2]}")

print("🚀 [تشغيل]: البوت يعمل بالكامل...")
bot.infinity_polling(timeout=60, long_polling_timeout=5)
