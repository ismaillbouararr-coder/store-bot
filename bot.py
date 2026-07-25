import time
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo

# الإعدادات الرئيسية للمتجر
TOKEN = '8987897788:AAHl3s-gGhB3xACt5Uqv1Bb0B3zAkAWxu48'
ADMIN_ID = 7339897843
CONTACT_LINK = 'https://t.me/RAMD3'
CHANNEL_LINK = 'https://t.me/RAMD02I'

bot = telebot.TeleBot(TOKEN)
user_states = {}

# 🧠 تخزين البيانات في الذاكرة بدلاً من SQLite
accounts = []       # قائمة الحسابات والمعروضات
users = set()       # مجموعة معرّفات المستخدمين (مُستقبلات الإشعارات)
pending_orders = [] # الطلبات المعلقة بانتظار موافقة الأدمن

acc_id_counter = 1
order_id_counter = 1

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
    
    # تنظيف النص لمنع أخطاء التنسيق
    clean_desc = desc.replace('*', '').replace('_', '').replace('`', '')
    
    notification_text = (
        f"📢 تم إضافة سلعة جديدة في المتجر!\n\n"
        f"📁 القسم: {category_name}\n"
        f"💵 السعر: {price}\n"
        f"📝 الوصف: {clean_desc[:100]}...\n\n"
        f"💡 ادخل إلى البوت الآن لتصفح التفاصيل والصور!"
    )
    
    for u_id in list(users):
        try:
            bot.send_message(u_id, notification_text)
            time.sleep(0.04) # فاصل أمان لتفادي الحظر
        except Exception:
            continue

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
    users.add(message.chat.id)
    bot.send_message(
        message.chat.id, 
        "👋 أهلاً بك في متجر الحسابات الرقمية! \n\nاختر القسم الذي تريد تصفحه من الأسفل ملاحظة‼️ يرجى التعامل بوسيط لضمان كفاءة البيع والثقة 💰:", 
        reply_markup=main_menu(message.from_user.id)
    )

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
    available = [a for a in accounts if a['is_sold'] == 0]

    if not available:
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
    for r in available:
        name = type_names.get(r['type'], 'سلعة')
        text += f"🔹 {name} | الرقم المعرف: {r['id']} | السعر: {r['price']}\n"
    
    text += "\n💡 لتصفح تفاصيل أي حساب ورؤية صوره، اضغط على القسم الخاص به من القائمة الرئيسية مباشرة."
    bot.send_message(call.message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel(call):
    if call.from_user.id != ADMIN_ID: return
    
    count = len(pending_orders)
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("➕ إضافة حساب جديد", callback_data="add_acc"))
    markup.row(InlineKeyboardButton(f"📥 مراجعة طلبات السلع ({count})", callback_data="review_pending_0"))
    markup.row(InlineKeyboardButton("✅ تحويل حساب إلى (مباع)", callback_data="set_sold"))
    markup.row(InlineKeyboardButton("❌ حذف حساب نهائياً", callback_data="del_acc"))
    markup.row(InlineKeyboardButton("📢 إرسال إعلان للجميع", callback_data="broadcast"))
    markup.row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu_back"))
    bot.edit_message_text(
        f"🛠 لوحة التحكم الخاصة بالأدمن:\nاختر العملية التي تريد القيام بها:\n\n📥 يوجد حالياً {count} منشورات معلقة بانتظار المراجعة.", 
        call.message.chat.id, call.message.message_id, reply_markup=markup
    )

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
    bot.send_message(message.chat.id, f"📸 تم استلام الوسيط رقم ({len(state_data['media_ids'])}). هل تريد إضافة المزيد من الصور أم تكتفي بهذا؟", reply_markup=markup)

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
    global acc_id_counter, order_id_counter
    state_data = user_states.get(user_id)
    if not state_data: return
    
    if state_data['is_admin'] == "1":
        new_account = {
            'id': acc_id_counter,
            'type': state_data['type'],
            'desc': state_data['desc'],
            'price': state_data['price'],
            'media_ids': state_data['media_ids'],
            'media_types': state_data['media_types'],
            'is_sold': 0
        }
        accounts.append(new_account)
        acc_id_counter += 1
        
        bot.send_message(chat_id, "✅ تم حفظ المنشور مع كامل ألبومه وإضافته للمتجر بنجاح!")
        notify_all_users(state_data['type'], state_data['price'], state_data['desc'])
    else:
        new_order = {
            'id': order_id_counter,
            'user_id': user_id,
            'type': state_data['type'],
            'desc': state_data['desc'],
            'price': state_data['price'],
            'media_ids': state_data['media_ids'],
            'media_types': state_data['media_types']
        }
        pending_orders.append(new_order)
        order_id_counter += 1
        
        bot.send_message(chat_id, "📥 تم إرسال منشورك بنجاح للأدمن للمراجعة!\nسيتم فحصه ونشره فوراً إذا كان موافقاً للشروط.")
        bot.send_message(ADMIN_ID, "🔔 إشعار: زبون جديد قام بتقديم سلعة للبيع، ادخل للوحة التحكم لمراجعتها.")
            
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
    
    accs = [a for a in accounts if a['type'] == acc_type and a['is_sold'] == 0]

    if not accs:
        bot.answer_callback_query(call.id, "🚫 لا توجد منشورات متوفرة حالياً في هذا القسم!", show_alert=True)
        return
        
    acc = accs[index]
    media_ids = acc['media_ids']
    media_types = acc['media_types']
        
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
    caption = f"📦 حساب {name_ar} متوفر حالياً:\n\n🆔 رقم الحساب (ID): {acc['id']}\n📝 الوصف:\n{acc['desc']}\n\n💵 السعر: {acc['price']}"
    
    markup = get_acc_markup(acc['id'], acc_type, index, len(accs), img_index, len(media_ids))
    
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("review_pending_") or call.data.startswith("revmed_"))
def review_pending(call):
    if call.from_user.id != ADMIN_ID: return
    
    is_media_click = call.data.startswith("revmed_")
    parts = call.data.split("_")
    index = int(parts[1]) if not is_media_click else int(parts[2])
    img_index = int(parts[3]) if is_media_click else 0
    
    if not pending_orders:
        try: 
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception: 
            pass
        bot.send_message(call.message.chat.id, "📥 لا توجد أي سلع أو منشورات معلقة حالياً لمراجعتها!", reply_markup=main_menu(ADMIN_ID))
        return
        
    if index >= len(pending_orders): index = 0
    
    row = pending_orders[index]
    order_id = row['id']
    user_id = row['user_id']
    acc_type = row['type']
    desc = row['desc']
    price = row['price']
    media_ids = row['media_ids']
    media_types = row['media_types']
        
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
    nav_buttons.append(InlineKeyboardButton(f"الطلبات: {index+1}/{len(pending_orders)}", callback_data="ignore"))
    if index < len(pending_orders) - 1:
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
    global acc_id_counter
    if call.from_user.id != ADMIN_ID: return
    order_id = int(call.data.split("_")[1])
    
    order = next((o for o in pending_orders if o['id'] == order_id), None)
    
    if order:
        new_account = {
            'id': acc_id_counter,
            'type': order['type'],
            'desc': order['desc'],
            'price': order['price'],
            'media_ids': order['media_ids'],
            'media_types': order['media_types'],
            'is_sold': 0
        }
        accounts.append(new_account)
        acc_id_counter += 1
        pending_orders.remove(order)
        
        bot.answer_callback_query(call.id, "✅ تم قبول السلعة ونشرها في المتجر بنجاح!", show_alert=True)
        try: 
            bot.send_message(order['user_id'], "🎉 أخبار سارة! تم مراجعة منشورك وقبوله من طرف الأدمن، وهو الآن معروض للبيع مع كامل صوره داخل البوت.")
        except Exception: 
            pass
            
        notify_all_users(order['type'], order['price'], order['desc'])
    else:
        bot.answer_callback_query(call.id, "❌ تعذر العثور على البيانات.")
        
    admin_panel(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject_order(call):
    if call.from_user.id != ADMIN_ID: return
    order_id = int(call.data.split("_")[1])
    
    order = next((o for o in pending_orders if o['id'] == order_id), None)
    
    if order:
        user_id = order['user_id']
        pending_orders.remove(order)
        bot.answer_callback_query(call.id, "❌ تم رفض السلعة وحذفها نهائياً.", show_alert=True)
        if user_id:
            try: 
                bot.send_message(user_id, "⚠️ للاسف، تم رفض منشور السلعة الذي أرسلته من طرف الإدارة.")
            except Exception: 
                pass
    
    admin_panel(call)

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
    
    acc = next((a for a in accounts if a['id'] == int(acc_id)), None)
    
    if acc:
        acc['is_sold'] = 1
        bot.send_message(message.chat.id, f"✅ تم نقل الحساب رقم {acc_id} إلى المبيعات السابقة بنجاح!")
    else:
        bot.send_message(message.chat.id, f"❌ لم يتم العثور على حساب يحمل الرقم {acc_id}.")

    user_states.pop(message.from_user.id, None)

@bot.callback_query_handler(func=lambda call: call.data == "del_acc")
def del_acc_step(call):
    if call.from_user.id != ADMIN_ID: return
    user_states[call.from_user.id] = {'step': 'delete_id'}
    bot.edit_message_text("❌ أرسل لي (رقم ID الحساب) لحذفه نهائياً من المتجر:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get('step') == 'delete_id')
def process_delete_id(message):
    if message.from_user.id != ADMIN_ID: return
    acc_id = message.text.strip()

    if not acc_id.isdigit():
        bot.send_message(message.chat.id, "⚠️ يرجى إرسال رقم الـ ID صحيح (أرقام فقط):")
        return

    acc = next((a for a in accounts if a['id'] == int(acc_id)), None)
    if acc:
        accounts.remove(acc)
        bot.send_message(message.chat.id, f"🗑️ تم حذف الحساب رقم {acc_id} نهائياً!")
    else:
        bot.send_message(message.chat.id, f"❌ لم يتم العثور على حساب يحمل الرقم {acc_id}.")

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
    
    count = 0
    user_list = list(users)
    bot.send_message(message.chat.id, f"⏳ جاري بدء إرسال الإعلان إلى {len(user_list)} مستخدم...")
    for u_id in user_list:
        try:
            bot.send_message(u_id, message.text)
            count += 1
            time.sleep(0.04) # فاصل زمني لتفادي حظر تليجرام
        except Exception: 
            continue
    bot.send_message(message.chat.id, f"✅ تم انتهاء الإرسال بنجاح وتعميم المنشور على {count} زبون.")
    user_states.pop(message.from_user.id, None)

@bot.callback_query_handler(func=lambda call: call.data == "sold_accs")
def show_sold(call):
    sold_list = [a for a in accounts if a['is_sold'] == 1]

    if not sold_list:
        bot.answer_callback_query(call.id, "لا توجد مبيعات مؤرشفة بعد داخل البوت!", show_alert=True)
        return
    bot.send_message(call.message.chat.id, "📦 هذه قائمة بالحسابات التي تم بيعها سابقاً ومؤرشفة:")
    for acc in sold_list:
        bot.send_message(call.message.chat.id, f"✅ تم بيع حساب رقم: {acc['id']} \n📝 الوصف: {acc['desc']}")

print("🚀 [تشغيل]: البوت يعمل الآن بالذاكرة المؤقتة بدون قواعد بيانات...")
bot.infinity_polling(timeout=60, long_polling_timeout=5)
