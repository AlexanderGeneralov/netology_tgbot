import random
import db_query
from telebot import types, TeleBot
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker
from config import TOKEN, db_password


db = 'postgres'
host_type = 'localhost'
host = '5432'
db_name = 'postgres'

DSN = f"postgresql://{db}:{db_password}@{host_type}:{host}/{db_name}"
engine = sq.create_engine(DSN)
Session = sessionmaker(bind=engine)
session = Session()

print('Start telegram bot...')

state_storage = StateMemoryStorage()

bot = TeleBot(TOKEN, state_storage=state_storage)


# class to create commands for keyboard
class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'
    CHOOSE_CATEGORY = "Выбрать категорию"


# class to create data to store in state machine
class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()
    word_category = State()


# function to start the bot
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    bot.send_message(message.chat.id, f"Привет, {user_name}!")
    db_query.add_user(user_id, session=session)
    choose_category(message)


# function for user to choose word category
def choose_category(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btns = [types.KeyboardButton(category) for category in db_query.get_word_category(session=session)]
    markup.add(*btns)
    bot.send_message(message.chat.id, "Выберите категорию слов", reply_markup=markup)
    bot.register_next_step_handler(message, set_category)


# function to add chosen category to state machine
def set_category(message):
    word_category = message.text
    bot.set_state(message.from_user.id, MyStates.word_category, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["word_category"] = word_category
    #print(f"Сообщение из фнкции set_category: {word_category}")
    create_card(message)


# function to create card with ru word and suggested variants of en translation on keyboard
def create_card(message):
    # extract data of category out of state machine
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        word_category = data["word_category"]

    #print(f"сообщение из функции create_card: {word_category}")
    # create list of ru - en word pairs by category
    pairs = db_query.get_word_by_category(word_category, session=session)
    random.shuffle(pairs)
    pairs = pairs[:4]  # take first 4 pairs of words
    target_word = pairs[0][0]  # ru word
    translate_word = pairs[0][1]  # en word
    another_words = [word[1] for word in pairs[1:]]  # another en words
    # create keyboard
    markup = types.ReplyKeyboardMarkup(row_width=2)
    btn_translate_word = types.KeyboardButton(translate_word)
    btn_another_words = [types.KeyboardButton(word) for word in another_words]
    btn_next_word = types.KeyboardButton(Command.NEXT)
    btn_choose_category = types.KeyboardButton(Command.CHOOSE_CATEGORY)
    btn_add_word = types.KeyboardButton(Command.ADD_WORD)
    btn_delete_word = types.KeyboardButton(Command.DELETE_WORD)
    btns = [btn_translate_word] + btn_another_words
    random.shuffle(btns)
    btns += [btn_next_word, btn_choose_category, btn_add_word, btn_delete_word]
    markup.add(*btns)
    bot.send_message(message.chat.id, f"Угадай перевод слова '{target_word}'", reply_markup=markup)
    # save data of words to state machine
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate_word
        data['another_words'] = another_words


# function to process user replies
@bot.message_handler(func=lambda message: True, content_types=["text"])
def card_message_reply(message):
    #print(f"Сообщение из функции card_message_reply: {message.text}")
    # extract data of word out of state machine
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['translate_word']

    word = data['target_word'] # use this word for add, delete functions
    user_id = str(message.from_user.id)
    chat_id = message.chat.id

    if message.text == target_word:
        bot.send_message(chat_id, "Все правильно!")
        create_card(message)
    elif message.text == "Выбрать категорию":
        choose_category(message)
    elif message.text == "Дальше ⏭":
        create_card(message)
    elif message.text == "Добавить слово ➕":
        add_word_to_personnel_list(chat_id, user_id, word)
    elif message.text == "Удалить слово🔙":
        delete_word_out_of_personnel_list(chat_id, user_id, word)
    else:
        bot.send_message(chat_id, "Ошибка!")


# function to add word to personnel list of words
def add_word_to_personnel_list(chat_id, user_id, word):
    if db_query.check_if_word_in_user_list(user_id, word, session=session):
        bot.send_message(chat_id, f"Слово '{word}' уже в вашем личном списке слов.")
    else:
        db_query.add_word(word, user_id, session=session)
        word_count = db_query.get_words_number_in_word_user(user_id, session=session)
        bot.send_message(chat_id, f"Слово '{word}' добавлено в ваш личный список слов.")
        bot.send_message(chat_id, f"Количество слов в вашем личном списке: {word_count}")


# function to delete word out of personnel list of words
def delete_word_out_of_personnel_list(chat_id, user_id, word):
    if not db_query.check_if_word_in_user_list(user_id, word, session=session):
        bot.send_message(chat_id, f"Слова '{word}' нет в вашем личном списке слов.")
    else:
        db_query.delete_word(word, user_id, session=session)
        bot.send_message(chat_id, f"Слово '{word}' удалено из вашего личного списка слов.")


bot.infinity_polling(skip_pending=True)
