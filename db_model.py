import sqlalchemy as sq
import json
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

db = 'postgres'
db_password = 'dacent0000'  # delete password
host_type = 'localhost'
host = '5432'
db_name = 'postgres'

DSN = f"postgresql://{db}:{db_password}@{host_type}:{host}/{db_name}"
engine = sq.create_engine(DSN)
Session = sessionmaker(bind=engine)
session = Session()


class Word(Base):
    __tablename__ = "word"

    id = sq.Column(sq.Integer, primary_key=True)
    ru_trans = sq.Column(sq.String(length=40), unique=True)
    en_trans = sq.Column(sq.String(length=40), unique=False)
    word_group = sq.Column(sq.String(length=40), unique=False)

    words_users = relationship('WordUser', back_populates='word')


class User(Base):
    __tablename__ = "user"

    id = sq.Column(sq.Integer, primary_key=True)
    user_serial = sq.Column(sq.String(length=20), unique=True)

    words_users = relationship('WordUser', back_populates='user')


class WordUser(Base):
    __tablename__ = "word_user"

    id = sq.Column(sq.Integer, primary_key=True)
    word_id = sq.Column(sq.Integer, sq.ForeignKey("word.id"), nullable=False)
    user_id = sq.Column(sq.Integer, sq.ForeignKey("user.id"), nullable=False)
    word_counter = sq.Column(sq.Integer, nullable=False)

    word = relationship(Word, back_populates='words_users')
    user = relationship(User, back_populates='words_users')


def create_tables():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def fill_tables(db_session):
    with open('test_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    for record in data:
        db_session.add(Word(
            ru_trans=record.get("ru_trans"),
            en_trans=record.get("en_trans"),
            word_group=record.get("word_group")))
    db_session.commit()


if __name__ == "__main__":
    create_tables()
    fill_tables(session)

