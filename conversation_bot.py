#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0613, C0116, C0103
# type: ignore[union-attr]
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
from research import Research
from decouple import config

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    PicklePersistence,
    CallbackContext,
)

import os

PORT = int(os.environ.get("PORT", 5000))

TOKEN = config("TOKEN")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

(
    CHOOSING,
    TYPING_URL,
    TYPING_NAME,
    LISTING,
    MODIFYING,
    MODIFYING_NAME,
    REMOVING,
) = range(7)

reply_keyboard = [
    ["Track", "List"],
    ["Modify", "Remove"],
    ["Done"],
]
markup = ReplyKeyboardMarkup(
    reply_keyboard, one_time_keyboard=True, resize_keyboard=True
)


def facts_to_str(user_data):
    facts = list()

    for key, value in user_data.items():
        facts.append(f"{key} - {value}")

    return "\n".join(facts).join(["\n", "\n"])


def start(update: Update, context: CallbackContext) -> None:
    reply_text = "Hi! My name is SubitoBot."
    if context.user_data:
        researches = context.user_data["researches"]
        # Start the tracking routine
        reply_text += "\n\nYou already monitoring these researches:\n"
        for research in researches:
            reply_text += research.print_research()
            routine_context = {
                "chat_id": update.message.chat_id,
                "research": research,
            }
            context.job_queue.run_repeating(
                send_notification, 60, context=routine_context, name=research.name
            )

    else:
        context.user_data["researches"] = []

    # context.user_data["researches"] = []
    reply_text += (
        "\n\n- Choose Track to start monitoring a new research on Subito.it.\n"
        "- Choose List to see the researches you are tracking.\n"
        "- Choose Modify to modify an existing research.\n"
        "- Choose Remove to delete a research."
    )

    update.message.reply_text(reply_text, reply_markup=markup)

    return CHOOSING


def type_url(update: Update, context: CallbackContext) -> None:
    reply_text = "Sure! Send me the URL of the research you would like to track.\n"
    update.message.reply_text(reply_text)

    return TYPING_URL


def type_name(update: Update, context: CallbackContext) -> None:
    url = update.message.text

    # Check if the URL is valid!

    # Check if this URL is already tracked
    if any(research.url == url for research in context.user_data["researches"]):
        reply_text = f"This URL is already tracked.\n"
        update.message.reply_text(reply_text, reply_markup=markup)
        return CHOOSING

    # If it's not present, create new Research object and add it to the list
    new_research = Research(url)
    new_research.get_items_on_sale()
    context.user_data["researches"].append(new_research)

    # Now ask the user to write the name
    reply_text = f"Now write me the name of this research.\n"
    update.message.reply_text(reply_text)
    return TYPING_NAME


def finalize_tracking(update: Update, context: CallbackContext) -> None:
    name = update.message.text

    # Check if this name is already present
    if any(research.name == name for research in context.user_data["researches"]):
        reply_text = f"This name is already taken. Use a different one.\n"
        update.message.reply_text(reply_text)
        return TYPING_NAME

    # If it's not present, change name to the last object of the list
    context.user_data["researches"][-1].change_name(name)
    new_research = context.user_data["researches"][-1]

    # Start the tracking routine for this research
    routine_context = {
        "chat_id": update.message.chat_id,
        "research": context.user_data["researches"][-1],
    }
    context.job_queue.run_repeating(
        send_notification, 60, context=routine_context, name=name
    )

    reply_text = f"Okay! I will notify you whenever something new is available."
    update.message.reply_text(reply_text, reply_markup=markup)
    return CHOOSING


def send_notification(context: CallbackContext):
    research = context.job.context["research"]
    old_items_price_list = research.items_price_list
    research.get_items_on_sale()

    check = set(research.items_price_list).issubset(set(old_items_price_list))

    if check is False:
        # If check is true the old list contains all the elements of the new one
        # So this means they are equal or some ads have been removed

        # Otherwise, the new list is not equal to or a subset of the old ond
        # So this means someone inserted a new ad
        reply_message = f"There are new results for {research.print_research()}.\n"

        context.bot.send_message(
            chat_id=context.job.context["chat_id"], text=reply_message
        )


def list_research(update: Update, context: CallbackContext) -> None:
    # Check if the user has already added at least one research
    if not context.user_data["researches"]:
        reply_text = f"You have not added something to track yet.\n"
        update.message.reply_text(reply_text, reply_markup=markup)
        return CHOOSING

    # Else select the user research list and print it
    researches = context.user_data["researches"]
    reply_text = f"These are the researches you are following.\n"
    for research in researches:
        reply_text += research.print_research()

    update.message.reply_text(reply_text, reply_markup=markup)
    return CHOOSING


