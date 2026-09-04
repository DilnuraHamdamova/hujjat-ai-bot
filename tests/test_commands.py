from app.bot.commands import default_commands


def test_default_command_menu_contains_supported_commands() -> None:
    commands = default_commands()
    assert [item.command for item in commands] == [
        "start",
        "help",
        "new",
        "stop",
        "my_cv",
        "delete_me",
    ]
