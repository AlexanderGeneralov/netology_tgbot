import random
import db_query
from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
import sqlalchemy as sq
from sqlalchemy import func
from db_model import Word, User, WordUser
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


class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'
    CHOOSE_CATEGORY = "Выбрать категорию"


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()
    word_category = State()


@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    print(user_id, user_name)
    bot.send_message(message.chat.id, f"Привет, {user_name}!")
    db_query.add_user(user_id, session=session)
    choose_category(message)


def choose_category(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btns = [types.KeyboardButton(category) for category in db_query.get_word_category(session=session)]
    markup.add(*btns)
    bot.send_message(message.chat.id, "Выберите категорию слов", reply_markup=markup)
    bot.register_next_step_handler(message, set_category)


def set_category(message):
    word_category = message.text
    bot.set_state(message.from_user.id, MyStates.word_category, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["word_category"] = word_category
    print(f"Сообщение из фнкции set_category: {word_category}")
    create_card(message)


def create_card(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        word_category = data["word_category"]

    print(f"сообщение из функции create_card: {word_category}")

    pairs = db_query.get_word_by_category(word_category, session=session)  # create list of ru - en word pairs by category
    random.shuffle(pairs)
    target_word = pairs[0][0]
    translate_word = pairs[0][1]
    another_words = [word[1] for word in pairs[1:]]

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
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

    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate_word
        data['another_words'] = another_words


@bot.message_handler(func=lambda message: True, content_types=["text"])
def card_message_reply(message):
    print(f"сообщение из функции card_message_reply: {message.text}")
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['translate_word']
    if message.text == target_word:
        bot.send_message(message.chat.id, "Все правильно!")
        create_card(message)
    elif message.text == "Выбрать категорию":
        choose_category(message)
    elif message.text == "Дальше ⏭":
        create_card(message)
    elif message.text == "Добавить слово ➕":
        user_id = str(message.from_user.id)
        print(user_id, data['target_word'])
        db_query.add_word(data['target_word'], user_id)
        bot.send_message(message.chat.id, f"Слово '{target_word}' добавлено в ваш личный список слов")
    else:
        bot.send_message(message.chat.id, "Ошибка!")


bot.infinity_polling(skip_pending=True)