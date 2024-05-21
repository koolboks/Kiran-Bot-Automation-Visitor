import os
import asyncio

from playwright.async_api import async_playwright
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackContext, CommandHandler, \
    CallbackQueryHandler

from config import TELEGRAM_TOKEN
from manage_json import load_json, save_json
from loguru import logger as log

telegram_bot_link = 'https://t.me/newBotFillerBot'

# Initialize the Telegram bot
API_TOKEN = TELEGRAM_TOKEN


# Function to greet the user and display the menu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username  # Assuming the username is available

    photo_url = "https://imgur.com/a/ipOjcQU"  # Replace with the actual URL of the photo
    caption = f"Hey @{username}\nWelcome to Form Filler for New Zealand Application!\nHow can I assist you today?\n\nYou can use /menu to display all available options."

    await update.effective_message.reply_photo(photo_url, caption=caption, parse_mode="HTML")


async def menu_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(text="Select Browser", callback_data='select_browser')],
        [InlineKeyboardButton(text="Upload/Input Your Data", callback_data='upload_data')],
        [InlineKeyboardButton(text="Start Form Filling", callback_data='start_form_filling')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_message.reply_text("Please select an option from the menu:", reply_markup=reply_markup)


# settings adjustment from Telegram
from manage_json import load_json, save_json

bot_manual_setting = False
preview = False
is_launched = False


async def menu(update, context):
    # Load settings from the JSON file
    settings_data = load_json(filename="settings.json")

    MANUAL = settings_data.get("MANUAL", False)  # Default value "no" if not found
    ALWAYS_SHOW_PREVIEW = settings_data.get("ALWAYS_SHOW_PREVIEW", "yes")  # Default value "yes" if not found
    IS_LAUNCHED = settings_data.get("IS_LAUNCHED", "yes")

    keyboard = [
        [
            InlineKeyboardButton(
                f"Manual ✅" if settings_data.get("MANUAL", False) else "Manual ❌",
                callback_data="toggle_manual"),
            InlineKeyboardButton(
                "Preview ✅" if settings_data.get("ALWAYS_SHOW_PREVIEW",
                                                 False) else "Preview ❌",
                callback_data="toggle_preview"),
        ],
        [InlineKeyboardButton("Select Browser 🌐", callback_data="select_browser")],
        [InlineKeyboardButton("Upload Data 📤", callback_data="upload_data")],
        [InlineKeyboardButton(
            "Launch." if settings_data.get("IS_LAUNCHED", False) else "Launch ..",
            callback_data="start_form_filling")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Adjust settings:", reply_markup=reply_markup)

    return bot_manual_setting, preview, is_launched


async def process_callback(update, context):
    global bot_manual_setting, preview, is_launched

    query = update.callback_query
    data = query.data

    settings_data = load_json(filename="settings.json")

    try:

        if data == "toggle_manual":
            bot_manual_setting = not bot_manual_setting
            settings_data["MANUAL"] = not settings_data['MANUAL']
            # print(' settings_data["MANUAL"]',   settings_data["MANUAL"])
            # Save the updated settings to the JSON file
            save_json(settings_data, filename="settings.json")


            await query.answer("Automatic Enabled" if not settings_data['MANUAL'] else "Manual Mode Enabled", show_alert=False)
            # Update the inline keyboard buttons with the new settings
            keyboard = [
                [
                    InlineKeyboardButton(
                        f"Manual ✅" if settings_data.get("MANUAL",False)  else "Manual ❌",
                        callback_data="toggle_manual"),
                    InlineKeyboardButton(
                        "Preview ✅" if settings_data.get("ALWAYS_SHOW_PREVIEW",
                                                         False) else "Preview ❌",
                        callback_data="toggle_preview"),
                ],
                [InlineKeyboardButton("Select Browser 🌐", callback_data="select_browser")],
                [InlineKeyboardButton("Upload Data 📤", callback_data="upload_data")],
                [InlineKeyboardButton(
                    "Launch." if settings_data.get("IS_LAUNCHED", False) else "Launch ..",
                    callback_data="start_form_filling")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_reply_markup(reply_markup=reply_markup)






        elif data == "toggle_preview":
            await query.answer("Preview toggle !")

            settings_data["ALWAYS_SHOW_PREVIEW"] = not settings_data["ALWAYS_SHOW_PREVIEW"]
            # Save the updated settings to the JSON file
            save_json(settings_data, filename="settings.json")

            await query.answer("Preview Enabled" if settings_data['ALWAYS_SHOW_PREVIEW'] else "Preview  Mode Disabled", show_alert=True)
            # Update the inline keyboard buttons with the new settings


            # Update the inline keyboard buttons with the new settings
            keyboard = [
                [
                    InlineKeyboardButton(
                        f"Manual ✅" if settings_data.get("MANUAL", False) else "Manual ❌",
                        callback_data="toggle_manual"),
                    InlineKeyboardButton(
                        "Preview ✅" if settings_data.get("ALWAYS_SHOW_PREVIEW",False)  else "Preview ❌",
                        callback_data="toggle_preview"),
                ],
                [InlineKeyboardButton("Select Browser 🌐", callback_data="select_browser")],
                [InlineKeyboardButton("Upload Data 📤", callback_data="upload_data")],
                [InlineKeyboardButton(
                    "Launch." if settings_data.get("IS_LAUNCHED", False) else "Launch ..",
                    callback_data="start_form_filling")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_reply_markup(reply_markup=reply_markup)
            # Save the updated settings to the JSON file
            save_json(settings_data, filename="settings.json")


        elif data == 'select_browser':
            await query.answer("Select Browser !")
            keyboard = [
                [InlineKeyboardButton(text="FireFox", callback_data='firefox')],
                [InlineKeyboardButton(text="Chrome", callback_data='chrome'),
                 InlineKeyboardButton(text="Webkit", callback_data='webkit')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(chat_id=update.effective_message.chat_id, text="Please select an option:",
                                           reply_markup=reply_markup)
        elif data == 'upload_data':
            # Implement the logic to upload/input data
            await query.answer()

            await context.bot.send_message(chat_id=update.effective_message.chat_id,
                                           text="Please send me the data.csv now !")


        elif data == "start_form_filling":
            await query.answer("button Clicked")

            is_launched = not is_launched

            settings_data["IS_LAUNCHED"] = not settings_data["IS_LAUNCHED"]

            save_json(settings_data, filename="settings.json")

            # Update the inline keyboard buttons with the new settings

            settings_data = load_json('settings.json')

            keyboard = [
                [
                    InlineKeyboardButton(
                        f"Manual ✅" if settings_data.get("MANUAL", False) else "Manual ❌",
                        callback_data="toggle_manual"),
                    InlineKeyboardButton(
                        "Preview ✅" if settings_data.get("ALWAYS_SHOW_PREVIEW",
                                                         False) else "Preview ❌",
                        callback_data="toggle_preview"),
                ],
                [InlineKeyboardButton("Select Browser 🌐", callback_data="select_browser")],
                [InlineKeyboardButton("Upload Data 📤", callback_data="upload_data")],
                [InlineKeyboardButton(
                    "Launch." if settings_data.get("IS_LAUNCHED") else "Launch ..",
                    callback_data="start_form_filling")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_reply_markup(reply_markup=reply_markup)

            await context.bot.send_message(chat_id=update.effective_message.chat_id,

                                           text="You are about to launch and start filling form please ensure your data are correct\nreply with 'Y' to start and 'N' to cancel")


    except Exception as e:
        pass


    # return bot_manual_setting, preview, is_launched


# async def process_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     data = query.data
#
#     if data == 'select_browser':
#         keyboard = [
#             [InlineKeyboardButton(text="FireFox", callback_data='firefox')],
#             [InlineKeyboardButton(text="Chrome", callback_data='chrome'),
#              InlineKeyboardButton(text="Webkit", callback_data='webkit')]
#         ]
#         reply_markup = InlineKeyboardMarkup(keyboard)
#         await context.bot.send_message(chat_id=update.effective_message.chat_id, text="Please select an option:",
#                                        reply_markup=reply_markup)
#     elif data == 'upload_data':
#         # Implement the logic to upload/input data
#         await context.bot.send_message(chat_id=update.effective_message.chat_id,
#                                        text="Please send me the data.csv now !")
#
#     elif data == 'start_form_filling':
#         await context.bot.send_message(chat_id=update.effective_message.chat_id,
#                                        text="You are about to launch and start filling form please ensure your data are correct\nreply with 'Y' to start and 'N' to cancel")
#
#     elif data == "toggle_manual":
#         bot_manual_setting = not bot_manual_setting
#         MANUAL = "yes" if bot_manual_setting else "no"
#     elif data == "toggle_preview":
#         preview = not preview
#         ALWAYS_SHOW_PREVIEW = "yes" if preview else "no"

# async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     data = update.message.text.lower()
#     new_data = {"user_confirmed": False}
#
#
#     if data == "y":
#
#         json_data = load_json()
#
#         if json_data.get("is_launched"):
#             await update.message.reply_text("Already launched the browser.........", reply_to_message_id=update.message.message_id)
#             return
#
#         new_data["is_launched"] = True
#         save_json(new_data)
#
#         message=await update.message.reply_text("Launching.........", reply_to_message_id=update.message.message_id)
#         # await main(update, context)
#         from new_zealand_2 import main
#
#         try:
#             await main(update=message)
#         except KeyboardInterrupt:
#             new_data = {}
#             new_data["is_launched"] = False
#             save_json(new_data)
#             await update.message.reply_text("Bot has beend stopped by user", reply_to_message_id=update.message.message_id)
#         except Exception as e:
#             new_data = {}
#             new_data["is_launched"] = False
#             save_json(new_data)
#             await update.message.reply_text(f"Bot has been stop but there is an error{e}",
#                                             reply_to_message_id=update.message.message_id)
#
#
#     elif data == "yes":
#
#         new_data["user_confirmed"] = True
#         save_json(new_data)
#
#     elif data == "no":
#         new_data["user_confirmed"] = False
#         save_json(new_data)
#         context.bot.send_message(chat_id=update.effective_chat.id,
#                                  text="Okay, staying on the current page.")

import threading

terminate_event = threading.Event()


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global runing_task
    if update.message.document:
        document = update.message.document
        # print(document)
        # Check if the document is a CSV file

        if document.mime_type == 'text/comma-separated-values' or document.mime_type == 'text/csv':
            # Check if the file name is correct
            if check_file_name(document.file_name):
                # Get the file object
                file_obj = await context.bot.get_file(document.file_id)
                # Download the file as bytes

                file_content = await file_obj.download_as_bytearray()
                # Save the file as data.csv
                with open("../data.csv", "wb") as f:
                    f.write(file_content)
                # Notify the user that the file is saved
                await update.message.reply_text("The CSV file has been saved as 'data.csv'.",
                                                reply_to_message_id=update.message.message_id)
            else:
                await update.message.reply_text("Please ensure the file name is 'data.csv'.",
                                                reply_to_message_id=update.message.message_id)
        else:
            await update.message.reply_text("Please upload a CSV file.", reply_to_message_id=update.message.message_id)
    else:
        #     update.message.reply_text("Please upload a document.")

        data = update.message.text.lower()
        new_data = {"user_confirmed": False}
        if data == "y":
            json_data = load_json()

            if json_data.get("is_launched"):
                await update.message.reply_text("Already launched the browser.........",
                                                reply_to_message_id=update.message.message_id)
                return

            new_data["is_launched"] = True
            save_json(new_data)

            message = await update.message.reply_text("Launching.........",
                                                      reply_to_message_id=update.message.message_id)

            # Define a function to run the main function asynchronously
            async def run_main_async():
                # from new_zealand_ import main
                from visitor_visitor import main
                try:
                    await main(update=message, bot=update)
                except KeyboardInterrupt:
                    new_data = {"is_launched": False, "user_confirmed": False}
                    save_json(new_data)
                    # message.reply_text("Bot has been stopped by user")
                except Exception as e:
                    print(e)
                    pass
                    # new_data = {}
                    # new_data["is_launched"] = False
                    # save_json(new_data)
                finally:
                    new_data = {"is_launched": False, "user_confirmed": False}
                    save_json(new_data)
                    print("Saved !")

                    import traceback
                    traceback.print_exc()

                    # message.reply_text(f"Bot has been stopped due to an error: {e}")

            # Run the main function asynchronously
            runing_task = asyncio.create_task(run_main_async())

            # # Define a function to run the main function in a separate thread
            # def run_main_thread():
            #     from new_zealand_ import main
            #     try:
            #         loop = asyncio.new_event_loop()
            #         asyncio.set_event_loop(loop)
            #         loop.run_until_complete(main(update=message, bot=update))
            #     except KeyboardInterrupt:
            #         new_data = {"is_launched": False, "user_confirmed": False}
            #         save_json(new_data)
            #         # message.reply_text("Bot has been stopped by user")
            #     except Exception as e:
            #         print(e)
            #         pass
            #         # new_data = {}
            #         # new_data["is_launched"] = False
            #         # save_json(new_data)
            #     finally:
            #         new_data = {"is_launched": False, "user_confirmed": False}
            #         save_json(new_data)
            #         print("Saved !")
            #
            #         import traceback
            #         traceback.print_exc()
            #
            #         # message.reply_text(f"Bot has been stopped due to an error: {e}")
            #
            # # Start a new thread to run the main function
            # main_thread = threading.Thread(target=run_main_thread)
            # main_thread.start()
        elif data == 'force':
            new_data["is_launched"] = False
            save_json(new_data)
            message = await update.message.reply_text(
                "Cache Clear and Browser Restore !\n\n please use 'Y' to Launch again...",
                reply_to_message_id=update.message.message_id)
        elif data == "ok":
            new_data["user_confirmed_proceed"] = '3'
            save_json(new_data)
            await update.message.reply_text("Ok i will move on please give me 12 sec....  ...",
                                            reply_to_message_id=update.message.message_id)

        elif data == "never":
            new_data["user_confirmed_proceed"] = '2'
            save_json(new_data)
            await update.message.reply_text("Ok i will close the pop up now !  ...",
                                            reply_to_message_id=update.message.message_id)

        elif data == "yes":
            new_data["user_confirmed"] = True
            save_json(new_data)

            await update.message.reply_text("Got it ...", reply_to_message_id=update.message.message_id)

        elif data == "no":
            new_data["user_confirmed"] = False
            save_json(new_data)
            await update.message.reply_text("Ok waiting for your yes", reply_to_message_id=update.message.message_id)
        elif data == "stop" or data == 's':

            await update.message.reply_text("stopping the chrome now use 'y' to relaunch",
                                            reply_to_message_id=update.message.message_id)
            try:

                r = runing_task.cancel("OK cancleed")
            except:

                await update.message.reply_text("No Chrome is currently open use 'Y' to re launch",
                                                reply_to_message_id=update.message.message_id)


def stop_main_thread():
    terminate_event.set()  # Set the Event to signal termination


def check_file_name(file_name):
    name, extension = os.path.splitext(file_name)
    return name.lower() == 'data' and extension.lower() == '.csv'


def main():
    try:

        log.info("Launching Application.........")
        log.info("Application Launched Successfully\nYou don't have to come here often")
        print('\n')
        log.info(f"Please visit : {telegram_bot_link} to start bot")
        application = ApplicationBuilder().token(API_TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("menu", menu))
        # application.add_handler(CommandHandler("setting", adjust_settings_from_telegram))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND | filters.ATTACHMENT, message_handler))
        application.add_handler(CallbackQueryHandler(process_callback))

        application.run_polling()
    except Exception as e:
        print(e, "from telegram people ")
    finally:
        new_data = {"is_launched": False, "user_confirmed": False}
        save_json(new_data)
        print("Saved !", "from telegram people")


if __name__ == '__main__':
    main()
