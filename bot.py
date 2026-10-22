import asyncio
import logging
import os
from datetime import datetime, date, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# Токен и настройки
API_TOKEN = '7611800171:AAH8a9b3sM8-4C-06U-P0zI1c8_w38s2y6A'
ADMIN_ID = 5211180124

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Исходный список 28 студентов
STUDENTS = [
    "Бабій Дмитро Олегович", "Баран Юрій Володимирович", "Бейко Іван Михайлович",
    "Болехівський Данило Юрійович", "Бомок Катерина Анатоліївна", "Бонк Денис Русланович",
    "Борейко Олексій Тарасович", "Валіон Артем Олександрович", "Вовк Олександр Романович",
    "Волянюк Остап Богданович", "Герега Олег Ігорович", "Гуляк Данило Ігорович",
    "Заставний Артем Андрійович", "Кобилянський Владислав Віталійович", "Козачонер Марк Олександрович",
    "Лазуркевич Максим Миколайович", "Маличок Діана Євгенівна", "Микієвич Денис Віталійович",
    "Ничик Андрій Сергійович", "Паламарчук Павло Олександрович", "Романів Олег Ігорович",
    "Середа Марія Миколаївна", "Сивопляс Захар Олексійович", "Слободян Роман Андрійович",
    "Харкарліс Олександр Ігорович", "Цепелінда Денис Сергійович", "Яценко Станіслав Костянтинович",
    "Яцух В'ячеслав Володимирович"
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

@dp.message(Command("replace"))
async def replace_student(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Ця команда доступна тільки адміністратору.")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ Вкажіть ПІБ: `/replace Прізвище Ім'я По батькові`", parse_mode="Markdown")
        return
    name_to_replace = args[1].strip()
    if name_to_replace in current_student_list:
        current_student_list.remove(name_to_replace)
        current_student_list.append(name_to_replace)
        await message.answer(f"✅ **{name_to_replace}** перенесено в кінець черги.", parse_mode="Markdown")
    else:
        await message.answer("❌ Студента не знайдено в списку.")

# Веб-сервер для прохождения проверки портов Render и UptimeRobot
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
    # Параллельный запуск веб-сервера и телеграм-бота
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot)
    )

if __name__ == '__main__':
    asyncio.run(main())
