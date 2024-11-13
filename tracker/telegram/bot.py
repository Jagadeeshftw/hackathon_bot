import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandObject, CommandStart
from aiogram.types.message import Message
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.keyboard import ReplyKeyboardBuilder, ReplyKeyboardMarkup
from dotenv import load_dotenv

from tracker import ISSUES_URL, PULLS_URL, get_issues_without_pull_requests
from tracker.utils import create_telegram_user, get_all_repostitories, get_user

load_dotenv()

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

bot = Bot(
    token=os.environ.get("TELEGRAM_BOT_TOKEN", str()),
    default=DefaultBotProperties(parse_mode="HTML"),
)
dp = Dispatcher()


@dp.message(CommandStart(deep_link=True, deep_link_encoded=True))
async def auth_link_handler(message: Message, command: CommandObject) -> None:
    """
    deep link handler saving the uuid and tracked repos by this user into db
    :param message: aiogram.types.Message object
    :param command: aiogram.filters.CommandObject object
    :return: None
    """
    uuid = command.args
    user = await get_user(uuid)

    await create_telegram_user(
        user=next(iter(user)), telegram_id=str(message.from_user.id)
    )
    await message.answer(
        f"Hello {message.from_user.mention_html()}!\n"
        f"Would you like to check some issues?",
        reply_markup=issue_button(),
    )


@dp.message(CommandStart())
async def start_message(message: Message) -> None:
    """
    A function that starts the bot.
    :param message: Message that starts the bot.
    :return: None
    """
    await message.answer(
        f"Hello {message.from_user.mention_html()}!\n"
        f"Would you like to check some issues?",
        reply_markup=issue_button(),
    )


@dp.message(F.text == "📓get missed deadlines📓")
async def send_deprecated_issue_assignees(msg: Message) -> None:
    """
    Sends information about assignees that missed the deadline.
    :param msg: Message instance for communication with a user
    :return: None
    """
    all_repositories = await get_all_repostitories(msg.from_user.id)

    for repository in all_repositories:
        issues = get_issues_without_pull_requests(
            issues_url=ISSUES_URL.format(
                owner=repository.get("author", str()),
                repo=repository.get("name", str()),
            ),
            pull_requests_url=PULLS_URL.format(
                owner=repository.get("author", str()),
                repo=repository.get("name", str()),
            ),
        )

        message = (
            "=" * 50
            + "\n"
            + f"Repository: {repository.get("author", str())}/{repository.get("name", str())}"
            + "\n"
            + "=" * 50
            + "\n\n"
        )

        for issue in issues:
            message += (
                "-----------------------------------\n"
                "Issue: " + issue.get("title", str()) + "\n"
                "User: " + issue.get("assignee", dict()).get("login", str()) + "\n"
                "Assigned:" + "\n"
                "\t\t\t\tDays ago: " + str(issue["days"]) + "\n"
                "-----------------------------------\n"
            )

        if not issues:
            message += "No missed deadlines."

        await msg.answer(f"<blockquote>{message}</blockquote>")


def issue_button() -> ReplyKeyboardMarkup:
    """
    A function that generates a button that allows the user to click on issues.
    :return: ReplyKeyboardMarkup
    """
    builder = ReplyKeyboardBuilder()
    builder.button(text="📓get missed deadlines📓")

    return builder.as_markup(resize_keyboard=True)


async def create_tg_link(uuid) -> str:
    return await create_start_link(bot=bot, payload=uuid, encode=True)


async def start_tg_bot() -> None:
    """
    A function that starts the bot.
    :return: None
    """
    try:
        await dp.start_polling(bot, polling_timeout=0)

    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(start_tg_bot())
