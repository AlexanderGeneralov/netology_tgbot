from sqlalchemy import func
from db_model import Word, User, WordUser


# function adds user by user TG account id to user table
def add_user(q_user_serial, session):
    if q_user_serial not in get_list_of_users(session):
        session.add(User(user_serial=q_user_serial))
        session.commit()
        print(f"User with ID: {q_user_serial} had been added.")
    else:
        pass


# function to get list of user from db
def get_list_of_users(session):
    lst = session.query(User.user_serial).all()
    return [item[0] for item in lst]


# function returns list of words added for specified user
def get_user_list_of_words(q_user_serial, session):
    list_of_words = session.query(Word.ru_trans) \
        .join(WordUser, Word.id == WordUser.word_id) \
        .join(User, User.id == WordUser.user_id) \
        .filter(User.user_serial == q_user_serial).all()
    return [item[0] for item in list_of_words]


# function checks if specified word is in user list, returns empty list or list with id
def check_if_word_in_user_list(q_user_serial, word, session):
    res = session.query(WordUser.id) \
        .join(Word, Word.id == WordUser.word_id) \
        .join(User, User.id == WordUser.user_id) \
        .filter(User.user_serial == q_user_serial, Word.ru_trans == word).all()
    return res


# function to return list of words for chosen category
def get_word_by_category(category, session):
    list_of_words = session.query(Word.ru_trans, Word.en_trans).filter(Word.word_group == category).all()
    return list_of_words


# function checks if word is in personnel list of words (word_user table) and add new word or print exception
def add_word(q_word, q_user_serial, session):

    if q_word in get_user_list_of_words(q_user_serial, session):
        print(f"Word '{q_word}' was already added")
        pass
    else:
        q_word_id = session.query(Word.id).filter(Word.ru_trans == q_word).scalar()
        q_user_id = session.query(User.id).filter(User.user_serial == q_user_serial).scalar()
        session.add(WordUser(
            word_id=q_word_id,
            user_id=q_user_id,
            )
        )
        session.commit()


# function returns id of a row for specified word for specified user
def get_word_user_id(q_word, q_user_serial, session):
    word_user_id = session.query(WordUser.id) \
        .select_from(WordUser) \
        .join(User, User.id == WordUser.user_id) \
        .join(Word, Word.id == WordUser.word_id) \
        .filter(Word.ru_trans == q_word and User.user_serial == q_user_serial).scalar()
    return word_user_id


# function returns counter of correct/wrong answers for specified word for specified user
def get_word_user_counter(q_word, q_user_serial, session):
    word_user_id = get_word_user_id(q_word, q_user_serial, session)
    counter = session.query(WordUser.word_counter).filter(WordUser.id == word_user_id).scalar()
    return counter


# function to delete specified word for specified user out of personnel list of words (user_word table)
def delete_word(q_word, q_user_serial, session):
    word_user_id = get_word_user_id(q_word, q_user_serial, session)
    session.query(WordUser).filter(WordUser.id == word_user_id).delete()
    session.commit()


# function to increment word counter for specified word for specified user (user_word table)
# function is not used
def increment_word_counter(q_word, q_user_serial, session):
    word_user_id = get_word_user_id(q_word, q_user_serial, session)
    counter = get_word_user_counter(q_word, q_user_serial, session)
    session.query(WordUser).filter(WordUser.id == word_user_id).update({'word_counter': counter + 1})
    session.commit()


# function to increment word counter for specified word for specified user (user_word table)
# function is not used
def decrement_word_counter(q_word, q_user_serial, session):
    word_user_id = get_word_user_id(q_word, q_user_serial, session)
    counter = get_word_user_counter(q_word, q_user_serial, session)
    session.query(WordUser).filter(WordUser.id == word_user_id).update({'word_counter': counter - 1})
    session.commit()


# function to count words number in personal list of words (user_word table)
def get_words_number_in_word_user(q_user_serial, session):
    number = session.query(func.count(WordUser.id)). \
        join(User, WordUser.user_id == User.id). \
        filter(User.user_serial == q_user_serial).scalar()
    return number


# function returns list of available categories of words
def get_word_category(session):
    category = session.query(Word.word_group).group_by(Word.word_group)
    return [item[0] for item in category]
