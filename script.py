# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, Response, stream_with_context, jsonify, redirect, url_for
from flask_login import LoginManager, current_user, logout_user, login_user, UserMixin, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.attributes import flag_modified
import json
import datetime
from werkzeug.security import check_password_hash, generate_password_hash
import re
from random import randint
import mailer

# Роли: 0 - редакция, 1 - root, 2 - высший администратор, 3 - администратор, 4 - ...,  5 - модератор, 8 - пользователь, 9 - не активирован, 10 - заморожен
app = Flask(__name__)
app.config['SECRET_KEY'] = "a very-very-very-very-very-very-very-very-very-very-very-very-very secret key, rly"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:userpassw@localhost/postgres'
app.config['SQLALCHEMY_POOL_SIZE'] = 1000
login_manager = LoginManager(app)
login_manager.login_view = 'login'

db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    ID = db.Column(db.Integer, primary_key = True, unique = True)
    login = db.Column(db.String(50), unique = True, nullable = False)
    email = db.Column(db.String(50), unique = True, nullable = True)
    password = db.Column(db.String(100), unique = False, nullable = False)
    
    birthday = db.Column(db.String(50), unique = False, nullable = True)
    name = db.Column(db.String(50), unique = False, nullable = True)
    surname = db.Column(db.String(50), unique = False, nullable = True)
    town = db.Column(db.String(60), unique=False, nullable = True)
    about_me = db.Column(db.String(500), unique = False, nullable = True)
    img = db.Column(db.String(200), unique = False, nullable = False)
    favorite = db.Column(db.String(10000), unique = False, nullable = False)

    created = db.Column(db.String(50), unique = False, nullable = False)
    role = db.Column(db.Integer, unique = False, nullable = False)
    warnings = db.Column(db.Integer, unique = False, nullable = False)
    code = db.Column(db.String(10), unique = False, nullable = True)

    def get_id(self):
        return (self.ID)

    def get_val(self):
        return ({
            "id" : self.ID, 
            "login" : self.login, 
            "email" : self.email, 
            "password" : self.password, 
            "birthday" : self.birthday,
            "name" : self.name, 
            "surname" : self.surname, 
            "town" : self.town, 
            "about_me" : self.about_me, 
            "img" : self.img, 
            "favorite" : self.favorite, 
            "created" : self.created, 
            "role" : self.role, 
            "warnings" : self.warnings,
            "code" : self.code
        })
    
    def is_authenticated(self):
        return True 
    
    def __repr__(self):
        return f"{self.ID}, {self.login}, {self.email}, {self.password}, {self.birthday}, {self.name}, {self.surname}, {self.town}, {self.about_me}, {self.img}, {self.favorite}, {self.created}, {self.role}, {self.code}"

class Comment(db.Model):
    __tablename__ = 'comments'
    ID = db.Column(db.Integer, primary_key = True, unique = True)
    userLogin = db.Column(db.String(50), unique = False, nullable = False)
    userImg = db.Column(db.String(200), unique = False, nullable = False)
    post = db.Column(db.Integer, unique = False, nullable = False)
    onComment = db.Column(db.Integer, unique = False, nullable = True)
    onFComment = db.Column(db.Integer, unique = False, nullable = True)
    text = db.Column(db.String(3000), unique = False, nullable = False)
    created = db.Column(db.String(50), unique = False, nullable = False)
    time = db.Column(db.String(15), unique = False, nullable = False)
    likes = db.Column(db.Integer, unique = False, nullable = False)
    dislikes = db.Column(db.Integer, unique = False, nullable = False)
    likers = db.Column(db.String(10000), unique = False, nullable = True)
    dislikers = db.Column(db.String(10000), unique = False, nullable = True)
    deleted = db.Column(db.Integer, unique = False, nullable = False)

    def get_val(self):
        return {
            "ID" : self.ID, 
            "post" : self.post,
            "onComment" : self.onComment, 
            "onFComment" : self.onFComment,
            "userLogin" : self.userLogin,
            "userImg" : self.userImg,
            "text" : self.text,
            "created" : self.created,
            "time" : self.time,
            "likes" : self.likes,
            "dislikes" : self.dislikes,
            "likers" : self.likers,
            "dislikers" : self.dislikers,
            "deleted": self.deleted
        }

