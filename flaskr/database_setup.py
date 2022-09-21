from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    user_name = Column(String(250), nullable=False)
    user_email = Column(String(50), nullable=False)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.user_name,
            'email': self.user_email,
            'id': self.id,
        }


class Article(Base):
    __tablename__ = 'article'

    id = Column(Integer, primary_key=True)
    title = Column(Text(), nullable=False)
    article_body = Column(Text(), nullable=False)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'title': self.title,
            'article_body': self.article_body,
            'user_id': self.user_id,
            'id': self.id,
        }


class Comments(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True)
    comment_text = Column(Text(), nullable=False)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    writer_id = Column(Integer, ForeignKey('article.user_id'))
    article_id = Column(Integer, ForeignKey('article.id'))
    article = relationship("Article", foreign_keys=[article_id])
    user = relationship("Article", foreign_keys=[writer_id])

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'comment': self.comment_text,
            'id': self.id,
            'article_id': self.article_id,
            'writer_id': self.writer_id
        }


engine = create_engine('sqlite:///blog-articles.db')
#
# error on removing the following statement
Base.metadata.create_all(engine)
