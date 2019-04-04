# -*- coding: utf-8 -*-


from nive.utils.path import DvPath
from nive.definitions import AppConf, DatabaseConf
from nive.portal import Portal
from nive_userdb.app import UserDB


def app_db(confs=None):
    appconf = AppConf("nive_userdb.app")
    appconf.modules.append("nive_userdb.userview.view")
    appconf.modules.append("nive.tools.sendMailTester")
    app = UserDB()
    app.Register(appconf)
    if confs:
        for c in confs:
            app.Register(c)
    p = Portal()
    p.Register(app)
    app.Startup(None)
    dbfile = DvPath(app.dbConfiguration.dbName)
    if not dbfile.IsFile():
        dbfile.CreateDirectories()
    db = app.db
    try:
        cursor = db.Execute("select id from pool_meta where id=1")
        db.Execute("select id from users where id=1", cursor=cursor)
        db.Execute("select id from users where token='1'", cursor=cursor)
        db.Execute("select id from users where tempcache='1'", cursor=cursor)
        db.Execute("select id from pool_files where id=1", cursor=cursor)
    except:
        app.GetTool("nive.tools.dbStructureUpdater")()
    return app

def app_nodb():
    appconf = AppConf("nive_userdb.app")
    appconf.modules.append("nive_userdb.userview.view")
    appconf.modules.append("nive.tools.sendMail")
    
    app = UserDB(appconf)
    app.dbConfiguration=DatabaseConf()
    p = Portal()
    p.Register(app)
    app.Startup(None)
    return app

def emptypool(app):
    db = app.db
    cursor = db.Execute("delete FROM pool_meta")
    db.Execute("delete FROM pool_files", cursor=cursor)
    db.Execute("delete FROM pool_fulltext", cursor=cursor)
    db.Execute("delete FROM pool_groups", cursor=cursor)
    db.Execute("delete FROM pool_sys", cursor=cursor)
    db.Execute("delete FROM users", cursor=cursor)
    cursor.close()
    db.Commit()

def createpool(path, app):
    path.CreateDirectories()
    app.GetTool("nive.tools.dbStructureUpdater")()

