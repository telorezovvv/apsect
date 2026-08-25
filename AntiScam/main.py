import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.enums import ChatMemberStatus
from aiogram.types import URLInputFile

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = "8845413737:AAE46zxhDbpEpqBK5HJbbFVOA7MCiGEu9uA"  # Токен бота от @BotFather
CHANNEL_ID = -1004443036308  # ID канала (отрицательное число, можно узнать у @getmyid_bot)
CHANNEL_INVITE_LINK = "https://t.me/+5slr_856RjtkNmEy"  # Ссылка-приглашение в канал

# ========== ИНИЦИАЛИЗАЦИЯ ==========
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище для отслеживания проверок (опционально)
user_check_status = {}


# ========== КЛАВИАТУРЫ ==========
def get_subscription_keyboard():
    """Клавиатура для проверки подписки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Подписаться на канал", url=CHANNEL_INVITE_LINK)
        ],
        [
            InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription")
        ]
    ])
    return keyboard


def get_main_keyboard():
    """Главная клавиатура (после успешной подписки)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Поиск пользователя", switch_inline_query_current_chat="")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")
        ]
    ])
    return keyboard


# ========== ПРОВЕРКА ПОДПИСКИ ==========
async def is_subscribed(user_id: int) -> bool:
    """Проверяет, подписан ли пользователь на канал"""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    except Exception as e:
        logging.error(f"Ошибка проверки подписки для {user_id}: {e}")
        return False


async def ensure_subscription(message: Message) -> bool:
    """Проверяет подписку и отправляет соответствующее сообщение"""
    user_id = message.from_user.id

    if await is_subscribed(user_id):
        return True

    # Пользователь не подписан
    await message.answer(
        "🔒 **Доступ запрещен!**\n\n"
        "Для использования бота необходимо подписаться на наш закрытый канал.\n"
        "Нажмите кнопку ниже, чтобы подать заявку на вступление.\n\n"
        "⚠️ **Важно:** После подачи заявки и одобрения админом, "
        "нажмите кнопку «Проверить подписку».",
        reply_markup=get_subscription_keyboard(),
        parse_mode="Markdown"
    )
    return False


# ========== ПОИСК НА ПЛАТФОРМАХ ==========
async def search_reddit(username: str) -> str | None:
    """Поиск на Reddit через публичное API"""
    try:
        url = f"https://www.reddit.com/user/{username}/about.json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "data" in data:
                        return f"https://reddit.com/user/{username}"
    except:
        pass
    return None


async def search_github(username: str) -> str | None:
    """Поиск на GitHub через публичное API"""
    try:
        url = f"https://api.github.com/users/{username}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return f"https://github.com/{username}"
    except:
        pass
    return None


async def search_youtube(username: str) -> str | None:
    """Поиск YouTube канала"""
    try:
        url = f"https://www.youtube.com/@{username}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return url
    except:
        pass
    return None


async def search_twitter(username: str) -> str | None:
    """Поиск в Twitter/X"""
    try:
        url = f"https://twitter.com/{username}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return url
    except:
        pass
    return None


async def search_instagram(username: str) -> str | None:
    """Поиск в Instagram"""
    try:
        url = f"https://www.instagram.com/{username}/"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return url
    except:
        pass
    return None


async def search_telegram(username: str) -> str | None:
    """Поиск в Telegram"""
    try:
        user = await bot.get_chat(f"@{username}")
        if user:
            return f"https://t.me/{username}"
    except:
        pass
    return None


async def search_vk(username: str) -> str | None:
    """Поиск ВКонтакте"""
    try:
        url = f"https://vk.com/{username}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return url
    except:
        pass
    return None


# ========== ОСНОВНАЯ ФУНКЦИЯ ПОИСКА ==========
async def find_user_all_platforms(username: str) -> dict:
    """Ищет пользователя на всех платформах"""
    results = {}

    search_functions = [
        ("Reddit", search_reddit),
        ("GitHub", search_github),
        ("YouTube", search_youtube),
        ("Twitter/X", search_twitter),
        ("Instagram", search_instagram),
        ("Telegram", search_telegram),
        ("VK", search_vk),
    ]

    for platform_name, search_func in search_functions:
        try:
            result = await search_func(username)
            if result:
                results[platform_name] = result
        except Exception as e:
            logging.error(f"Ошибка поиска на {platform_name}: {e}")

    return results


