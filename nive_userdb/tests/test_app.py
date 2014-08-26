# -*- coding: utf-8 -*-

import time
import unittest

from nive.security import AdminUser, UserFound
from nive_userdb.tests.db_app import *
from nive_userdb.tests import __local


class ObjectTest_db(object):

    def setUp(self):
        self._loadApp()

    def tearDown(self):
        self.app.Close()
        pass
    
    def test_add(self):
        a=self.app
        root=a.root()
        user = User("test")
        # root
        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByName("user2", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByName("user3", activeOnly=0)))
        data = {"password": "11111", "surname": "surname", "lastname": "lastname", "organistion": "organisation"}
        
        data["name"] = "user1"
        data["email"] = "user1@aaa.ccc"
        o,r = root.AddUser(data, activate=1, generatePW=0, mail=None, notify=False, groups="", currentUser=user)
        self.assert_(o,r)
        o,r = root.AddUser(data, activate=1, generatePW=0, mail=None, notify=False, groups="", currentUser=user)
        self.assertFalse(o,r)

        data["name"] = "user2"
        data["email"] = "user2@aaa.ccc"
        o,r = root.AddUser(data, activate=1, generatePW=1, mail=None, notify=False, groups="group:author", currentUser=user)
        self.assert_(o,r)

        data["name"] = "user3"
        data["email"] = "user3@aaa.ccc"
        o,r = root.AddUser(data, activate=0, generatePW=1, mail=None, notify=False, groups="group:editor", currentUser=user)
        self.assert_(o,r)
        self.assert_("group:editor" in o.data.groups, o.data.groups)
        self.assert_(o.data.password != "11111")
        self.assertFalse(o.meta.pool_state)
        
        root.MailUserPass(email = "user1", mailtmpl = None)
        root.MailUserPass(email = "user2@aaa.ccc", mailtmpl = None, createNewPasswd=False)
        root.MailUserPass(email = "user3@aaa.ccc", mailtmpl = None)
        
        self.assert_(root.GetUserByName("user2", activeOnly=1))
        self.assert_(root.GetUserByID(o.id, activeOnly=0))
        self.assert_(root.GetUserByMail("user2@aaa.ccc", activeOnly=1))
        
        self.assert_(root.LookupUser(name="user1", id=None, activeOnly=1))
        self.assertFalse(root.LookupUser(name="user3", id=None, activeOnly=1))
        self.assert_(root.LookupUser(name="user3", id=None, activeOnly=0))
        
        self.assert_(len(root.GetUserInfos([str(root.GetUserByName("user1", activeOnly=0)), 
                                            str(root.GetUserByName("user2", activeOnly=0))], 
                                           fields=["name", "email", "title"], activeOnly=1))==2)

        self.assert_(len(root.GetUsersWithGroup("group:author", fields=["name"], activeOnly=1)))
        self.assert_(len(root.GetUsersWithGroup("group:editor", fields=["name"], activeOnly=0)))
        self.assertFalse(len(root.GetUsersWithGroup("group:editor", fields=["name"], activeOnly=1)))
        self.assert_(len(root.GetUsers()))
        
        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByName("user2", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByName("user3", activeOnly=0)))

        
    def test_login(self):
        a=self.app
        root=a.root()
        user = User("test")
        # root
        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByName("user2", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByName("user3", activeOnly=0)))
        data = {"password": "11111", "surname": "surname", "lastname": "lastname", "organistion": "organisation"}
        
        data["name"] = "user1"
        data["email"] = "user1@aaa.ccc"
        o,r = root.AddUser(data, activate=1, generatePW=0, mail=None, notify=False, groups="", currentUser=user)
        self.assert_(o,r)
        l,r = root.Login("user1", "11111", raiseUnauthorized = 0)
        self.assert_(l,r)
        self.assert_(root.Logout(str(root.GetUserByName("user1", activeOnly=0))))
        l,r = root.Login("user1", "aaaaa", raiseUnauthorized = 0)
        self.assertFalse(l,r)
        l,r = root.Login("user1", "", raiseUnauthorized = 0)
        self.assertFalse(l,r)

        data["name"] = "user2"
        data["email"] = "user2@aaa.ccc"
        o,r = root.AddUser(data, activate=1, generatePW=1, mail=None, notify=False, groups="", currentUser=user)
        self.assert_(o,r)
        l,r = root.Login("user2", o.data.password, raiseUnauthorized = 0)
        self.assertFalse(l,r)
        root.Logout("user2")
        l,r = root.Login("user2", "11111", raiseUnauthorized = 0)
        self.assertFalse(l,r)

        data["name"] = "user3"
        data["email"] = "user3@aaa.ccc"
        o,r = root.AddUser(data, activate=0, generatePW=1, mail=None, notify=False, groups="group:author", currentUser=user)
        self.assert_(o,r)
        l,r = root.Login("user3", o.data.password, raiseUnauthorized = 0)
        self.assertFalse(l,r)
        root.Logout("user3")
        
        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByName("user2", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByName("user3", activeOnly=0)))


    def test_user(self):
        a=self.app
        root=a.root()
        user = User("test")
        # root
        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))
        data = {"password": "11111", "surname": "surname", "lastname": "lastname", "organistion": "organisation"}
        
        data["name"] = "user1"
        data["email"] = "user1@aaa.ccc"
        o,r = root.AddUser(data, activate=1, generatePW=0, mail=None, notify=False, groups="", currentUser=user)

        self.assert_(o.SecureUpdate(data, user))
        self.assert_(o.UpdateGroups(["group:author"]))
        self.assert_(o.GetGroups()==("group:author",), o.GetGroups())
        self.assert_(o.AddGroup("group:editor"))
        self.assert_(o.GetGroups()==("group:author","group:editor"), o.GetGroups())
        self.assert_(o.InGroups("group:editor"))
        self.assert_(o.InGroups("group:author"))
    
        self.assert_(o.ReadableName()=="surname lastname")

        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))


