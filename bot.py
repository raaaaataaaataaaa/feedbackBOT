import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, Text
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage

# Вставьте сюда токен вашего бота от @BotFather
BOT_TOKEN = "8912412881:AAGTtGegWjoHyOvmEjsGxxg-xyEpETtwKFk"

# Вставьте сюда ваш Telegram ID (можно узнать у бота @userinfobot)
ADMIN_ID = 658716284

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Словарь для хранения состояния: какой пользователь пишет какому админу
# user_id -> admin_id (если пользователь хочет ответить конкретному админу)
user_sessions = {}

# Клавиатура для пользователя
user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Написать сообщение")]
    ],
    resize_keyboard=True
)

# Клавиатура для админа
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤 Получить сообщение")]
    ],
    resize_keyboard=True
)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    if message.from_user.id == ADMIN_ID:
        await message.answer(
            "👋 Привет, Админ!\n\n"
            "Я бот для обратной связи.\n"
            "Нажмите '👤 Получить сообщение', чтобы читать сообщения от пользователей.\n"
            "Чтобы ответить пользователю, просто ответьте на его сообщение реплаем.",
            reply_markup=admin_keyboard
        )
    else:
        await message.answer(
            "👋 Привет! Это бот обратной связи.\n\n"
            "Нажмите '📝 Написать сообщение', чтобы отправить сообщение администратору.",
            reply_markup=user_keyboard
        )


@dp.message(Text("📝 Написать сообщение"))
async def write_message(message: Message):
    """Пользователь начинает писать сообщение"""
    await message.answer(
        "✍️ Напишите ваше сообщение. Оно будет отправлено администратору."
    )
    # Устанавливаем флаг, что пользователь собирается отправить сообщение
    user_sessions[message.from_user.id] = {"waiting_for_message": True}


@dp.message(Text("👤 Получить сообщение"))
async def get_messages(message: Message):
    """Админ запрашивает сообщения"""
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("📨 Ожидайте новые сообщения от пользователей...")


@dp.message()
async def handle_messages(message: Message):
    """Обработка всех сообщений"""
    user_id = message.from_user.id

    # Если это админ и он отвечает реплеем на сообщение пользователя
    if user_id == ADMIN_ID and message.reply_to_message:
        original_message = message.reply_to_message

        # Извлекаем ID пользователя из текста оригинального сообщения
        # Формат: "От пользователя: {user_id}\n\n{текст}"
        if original_message.text and original_message.text.startswith("От пользователя:"):
            try:
                lines = original_message.text.split("\n\n")
                target_user_id = int(lines[0].replace("От пользователя: ", ""))

                # Пересылаем ответ пользователю
                await bot.send_message(
                    target_user_id,
                    f"📬 Ответ от администратора:\n\n{message.text if message.text else message.caption}"
                )
                await message.answer("✅ Ответ отправлен пользователю!")
                return
            except (ValueError, IndexError):
                pass

    # Если это обычное сообщение от пользователя (не команда и не кнопка)
    if user_id != ADMIN_ID and not message.text.startswith("/"):
        # Проверяем, ожидает ли бот сообщение от этого пользователя
        if user_sessions.get(user_id, {}).get("waiting_for_message"):
            # Формируем сообщение для админа
            admin_message = (
                f"От пользователя: {user_id}\n\n"
                f"{message.text if message.text else message.caption if message.caption else 'Медиафайл'}"
            )

            # Отправляем сообщение админу
            try:
                if message.photo:
                    await bot.send_photo(
                        ADMIN_ID,
                        photo=message.photo[-1].file_id,
                        caption=admin_message
                    )
                elif message.document:
                    await bot.send_document(
                        ADMIN_ID,
                        document=message.document.file_id,
                        caption=admin_message
                    )
                elif message.voice:
                    await bot.send_voice(
                        ADMIN_ID,
                        voice=message.voice.file_id,
                        caption=admin_message
                    )
                else:
                    await bot.send_message(ADMIN_ID, admin_message)

                # Сбрасываем состояние ожидания
                user_sessions[user_id]["waiting_for_message"] = False

                # Подтверждаем пользователю
                await message.answer("✅ Ваше сообщение отправлено администратору!")

            except Exception as e:
                logging.error(f"Ошибка отправки сообщения: {e}")
                await message.answer("❌ Произошла ошибка при отправке сообщения.")


async def main():
    """Запуск бота"""
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
