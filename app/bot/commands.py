from aiogram.types import BotCommand


def default_commands() -> list[BotCommand]:
    """Commands shown when the user taps Telegram's slash button."""
    return [
        BotCommand(command="start", description="Asosiy menyu"),
        BotCommand(command="help", description="Yordam"),
        BotCommand(command="new", description="Yangi hujjat yaratish"),
        BotCommand(command="stop", description="Joriy jarayonni to‘xtatish"),
        BotCommand(command="my_cv", description="Oxirgi hujjatni ko‘rish"),
        BotCommand(command="delete_me", description="Barcha ma’lumotlarni o‘chirish"),
    ]
