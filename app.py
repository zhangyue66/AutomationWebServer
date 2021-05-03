from flask import Flask, render_template, request, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
import click

from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

import os
import sys

WIN = sys.platform.startswith("win")
if WIN:
    prefix = "sqlite:///"
else:
    prefix = "sqlite:////"

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev"
app.config["SQLALCHEMY_DATABASE_URI"] = prefix + os.path.join(app.root_path,"data.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False # shutdown the monitor for Model

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
#login_manager.login_message  error message for wrong login

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    return user

class User(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))

    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self,password):
        return check_password_hash(self.password_hash,password)

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

@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    """Create user."""
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)
        db.session.add(user)

    db.session.commit()
    click.echo('User Creation Done.')


@app.route('/',methods=["GET","POST"])
def index():
    #print(request.method)
    if request.method == "POST":
        if not current_user.is_authenticated:
            return redirect((url_for("index")))
        title = request.form.get("title")
        year = request.form.get("year")

        # validate data
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash("Invalid input.")
            return redirect(url_for("index")) # ridrect to main page
        #if data is valid
        movie = Movie(title=title,year=year)
        db.session.add(movie)
        db.session.commit()
        flash("Item created successful in Databse!")
        return redirect(url_for("index"))

    movies = Movie.query.all()
    return render_template("index.html",movies=movies)


@app.errorhandler(404)
def page_not_found(error):

    return render_template("404.html"),404

@app.context_processor
def inject_user():
    user = User.query.first()
    return dict(user=user) # return {'user': user}

@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if request.method == 'POST':  # 处理编辑表单的提交请求
        title = request.form['title']
        year = request.form['year']

        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id))  # 重定向回对应的编辑页面

        movie.title = title  # 更新标题
        movie.year = year  # 更新年份
        db.session.commit()  # 提交数据库会话
        flash('Item updated.')
        return redirect(url_for('index'))  # 重定向回主页

    return render_template('edit.html', movie=movie)

@app.route('/movie/delete/<int:movie_id>', methods=['POST'])  # 限定只接受 POST 请求
@login_required
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)  # 获取电影记录
    db.session.delete(movie)  # 删除对应的记录
    db.session.commit()  # 提交数据库会话
    flash('Item deleted.')
    return redirect(url_for('index'))  # 重定向回主页

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))

        user = User.query.first()
        # 验证用户名和密码是否一致
        if username == user.username and user.validate_password(password):
            login_user(user)  # 登入用户
            flash('Login success.')
            return redirect(url_for('index'))  # 重定向到主页

        flash('Invalid username or password.')  # 如果验证失败，显示错误消息
        return redirect(url_for('login'))  # 重定向回登录页面

    return render_template('login.html')

@app.route('/logout')
@login_required  # 用于视图保护，后面会详细介绍
def logout():
    logout_user()  # 登出用户
    flash('Goodbye.')
    return redirect(url_for('index'))  # 重定向回首页

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']

        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))

        current_user.name = name
        # current_user 会返回当前登录用户的数据库记录对象
        # 等同于下面的用法
        # user = User.query.first()
        # user.name = name
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('index'))

    return render_template('settings.html')

if __name__ == "__main__":
    app.run()