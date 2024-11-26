from telegram import ReplyKeyboardMarkup
from utils.text_loader import get_texts
from utils.storage import save_user_data
from constants import (
    LANGUAGE,
    MAIN_MENU,
    REGISTRATION_INFO,
    REG_NAME,
    REG_LAST_NAME,
    REG_TELEGRAM,
    REG_EMAIL,
    REG_PHONE,
    REG_COUNTRY,
    REG_PROMO,
)
import re
from telegram.constants import ParseMode
import logging


# Set up logging
logger = logging.getLogger(__name__)


# Start command handler
async def start(update, context):
    """
    Initializes the bot, detects the user's language, and displays the welcome message.

    1. Detects the user's preferred language from Telegram (default: English).
    2. Loads texts dynamically based on the selected language.
    3. Displays the welcome message and prompts the user to choose their language.
    """
    # Detect language or default to English
    lang = (
        update.message.from_user.language_code[:2]
        if update.message.from_user.language_code
        else "en"
    )
    context.user_data["language"] = lang if lang in ["en", "ar", "fr"] else "en"

    # Load texts for the selected language
    try:
        texts = get_texts(context.user_data["language"])
    except KeyError:
        # Fallback to English if the language is not supported
        texts = get_texts("en")

    # Display welcome message and language selection options
    try:
        reply_markup = ReplyKeyboardMarkup(
            texts["languages"], one_time_keyboard=True, resize_keyboard=True
        )
        await update.message.reply_text(texts["welcome"], parse_mode=ParseMode.MARKDOWN)
        await update.message.reply_text(
            texts["language_prompt"], reply_markup=reply_markup
        )
    except KeyError as e:
        # Handle missing keys in the texts dictionary
        await update.message.reply_text(
            "❌ An error occurred while processing your request. Please try again later.",
            parse_mode=ParseMode.MARKDOWN,
        )
        # Log the error (ensure logging is set up in your app)
        print(f"KeyError in start function: {e}")
        return ConversationHandler.END

    return LANGUAGE


