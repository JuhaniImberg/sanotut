#!venv/bin/python
# coding: utf-8

import sys
sys.dont_write_bytecode = True
import os
import config
import mysql.connector
import string
import random
from passlib.apps import custom_app_context as pwd_context

db = mysql.connector.connect(password=config.password,
                             user=config.user,
                             host=config.host,
                             database=config.database,
                             buffered=True)

c = db.cursor()


def main():
    if "initdb" in sys.argv:
        initdb()
    elif "count" in sys.argv:
        count()
    elif "usercount" in sys.argv:
        usercount()
    elif "passwd" in sys.argv:
        passwd()
    else:
        print "./manage.py <command>"
        print ""
        print "  initdb          initialize MySQL"
        print "  count           find anomalies in votes"
        print "  usercount       list users"
        print "  passwd          set password"


def passwd():
    uid = input("User ID: ")
    allchoice = string.lowercase + string.uppercase + string.digits
    new = ''.join(random.choice(allchoice) for i in range(12))
    print "Setting user id %s password to %s" % (uid, new)
    hash = pwd_context.encrypt(new)
    res = c.execute("UPDATE sanotut_users SET password = (%s) WHERE id = (%s)",
                    (hash, uid))
    print res
    db.commit()


def count():
    c.execute("SELECT * FROM sanotut")
    pa = c.fetchall()
    for p in pa:
        c.execute("SELECT * FROM sanotut_votes WHERE post_id=(%s)", (p[0],))
        va = c.fetchall()
        n = 0
        for v in va:
            n += v[4]
        if n != p[4]:
            print "%i: %i points =/= %i votes" % (p[0], p[4], n,)


def usercount():
    c.execute("SELECT * FROM sanotut_users")
    ua = c.fetchall()
    ng = 0
    ngl = 0
    for u in ua:
        c.execute("SELECT * FROM sanotut_votes WHERE user_id=(%s)", (u[0],))
        va = c.fetchall()
        n = 0
        for v in va:
            n += v[4]
        ng += n
        ngl += len(va)
        print "%s: %s%s votes with diff %s" % (str(u[0]).rjust(3), u[1].ljust(30), str(len(va)).rjust(4), str(n).rjust(4),)
    print "%i users with %i votes with diff %i" % (len(ua), ngl, ng)


def initdb():
    c.execute("""   CREATE TABLE IF NOT EXISTS sanotut (
                    id INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    time DATETIME,
                    message TEXT,
                    computer TEXT,
                    points INTEGER NOT NULL DEFAULT 0
                    );""")
    c.execute("""   CREATE TABLE IF NOT EXISTS sanotut_users (
                    id INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role INTEGER NOT NULL DEFAULT 0,
                    session VARCHAR(255),
                    UNIQUE (email)
                    );""")
    c.execute("""   CREATE TABLE IF NOT EXISTS sanotut_votes (
                    id INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    time DATETIME,
                    user_id INTEGER,
                    post_id INTEGER,
                    diff INTEGER
                    );""")

    db.commit()

if __name__ == "__main__":
    main()
