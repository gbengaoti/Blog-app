# Blog-app
Blog app implemented in Flask

This project was implemented by me as a practice for concepts learnt in courses from Full stack development Nanodegree.

The app allows users sign in using OAUTH from Facebook and Google APIs.

Once signed in, the user can add, delete and edit articles in their personalized blog.

Guests and signed users can view articles from every user.

Only creators of articles can perform addition, deletion and creation of articles to their blog.

The app uses sqlalchemy for the database.

The required libaries are in a bash file called pg_config.sh

To use the blog app - run the database_setup.py file, this creates the database

Populate the database by running lotsofusersposts.py

Lastly, run project.py