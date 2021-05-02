from flask import Flask,render_template
from flask_sqlalchemy import SQLAlchemy
import click

import os
import sys

WIN = sys.platform.startswith("win")
if WIN:
    prefix = "sqlite:///"
else:
    prefix = "sqlite:////"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = prefix + os.path.join(app.root_path,"data.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False # shutdown the monitor for Model

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(20))

class Movie(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(60))
    year = db.Column(db.String(4))

@app.cli.command()
@click.option("--drop",is_flag=True,help="Create after Drop")
def initdb(drop):
    if drop:
        db.drop_all()
    db.create_all()
    click.echo("Initialized Database!")

@app.cli.command()
def forge():
    db.create_all()

    name = 'Yue Zhang'
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]

    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m["title"],year=m["year"])
        db.session.add(movie)

    db.session.commit()
    click.echo("Done.")



@app.route('/')
def index():

    movies = Movie.query.all()
    return render_template("index.html",movies=movies)


@app.errorhandler(404)
def page_not_found(error):

    return render_template("404.html"),404

@app.context_processor
def inject_user():
    user = User.query.first()
    return dict(user=user) # return {'user': user}



if __name__ == "__main__":
    app.run()