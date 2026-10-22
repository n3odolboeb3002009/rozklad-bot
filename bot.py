import asyncio
import logging
import os
from datetime import datetime, date, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

API_TOKEN = '8649918373:AAHkW1z6a58FWPiyqwdQNnlo6VfBlkmIhDE'
ADMIN_ID = 5211180124

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
    text = "📋 **Поточний порядок черги (КІ-106):**\n\n"
    for i, name in enumerate(current_student_list, 1):
        text += f"{i}. {name}\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("help"))
async def send_help(message: types.Message):
    text = (
        "🤖 **Доступні команди бота:**\n\n"
        "• `/schedule` — Графік чергування на тиждень\n"
        "• `/list` — Поточний порядок черги студентів\n"
        "• `/help` — Список команд\n"
    )
    if message.from_user.id == ADMIN_ID:
        text += (
            "\n👑 **Команди адміністратора:**\n"
            "• `/replace [номер1] [номер2]` — Поміняти двох студентів місцями (наприклад: `/replace 1 6`)\n"
            "• `/skip` — Зсунути чергу на 1 людину вправо (пропустити поточного)\n"
        )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("replace"))
async def replace_students(message: types.Message):
    if message.from_user.id != ADMIN_ID:
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
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Ця команда доступна тільки адміністратору.")
        return
    
    # Переносимо першу людину на одну позицію вправо (на 2-ге місце)
    first = current_student_list.pop(0)
    current_student_list.insert(1, first)
    await message.answer(f"✅ Чергу зміщено. Студент **{first}** пропущений на одну позицію вперед.", parse_mode="Markdown")

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
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot)
    )

if __name__ == '__main__':
    asyncio.run(main())
