import asyncio
from datetime import datetime, timedelta
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

TOKEN = "8649918373:AAGNnM3PTjgW4wGR90SUHcE-KyyZtdGVPpQ"

# Ваш Telegram ID
ADMIN_ID = 5211180124

# Повторяющийся список всех 28 человек
PEOPLE = [
    "Вітьенько Катерина Олегівна",
    "Гніздів Роман Володимирович",
    "Гончаров Сергій Олександрович",
    "Горпинич Ілля Володимирович",
    "Гуляка Дмитро Андрійович",
    "Давидович Мар'ян Ігорович",
    "Дручок Тарас Володимирович",
    "Коп'як Матвій Володимирович",
    "Лазар Максим Мирославович",
    "Лівінський Володимир Олегович",
    "Любчик Марк Віталійович",
    "Максим'як Михайло Юрійович",
    "Маличок Діана Євгенівна",
    "Матушинець Денис Євгенович",
    "Мацалап Станіслав Юрійович",
    "Милян Михайло Андрійович",
    "Ориник Владислав Степанович",
    "Пісаржевський Денис Назарович",
    "Порохняк Дмитрій",
    "Серба В'ячеслав Михайлович",
    "Сидій Арсен Вікторович",
    "Скочило Максим Андрійович",
    "Твердохліб Євген Ярославович",
    "Фурман Максим Миколайович",
    "Абіякін Олександр Ігорович",
    "Бережанський Владислав Олександрович",
    "Било Владислав Віталійович",
    "Була Олексій Богданович",
]

bot = Bot(token=TOKEN)
dp = Dispatcher()


def generate_schedule():
  schedule = []
  start_date = datetime.now()
  person_index = 0
  days_added = 0
  current_date = start_date

  # Формируем график на 14 рабочих дней вперед
  while days_added < 14:
    if current_date.weekday() != 6:  # Пропускаем воскресенье (6)
      p1 = PEOPLE[person_index % len(PEOPLE)]
      p2 = PEOPLE[(person_index + 1) % len(PEOPLE)]
      date_str = current_date.strftime("%d.%m.%Y (%A)")
      schedule.append(f"📅 **{date_str}**: {p1} та {p2}")
      person_index += 2
      days_added += 1
    current_date += timedelta(days=1)

  return "\n".join(schedule)


# Команду просмотра расписания могут вызывать все
@dp.message(Command("schedule"))
async def send_schedule(message: Message):
  text = (
      "📋 **Графік чергування (по 2 людини, окрім неділі):**\n\n"
      + generate_schedule()
  )
  await message.answer(text, parse_mode="Markdown")


# Команду замены может вызывать ТОЛЬКО администратор (ADMIN_ID)
@dp.message(Command("replace"))
async def replace_person(message: Message):
  if message.from_user.id != ADMIN_ID:
    await message.answer("❌ У вас немає прав для зміни розкладу.")
    return

  args = message.text.split(maxsplit=1)
  if len(args) < 2:
    await message.answer(
        "Будь ласка, вкажіть ім'я людини, наприклад:\n`/replace Маличок Діана"
        " Євгенівна`",
        parse_mode="Markdown",
    )
    return

  name_to_replace = args[1].strip()

  found = False
  for i, person in enumerate(PEOPLE):
    if name_to_replace.lower() in person.lower():
      removed = PEOPLE.pop(i)
      PEOPLE.append(removed)
      found = True
      await message.answer(
          f"✅ **{removed}** перенесено в кінець черги. Графік оновлено.",
          parse_mode="Markdown",
      )
      break

  if not found:
    await message.answer(
        f"❌ Людину з ім'ям '{name_to_replace}' не знайдено у списку."
    )


async def main():
  logging.basicConfig(level=logging.INFO)
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())