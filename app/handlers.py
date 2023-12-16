from telegram import ChatAction, Update
from telegram.ext import CallbackContext

from app.searcher import google_search, send_request, send_request_with_search
from app.utils import get_search_state, latest_key, logger, db, get_user_info
from strings import default_provider, helpmsg, admin_id, admin_ids, user_provider_preferences
from WebScrape import WebScraper


# Command handler for the /start command
def start(update: Update, context: CallbackContext):
  user_id, user_name, username = get_user_info(update)

  try:
    user_message = "Hey OMG, you're talking with user with username {} and his user ID: {}. Say Welcome to OMG Bot to him/her!".format(
        user_name, user_id)

    response = send_request(user_message, user_id, context, update)

    if (response.strip() == ""):
      update.message.reply_text(
          "Hurray, I'm OMG bot!\n```Welcome!```\nAsk me whatever you want.\nUse /help command for more!",
          parse_mode='Markdown')
    else:
      try:
        update.message.reply_text(response, parse_mode='Markdown')
      except Exception as e:
        update.message.reply_text(response)
  except Exception as e:
    logger.error(e)
    update.message.reply_text(
        "Hurray, I'm OMG bot!\n```Welcome!```\nAsk me whatever you want.\nUse /help command for more!",
        parse_mode='Markdown')


# Command handler for the /help command
def help_command(update: Update, context: CallbackContext):
  help_message = helpmsg
  update.message.reply_text(help_message, parse_mode='Markdown')


# Command handler for the /developer command
def developer(update: Update, context: CallbackContext):
  update.message.reply_text("```Developer: Gemechis Chala```\n@ScorpiDev",
                            parse_mode='Markdown')


# Message handler to check search preference and use appropriate method
def handle_message(update: Update, context: CallbackContext):
    user_id, user_name, username = get_user_info(update)
    user_message = "User: " + update.message.text
    context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)

    # Check if search is enabled
    search_enabled = get_search_state(user_id)

    # Choose the appropriate method based on search preference
    if search_enabled:
        search_results = google_search(update.message.text)
        response = send_request_with_search(user_message, search_results, user_id, context, update)
    else:
        response = send_request(user_message, user_id, context, update)

    if (response.strip() == ""):
        response = "Try again, please. I don't get it...\nIf I send this one more times, use /clearsession to clear my brain filled with your conversations."
        update.message.reply_text(response)
    else:
        try:
            update.message.reply_text(response, parse_mode='Markdown')
        except Exception as e:
            update.message.reply_text(response)

    # Store the user's message and AI response in the database
    store_message(user_id, update.message.text, response)

# Handler to log messages to the database
def log(update: Update, context: CallbackContext):
    # Log messages to the database
    store_message(update.message.from_user.id, update.message.text, '')

# Handler to fetch the latest message
def fetch(update: Update, context: CallbackContext):
    # Fetch and reply with the latest message
    user_id = update.message.from_user.id
    messages = get_user_previous_messages(user_id)
    update.message.reply_text(messages)

    # Send an AI response based on the latest message
    ai_response = send_request(update.message.text, user_id, context, update)
    update.message.reply_text(ai_response)