class Post(db.Model):
    __tablename__ = 'posts'
    ID = db.Column(db.Integer, primary_key = True, unique = True)
    name = db.Column(db.String(200), unique = True, nullable = False)
    summ = db.Column(db.Integer, unique = False, nullable = False)
    count = db.Column(db.Integer, unique = False, nullable = False)
    comments = db.Column(db.Integer, unique = False, nullable = False)
    activate = db.Column(db.String(20), unique = False, nullable = True)
    author = db.Column(db.String(50), unique = False, nullable = False)

    def get_val(self):
        return {
            "ID" : self.ID,
            "name" : self.name,
            "summ" : self.summ,
            "count" : self.count,
            "comments" : self.comments,
            "activate" : self.activate,
            "author" : self.author
        }


# additional functions
def upload_list():
    global media, onPage, pages, postpages
    media = {}
    onPage = 8
    with open("static\\content\\namelist.json", encoding='utf-8') as read_file:
        List = json.load(read_file)
        List.reverse()
    pages = len(List) // onPage + 1
    postpages = { i : [] for i in range(pages) }
    for i in range(0, len(List)):
        with open(f"static\\content\\jsons\\{List[i]}.json", encoding="utf-8") as read_file:
            data = json.load(read_file)
        media.update({data["name"] : data})
        page = i // onPage + 1
        if  Post.query.filter_by(name = data["name"]).first() == None:
            new_post = Post(name = data["name"], author = data["author"], summ = 0, count = 0, comments = 0)
            db.session.add(new_post)
        else: pass
        postpages[page-1].append(Post.query.filter_by(name = data["name"]).first())
    db.session.commit()
    return print("List uploaded")

def auth_label():
    if current_user.is_authenticated:
        return("Выйти")
    else:
        return("Войти")

def check_symb(x):
    symb = bool(re.search("""[!?:;"'.,+$@/]""", x))
    return(symb)

def formater(x):
    x = x.lstrip()
    if x != "":
        return x
    else:
        return None


@login_manager.user_loader
def load_user(ID):
    return User.query.get(int(ID))
    

# navigation functions
@app.route("/", methods = ["GET"])
def go_to_main():
    count = User.query.count()
    res = [User.query.get(i).get_val() for i in range(1, count+1)]
    print(res)
    return render_template("main.html", title="Русский Восход", auth = auth_label())

@app.route("/media-list/<page_num>", methods=["GET"])
def go_to_media(page_num):
    page_num = int(page_num)
    if current_user.is_authenticated: user = current_user.get_val()
    else: user = None
    posts = []
    for i in postpages[page_num-1]:
        values = i.get_val()
        values.update(media[values["name"]])
        values["ID"] = str(values["ID"])
        posts.append(values)
    return render_template("media.html", list = posts, pages = [page_num, pages], title ="Медиа | Русский Восход", auth = auth_label(), user = user)

@app.route("/media/<blog>", methods=["GET"])
def show_content(blog):
    content = media[blog]
    content.update(Post.query.filter_by(name=blog).first().get_val())
    if current_user.is_authenticated: uinfo = current_user.get_val()
    else: uinfo = None
    return render_template(f"blog_templates/{content['template']}", uinfo = uinfo, inf = content, auth = auth_label(), title=content["title"])


# user functions
@app.route("/login", methods=["POST"])
def login():
    login = request.form["login"]
    password = request.form["passw"]
    user = User.query.filter_by(login=login).first()
    if User.query.filter_by(login=login).first():
        user = User.query.filter_by(login=login).first()
    else:
        user = User.query.filter_by(email = login).first()

    if user:
        info = user.get_val()
        if info["role"] != "9":
            if check_password_hash(info["password"], password):
                login_user(user)
                if request.args.get('next'):
                    return request.args.get('next')
                else:
                    return redirect(url_for("to_profile"))
            else:
                return render_template("auth.html", errorMes = "Неверный пароль", auth = auth_label())
        else: 
            return render_template("auth.html", errorMes = "Пользователь не найден", auth = auth_label())
    else:
        return render_template("auth.html", errorMes = "Пользователь не найден", auth = auth_label())

# log out OR go to auth/reg
@app.route("/go-to-authentication-or-logout", methods=["GET"])
def go_to_auth_logout():
    if current_user.is_authenticated:
        logout_user()
        return redirect(url_for("go_to_main"))
    else:
        return render_template("auth.html", auth = auth_label(), title="Авторизация | Русский Восход")


