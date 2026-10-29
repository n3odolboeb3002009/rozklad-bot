import asyncio
import logging
import os
from datetime import datetime, date, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BotCommand
from aiohttp import web

API_TOKEN = '8649918373:AAHkW1z6a58FWPiyqwdQNnlo6VfBlkmIhDE'

ADMIN_IDS = [5211180124, 5278601121] 
GROUP_CHAT_ID = None

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Постійний непорушний список студентів (номери 1-28 назавжди зафіксовані)
STUDENTS = [
    "Абіякін Олександр Ігорович", "Бережанський Владислав Олександрович", "Било Владислав Віталійович",
    "Була Олексій Богданович", "Вітенько Катерина Олегівна", "Гніздів Роман Володимирович",
    "Гончаров Сергій Олександрович", "Горпинич Ілля Володимирович", "Гуляка Дмитро Андрійович",
    "Давидович Мар'ян Ігорович", "Дручок Тарас Володимирович", "Коп'як Матвій Володимирович",
    "Лазар Максим Мирославович", "Лівінський Володимир Олегович", "Любчик Марк Віталійович",
    "Максим'як Михайло Юрійович", "Маличок Діана Євгенівна", "Матушинець Денис Євгенович",
    "Мацалап Станіслав Юрійович", "Милян Михайло Андрійович", "Ориник Владислав Степанович",
    "Пісаржевський Денис Назарович", "Порохняк Дмитрій", "Серба В'ячеслав Михайлович",
    "Сидій Арсен Вікторович", "Скочило Максим Андрійович", "Твердохліб Євген Ярославович",
    "Фурман Максим Миколайович"
]

# Черга у вигляді індексів (не змінює номери людей у базовому списку)
queue_indices = list(range(len(STUDENTS)))
excluded_indices = set()
START_DATE = date(2026, 1, 1)

def get_active_queue():
    return [idx for idx in queue_indices if idx not in excluded_indices]

def get_duty_pair_for_date(target_date: date):
    active_q = get_active_queue()
    if not active_q or target_date.weekday() == 6:
        return None
    
    days_diff = (target_date - START_DATE).days
    total_working_days = sum(1 for d in range(days_diff) if (START_DATE + timedelta(days=d)).weekday() != 6) if days_diff > 0 else 0
    
    idx = (total_working_days * 2) % len(active_q)
    p1 = STUDENTS[active_q[idx]]
    p2 = STUDENTS[active_q[(idx + 1) % len(active_q)]]
    return p1, p2

async def set_main_menu(bot: Bot):
    commands = [
        BotCommand(command="start", description="Головна сторінка"),
        BotCommand(command="schedule", description="Графік на тиждень"),
        BotCommand(command="history", description="Історія минулих чергувань"),
        BotCommand(command="stats", description="Статистика чергувань"),
        BotCommand(command="find", description="Пошук дат чергувань студента"),
        BotCommand(command="list", description="Список студентів (постійні номери)"),
        BotCommand(command="help", description="Список команд")
    ]
    await bot.set_my_commands(commands)

@dp.message(Command("start"))
async def send_start(message: types.Message):
    text = (
        "**Бот розкладу чергувань групи КІ-106**\n"
        "Автор: Маличок Діана ([@l5211180124](https://t.me/l5211180124))\n\n"
        "Скористайтеся командою /help, щоб переглянути список доступних команд."
    )
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)

@dp.message(Command("schedule"))
async def send_schedule(message: types.Message):
    global GROUP_CHAT_ID
    if message.chat.type in ["group", "supergroup"]:
        GROUP_CHAT_ID = message.chat.id

    today = date.today()
    days_ukr = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"]
    text = "📋 **Графік чергування (KI-106):**\n\n"
    for i in range(7):
        day_date = today + timedelta(days=i)
        day_name = days_ukr[day_date.weekday()]
        date_str = day_date.strftime("%d.%m")
        if day_date.weekday() == 6:
            text += f"🔴 **{date_str} ({day_name}):** Вихідний\n"
        else:
            pair = get_duty_pair_for_date(day_date)
            if pair:
                text += f"🟢 **{date_str} ({day_name}):** {pair[0]} та {pair[1]}\n"
            else:
                text += f"⚪ **{date_str} ({day_name}):** Немає активних студентів\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("history"))
async def send_history(message: types.Message):
    today = date.today()
    days_ukr = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"]
    text = "📜 **Історія чергувань (минулі дні):**\n\n"
    for i in range(1, 6):
        day_date = today - timedelta(days=i)
        day_name = days_ukr[day_date.weekday()]
        date_str = day_date.strftime("%d.%m")
        if day_date.weekday() == 6:
            text += f"🔴 **{date_str} ({day_name}):** Вихідний\n"
        else:
            pair = get_duty_pair_for_date(day_date)
            if pair:
                text += f"⚪ **{date_str} ({day_name}):** {pair[0]} та {pair[1]}\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("stats"))
