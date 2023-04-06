import logging
from telegram.ext import Application, MessageHandler, filters
from telegram.ext import CommandHandler
from chem_utils import *

# логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)
logger = logging.getLogger(__name__)


# после вызова /start
async def start(update, context):
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет {user.mention_html()}! Вводи на одной строке через пробел, в самих формулах веществ пробелов нет.")


async def help_command(update, context):
    await update.message.reply_text("Вводи на одной строке через пробел, в самих формулах веществ пробелов нет.")


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
    await update.message.reply_text()


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
