# -*- coding: utf-8 -*-

import time
import unittest

from nive.utils.path import DvPath
from nive.definitions import AppConf, DatabaseConf
from nive.security import User
from nive.portal import Portal
from nive_userdb.app import UserDB


def app_db(confs=None):
    appconf = AppConf("nive_userdb.app")
    appconf.modules.append("nive_userdb.userview.view")
    appconf.modules.append("nive.tools.sendMailTester")
    a = UserDB()
    a.Register(appconf)
    if confs:
        for c in confs:
            a.Register(c)
    p = Portal()
    p.Register(a)
    a.Startup(None)
    dbfile = DvPath(a.dbConfiguration.dbName)
    if not dbfile.IsFile():
        dbfile.CreateDirectories()
    try:
        a.Query("select id from pool_meta where id=1")
        a.Query("select id from users where id=1")
        a.Query("select id from users where token='1'")
        a.Query("select id from users where tempcache='1'")
        a.Query("select id from pool_files where id=1")
    except:
        a.GetTool("nive.tools.dbStructureUpdater")()
    return a

def app_nodb():
    appconf = AppConf("nive_userdb.app")
    appconf.modules.append("nive_userdb.userview.view")
    appconf.modules.append("nive.tools.sendMail")
    
    a = UserDB(appconf)
    a.dbConfiguration=DatabaseConf()
    p = Portal()
    p.Register(a)
    a.Startup(None)
    return a

def emptypool(app):
    db = app.db
    db.Query(u"delete FROM pool_meta")
    db.Query(u"delete FROM pool_files")
    db.Query(u"delete FROM pool_fulltext")
    db.Query(u"delete FROM pool_groups")
    db.Query(u"delete FROM pool_sys")
    db.Query(u"delete FROM users")
    import shutil
    shutil.rmtree(str(db.root), ignore_errors=True)
    db.root.CreateDirectories()

def createpool(path,app):
    path.CreateDirectories()
    app.GetTool("nive.tools.dbStructureUpdater")()

def create_user(name,email):
    type = "user"
    data = {"name": name, "password": "11111", "email": email, "surname": "surname", "lastname": "lastname", "organistion": "organisation"}
    user = User("test")
    r = a.GetRoot()
    o = r.Create(type, data = data, user = user)
    #o.Commit()
    return o

