import logging
from telegram.ext import Application, MessageHandler, filters
from telegram.ext import CommandHandler


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


async def start(update, context):
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет {user.mention_html()}! Ты знаешь, что химия топ?!",
    )


async def echo(update, context):
    await update.message.reply_text("Химия топ!")


async def help_command(update, context):
    await update.message.reply_text("Пока я говорю только, что химия топ. А вы что, не верите?")


async def calculate_coeffs_command(update, context):
    # TODO: Короче, сначала нужно спросить у пользователя исходные вещества в реакции.
    #  Затем ты вызываешь мою функцию fill_reaction из chem_utils, она пытается автоматически задать
    #  продукты реакции. Если они нашлись, вызываешь функцию fill_coefficients и передаешь туда все четыре
    #  вещества. Если не нашлись, спрашиваешь у пользователя продукты реакции, а затем также вызываешь функцию.
    #  В принципе, то что вернула функция можно безболезненно отправить, я уже все отформатировал. Или можешь с этим
    #  побольше повозиться и подобрать лучший вариант если хочешь
    pass


def main():
    application = Application.builder().token('6118669795:AAFpiYLMNG1pRoLTpZbx0OjegOv7gYzLbsY').build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    text_handler = MessageHandler(filters.TEXT, echo)
    application.add_handler(text_handler)
    application.run_polling()


if __name__ == '__main__':
    main()

