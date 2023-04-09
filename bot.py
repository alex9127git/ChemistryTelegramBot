import logging
from telegram.ext import Application, MessageHandler, filters
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from chem_utils import *


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)
logger = logging.getLogger(__name__)


async def start(update, context):
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет {user.mention_html()}! Я помогаю составлять химические уравнения.")
    await update.message.reply_html(
        r"Для того, чтобы сгенерировать реакцию введите /get_reactiom")


async def help_command(update, context):
    await update.message.reply_text("Ну... Химия топ, а вообще я робот")


async def gen_reaction(update, context):
    await update.message.reply_text("Так, начинаем жёстко генерировать реакшон!")


async def stop(update, context):
    await update.message.reply_text("ОК, задача отменена.")
    return ConversationHandler.END


async def reaction_master(update, context):
    # sub = substance = subscribe :)
    sub1 = update.message.text.split()
    while len(sub1) < 2:
        sub1.append('')
    try:
        spisok = fill_reaction(sub1[0], sub1[1])
        fill_coefficients(sub1[0], sub1[1], spisok[0], spisok[1])
    except SubstanceDecodeError:
        await update.message.reply_text("Не определены продукты реакции, введите их самостоятельно!")
        await update.message.reply_text("На всякий случай предупреждаю об необходимости осознанного ввода.")
        sub2 = update.message.text.split()
        fill_coefficients(sub1[0], sub1[1], sub2[0], sub2[1])
    except AutoCompletionError:
        await update.message.reply_text("Не определены продукты реакции, введите их самостоятельно!")
        await update.message.reply_text("На всякий случай предупреждаю об необходимости осознанного ввода.")
        sub2 = update.message.text.split()
        fill_coefficients(sub1[0], sub1[1], sub2[0], sub2[1])
    except InvalidReactionError:
        await update.message.reply_text("Просьба вводить что-то осознанное с точки зрения химии!")
    return ConversationHandler.END


def main():
    application = Application.builder().token('6118669795:AAFpiYLMNG1pRoLTpZbx0OjegOv7gYzLbsY').build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    text_handler = MessageHandler(filters.TEXT, reaction_master)

    dialog = ConversationHandler(
        entry_points=[CommandHandler('get_reaction', start)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, reaction_master)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    application.add_handler(text_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
