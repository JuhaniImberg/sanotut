#!venv/bin/python
# coding: utf-8

# standard
import sys
sys.dont_write_bytecode = True
import os
import re
import pwd
import string
import random
import time
import datetime

# our
import config

# packages
from passlib.apps import custom_app_context as pwd_context
from flask import (Flask, render_template, flash, redirect, request, abort,
                   session, g)
import mysql.connector

# globals
app = Flask(__name__,
            template_folder="sanotut/templates",
            static_folder="sanotut/static")
app.config["SECRET_KEY"] = config.secret

db = mysql.connector.connect(password=config.password,
                             user=config.user,
                             host=config.host,
                             database=config.database,
                             buffered=True)
c = db.cursor()


def checksesval():
    if "sesval" not in session or "email" not in session or "logged_in" not in session:
        return None
    c.execute(("SELECT * FROM sanotut_users "
               "WHERE session = (%s) AND email = (%s)"),
             (session["sesval"], session["email"],))
    res = c.fetchone()
    if res == None:
        return None
    if len(res[4]) == 64:
        return res[0]
    return None


def validemail(email):
    if email == None:
        return False
    m = re.match("^(\w+)@paivola.fi$", email)
    if m == None:
        return False
    if config.realaccouts:
        try:
            pwd.getpwnam(m.group(1))
        except KeyError:
            return False
    return True


def checklogout():
    uid = checksesval()
    if uid == None:
        if "sesval" in session:
            del session["sesval"]
        if "email" in session:
            del session["email"]
        if "logged_in" in session:
            del session["logged_in"]


def render(template, **kwargs):
    style = session["style"] if "style" in session else "classic"
    return render_template(style + "/" + template, **kwargs)


@app.route('/')
def route_index():
    checklogout()
    sort = request.args.get('sort', '')
    if sort == "best":
        c.execute("SELECT * FROM sanotut ORDER BY points DESC")
    elif sort == "worst":
        c.execute("SELECT * FROM sanotut ORDER BY points ASC")
    else:
        sort = "new"
        c.execute("SELECT * FROM sanotut ORDER BY id DESC")
    entries = c.fetchall()
    uid = checksesval()
    voted = []
    if uid != None:
        c.execute("SELECT * FROM sanotut_votes WHERE user_id=(%s)", (uid,))
        voted = [(row[3], row[4]) for row in c.fetchall()]
    return render("index.html",
                  entries=entries,
                  voted=voted,
                  nohide=(True if sort == "worst" else False),
                  name=sort)


@app.route('/add', methods=['GET', 'POST'])
def route_add():
    checklogout()
    if request.method == 'POST':
        if "sanottu" not in request.form:
            abort(400)
        c.execute(("INSERT INTO sanotut "
                   "(message, computer, time) "
                   "VALUES (%s, %s, %s)"),
                  (request.form[
                      "sanottu"].replace("<", "&lt;").replace(">", "&gt;"),
                   request.remote_addr,
                   datetime.datetime.now()))
        db.commit()
        return redirect("/")
    return render("add.html", name="add")


@app.route('/register', methods=['GET', 'POST'])
def route_register():
    checklogout()
    if request.method == 'POST':
        if "email" not in request.form or not validemail(request.form["email"]):
            flash(u"Sähköposti ei vastaa vaadittua kaavaa!")
            return redirect("/register")
        if "password" not in request.form or len(request.form["password"]) < 6:
            flash(u"Salasanasi tulee olla yli viisi merkkiä!")
            return redirect("/register")
        hash = pwd_context.encrypt(request.form["password"])

        try:
            c.execute(("INSERT INTO sanotut_users "
                       "(email, password) "
                       "VALUES (%s, %s)"),
                     (request.form["email"], hash,))
        except Exception:
            flash(u"Tuo sposti on rekisteröity jo!")
            return redirect("/register")

        db.commit()

        flash(u"Voit nyt kirjautua sisään!")
        return redirect("/login", name="login")
    return render("register.html", name="register")


@app.route('/login', methods=['GET', 'POST'])
def route_login():
    checklogout()
    if request.method == 'POST':
        if "email" not in request.form or "password" not in request.form:
            flash(u"Anna sposti ja salasana.")
            return redirect("/login")
        c.execute(("SELECT * FROM sanotut_users "
                   "WHERE email = (%s)"),
                 (request.form["email"],))
        res = c.fetchone()
        if res == None or not pwd_context.verify(request.form["password"], res[2]):
            flash(u"Ei moista sposti/salasana paria!")
            return redirect("/login")
        allchoice = string.lowercase + string.uppercase + string.digits
        sesval = ''.join(random.choice(allchoice) for i in range(64))

        c.execute("UPDATE sanotut_users SET session = (%s) WHERE id = (%s)",
                 (sesval, res[0],))
        db.commit()

        session["sesval"] = sesval
        session["email"] = request.form["email"]
        session["logged_in"] = True

        flash(u"Kirjauduit sisään.")
        return redirect("/")
    return render("login.html", name="login")


