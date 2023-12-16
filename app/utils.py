import logging
import sqlite3  
from strings import default_provider, user_provider_preferences

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)


# SQLite connection and cursor initialization
conn = sqlite3.connect('chat_data.db')
cursor = conn.cursor()

# Create the necessary table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_data (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        chat_message TEXT,
        bot_response TEXT,
        preferences TEXT
    )
''')


# Function to get user info
def get_user_info(update):
    user = update.message.from_user
    user_id = user.id
    user_name = user.first_name
    username = user.username if user.username else user_name
    return user_id, user_name, username

# Function to get search state
def get_search_state(user_id):
    try:
        search_state = cursor.execute(f"SELECT search_state FROM chat_data WHERE user_id = {user_id}").fetchone()
        return search_state[0] if search_state is not None else False
    except Exception as e:
        logger.error(e)
        return False

# Function to set search state
def set_search_state(user_id, search_state):
    try:
        # Ensure search_state is a valid integer
        search_state = int(search_state)

        # Now set the search state
        cursor.execute(f"UPDATE chat_data SET search_state = {search_state} WHERE user_id = {user_id}")
        conn.commit()
    except ValueError as ve:
        logger.error(f"Invalid search state value: {search_state}. It should be an integer.")
    except Exception as e:
        logger.error(e)

# Function to store user messages and AI responses in the database with logging
def store_message(user_id, user_message, ai_response):
    try:
        cursor.execute('''
            INSERT INTO chat_data (user_id, username, chat_message, bot_response, preferences)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, '', user_message, ai_response, ''))
        conn.commit()

        # Log the stored message
        logger.info(f"Stored message for user {user_id}: {user_message} -> {ai_response}")
    except Exception as e:
        # Log any errors that occur during storage
        logger.error(f"Error storing message for user {user_id}: {e}")

# Function to get the user's preferred provider name
def get_user_provider_name(user_id):
    # Implement as needed based on your logic
    # For example, you can query the database or use a default value
    return user_provider_preferences.get(user_id, default_provider)

# Function to get the user's previous messages from the database
def get_user_previous_messages(user_id):
    try:
        user_key = str(user_id)
        messages = cursor.execute(f"SELECT chat_message, bot_response FROM chat_data WHERE user_id = {user_id}").fetchall()
        return "\n".join([f"User: {msg[0]}\nYou: {msg[1]}" for msg in messages])
    except Exception as e:
        logger.error(e)
        return ''

# Function to get the latest key from the database
def latest_key():
    try:
        keys = cursor.execute('SELECT user_id FROM chat_data').fetchall()
        return max([key[0] for key in keys]) if keys else 0
    except Exception as e:
        logger.error(e)
        return 0
