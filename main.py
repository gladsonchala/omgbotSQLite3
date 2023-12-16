from flask import Flask
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from app import handlers, searcher
from app.handlers import set_global_provider, set_global_preferences, add_admin_id, delete_admin_id, link_handler
from strings import bot_token

app = Flask(__name__)

def main():
    updater = Updater(token=bot_token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", handlers.start))
    dispatcher.add_handler(CommandHandler("help", handlers.help_command))
    dispatcher.add_handler(CommandHandler("developer", handlers.developer))
    dispatcher.add_handler(CommandHandler("setprovider", handlers.set_provider_name))
    dispatcher.add_handler(CommandHandler("clearsession", handlers.clear_session))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handlers.handle_message))
    dispatcher.add_handler(CommandHandler("fetch", handlers.fetch))
    dispatcher.add_handler(CommandHandler("search", searcher.search_command_handler))
    dispatcher.add_handler(CommandHandler("searchon", searcher.enable_search))
    dispatcher.add_handler(CommandHandler("searchoff", searcher.disable_search))
    dispatcher.add_handler(CommandHandler("setglobalprovider", set_global_provider))
    dispatcher.add_handler(CommandHandler("setglobalpreferences", set_global_preferences))
    dispatcher.add_handler(CommandHandler("addadminid", add_admin_id))
    dispatcher.add_handler(CommandHandler("deleteadminid", delete_admin_id))
    dispatcher.add_handler(CommandHandler("link", link_handler))

    # Note: Using Gunicorn for production deployment
    # Example command to run the application with Gunicorn:
    # gunicorn -w 4 -b 0.0.0.0:81 main:app
    # Adjust the number of workers (-w) as needed based on your server's capabilities

if __name__ == '__main__':
    main()