@app.route("/register-new-account", methods=["POST"])
def register():
    login = request.form["login"]
    password = request.form["passw"]
    email = request.form["email"]
    date = datetime.datetime.today().strftime("%d.%m.%Y")
    password = generate_password_hash(password).lstrip()

    try:
        code = randint(100000, 999999)
        s1 = User.query.filter_by(login = login).first()
        s2 = User.query.filter_by(email = email).first()
        role = False
        if s1:
            role = int(get_dict(s1)["role"])
        elif s2:
            role = int(get_dict(s2)["role"])

        if role == 9:
            if s1:
                User.query.filter_by(login = login).delete()
            elif s2:
                User.query.filter_by(email = email).delete()
        
        user = db.session.add(User(login = login, password = password, email = email, role = 9, img = "user_imgs/defaultuser.webp", created = date, code = code, favorite = "", warnings = 0))
        db.session.commit()
        mailer.send_email(email, "Подтверждение действия", f"Код активации: <h3> {code} </h3>")
        return redirect(url_for("to_activate") + '?user=' + login)
    except:
        return redirect(url_for("go_register"))

@app.route("/check-input", methods=["POST"])
def check():
    login = request.form["login"]
    email = request.form["email"]
    passw = request.form["passw"]

    ULogin = User.query.filter_by(login = login).first().get_val()
    UEmail = User.query.filter_by(email = email).first().get_val()
    if ULogin and ULogin["role"] != "9":
        return jsonify("Этот псевдоним уже занят")
    elif UEmail and UEmail["role"] != "9":
        return jsonify("Этот email занят")
        
    if login != "" and bool(re.search("""[!?:;"'.,+$@/]""", login)):
        return jsonify(f"Псевдоним")
    elif email != "" and bool(re.search("[a-zA-Z0-9]+[@]+[a-z]+[.]+[a-z]", email)) != True:
        return jsonify(f"Почта")
    elif passw != "" and bool(re.search("""[!?:;"'.,+$@/]""", passw)):
        return jsonify(f"Пароль")
    elif login != "" and login.strip() == "":
        return jsonify(f"Псевдоним не должен быть пустым")
    elif passw != "" and passw.strip() == "":
        return jsonify(f"Пароль не должен быть пустым")

    return jsonify(False)

@login_required
@app.route("/chage-info", methods=["POST"])
def change():
    Id = current_user.get_id()
    user = User.query.filter_by(ID = Id).first()

    user.about_me = formater(request.form["about_me"])
    user.name = formater(request.form["name"])
    user.surname = formater(request.form["surname"])
    birth = request.form["birthday"].split("-")
    user.birthday = f"{birth[2]}.{birth[1]}.{birth[0]}"
    user.town = formater(request.form["town"])
    db.session.commit()
    return redirect(url_for("to_profile"))

@app.route("/activate/<user>", methods=["POST"])
def activate(user):
    acc = User.query.filter_by(login = user).first()
    values = acc.get_val()
    codeR = values["code"]
    codeL = request.form["code"]
    if codeR == codeL and values["role"] == "9":
        acc.role = 8
        acc.code = ""
        db.session.add(acc)
        db.session.commit()
        login_user(acc)
        return redirect(url_for("to_profile"))
    else:
        return redirect(url_for("to_activate") + '?user=' + user + '&errorMess=Неверный код активации')

@app.route("/resend-code/<user>", methods=["GET"])
def resend_code(user):
    acc = User.query.filter_by(login = user).first()
    dic = acc.get_val()
    if dic["role"] == "9" and dic["code"] != "":
        code = randint(100000, 999999)
        acc.code = code
        db.session.commit()
        mailer.send_email(dic["email"], "Подтверждение действия", f"Новый код активации: <nobr><h3> {code} </h3>")
        return redirect(url_for("to_activate") + '?user=' + user + '&errorMess=Новый код отправлен')
    else:
        return redirect(url_for("go_to_main"))

@login_required
@app.route("/change-favourite/<post>", methods=["GET"])
def change_favourite(post):
    Id = current_user.get_id()
    user = User.query.filter_by(ID = Id).first()
    post = post+" "

    if post in user.favorite:
        user.favorite = user.favorite.replace(post, "")
        db.session.commit()
        return jsonify("deleted")
    else:
        user.favorite += post
        db.session.commit()
        return jsonify("added")