async def send_stats(message: types.Message):
    today = date.today()
    counts = {student: 0 for student in STUDENTS}
    
    current_d = START_DATE
    while current_d <= today:
        if current_d.weekday() != 6:
            days_diff = (current_d - START_DATE).days
            active_q = get_active_queue()
            if active_q:
                total_working_days = sum(1 for d in range(days_diff) if (START_DATE + timedelta(days=d)).weekday() != 6) if days_diff > 0 else 0
                idx = (total_working_days * 2) % len(active_q)
                p1 = STUDENTS[active_q[idx]]
                p2 = STUDENTS[active_q[(idx + 1) % len(active_q)]]
                if p1 in counts: counts[p1] += 1
                if p2 in counts: counts[p2] += 1
        current_d += timedelta(days=1)

    sorted_stats = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    text = "📊 **Статистика чергувань:**\n\n"
    for name, count in sorted_stats:
        status = " (тимчасово видалений)" if STUDENTS.index(name) in excluded_indices else ""
        text += f"• {name}{status} — {count} раз(и)\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("find"))
async def find_student_duties(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ **Не вказано прізвище!**\nПриклад використання:\n`/find Маличок`", parse_mode="Markdown")
        return
    
    query = args[1].strip().lower()
    found_dates = []
    today = date.today()
    days_ukr = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
    
    for i in range(-30, 31):
        d = today + timedelta(days=i)
        if d.weekday() == 6: continue
        pair = get_duty_pair_for_date(d)
        if pair and (query in pair[0].lower() or query in pair[1].lower()):
            found_dates.append(f"• {d.strftime('%d.%m.%Y')} ({days_ukr[d.weekday()]})")

    if found_dates:
        text = f"🔍 **Знайдені чергування для '{args[1]}':**\n\n" + "\n".join(found_dates[:15])
    else:
        text = "❌ За цим запитом найближчим часом чергувань не знайдено."
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("list"))
async def show_students_list(message: types.Message):
    text = "📋 **Список студентів КІ-106:**\n\n"
    for i, name in enumerate(STUDENTS, 1):
        status = " 🔴 *(тимчасово видалений)*" if (i - 1) in excluded_indices else ""
        text += f"{i}. {name}{status}\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("help"))
async def send_help(message: types.Message):
    text = (
        "**Доступні команди бота:**\n\n"
        "• `/start` — Головна сторінка та інформація\n"
        "• `/schedule` — Графік на тиждень\n"
        "• `/history` — Історія минулих чергувань\n"
        "• `/stats` — Статистика кількості чергувань\n"
        "• `/find [Прізвище]` — Пошук дат чергувань студента\n"
        "• `/list` — Список студентів\n"
        "• `/help` — Список команд\n"
    )
    if message.from_user.id in ADMIN_IDS:
        text += (
            "\n👑 **Команди адміністратора:**\n"
            "• `/replace [н1] [н2]` — Поміняти двох у черзі (напр: `/replace 1 6`)\n"
            "• `/skip` — Пропустити поточних (зсунути чергу вправо)\n"
            "• `/setpair [номери або прізвища]` — Почати графік з конкретної пари\n"
            "• `/exclude [номер]` — Тимчасово приховати студента\n"
            "• `/include [номер]` — Повернути студента у чергу\n"
            "• `/reset` — Скинути чергу до початкового стану\n"
        )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("replace"))
