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

current_student_list = STUDENTS.copy()
START_DATE = date(2026, 1, 1)

def get_duty_pair_for_date(target_date: date):
    days_diff = (target_date - START_DATE).days
    total_working_days = sum(1 for d in range(days_diff) if (START_DATE + timedelta(days=d)).weekday() != 6) if days_diff > 0 else 0
    if target_date.weekday() == 6:
        return None
    idx = (total_working_days * 2) % len(current_student_list)
    p1 = current_student_list[idx]
    p2 = current_student_list[(idx + 1) % len(current_student_list)]
    return p1, p2

async def set_main_menu(bot: Bot):
    commands = [
        BotCommand(command="schedule", description="Графік на тиждень"),
        BotCommand(command="history", description="Історія минулих чергувань"),
        BotCommand(command="stats", description="Статистика чергувань"),
        BotCommand(command="find", description="Пошук дат чергувань студента"),
        BotCommand(command="list", description="Поточний порядок черги"),
        BotCommand(command="help", description="Список команд")
    ]
    await bot.set_my_commands(commands)

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
            text += f"🟢 **{date_str} ({day_name}):** {pair[0]} та {pair[1]}\n"
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
            text += f"⚪ **{date_str} ({day_name}):** {pair[0]} та {pair[1]}\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("stats"))
async def send_stats(message: types.Message):
    today = date.today()
    counts = {student: 0 for student in STUDENTS}
    
    current_d = START_DATE
    while current_d <= today:
        if current_d.weekday() != 6:
            pair = get_duty_pair_for_date(current_d)
            if pair:
                if pair[0] in counts: counts[pair[0]] += 1
                if pair[1] in counts: counts[pair[1]] += 1
        current_d += timedelta(days=1)

    sorted_stats = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    text = "📊 **Статистика чергувань (скільки разів чергували):**\n\n"
    for name, count in sorted_stats:
        text += f"• {name} — {count} раз(и)\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("find"))
async def find_student_duties(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ Вкажіть прізвище: `/find Маличок`", parse_mode="Markdown")
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
    text = "📋 **Поточний порядок черги (КІ-106):**\n\n"
    for i, name in enumerate(current_student_list, 1):
        text += f"{i}. {name}\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("help"))
async def send_help(message: types.Message):
    text = (
        "🤖 **Доступні команди бота:**\n\n"
        "• `/schedule` — Графік на тиждень\n"
        "• `/history` — Історія минулих чергувань\n"
        "• `/stats` — Статистика кількості чергувань\n"
        "• `/find [Прізвище]` — Пошук дат чергувань студента\n"
        "• `/list` — Поточний порядок черги\n"
        "• `/help` — Список команд\n"
    )
    if message.from_user.id in ADMIN_IDS:
        text += (
            "\n👑 **Команди адміністратора:**\n"
            "• `/replace [н1] [н2]` — Поміняти двох студентів місцями (напр: `/replace 1 6`)\n"
            "• `/skip` — Пропустити поточного студента (зсунути чергу вправо)\n"
            "• `/reset` — Скинути чергу до початкового списку\n"
        )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("replace"))
async def replace_students(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Ця команда доступна тільки адміністратору.")
        return
    args = message.text.split()
    if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():
        await message.answer("⚠️ Вкажіть два числа: `/replace 1 6`", parse_mode="Markdown")
        return
    
    idx1 = int(args[1]) - 1
    idx2 = int(args[2]) - 1

    if 0 <= idx1 < len(current_student_list) and 0 <= idx2 < len(current_student_list):
        current_student_list[idx1], current_student_list[idx2] = current_student_list[idx2], current_student_list[idx1]
        await message.answer(f"✅ Успішно поміняно місцями:\n1) {current_student_list[idx2]}\n2) {current_student_list[idx1]}", parse_mode="Markdown")
    else:
        await message.answer("❌ Неправильні номери студентів.")

@dp.message(Command("skip"))
async def skip_student(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Ця команда доступна тільки адміністратору.")
        return
    
    first = current_student_list.pop(0)
    current_student_list.insert(1, first)
    await message.answer(f"✅ Чергу зміщено. Студент **{first}** пропущений на одну позицію вперед.", parse_mode="Markdown")

@dp.message(Command("reset"))
async def reset_list(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Ця команда доступна тільки адміністратору.")
        return
    
    global current_student_list
    current_student_list = STUDENTS.copy()
    await message.answer("🔄 Список черги успішно скинуто до початкового стану!", parse_mode="Markdown")

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
    await set_main_menu(bot)  # Реєструємо меню команд при запуску
    asyncio.create_task(daily_reminder())
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot)
    )

if __name__ == '__main__':
    asyncio.run(main())
