import asyncio
import logging
import os
from datetime import datetime, date, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# Токен и настройки
API_TOKEN = '8649918373:AAHkW1z6a58FWPiyqwdQNnlo6VfBlkmIhDE'
ADMIN_ID = 5211180124

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Повний список 28 студентів (без Харишина та Гриціва)
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

@dp.message(Command("schedule"))
async def send_schedule(message: types.Message):
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

@dp.message(Command("list"))
async def show_students_list(message: types.Message):
    text = "📋 **Список студентів КІ-106:**\n\n"
    for i, name in enumerate(STUDENTS, 1):
        text += f"{i}. {name}\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("help"))
async def send_help(message: types.Message):
    text = (
        "🤖 **Доступні команди бота:**\n\n"
        "• `/schedule` — Показать график чергування на тиждень\n"
        "• `/list` — Показати повний список студентів з номерами\n"
        "• `/help` — Показати список доступних команд\n"
    )
    if message.from_user.id == ADMIN_ID:
        text += (
            "\n👑 **Команди адміністратора:**\n"
            "• `/replace [номер або ПІБ]` — Перенести студента в кінець черги\n"
            "_Приклад:_ `/replace 17` або `/replace Маличок`"
        )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("replace"))
async def replace_student(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Ця команда доступна тільки адміністратору.")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ Вкажіть номер або ПІБ: `/replace 17` або `/replace Маличок`", parse_mode="Markdown")
        return
    
    query = args[1].strip()
    name_to_replace = None

    if query.isdigit():
        idx = int(query) - 1
        if 0 <= idx < len(STUDENTS):
            name_to_replace = STUDENTS[idx]
    else:
        for student in STUDENTS:
            if query.lower() in student.lower():
                name_to_replace = student
                break

    if name_to_replace and name_to_replace in current_student_list:
        current_student_list.remove(name_to_replace)
        current_student_list.append(name_to_replace)
        await message.answer(f"✅ **{name_to_replace}** перенесено в кінець черги.", parse_mode="Markdown")
    else:
        await message.answer("❌ Студента не знайдено за цим номером або ім'ям.")

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
    logging.info(f"🟢 Web server successfully started and listening on port {port}")

async def main():
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot)
    )

if __name__ == '__main__':
    asyncio.run(main())
