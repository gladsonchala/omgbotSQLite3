import logging

from replit import db

from strings import default_provider, user_provider_preferences

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

db = db if not db is None else {}


def get_user_info(update):
  user = update.message.from_user
  user_id = user.id
  user_name = user.first_name
  username = user.username if user.username else user_name

  return user_id, user_name, username


# Function to get search state
def get_search_state(user_id):
  try:
    search_state = db.get(f"search_enabled_{user_id}")
    return search_state if search_state is not None else False
  except Exception as e:
    logger.error(e)
    return False


# Function to set search state
def set_search_state(user_id, search_state):
  try:
    # Ensure search_state is a valid integer
    search_state = int(search_state)

    # Now set the search state
    db[f"search_enabled_{user_id}"] = search_state
  except ValueError as ve:
    logger.error(
        f"Invalid search state value: {search_state}. It should be an integer."
    )
  except Exception as e:
    logger.error(e)


# Function to store user messages and AI responses in the database with logging
def store_message(user_id, user_message, ai_response):
  try:
    key = f"{user_id}_{latest_key() + 1}"
    db[key] = f"User: {user_message}\nYou: {ai_response}"

    # Log the stored message
    logger.info(
        f"Stored message for user {user_id}: {user_message} -> {ai_response}")
  except Exception as e:
    # Log any errors that occur during storage
    logger.error(f"Error storing message for user {user_id}: {e}")


# Function to get the user's preferred provider name
def get_user_provider_name(user_id):
  return user_provider_preferences.get(user_id, default_provider)


# Function to get the user's previous messages from the database
def get_user_previous_messages(user_id):
  user_key = str(user_id)
  messages = [db[key] for key in db.keys() if key.startswith(user_key)]
  return "\n".join(messages)


# Function to get the latest key from the Replit database
def latest_key():
  try:
    keys = db.keys()
    return int(keys[-1].split('_')[1]) if keys else 0
  except Exception as e:
    logger.error(e)
    return 0