# Language selection handler
async def choose_language(update, context):
    """
    Handles language selection by mapping the user's choice to a language code.
    Loads texts for the selected language and displays the main menu.
    """
    # Dynamically map emoji text to language code from available languages
    available_languages = {
        "en": {"language_name": "🇬🇧 English"},
        "fr": {"language_name": "🇫🇷 Français"},
        "ar": {"language_name": "🇦🇪 العربية"},
    }
    lang_map = {
        details["language_name"]: code for code, details in available_languages.items()
    }

    # Get user's language selection
    selected_language = update.message.text
    lang = lang_map.get(selected_language)

    if not lang:
        # Handle invalid selection
        await update.message.reply_text(
            "❌ Invalid language selection. Defaulting to English."
        )
        lang = "en"  # Default to English if the selection is invalid

    context.user_data["language"] = lang

    # Load texts for the selected language
    try:
        texts = get_texts(lang)
    except KeyError:
        # Log the error and default to English texts
        print(f"Error: Missing texts for language '{lang}'. Falling back to English.")
        texts = get_texts("en")
        context.user_data["language"] = "en"

    # Show main menu in the selected language
    reply_markup = ReplyKeyboardMarkup(
        texts["menu_buttons"], one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(
        texts["main_menu_prompt"], reply_markup=reply_markup
    )

    # Log the selected language
    print(f"Language selected: {lang}")
    return MAIN_MENU


async def main_menu(update, context):
    """
    Displays the main menu and handles user choices.
    """
    lang = context.user_data.get(
        "language", "en"
    )  # Default to English if language is not set
    texts = get_texts(lang)  # Fetch texts based on the language
    user_choice = update.message.text  # The button text sent back by Telegram

    # Debugging
    print(f"User choice: {user_choice}")
    print(
        f"Available buttons: {[texts['button_register'], texts['button_commission'], texts['button_marketing'], texts['button_faq'], texts['button_support'], texts['button_back']]}"
    )

    # Match user choice with dynamic text
    if user_choice == texts["button_register"]:
        return await start_registration(update, context)

    if user_choice == texts["button_commission"]:
        await update.message.reply_text(texts["commission"], parse_mode="Markdown")
        return MAIN_MENU

    if user_choice == texts["button_marketing"]:
        await update.message.reply_text(texts["marketing_tips"], parse_mode="Markdown")
        return MAIN_MENU

    if user_choice == texts["button_faq"]:
        await update.message.reply_text(texts["faq"], parse_mode="Markdown")
        return MAIN_MENU

    if user_choice == texts["button_support"]:
        await update.message.reply_text(texts["support"], parse_mode="Markdown")
        return MAIN_MENU

    if user_choice == texts["button_back"]:
        return await start(update, context)

    # Handle invalid input
    await update.message.reply_text(
        texts.get(
            "invalid_option",
            "❌ Invalid option. Please choose a valid option from the menu.",
        )
    )
    return MAIN_MENU


async def start_registration(update, context):
    """
    Prompts the user to choose between manual or bot-assisted registration.
    """
    lang = context.user_data.get('language', 'en')
    texts = get_texts(lang)

    # Display manual and step-by-step registration options with Back button
    buttons = [
        [texts['button_register_manually'], texts['button_register_step']],
        [texts['button_back']]  # Back button to return to the main menu
    ]
    reply_markup = ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)

    # Send the registration choice text
    await update.message.reply_text(
        texts['registration_choice'],
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return REGISTRATION_INFO


async def handle_registration_choice(update, context):
    """
    Handles the user's choice between manual or bot-assisted registration.
    Ensures state consistency and prevents invalid input issues.
    """
    user_choice = update.message.text.strip()  # Get the user's choice
    lang = context.user_data.get('language', 'en')  # Get the user's selected language
    texts = get_texts(lang)  # Load texts in the selected language

    # Debugging: Log the user's choice and the expected options
    print(f"User choice: {user_choice}")
    print(f"Expected options: {texts['button_register_manually']}, {texts['button_register_step']}")

    # Handle "Register Manually"
    if user_choice == texts['button_register_manually']:
        # Clear registration data (if any) to prevent conflicts
        context.user_data['registration'] = None

        # Send the manual registration link
        await update.message.reply_text(
            texts.get(
                'manual_register_link',
                "🔗 Please use this link to register: [Register Here](https://lb-aff.com/L?tag=d_3895532m_22613c_ref&site=3895532&ad=22613&r=sign-up)"
            ),
            parse_mode='Markdown'
        )

        # Clear the menu and notify the user that they can go back
        await update.message.reply_text(
            texts.get('registration_done', "✅ Thank you! Please return to the main menu to continue."),
            reply_markup=ReplyKeyboardMarkup(
                [[texts['button_back']]],
                one_time_keyboard=True,
                resize_keyboard=True
            ),
            parse_mode='Markdown'
        )

        # Reset to the main menu
        return MAIN_MENU

    # Handle "Register Step by Step"
    elif user_choice == texts['button_register_step']:
        # Initialize new registration data
        context.user_data['registration'] = {}  # Clear any previous data
        await update.message.reply_text(
            texts['ask_first_name'],
            parse_mode='Markdown'
        )
        return REG_NAME  # Proceed to ask for the first name

    # Handle invalid input in the registration menu
    else:
        # If user input doesn't match any expected option
        await update.message.reply_text(
            texts.get('invalid_option', "❌ Please choose a valid option from the menu."),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup(
                [
                    [texts['button_register_manually'], texts['button_register_step']],
                    [texts['button_back']]
                ],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return REGISTRATION_INFO  # Stay in the registration menu

async def ask_for_first_name(update, context):
    """
    Collects the user's first name and allows the user to go back to the registration menu using the Back button.
    """
    lang = context.user_data.get('language', 'en')
    texts = get_texts(lang)

    # If the user presses Back, return to the registration menu
    if update.message.text == texts['button_back']:
        return await start_registration(update, context)  # Back to the registration menu

    # Validate the user's input for the first name
    first_name = update.message.text.strip()
    if not first_name:
        await update.message.reply_text(
            texts.get('error_empty_first_name', "❌ First name cannot be empty. Please provide your *first name*."),
            parse_mode='Markdown'
        )
        return REG_NAME  # Repeat this step if validation fails

    # Save the first name
    context.user_data['registration']['first_name'] = first_name

    # Ask for the last name and display only the Back button
    reply_markup = ReplyKeyboardMarkup([[texts['button_back']]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        texts.get('ask_last_name', "📝 Great! Now, what is your *last name*?"),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return REG_LAST_NAME


async def ask_for_last_name(update, context):
    """
    Collects the user's last name and redirects back to the registration menu if the Back button is clicked.
    """
    lang = context.user_data.get('language', 'en')
    texts = get_texts(lang)

    # If the user presses Back, return to the registration menu
    if update.message.text == texts['button_back']:
        return await start_registration(update, context)

    # Validate last name
    last_name = update.message.text.strip()
    if not last_name:
        await update.message.reply_text(
            texts.get('error_empty_last_name', "❌ Last name cannot be empty. Please provide your *last name*."),
            parse_mode='Markdown'
        )
        return REG_LAST_NAME

    # Save the last name
    context.user_data['registration']['last_name'] = last_name

    # Ask for the Telegram username, showing only the Back button
    reply_markup = ReplyKeyboardMarkup([[texts['button_back']]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        texts.get('ask_telegram_username', "📛 Great! Now, what is your *Telegram username*?"),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return REG_TELEGRAM


async def ask_for_telegram(update, context):
    """
    Collects the user's Telegram username and redirects back to the registration menu if the Back button is clicked.
    """
    lang = context.user_data.get('language', 'en')
    texts = get_texts(lang)

    # If the user presses Back, return to the registration menu
    if update.message.text == texts['button_back']:
        return await start_registration(update, context)

    # Validate Telegram username
    telegram_username = update.message.text.strip()
    if not telegram_username.startswith('@'):
        await update.message.reply_text(
            texts.get('error_invalid_telegram', "❌ Telegram username must start with '@'. Please enter a valid username."),
            parse_mode='Markdown'
        )
        return REG_TELEGRAM

    # Save the Telegram username
    context.user_data['registration']['telegram'] = telegram_username

    # Ask for the email address, showing only the Back button
    reply_markup = ReplyKeyboardMarkup([[texts['button_back']]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        texts.get('ask_email', "📧 What is your *email address*?"),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return REG_EMAIL


async def ask_for_email(update, context):
    """
    Collects the user's email address and redirects back to the registration menu if the Back button is clicked.
    """
    lang = context.user_data.get('language', 'en')
    texts = get_texts(lang)

    # If the user presses Back, return to the registration menu
    if update.message.text == texts['button_back']:
        return await start_registration(update, context)

    # Validate email format
    email = update.message.text.strip()
    email_pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    if not re.match(email_pattern, email):
        await update.message.reply_text(
            texts.get('error_invalid_email', "❌ Invalid email address. Please provide a valid email."),
            parse_mode='Markdown'
        )
        return REG_EMAIL

    # Save the email
    context.user_data['registration']['email'] = email

    # Ask for the phone number, showing only the Back button
    reply_markup = ReplyKeyboardMarkup([[texts['button_back']]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        texts.get('ask_phone_number', "📱 What is your *phone number*?"),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return REG_PHONE


async def ask_for_phone(update, context):
    """
    Collects the user's phone number and redirects back to the registration menu if the Back button is clicked.
    """
    lang = context.user_data.get('language', 'en')
    texts = get_texts(lang)

    # If the user presses Back, return to the registration menu
    if update.message.text == texts['button_back']:
        return await start_registration(update, context)

    # Validate phone number
    phone = update.message.text.strip()
    phone_pattern = r"^\+?[0-9]{7,15}$"  # Allow optional '+' for international numbers
    if not re.match(phone_pattern, phone):
        await update.message.reply_text(
            texts.get('error_invalid_phone', "❌ Phone number must be numeric and 7-15 digits long. Please enter a valid phone number."),
            parse_mode='Markdown'
        )
        return REG_PHONE

    # Save phone number
    context.user_data['registration']['phone'] = phone

    # Ask for the country, showing only the Back button
    reply_markup = ReplyKeyboardMarkup([[texts['button_back']]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        texts.get('ask_country', "🌍 Which *country* are you in?"),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return REG_COUNTRY


async def ask_for_country(update, context):
    """
    Collects the user's country and redirects back to the registration menu if the Back button is clicked.
    """
    lang = context.user_data.get('language', 'en')
    texts = get_texts(lang)

    # If the user presses Back, return to the registration menu
    if update.message.text == texts['button_back']:
        return await start_registration(update, context)

    # Validate country name (must contain only letters)
    country = update.message.text.strip()
    if not country.isalpha():
        await update.message.reply_text(
            texts.get('error_invalid_country', "❌ Country name must contain only letters. Please enter a valid country."),
            parse_mode='Markdown'
        )
        return REG_COUNTRY

    # Save the country
    context.user_data['registration']['country'] = country

    # Ask for the promo code, showing only the Back button
    reply_markup = ReplyKeyboardMarkup([[texts['button_back']]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        texts.get('ask_promo_code', "🎫 Finally, what is your preferred *promo code* (e.g., 'Linebet2024')?"),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return REG_PROMO

async def save_registration(update, context):
    """
    Collects the promo code, saves registration data, and confirms the process.
    """
    lang = context.user_data.get('language', 'en')
    texts = get_texts(lang)

    # If the user presses Back, return to the registration menu
    if update.message.text == texts['button_back']:
        return await start_registration(update, context)

    # Save the promo code
    promo_code = update.message.text.strip()
    context.user_data['registration']['promo'] = promo_code

    # Save all registration data
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    registration_data = context.user_data.get('registration', {})

    try:
        save_user_data(user_id, {
            'username': username,
            'registration_data': registration_data
        })
        # Notify user of successful registration
        await update.message.reply_text(
            texts.get('registration_success', "✅ Thank you for registering! Our team will contact you shortly."),
            parse_mode='Markdown'
        )
    except Exception as e:
        # Handle errors during data saving
        await update.message.reply_text(
            "❌ An error occurred while saving your registration. Please try again later.",
            parse_mode='Markdown'
        )
        return MAIN_MENU

    # Return to the main menu
    return MAIN_MENU

async def fallback(update, context):
    """
    Handles unexpected input and redirects to the current step or the main menu.
    """
    lang = context.user_data.get('language', 'en')
    texts = get_texts(lang)

    # Check if the user is in the middle of registration
    current_step = context.user_data.get('current_step')
    if current_step:
        await update.message.reply_text(
            texts.get('invalid_option', "❌ Invalid option. Please provide the correct input."),
            parse_mode='Markdown'
        )
        return current_step

    # If not in registration, redirect to the main menu
    await update.message.reply_text(
        texts.get('invalid_option', "❌ Invalid option. Please choose a valid option."),
        parse_mode='Markdown'
    )
    return MAIN_MENU


async def registration_info(update, context):
    """
    Handles the final step of registration, saves user data, and confirms registration.
    """
    # Get selected language and texts
    lang = context.user_data.get("language", "en")  # Default to English
    texts = get_texts(lang)

    try:
        # Collect the user's registration data
        user_id = update.message.from_user.id
        username = update.message.from_user.username
        user_data = context.user_data.get("registration", {})

        # Save user data
        save_user_data(user_id, {"username": username, "registration_data": user_data})
        logger.info(f"User {user_id} ({username}) registration completed: {user_data}")

        # Notify the user of successful registration
        await update.message.reply_text(
            texts.get(
                "after_registration_contact",
                "✅ Thank you! Our team will contact you shortly.",
            ),
            parse_mode="Markdown",
        )

    except Exception as e:
        # Log the error and notify the user
        logger.error(
            f"Error during registration for user {update.message.from_user.id}: {e}"
        )
        await update.message.reply_text(
            "❌ An error occurred while processing your registration. Please try again later.",
            parse_mode="Markdown",
        )

    # Return to the main menu
    return MAIN_MENU


async def navigate_back(update, context, current_menu):
    """
    Handles navigation when the back button is clicked.
    """
    lang = context.user_data.get("language", "en")
    texts = get_texts(lang)

    if current_menu == "registration":
        return await start_registration(update, context)
    else:  # Default to main menu
        return await main_menu(update, context)