# ========== ХЭНДЛЕРЫ ==========
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id

    # Проверяем подписку
    if await is_subscribed(user_id):
        # Пользователь уже подписан
        await message.answer(
            "👋 **Добро пожаловать!**\n\n"
            "✅ Вы подписаны на наш канал.\n"
            "Теперь вы можете пользоваться ботом.\n\n"
            "📌 **Как использовать:**\n"
            "Просто отправьте мне юзернейм (без @), "
            "и я найду его на всех популярных платформах.",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    else:
        # Пользователь не подписан
        await message.answer(
            "🔒 **Доступ запрещен!**\n\n"
            "Для использования бота необходимо подписаться на наш закрытый канал.\n"
            "Нажмите кнопку ниже, чтобы подать заявку на вступление.\n\n"
            "⚠️ **Важно:** После подачи заявки и одобрения админом, "
            "нажмите кнопку «Проверить подписку».",
            reply_markup=get_subscription_keyboard(),
            parse_mode="Markdown"
        )


@dp.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Проверить подписку'"""
    user_id = callback.from_user.id

    # Проверяем подписку
    if await is_subscribed(user_id):
        await callback.message.delete()  # Удаляем сообщение с кнопками

        await callback.message.answer(
            "✅ **Подписка подтверждена!**\n\n"
            "Теперь вы можете пользоваться ботом.\n"
            "Просто отправьте мне юзернейм (без @).",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer("✅ Подписка подтверждена!", show_alert=True)
    else:
        await callback.answer(
            "❌ Вы еще не подписаны на канал!\n"
            "Подайте заявку на вступление и попробуйте снова.",
            show_alert=True
        )


@dp.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Помощь'"""
    await callback.message.answer(
        "ℹ️ **Помощь по использованию бота:**\n\n"
        "1. Отправьте мне юзернейм (например: `john_doe`)\n"
        "2. Я проверю его наличие на платформах:\n"
        "   • Reddit\n"
        "   • GitHub\n"
        "   • YouTube\n"
        "   • Twitter/X\n"
        "   • Instagram\n"
        "   • Telegram\n"
        "   • VK\n\n"
        "3. Получите ссылки на профили, если они найдены.\n\n"
        "⚠️ **Важно:** Бот работает только для подписчиков канала.",
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.message(F.text)
async def handle_username(message: Message):
    """Обработчик текстовых сообщений (юзернеймов)"""
    # Сначала проверяем подписку
    if not await is_subscribed(message.from_user.id):
        await message.answer(
            "🔒 **Доступ запрещен!**\n\n"
            "Вы не подписаны на наш канал.\n"
            "Используйте команду /start для получения инструкций.",
            parse_mode="Markdown"
        )
        return

    username = message.text.strip()

    # Убираем @ если есть
    if username.startswith("@"):
        username = username[1:]

    # Проверяем, что это похоже на юзернейм
    if not username or len(username) < 3:
        await message.answer(
            "❌ **Некорректный юзернейм**\n\n"
            "Юзернейм должен содержать минимум 3 символа.\n"
            "Допустимы: буквы, цифры, символы _ и ."
        )
        return

    # Поиск
    status_msg = await message.answer(f"🔍 Ищу пользователя @{username} на всех платформах...")

    results = await find_user_all_platforms(username)

    if not results:
        await status_msg.edit_text(
            f"😔 **Пользователь @{username} не найден**\n\n"
            "Проверьте правильность написания юзернейма.\n"
            "Возможно, пользователь зарегистрирован под другим именем."
        )
        return

    # Формируем ответ
    response = f"✅ **Найден пользователь @{username}**\n\n"
    for platform, url in results.items():
        response += f"• **{platform}:** {url}\n"

    response += "\n📌 Нажмите на ссылку, чтобы перейти к профилю."

    await status_msg.edit_text(response, disable_web_page_preview=True)


# ========== ЗАПУСК ==========
async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    print("🤖 Бот запущен!")
    print(f"📢 Канал ID: {CHANNEL_ID}")
    print("✅ Бот готов к работе!")

    # Устанавливаем команды для меню бота
    await bot.set_my_commands([
        types.BotCommand(command="start", description="🔄 Перезапустить бота"),
        types.BotCommand(command="help", description="ℹ️ Помощь"),
    ])

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())