# additional navigation
@login_required
@app.route("/go-to-profile", methods=["GET"])
def to_profile():
    return render_template("profile.html", title = "Профиль | Русский восход", auth = auth_label(), info = current_user.get_val())

@app.route("/show-user/<login>", methods=["GET"])
def show_user(login):
    user = User.query.filter_by(login = login).first()
    return render_template("profile.html", title = "Профиль пользователя | Русский восход", auth = auth_label(), info = user.get_val())

@app.route("/go-to-register", methods=["GET"])
def go_register():
    return render_template("register.html", title ="Регистрация | Русский Восход", auth = auth_label())

@app.route("/to-activate", methods=["GET", "POST"])
def to_activate():
    errorMess = request.args.get("errorMess")
    return render_template("activate.html", title = "Активация профиля | Русский восход", auth = auth_label(), errorMess = errorMess)

@login_required
@app.route("/to-profile-changes", methods=["GET"])
def to_change():
    info = current_user.get_val
    birth = info["birthday"].split(".")
    info["birthday"] = f"{birth[2]}-{birth[1]}-{birth[0]}"
    return render_template("profchange.html", title="Редактирование профиля | Русский восход", auth = auth_label(), info = info)


# comments and likes
@login_required
@app.route("/new-comment", methods=["POST"])
def new_comment():
    onComment = request.form["onComment"]
    if not onComment: 
        onComment = None
        onFComment = None
    else:
        f = Comment.query.filter_by(ID = onComment).first().get_val()["onFComment"]
        if f: onFComment = f
        else: onFComment = onComment
    postID = request.form["ID"]
    text = request.form["text"]
    user = current_user.get_val()
    post = Post.query.filter_by(ID = int(postID)).first()
    post.comments += 1
    comm = Comment(text = text, post = postID, onComment = onComment, onFComment = onFComment, userLogin = user["login"], userImg = user["img"], created = datetime.datetime.today().strftime("%d.%m.%Y"), time = datetime.datetime.today().strftime("%H:%M"), likes = 0, dislikes = 0, likers = "", dislikers = "", deleted = 0)
    db.session.add(comm)
    db.session.commit()
    return "Ok"

@app.route("/delete-comment/<ID>", methods=["POST", "GET"])
def delete_comment(ID):
    try:
        comm = Comment.query.filter_by(ID = int(ID))[0]
        values = comm.get_val()
        user = current_user.get_val()
        if values["userLogin"] == user["login"] and values["deleted"] == 0:
            post = Post.query.filter_by(ID = values["post"])[0]
            count = post.comments - 1
            for i in Comment.query.filter_by(onFComment = ID): 
                i.deleted = 2
                db.session.add(i)
                count -= 1
            post.comments = count
            db.session.add(post)
            comm.deleted = 1
            db.session.add(comm)
            db.session.commit()
            return "Ok"
        else: return "Error"
    except: return "Error"

@app.route("/get-comments", methods=["POST"])
def get_comments():
    ID = request.form["ID"]
    comments = Comment.query.filter_by(post = ID)
    res = [i.get_val() for i in comments]
    return jsonify(res, current_user.get_id())

@login_required
@app.route("/react-on-comment", methods=["POST"])
def react_on_comment():
    ID = int(request.form["ID"])
    reaction = request.form["reaction"]
    uid = str(current_user.get_id())
    comm = Comment.query.filter_by(ID = ID).first()
    if reaction == "like":
        if uid in comm.likers:
            comm.likers = comm.likers.replace(f"{uid} ", "")
            comm.likes -= 1
        else:
            if uid in comm.dislikers:
                comm.dislikers = comm.dislikers.replace(f"{uid} ", "")
                comm.dislikes -= 1
            comm.likers += f"{uid} "
            comm.likes += 1
    elif reaction == "dislike":
        if uid in comm.dislikers:
            comm.dislikers = comm.dislikers.replace(f"{uid} ", "")
            comm.dislikes -= 1
        else:
            if uid in comm.likers:
                comm.likers = comm.likers.replace(f"{uid} ", "")
                comm.likes -= 1
            comm.dislikers += f"{uid} "
            comm.dislikes += 1
    db.session.commit()
    return "Ok"

            


if __name__ == "__main__":
    upload_list()
    app.run(debug = True, host="0.0.0.0", threaded = True)