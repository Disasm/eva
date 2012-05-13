#!/usr/bin/python2
# -*- coding: koi8-r -*-

import sys
import xmpp
import time
import sqlite3


class Database:
    def __init__(self, dbname):
        self.con = sqlite3.connect(dbname)
        self.cur = self.con.cursor()

        try:
            self.cur.execute("SELECT id FROM messages LIMIT 1")
        except sqlite3.Error, e:
            print "creating tables..."
            self.create_tables()

    def close(self):
        if self.cur:
            self.cur.close()
            self.cur = None
        if self.con:
            self.con.close()
            self.con = None

    def add_message(self, tm, type1, jid, nick, body):
        self.cur.execute("INSERT INTO messages (time, type, jid, nick, body) values (?, ?, ?, ?, ?)", [tm, type1, jid, nick, body])
        self.con.commit()

    def create_tables(self):
        self.cur.execute('CREATE TABLE messages(id INTEGER PRIMARY KEY, time TEXT, type TEXT, jid TEXT, nick TEXT, body TEXT)')
        self.con.commit()



def timestr():
    #tm = time.localtime()
    return time.strftime("%Y-%m-%d %H:%M:%S")

def messageCB(conn,msg):
    tm = timestr()
    type1 = msg.getType()
    jid = unicode(msg.getFrom())
    nick = unicode(msg.getFrom().getResource())
    body = msg.getBody()

    global database
    database.add_message(tm, type1, jid, nick, body)

    print "=========="
    #print dir(msg)
    print "type:", type1
    print "time:", tm
    print "jid:", jid.encode('utf8')
    print "body:", body.encode('utf8')

    if type1 == "chat":
        conn.send(xmpp.Message(msg.getFrom(), "This is conference logger bot"))
    """
    if msg.getType() == "groupchat":
        print jid +": " + body
    if msg.getType() == "chat":
        print "private: " + jid + ":" + body
    """


def presenceCB(sess,pres):
    tm = timestr()
    type1 = pres.getType()
    jid = unicode(pres.getFrom())
    nick = unicode(pres.getFrom().getResource())

    if type1==None:
        type1 = "online"

    print "=========="
    print "jid:", jid.encode('utf8')
    print "presence type:", type1
    print "time:", tm

    global database
    database.add_message(tm, "presence", jid, nick, type1)

def StepOn(conn):
    try:
        conn.Process(1)
    except KeyboardInterrupt: return 0
    return 1

def GoOn(conn):
    while StepOn(conn): pass

if len(sys.argv)<5:
    print "Usage: bot.py username@server.net password conference@jid name"
else:
    database = Database("logs.db")
    
    jid=xmpp.JID(sys.argv[1])
    user,server,password=jid.getNode(),jid.getDomain(),sys.argv[2]

    conn=xmpp.Client(server,debug=[])
    conres=conn.connect()
    if not conres:
        print "Unable to connect to server %s!"%server
        sys.exit(1)
    if conres<>'tls':
        print "Warning: unable to estabilish secure connection - TLS failed!"
    authres=conn.auth(user,password)
    if not authres:
        print "Unable to authorize on %s - check login/password."%server
        sys.exit(1)
    if authres<>'sasl':
        print "Warning: unable to perform SASL auth os %s. Old authentication method used!"%server
    conn.RegisterHandler('message',messageCB)
    conn.RegisterHandler('presence',presenceCB)
    conn.sendInitPresence()
    print "Bot started."

    room = sys.argv[3]+"/"+sys.argv[4]
    print "Joining " + room

    conn.send(xmpp.Presence(to=room))
    
    GoOn(conn)