class ObjectTest_db_sqlite(ObjectTest_db, __local.SqliteTestCase):
    pass
class ObjectTest_db_mysql(ObjectTest_db, __local.MySqlTestCase):
    pass
class ObjectTest_db_postgres(ObjectTest_db, __local.PostgreSqlTestCase):
    pass


class AdminuserTest_db(__local.DefaultTestCase):

    def setUp(self):
        self._loadApp()
        self.app.configuration.unlock()
        self.app.configuration.admin = {"name":"admin", "password":"11111", "email":"admin@aaa.ccc", "groups":("group:admin",)}
        self.app.configuration.loginByEmail = True
        self.app.configuration.lock()
        
    def tearDown(self):
        self.app.Close()
        pass
    
    def test_login(self):
        user = User("test")
        a=self.app
        root=a.root()
        root.identityField=u"name"
        root.DeleteUser("adminXXXXX")
        root.DeleteUser("admin")

        data = {"password": "11111", "surname": "surname", "lastname": "lastname", "organistion": "organisation"}
        data["name"] = "admin"
        data["email"] = "admin@aaa.cccXXXXX"
        o,r = root.AddUser(data, activate=1, generatePW=0, mail=None, notify=False, groups="", currentUser=user)
        self.assertFalse(o,r)
        data["name"] = "adminXXXXX"
        data["email"] = "admin@aaa.ccc"
        o,r = root.AddUser(data, activate=1, generatePW=0, mail=None, notify=False, groups="", currentUser=user)
        self.assertFalse(o,r)

        l,r = root.Login("admin", "11111", raiseUnauthorized = 0)
        self.assert_(l,r)
        self.assert_(root.Logout("admin"))
        l,r = root.Login("admin", "aaaaa", raiseUnauthorized = 0)
        self.assertFalse(l,r)
        l,r = root.Login("admin", "", raiseUnauthorized = 0)
        self.assertFalse(l,r)

        