def modify_research(update: Update, context: CallbackContext) -> None:
    # If there are saved researches, then choose which to modify
    if not context.user_data["researches"]:
        reply_text = f"You have not added something to track yet.\n"
        update.message.reply_text(reply_text, reply_markup=markup)
        return CHOOSING

    reply_text = "Sure! Select which research you would like to modify.\n"
    # Select all saved researches and print them on a ReplyMarkupKeyboard
    research_list = context.user_data["researches"]
    name_list = []
    for res in research_list:
        name_list.append([res.name])

    markup = ReplyKeyboardMarkup(
        name_list, one_time_keyboard=True, resize_keyboard=True
    )
    update.message.reply_text(reply_text, reply_markup=markup)
    return MODIFYING


def modify_name(update: Update, context: CallbackContext) -> None:
    name = update.message.text
    context.user_data["old_name"] = name

    # Now ask the user to write the name
    reply_text = f"Now write me the new name.\n"
    update.message.reply_text(reply_text)

    return MODIFYING_NAME


def finalize_modifying(update: Update, context: CallbackContext) -> None:
    new_name = update.message.text
    old_name = context.user_data["old_name"]
    del context.user_data["old_name"]

    # Modify in research list the query with the received name
    for i, res in enumerate(context.user_data["researches"]):
        if res.name == old_name:
            context.user_data["researches"][i].name = new_name
            # Modify also the routine in the job queue
            for job in context.job_queue.get_jobs_by_name(old_name):
                # Remove old one
                job.schedule_removal()

                # Create new one
                routine_context = {
                    "chat_id": update.message.chat_id,
                    "research": res,
                }
                context.job_queue.run_repeating(
                    send_notification, 60, context=routine_context, name=new_name
                )
            reply_text = "Name successfully changed!"
            update.message.reply_text(reply_text, reply_markup=markup)
            break

    return CHOOSING


def remove_research(update: Update, context: CallbackContext) -> None:
    if not context.user_data["researches"]:
        reply_text = f"You have not added something to track yet.\n"
        update.message.reply_text(reply_text, reply_markup=markup)
        return CHOOSING

    # If there are saved researches, then choose which to remove
    reply_text = "Sure! Select which research you would like to remove.\n"
    # Select all saved researches and print them on a ReplyMarkupKeyboard
    research_list = context.user_data["researches"]
    name_list = []
    for res in research_list:
        name_list.append([res.name])

    markup = ReplyKeyboardMarkup(
        name_list, one_time_keyboard=True, resize_keyboard=True
    )
    update.message.reply_text(reply_text, reply_markup=markup)
    return REMOVING


def finalize_removing(update: Update, context: CallbackContext) -> None:
    name = update.message.text

    # Remove from research list the query with the received name
    for i, res in enumerate(context.user_data["researches"]):
        if res.name == name:
            del context.user_data["researches"][i]
            # Remove also the routine from job queue
            for job in context.job_queue.get_jobs_by_name(name):
                job.schedule_removal()
            reply_text = "Query successfully removed!"
            update.message.reply_text(reply_text, reply_markup=markup)
            break

    return CHOOSING


def done(update: Update, context: CallbackContext) -> None:
    if "choice" in context.user_data:
        del context.user_data["choice"]

    update.message.reply_text("Bye!")
    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    # Create the Updater and pass it your bot's token.
    pp = PicklePersistence(filename="conversationbot")
    updater = Updater(TOKEN, persistence=pp, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(
                    Filters.regex("^(Track)$"),
                    type_url,
                ),
                MessageHandler(
                    Filters.regex("^(List)$"),
                    list_research,
                ),
                MessageHandler(
                    Filters.regex("^(Modify)$"),
                    modify_research,
                ),
                MessageHandler(
                    Filters.regex("^(Remove)$"),
                    remove_research,
                ),
            ],
            TYPING_URL: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex("^Done$")),
                    type_name,
                )
            ],
            TYPING_NAME: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex("^Done$")),
                    finalize_tracking,
                )
            ],
            MODIFYING: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex("^Done$")),
                    modify_name,
                )
            ],
            MODIFYING_NAME: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex("^Done$")),
                    finalize_modifying,
                )
            ],
            REMOVING: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex("^Done$")),
                    finalize_removing,
                )
            ],
        },
        fallbacks=[MessageHandler(Filters.regex("^Done$"), done)],
        name="my_conversation",
        persistent=True,
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()
    # updater.start_webhook(listen="0.0.0.0", port=int(PORT), url_path=TOKEN)
    # updater.bot.setWebhook("https://blooming-citadel-68071.herokuapp.com/" + TOKEN)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
