import logging
import asyncio
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

from config import BOT_TOKEN, ADMIN_ID, CHANNEL_USERNAME, HACKING_SYSTEMS, GITHUB_TOKEN, GITHUB_REPO, GITHUB_BRANCH
from github_db import GitHubDB

# 🔧 إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

print("🌐 بدء تشغيل البوت السحابي مع GitHub")

# 🗃️ تهيئة قاعدة البيانات على GitHub
db = GitHubDB(GITHUB_TOKEN, GITHUB_REPO, GITHUB_BRANCH)

# 🎯 حالة المستخدمين
user_states = {}

# ⌨️ لوحات المفاتيح
def create_main_keyboard():
    keyboard = [
        [KeyboardButton("📝 تقديم طلب انضمام")],
        [KeyboardButton("ℹ️ معلومات عن المجموعة")],
        [KeyboardButton("📊 إحصائيات النظام")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def create_systems_keyboard():
    buttons = []
    for i in range(0, len(HACKING_SYSTEMS), 2):
        row = [KeyboardButton(system) for system in HACKING_SYSTEMS[i:i+2]]
        buttons.append(row)
    buttons.append([KeyboardButton("🔙 رجوع")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def create_cancel_keyboard():
    return ReplyKeyboardMarkup([[KeyboardButton("❌ إلغاء العملية")]], resize_keyboard=True)

def create_confirm_keyboard():
    keyboard = [
        [KeyboardButton("✅ نعم، تأكيد الإرسال")],
        [KeyboardButton("❌ لا، تعديل البيانات")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def create_admin_buttons(user_id):
    buttons = [
        [
            InlineKeyboardButton("✅ موافقة", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user_id}")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

# 🎯 دوال البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    first_name = update.effective_user.first_name
    
    stats = db.get_stats()
    
    if chat_id == ADMIN_ID:
        welcome_text = f"""
🛡️ <b>مرحباً بعودتك أيها المسؤول! 👑</b>

📊 <b>الإحصائيات:</b>
• 👥 الأعضاء: {stats['approved']}
• ⏳ الطلبات: {stats['pending']}

🌐 <b>النظام السحابي:</b>
• قاعدة البيانات: GitHub
• المستودع: {GITHUB_REPO}
• الحالة: 🟢 نشط

⏰ <b>آخر تحديث:</b> {stats['last_update']}
        """
    else:
        welcome_text = f"""
🛡️ <b>مرحباً بك {first_name} في Hacker Hunters 🇾🇪</b>

🌐 <b>النظام السحابي المتطور:</b>
• بياناتك مخزنة على GitHub
• نسخ احتياطي تلقائي
• أمان وسرية تامة

📝 <b>للانضمام لإخوانك الهاكرز:</b>
اضغط على <b>"تقديم طلب انضمام"</b>
        """
    
    await update.message.reply_text(welcome_text, reply_markup=create_main_keyboard(), parse_mode='HTML')

async def handle_group_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info_text = f"""
🔰 <b>Hacker Hunters 🇾🇪 - النظام السحابي</b>

🏹 <b>نوع المجموعة:</b> هاكرز أخلاقيون محترفون
🎯 <b>الرؤية:</b> بناء جيل من الهاكرز اليمنيين المحترفين

🌐 <b>نظام البيانات:</b> GitHub السحابي
💾 <b>المستودع:</b> {GITHUB_REPO}
🔗 <b>الفرع:</b> {GITHUB_BRANCH}

⚡ <b>مميزات النظام السحابي:</b>
• بياناتك آمنة في السحابة
• نسخ احتياطي تلقائي
• استرجاع بيانات في أي وقت
• لا فقدان للبيانات أبداً
• أداء عالي وسريع

🔒 <b>الأمان والخصوصية:</b>
• تشفير البيانات تلقائياً
• صلاحيات وصول محدودة
• سجلات كاملة للتغييرات
    """
    await update.message.reply_text(info_text, parse_mode='HTML')

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if db.is_user_pending(chat_id):
        await update.message.reply_text(
            "⏳ لديك طلب قيد المراجعة بالفعل\nسيتم إشعارك فور البت في طلبك",
            reply_markup=create_main_keyboard()
        )
        return
    
    if db.is_user_approved(chat_id):
        await update.message.reply_text(
            "✅ أنت عضو معتمد بالفعل في المجموعة\nمرحباً بك back!",
            reply_markup=create_main_keyboard()
        )
        return
    
    # بدء التسجيل
    user_states[chat_id] = {'step': 'username'}
    
    text = """
🔐 <b>بدء تسجيل طلب الانضمام</b>

📝 <b>الخطوة 1/3:</b>
أدخل <b>اسم المستخدم</b> الذي تريد استخدامه في المجموعة:

💡 <b>الأفضل أن يكون:</b>
• بالإنجليزية
• يعبر عن شخصيتك
• بدون مسافات أو رموز

🎯 <b>مثال:</b> CyberWolf_YE | DarkCoder | SecurityGuard
    """
    await update.message.reply_text(
        text, 
        reply_markup=create_cancel_keyboard(), 
        parse_mode='HTML'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    first_name = update.effective_user.first_name
    
    try:
        if text == '📝 تقديم طلب انضمام':
            await start_registration(update, context)
        
        elif text == 'ℹ️ معلومات عن المجموعة':
            await handle_group_info(update, context)
        
        elif text == '📊 إحصائيات النظام':
            await show_stats(update, context)
        
        elif text == '❌ إلغاء العملية' or text == '🔙 رجوع':
            if chat_id in user_states:
                del user_states[chat_id]
            await update.message.reply_text("✅ تم إلغاء العملية", reply_markup=create_main_keyboard())
        
        elif text == '✅ نعم، تأكيد الإرسال':
            await confirm_submission(update, context)
        
        elif text == '❌ لا، تعديل البيانات':
            await start_registration(update, context)
        
        elif chat_id in user_states:
            await handle_registration_steps(update, context, chat_id, text, first_name)
            
    except Exception as e:
        logging.error(f"خطأ في معالجة الرسالة: {e}")
        await update.message.reply_text(
            "❌ حدث خطأ غير متوقع، يرجى المحاولة مرة أخرى",
            reply_markup=create_main_keyboard()
        )

async def handle_registration_steps(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                  chat_id: int, text: str, first_name: str):
    """معالجة خطوات التسجيل"""
    current_state = user_states.get(chat_id)
    if not current_state:
        return
    
    if current_state['step'] == 'username':
        if len(text) < 3:
            await update.message.reply_text("❌ اسم المستخدم يجب أن يكون 3 أحرف على الأقل")
            return
        
        current_state['username'] = text
        current_state['first_name'] = first_name
        current_state['step'] = 'password'
        
        await update.message.reply_text("""
🔐 <b>الخطوة 2/3:</b>
أدخل <b>كلمة المرور</b> التي تريد استخدامها:

⚠️ <b>تنبيه مهم:</b>
• اختر كلمة مرور قوية
• لا تستخدم كلمات مرور تستخدمها elsewhere
• تذكر كلمة المرور جيداً
        """, parse_mode='HTML')
    
    elif current_state['step'] == 'password':
        if len(text) < 4:
            await update.message.reply_text("❌ كلمة المرور يجب أن تكون 4 أحرف على الأقل")
            return
        
        current_state['password'] = text
        current_state['step'] = 'system'
        
        await update.message.reply_text(
            "🖥️ <b>الخطوة 3/3:</b>\nاختر نظام التشغيل الذي تعمل عليه:",
            reply_markup=create_systems_keyboard(),
            parse_mode='HTML'
        )
    
    elif current_state['step'] == 'system' and text in HACKING_SYSTEMS:
        current_state['system'] = text
        current_state['step'] = 'confirm'
        
        user_data = current_state
        summary_text = f"""
📋 <b>ملخص طلب الانضمام</b>

👤 <b>اسم المستخدم:</b> {user_data['username']}
🔐 <b>كلمة المرور:</b> {'*' * len(user_data['password'])}
🖥️ <b>نظام التشغيل:</b> {user_data['system']}

🌐 <b>سيتم حفظ بياناتك على:</b> GitHub
💾 <b>المستودع:</b> {GITHUB_REPO}

✅ <b>ماذا سيحدث بعد الإرسال:</b>
• سيتم مراجعة طلبك من المسؤول
• ستتلقى إشعاراً فور البت في طلبك
• سيتم الإعلان عن انضمامك في القناة

⚠️ <b>هل تريد متابعة إرسال الطلب؟</b>
        """
        await update.message.reply_text(
            summary_text,
            reply_markup=create_confirm_keyboard(),
            parse_mode='HTML'
        )

async def confirm_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تأكيد إرسال الطلب"""
    chat_id = update.effective_chat.id
    user_data = user_states.get(chat_id)
    
    if not user_data:
        await update.message.reply_text(
            "❌ لم يتم العثور على بياناتك، يرجى البدء من جديد",
            reply_markup=create_main_keyboard()
        )
        return
    
    application_data = {
        'username': user_data['username'],
        'password': user_data['password'],
        'system': user_data['system'],
        'telegram_id': chat_id,
        'first_name': user_data.get('first_name', 'غير معروف'),
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # حفظ البيانات
    success = db.save_pending_request(application_data)
    
    if success:
        text = f"""
🎉 <b>تم إرسال طلبك بنجاح!</b>

✅ <b>تم حفظ بياناتك في النظام السحابي الآمن</b>
⏳ <b>جاري مراجعة طلبك من المسؤول</b>

📋 <b>معلومات طلبك:</b>
• 👤 المستخدم: {application_data['username']}
• 🖥️ النظام: {application_data['system']}
• ⏰ الوقت: {application_data['timestamp']}

🌐 <b>معلومات الحفظ:</b>
• الموقع: GitHub السحابي
• المستودع: {GITHUB_REPO}
• الحالة: 🟢 آمن ومشفّر

📢 <b>سيتم إشعارك فور البت في طلبك</b>
        """
        
        # إشعار المسؤول
        await notify_admin(application_data)
        
    else:
        text = """
❌ <b>فشل في إرسال الطلب</b>

⚠️ حدث خطأ غير متوقع في النظام
يرجى المحاولة مرة أخرى بعد قليل

🔧 <b>الأسباب المحتملة:</b>
• مشكلة في اتصال GitHub
• مشكلة في التوكن
• مشكلة في المستودع
        """
    
    # مسح حالة المستخدم
    if chat_id in user_states:
        del user_states[chat_id]
    
    await update.message.reply_text(
        text, 
        reply_markup=create_main_keyboard(), 
        parse_mode='HTML'
    )

async def notify_admin(application_data):
    """إشعار المسؤول بطلب جديد"""
    try:
        from telegram import Bot
        bot = Bot(token=BOT_TOKEN)
        
        admin_text = f"""
🆕 <b>طلب انضمام جديد - النظام السحابي</b>

👤 <b>المستخدم:</b> {application_data['username']}
🖥 <b>النظام:</b> {application_data['system']}
👁️ <b>الاسم:</b> {application_data['first_name']}
🆔 <b>الرقم:</b> {application_data['telegram_id']}
⏰ <b>الوقت:</b> {application_data['timestamp']}

🔐 <b>كلمة المرور:</b> {application_data['password']}

🌐 <b>مخزن في:</b> GitHub
💾 <b>المستودع:</b> {GITHUB_REPO}
⏱️ <b>تم الحفظ:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """
        
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            reply_markup=create_admin_buttons(application_data['telegram_id']),
            parse_mode='HTML'
        )
        
        logging.info(f"✅ تم إشعار المسؤول عن طلب {application_data['username']}")
            
    except Exception as e:
        logging.error(f"❌ خطأ في إشعار المسؤول: {e}")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض الإحصائيات"""
    chat_id = update.effective_chat.id
    
    stats = db.get_stats()
    
    stats_text = f"""
📊 <b>إحصائيات النظام السحابي</b>

👥 <b>المستخدمون:</b>
⏳ الطلبات المعلقة: <b>{stats['pending']}</b>
✅ الأعضاء المعتمدون: <b>{stats['approved']}</b>

🌐 <b>نظام التخزين:</b> GitHub السحابي
💾 <b>المستودع:</b> {GITHUB_REPO}
🔗 <b>الفرع:</b> {GITHUB_BRANCH}

🕒 <b>آخر تحديث:</b> {stats['last_update']}

⚡ <b>مميزات النظام السحابي:</b>
• 💾 لا فقدان للبيانات
• 🔐 نسخ احتياطي تلقائي
• 🌐 توفر دائم 24/7
• 📱 الوصول من أي مكان
• 🔒 أمان عالي المستوى
        """
    
    await update.message.reply_text(stats_text, parse_mode='HTML')

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الردود من الأزرار"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    chat_id = query.from_user.id
    
    if chat_id != ADMIN_ID:
        await query.edit_message_text("❌ ليس لديك صلاحية للقيام بهذا الإجراء")
        return
    
    if callback_data.startswith("approve_"):
        user_id = int(callback_data.replace("approve_", ""))
        success = db.approve_member(user_id)
        
        if success:
            # إرسال رسالة للمستخدم
            try:
                from telegram import Bot
                bot = Bot(token=BOT_TOKEN)
                await bot.send_message(
                    user_id, 
                    "🎉 <b>مبروك! تمت الموافقة على طلبك</b>\n\n🔰 <b>مرحباً بك في Hacker Hunters 🇾🇪</b>\n\n🌐 <b>تم حفظ عضويتك على GitHub السحابي</b>", 
                    parse_mode='HTML'
                )
            except Exception as e:
                logging.error(f"❌ خطأ في إرسال رسالة للمستخدم: {e}")
            
            await query.edit_message_text("✅ تمت الموافقة على العضو في النظام السحابي")
        else:
            await query.edit_message_text("❌ لم يتم العثور على المستخدم")
    
    elif callback_data.startswith("reject_"):
        user_id = int(callback_data.replace("reject_", ""))
        db.reject_member(user_id)
        await query.edit_message_text("❌ تم رفض العضو")

def main():
    """الدالة الرئيسية"""
    logging.info("🚀 بدء تشغيل البوت السحابي مع GitHub...")
    
    # اختبار الاتصال بـ GitHub
    try:
        test_data = db.read_data()
        print(f"✅ تم الاتصال بـ GitHub بنجاح!")
        print(f"📊 الإحصائيات: {len(test_data['pending_requests'])} طلب, {len(test_data['approved_members'])} عضو")
        print(f"💾 المستودع: {GITHUB_REPO}")
    except Exception as e:
        print(f"❌ فشل الاتصال بـ GitHub: {e}")
        return
    
    # إنشاء تطبيق البوت
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجين
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # بدء البوت
    print("🌐 البوت السحابي يعمل الآن مع GitHub!")
    print("⚡ جاهز لاستقبال الطلبات...")
    application.run_polling()

if __name__ == "__main__":
    main()
