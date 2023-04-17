import logging
from telegram.ext import Application, MessageHandler, filters
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from chem_utils import *

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)
logger = logging.getLogger(__name__)

STATE_INPUT = 1


async def start(update, context):
    user = update.effective_user
    await update.message.reply_html(
        f"Привет {user.mention_html()}!"
        f"Я помогаю с химией. Введите команду /help для получения информации о моих возможностях")


async def help_command(update, context):
    await update.message.reply_text("Список допустимых команд:")
    await update.message.reply_text("Команда /get_reaction - получение рекции и расстановка коэффициентов")
    await update.message.reply_text(
        "Команда /getw_element - рассчитывает массовую долю выбранного элемента в выбранном веществе")
    await update.message.reply_text("Команда /formula - рассчитывает формулу веществ по массовым долям его элементов")
    await update.message.reply_text('Команда /himia_top - выводит сообщение "Химия топ!"')


async def stop(update, context):
    await update.message.reply_text("<Задача отменена>")
    return ConversationHandler.END


async def gen_reaction(update, context):
    await update.message.reply_text("Вводите исходные элементы реакции (через пробел)")
    context.user_data.clear()
    return STATE_INPUT


async def mes(update, context):
    await update.message.reply_text("Химия топ!")


async def accept_inputs(update, context):
    if context.user_data.get("reaction_inputs") is None:
        reaction_inputs = update.message.text.split()
        while len(reaction_inputs) < 2:
            reaction_inputs.append('')
        context.user_data["reaction_inputs"] = reaction_inputs
        try:
            reaction_outputs = fill_reaction(*reaction_inputs)
        except SubstanceDecodeError:
            await update.message.reply_text("Не определены продукты реакции, введите их самостоятельно!")
            await update.message.reply_text("На всякий случай предупреждаю об необходимости осознанного ввода.")
            return STATE_INPUT
        except AutoCompletionError:
            await update.message.reply_text("Не определены продукты реакции, введите их самостоятельно!")
            await update.message.reply_text("На всякий случай предупреждаю об необходимости осознанного ввода.")
            return STATE_INPUT
        except InvalidReactionError as e:
            await update.message.reply_text(f"Ошибка: {e}")
            return ConversationHandler.END
        else:
            context.user_data["reaction_outputs"] = reaction_outputs
            await update.message.reply_text(
                f"Автоматически определены продукты реакции: {', '.join(context.user_data['reaction_outputs'])}")
            await done(update, context)
            return ConversationHandler.END
    elif context.user_data.get("reaction_outputs") is None:
        reaction_outputs = update.message.text.split()
        while len(reaction_outputs) < 2:
            reaction_outputs.append('')
        context.user_data["reaction_outputs"] = reaction_outputs
        await done(update, context)
        return ConversationHandler.END


async def ge(update, context):
    if context.user_data.get("reaction_inputs") is None:
        reaction_inputs = update.message.text.split()
        context.user_data["reaction_inputs"] = reaction_inputs
        await update.message.reply_text(calculate_mass(reaction_inputs[0], reaction_inputs[1]))
        return ConversationHandler.END


async def getw_element(update, context):
    await update.message.reply_text("Введите вещество и формулу (через пробел на одной строке)")
    context.user_data.clear()
    return STATE_INPUT


async def formula(update, context):
    # ?
    await update.message.reply_text("Введите массовые доли элеметов")
    context.user_data.clear()
    return STATE_INPUT


async def done(update, context):
    try:
        ta = fill_coefficients(*context.user_data["reaction_inputs"], *context.user_data["reaction_outputs"])
        await update.message.reply_text(ta)
    except InvalidReactionError:
        await update.message.reply_text(f"Ошибка: {e}")


def main():
    dialog1 = ConversationHandler(
        entry_points=[CommandHandler('gen_reaction', gen_reaction)],
        states={
            STATE_INPUT: [MessageHandler(filters.Regex(r"^[A-Za-z0-9\(\)]*( [A-Za-z0-9\(\)]*|)$"), accept_inputs)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    dialog2 = ConversationHandler(
        entry_points=[CommandHandler('getw_element', getw_element)],
        states={
            STATE_INPUT: [MessageHandler(filters.Regex(r"^[A-Za-z0-9\(\)]*( [A-Za-z0-9\(\)]*|)$"), accept_inputs)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    dialog3 = ConversationHandler(
        entry_points=[CommandHandler('formula', formula)],
        states={
            STATE_INPUT: [MessageHandler(filters.Regex(r"^[A-Za-z0-9\(\)]*( [A-Za-z0-9\(\)]*|)$"), accept_inputs)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    application = Application.builder().token('6118669795:AAFpiYLMNG1pRoLTpZbx0OjegOv7gYzLbsY').build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("himia_top", mes))
    application.add_handler(dialog1)
    application.add_handler(dialog2)
    application.add_handler(dialog3)
    application.run_polling()


if __name__ == '__main__':
    main()