# Command to set provider name
def set_provider_name(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    message_text = update.message.text.strip()

    if message_text == '/setprovider':
        # User wants to reset to the default provider
        # Update the SQLite database with the default provider
        cursor.execute(f"UPDATE chat_data SET preferences = ? WHERE user_id = ?", (default_provider, user_id))
        conn.commit()
        update.message.reply_text(f"Provider name set to the default!")
    else:
        # User wants to set a custom provider
        custom_provider = message_text[len('/setprovider '):]
        # Update the SQLite database with the custom provider
        cursor.execute(f"UPDATE chat_data SET preferences = ? WHERE user_id = ?", (custom_provider, user_id))
        conn.commit()
        update.message.reply_text(
            f"Provider name set to: {custom_provider} for this chat session.\nNote: If you don't know what it is, please click on this: /setprovider to change to default."
        )

# Command handler to clear session
def clear_session(update, context):
    try:
        user_id = update.message.from_user.id
        # Clear the user's session in the SQLite database
        cursor.execute(f"DELETE FROM chat_data WHERE user_id = {user_id}")
        conn.commit()
        update.message.reply_text("Session cleared successfully.")
    except Exception as e:
        logger.error(e)


# Command handler to set provider globally
def set_global_provider(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id == admin_id:
        provider_name = context.args[0] if context.args else default_provider
        # Update the global provider in strings.py
        update_global_provider(provider_name)
        # Update the SQLite database with the global provider for all users
        cursor.execute(f"UPDATE chat_data SET preferences = ?", (provider_name,))
        conn.commit()
        update.message.reply_text(f"Global provider set to: {provider_name}")
    else:
        update.message.reply_text("You don't have permission to use this command.")


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


def link_handler(update, context):
  # Extract user information
  user_id, user_name, username = get_user_info(update)

  # Extract the link from the user's message
  user_message = update.message.text
  if user_message.startswith("/link "):
    url = user_message[len("/link "):].strip()

    # Perform link scraping using WebScraper
    context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
    link_scraper = WebScraper(url)
    scraped_text = link_scraper.scrape_visible_text()
    urlScrapedData = "Link: " + url + "\nThe Webpage Data" + scraped_text

    # Send the scraped text to the AI request
    ai_response = send_request(urlScrapedData, user_id, context, update)

    # Reply to the user with AI response
    try:
      update.message.reply_text(f"{ai_response}", parse_mode='Markdown')
    except Exception:
      update.message.reply_text(ai_response)
  else:
    update.message.reply_text(
        "Invalid command format. Please use '/link <url>'.")


#############################

# Function to update the global provider in strings.py
def update_global_provider(provider_name):
  with open("strings.py", "r") as file:
    data = file.readlines()

  for i, line in enumerate(data):
    if "default_provider" in line:
      data[i] = f'default_provider = "{provider_name}"\n'

  with open("strings.py", "w") as file:
    file.writelines(data)


#############################


# Command handler to set preferences globally
def set_global_preferences(update: Update, context: CallbackContext):
  user_id = update.message.from_user.id
  if user_id in admin_ids:
    # Check if at least one argument is provided
    if not context.args:
      update.message.reply_text(
          "Please provide at least one preference to update.")
      return

    # Get preference name and value from arguments
    preference_name = context.args[0].lower()
    preference_value = " ".join(context.args[1:])

    # Update the global preference in strings.py
    update_global_preference(preference_name, preference_value)
    update.message.reply_text(
        f"Global {preference_name} set to: {preference_value}")
  else:
    update.message.reply_text("You don't have permission to use this command.")


# Function to update the global preference in strings.py
def update_global_preference(preference_name, preference_value):
  with open("strings.py", "r") as file:
    data = file.readlines()

  for i, line in enumerate(data):
    if f"{preference_name} =" in line:
      data[i] = f'{preference_name} = "{preference_value}"\n'

  with open("strings.py", "w") as file:
    file.writelines(data)


######################################


# Command handler to add a user ID to the admin_ids list
def add_admin_id(update: Update, context: CallbackContext):
  user_id = update.message.from_user.id
  if user_id in admin_ids:
    # Check if at least one argument is provided
    if not context.args:
      update.message.reply_text(
          "Please provide a user ID to add to admin_ids.")
      return

    # Get the user ID from the argument
    new_admin_id = int(context.args[0])

    # Add the new user ID to admin_ids if not already present
    if new_admin_id not in admin_ids:
      admin_ids.append(new_admin_id)
      update.message.reply_text(f"User ID {new_admin_id} added to admin_ids.")
    else:
      update.message.reply_text(
          f"User ID {new_admin_id} is already in admin_ids.")
  else:
    update.message.reply_text("You don't have permission to use this command.")


# Command handler to delete a user ID from the admin_ids list
def delete_admin_id(update: Update, context: CallbackContext):
  user_id = update.message.from_user.id
  if user_id in admin_ids:
    # Check if at least one argument is provided
    if not context.args:
      update.message.reply_text(
          "Please provide a user ID to delete from admin_ids.")
      return

    # Get the user ID from the argument
    del_admin_id = int(context.args[0])

    # Delete the user ID from admin_ids if present
    if del_admin_id in admin_ids:
      admin_ids.remove(del_admin_id)
      update.message.reply_text(
          f"User ID {del_admin_id} deleted from admin_ids.")
    else:
      update.message.reply_text(f"User ID {del_admin_id} is not in admin_ids.")
  else:
    update.message.reply_text("You don't have permission to use this command.")
