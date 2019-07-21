from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
 
from database_setup import User, Base, Article, Comments
 
engine = create_engine('sqlite:///blogarticles.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

user1 = User(user_name = "Gbenga", user_email = "gbengaoti2@gmail.com")

session.add(user1)
session.commit()

user2 = User(user_name = "admin", user_email = "admin@gmail.com")

session.add(user2)
session.commit()

article1 = Article(title = "Summer in Lodz", article_body = "I loved travelling in Lodz while interning at University of Lodz", user = user1)

session.add(article1)
session.commit()

comment1 = Comments(comment_text = "Sounds like a great summer !", article = article1, user = article1)

session.add(comment1)
session.commit()

article2 = Article(title = "Missed flights and Christmases", article_body = "What's missing your first flight like? I'll tell you in 200 words", user = user1)

session.add(article2)
session.commit()

comment2 = Comments(comment_text = "Hope you got a great Christmas",  article = article2, user = article2)

session.add(comment2)
session.commit()

print ("added posts, users and comments!")