@app.route('/passwd', methods=['GET', 'POST'])
def route_passwd():
    checklogout()

    uid = checksesval()
    if uid is None:
        return u"error: et ole kirjautunut sisään", 400

    if request.method == 'POST':
        if "new" not in request.form or len(request.form["new"]) < 6:
            flash(u"Uusi salasana ei täyttänyt vaatimuksia")
            return redirect("/passwd")
        c.execute(("SELECT * FROM sanotut_users "
                   "WHERE email = (%s)"),
                 (session["email"],))
        res = c.fetchone()
        if res == None or not pwd_context.verify(request.form.get("old", ""), res[2]):
            flash(u"Vanha salasana väärin")
            return redirect("/passwd")

        c.execute("UPDATE sanotut_users SET password = (%s) WHERE id = (%s)",
                  (pwd_context.encrypt(request.form["new"]), uid))
        db.commit()

        flash(u"Salasana vaihdettu.")
        return redirect("/")
    return render("passwd.html")


@app.route('/logout')
def route_logout():
    uid = checksesval()
    if uid == None:
        del session["sesval"]
        del session["email"]
        del session["logged_in"]
        flash(u"Olet jo kirjautunut ulos.")
        return redirect("/")
    c.execute("UPDATE sanotut_users SET session = NULL WHERE id = (%s)",
             (uid,))
    del session["sesval"]
    del session["email"]
    del session["logged_in"]
    flash(u"Olet kirjautunut ulos.")
    return redirect("/")


@app.route('/vote', methods=['POST'])
def route_vote():
    if request.data == None:
        abort(400)

    uid = checksesval()
    if uid == None:
        return u"error: et ole kirjautunut sisään", 400

    spl = request.data.split(":")
    if len(spl) != 2:
        abort(400)
    meth = spl[0]
    id = int(spl[1])
    amount = 0
    if meth == "up":
        amount = 1
    elif meth == "down":
        amount = -1
    else:
        return "error: unkown method", 400

    c.execute(("SELECT * FROM sanotut_votes "
               "WHERE post_id=(%s) AND user_id=(%s)"), (id, uid,))
    earlier = c.fetchone()
    if earlier != None:
        if earlier[4] == amount:
            return u"error: olet jo äänestänyt tuota", 400
        c.execute(("DELETE FROM sanotut_votes "
                   "WHERE id=(%s)"), (earlier[0],))
        c.execute(("UPDATE sanotut "
                   "SET points=points+(%(amount)s) WHERE id=(%(id)s)"),
                  {"amount": amount, "id": id})
        db.commit()
        return "success:%s:%i" % (meth, id), 200

    c.execute(("INSERT INTO sanotut_votes "
               "(time, user_id, post_id, diff) VALUES (%s, %s, %s, %s)"),
             (datetime.datetime.now(), uid, id, amount))
    c.execute(("UPDATE sanotut "
               "SET points=points+(%(amount)s) WHERE id=(%(id)s)"),
              {"amount": amount, "id": id})
    db.commit()
    return "success:%s:%i" % (meth, id), 200


@app.route('/stats')
def route_stats():
    checklogout()
    data = {}
    c.execute("SELECT COUNT(*) FROM sanotut")
    data["posts"] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM sanotut_votes")
    data["votes"] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM sanotut_users")
    data["users"] = c.fetchone()[0]
    c.execute("SELECT * FROM sanotut_votes")
    arr = c.fetchall()
    data["diff"] = 0
    for i in arr:
        data["diff"] += i[4]
    return render("stats.html", data=data, name="stats")


@app.route('/style/<string:name>')
def route_style(name):
    session["style"] = name
    return redirect("/")


@app.before_request
def before_request():
    g.start = time.time()


@app.after_request
def after_request(response):
    diff = time.time() - g.start
    if (response.response):
        if response.content_type.startswith("text/html;"):
            if "__EXECUTION_TIME__" in response.response[0]:
                response.response[0] = response.response[
                    0].replace('__EXECUTION_TIME__', "{0:.4f}s".format(diff))
                response.headers["content-length"] = len(response.response[0])
    return response


@app.context_processor
def utility_processor():
    def hasvoted(val, arr, diff):
        for i in arr:
            if val == i[0] and diff == i[1]:
                return True
        return False

    return dict(hasvoted=hasvoted)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