async def replace_students(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Ця команда доступна тільки адміністратору.")
        return
    args = message.text.split()
    if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():
        await message.answer("⚠️ **Неправильний формат!**\nПриклад використання:\n`/replace 1 6` (номери зі списку)", parse_mode="Markdown")
        return
    
    pos1 = int(args[1]) - 1
    pos2 = int(args[2]) - 1

    if pos1 in queue_indices and pos2 in queue_indices:
        idx1 = queue_indices.index(pos1)
        idx2 = queue_indices.index(pos2)
        queue_indices[idx1], queue_indices[idx2] = queue_indices[idx2], queue_indices[idx1]
        await message.answer(f"✅ Успішно поміняно місцями у черзі:\n1) {STUDENTS[pos1]}\n2) {STUDENTS[pos2]}", parse_mode="Markdown")
    else:
        await message.answer("❌ Неправильні номери студентів.")

@dp.message(Command("skip"))
async def skip_student(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Ця команда доступна тільки адміністратору.")
        return
    
    active_q = get_active_queue()
    if len(active_q) < 2:
        await message.answer("❌ Недостатньо активних студентів у списку.")
        return
    
    p1 = active_q.pop(0)
    p2 = active_q.pop(0)
    active_q.append(p1)
    active_q.append(p2)
    
    global queue_indices
    other_indices = [idx for idx in queue_indices if idx not in active_q]
    queue_indices = active_q + other_indices
    
    await message.answer("✅ Чергу успішно зсунуто вправо (сьогоднішня пара пропущена).", parse_mode="Markdown")

@dp.message(Command("setpair"))
async def set_pair(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Ця команда доступна тільки адміністратору.")
        return
    
    text_input = message.text.replace("/setpair", "").strip()
    if not text_input:
        await message.answer("⚠️ **Не вказано параметри!**\nПриклад за номерами: `/setpair 24 25`\nПриклад за прізвищами: `/setpair Серба, Сидій`", parse_mode="Markdown")
        return
    
    parts = [p.strip() for p in text_input.replace(" та ", ",").split(",")]
    if len(parts) < 2:
        parts = text_input.split()
        
    if len(parts) < 2:
        await message.answer("⚠️ Потрібно вказати **два** числа або два прізвища.\nПриклад: `/setpair 24 25`", parse_mode="Markdown")
        return
    
    idx1, idx2 = None, None
    
    if parts[0].isdigit() and parts[1].isdigit():
        idx1 = int(parts[0]) - 1
        idx2 = int(parts[1]) - 1
        if not (0 <= idx1 < len(STUDENTS) and 0 <= idx2 < len(STUDENTS)):
            await message.answer("❌ **Помилка:** Неправильні номери студентів (мають бути від 1 до 28).", parse_mode="Markdown")
            return
    else:
        q1_query, q2_query = parts[0].lower(), parts[1].lower()
        for i, s in enumerate(STUDENTS):
            s_lower = s.lower()
            if idx1 is None and q1_query in s_lower:
                idx1 = i
            elif idx2 is None and q2_query in s_lower:
                idx2 = i
                
        if idx1 is None or idx2 is None:
            await message.answer("❌ **Помилка:** Одне або обидва прізвища не знайдено у списку групи КІ-106.", parse_mode="Markdown")
            return
            
    active_q = get_active_queue()
    if idx1 not in active_q or idx2 not in active_q:
        await message.answer("❌ **Помилка:** Один із студентів тимчасово виключений (`/exclude`). Спочатку поверніть його через `/include`.", parse_mode="Markdown")
        return
        
    pos1 = active_q.index(idx1)
    pos2 = active_q.index(idx2)
    
    is_adjacent = (pos2 == pos1 + 1) or (pos1 == len(active_q) - 1 and pos2 == 0)
    
    if not is_adjacent:
        await message.answer(f"❌ **Помилка:** Студенти **{STUDENTS[idx1]}** та **{STUDENTS[idx2]}** не йдуть наступними в черзі один за одним!", parse_mode="Markdown")
        return
        
    global queue_indices
    while active_q[0] != idx1:
        item = active_q.pop(0)
        active_q.append(item)
        
    other_indices = [idx for idx in queue_indices if idx not in active_q]
    queue_indices = active_q + other_indices
    
    await message.answer(f"✅ Графік успішно переналаштовано! Першими на чергуванні тепер встановлені:\n🟢 **{STUDENTS[idx1]} та {STUDENTS[idx2]}**", parse_mode="Markdown")

@dp.message(Command("exclude"))
async def exclude_student(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Ця команда доступна тільки адміністратору.")
        return
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ **Не вказано номер студента!**\nПриклад використання:\n`/exclude 5`", parse_mode="Markdown")
        return
    
    idx = int(args[1]) - 1
    if 0 <= idx < len(STUDENTS):
        excluded_indices.add(idx)
        await message.answer(f"🔴 Студент **{STUDENTS[idx]}** тимчасово видалений з чергування.", parse_mode="Markdown")
    else:
        await message.answer("❌ Неправильний номер студента.")

@dp.message(Command("include"))
async def include_student(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Ця команда доступна тільки адміністратору.")
        return
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ **Не вказано номер студента!**\nПриклад використання:\n`/include 5`", parse_mode="Markdown")
        return
    
    idx = int(args[1]) - 1
    if 0 <= idx < len(STUDENTS):
        if idx in excluded_indices:
            excluded_indices.remove(idx)
            await message.answer(f"🟢 Студент **{STUDENTS[idx]}** повернутий у чергу.", parse_mode="Markdown")
        else:
            await message.answer("ℹ️ Цей студент і так активний у черзі.")
    else:
        await message.answer("❌ Неправильний номер студента.")

@dp.message(Command("reset"))
async def reset_list(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Ця команда доступна тільки адміністратору.")
        return
    
    global queue_indices, excluded_indices
    queue_indices = list(range(len(STUDENTS)))
    excluded_indices.clear()
    await message.answer("🔄 Чергу та видалення успішно скинуто до початкового стану!", parse_mode="Markdown")

async def daily_reminder():
    while True:
        now = datetime.now()
        target = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        wait_seconds = (target - now).total_seconds()
        
        await asyncio.sleep(wait_seconds)
        
        if GROUP_CHAT_ID:
            today = date.today()
            if today.weekday() != 6:
                pair = get_duty_pair_for_date(today)
                if pair:
                    text = f"🔔 **Доброго ранку! Нагадування про чергування на сьогодні ({today.strftime('%d.%m')}):**\n\n🟢 {pair[0]} та {pair[1]}"
                    try:
                        await bot.send_message(GROUP_CHAT_ID, text, parse_mode="Markdown")
                    except Exception as e:
                        logging.error(f"Не вдалося надіслати нагадування: {e}")
        await asyncio.sleep(60)

async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    await set_main_menu(bot)
    asyncio.create_task(daily_reminder())
    # Виправляємо запуск асинхронних задач через asyncio.gather з await
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot)
    )

if __name__ == '__main__':
    asyncio.run(main())
