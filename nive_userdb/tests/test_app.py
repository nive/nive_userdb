# -*- coding: utf-8 -*-

from pyramid import testing
import AuthEncoding

from nive_userdb.tests import __local
from nive_userdb.tests import db_app

from nive.security import User

from nive_userdb.app import UsernameValidator, EmailValidator, IsReservedUserName, Invalid


class ObjectTest_db(object):

    def setUp(self):
        request = testing.DummyRequest()
        request._LOCALE_ = "en"
        self.request = request
        self.config = testing.setUp(request=request)
        self.config.include('pyramid_chameleon')
        self._loadApp()
        self.app.Startup(self.config)

    def tearDown(self):
        db_app.emptypool(self.app)
        self.app.Close()
        testing.tearDown()

    
    def test_add(self):
        a=self.app
        root=a.root
        user = User("test")
        # root
        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByName("user2", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByName("user3", activeOnly=0)))
        data = {"password": "11111", "surname": "surname", "lastname": "lastname", "organistion": "organisation"}
        
        data["name"] = "user1"
        data["email"] = "user1@aaa.ccc"
        o,r = root.AddUser(data, activate=1, generatePW=0, mail=None, groups="", currentUser=user, url="")
        self.assertTrue(o,r)
        o,r = root.AddUser(data, activate=1, generatePW=0, mail=None, groups="", currentUser=user, url="")
        self.assertFalse(o,r)

        data["name"] = "user2"
        data["email"] = "user2@aaa.ccc"
        o,r = root.AddUser(data, activate=1, generatePW=1, mail=None, groups="group:author", currentUser=user, url="")
        self.assertTrue(o,r)

        data["name"] = "user3"
        data["email"] = "user3@aaa.ccc"
        o,r = root.AddUser(data, activate=0, generatePW=1, mail=None, groups="group:editor", currentUser=user, url="")
        self.assertTrue(o,r)
        self.assertTrue("group:editor" in o.data.groups, o.data.groups)
        self.assertTrue(o.data.password != "11111")
        self.assertFalse(o.meta.pool_state)
        
        root.MailUserPass(name = "user1", url="")
        root.MailUserPass(name = "user2@aaa.ccc", newPasswd="111111", url="")
        root.MailUserPass(name = "user3@aaa.ccc", url="")

        self.assertTrue(root.GetUserByName("user2", activeOnly=1))
        self.assertTrue(root.GetUserByID(o.id, activeOnly=0))
        self.assertTrue(root.GetUserByMail("user2@aaa.ccc", activeOnly=1))
        
        self.assertTrue(root.LookupUser(name="user1", id=None, activeOnly=1))
        self.assertFalse(root.LookupUser(name="user3", id=None, activeOnly=1))
        self.assertTrue(root.LookupUser(name="user3", id=None, activeOnly=0))
        
        self.assertTrue(len(root.GetUserInfos([str(root.GetUserByName("user1", activeOnly=0)), 
                                            str(root.GetUserByName("user2", activeOnly=0))], 
                                           fields=["name", "email", "title"], activeOnly=1))==2)

        self.assertTrue(len(root.GetUsersWithGroup("group:author", fields=["name"], activeOnly=1)))
        self.assertTrue(len(root.GetUsersWithGroup("group:editor", fields=["name"], activeOnly=0)))
        self.assertFalse(len(root.GetUsersWithGroup("group:editor", fields=["name"], activeOnly=1)))
        self.assertTrue(len(root.GetUsers()))
        
        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByName("user2", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByName("user3", activeOnly=0)))


    def test_add_name(self):
        a=self.app
        root=a.root
        user = User("test")
        # root
        root.DeleteUser(str(root.GetUserByMail("user2@aaa.ccc", activeOnly=0)))
        data = {"password": "11111", "surname": "surname", "lastname": "lastname", "organistion": "organisation"}

        data["name"] = "user2"
        data["email"] = "user2@aaa.ccc"
        o,r = root.AddUser(data, activate=1, generatePW=0, generateName=True, mail=None, groups="", currentUser=user, url="")
        self.assertTrue(o,r)
        self.assertTrue(o.data.name)
        self.assertTrue(o.data.name!="user2")

        self.assertTrue(root.LookupUser(name=o.data.name, id=None, activeOnly=1))

        root.DeleteUser(str(o))


    def test_login(self):
        a=self.app
        root=a.root
        user = User("test")
        # root
        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByMail("user1@aaa.ccc", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByName("user2", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByMail("user2@aaa.ccc", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByName("user3", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByMail("user3@aaa.ccc", activeOnly=0)))
        data = {"password": "11111", "surname": "surname", "lastname": "lastname", "organistion": "organisation"}
        
        data["name"] = "user1"
        data["email"] = "user1@aaa.ccc"
        o,r = root.AddUser(data, activate=1, generatePW=0, mail=None, groups="", currentUser=user)
        self.assertTrue(o,r)
        l,r = root.Login("user1", "11111", raiseUnauthorized = 0)
        self.assertTrue(l,r)
        self.assertTrue(root.Logout(str(root.GetUserByName("user1", activeOnly=0))))
        l,r = root.Login("user1", "aaaaa", raiseUnauthorized = 0)
        self.assertFalse(l,r)
        l,r = root.Login("user1", "", raiseUnauthorized = 0)
        self.assertFalse(l,r)

        data["name"] = "user2"
        data["email"] = "user2@aaa.ccc"
        o,r = root.AddUser(data, activate=1, generatePW=1, mail=None, groups="", currentUser=user)
        self.assertTrue(o,r)
        l,r = root.Login("user2", o.data.password, raiseUnauthorized = 0)
        self.assertFalse(l,r)
        root.Logout("user2")
        l,r = root.Login("user2", "11111", raiseUnauthorized = 0)
        self.assertFalse(l,r)

        data["name"] = "user3"
        data["email"] = "user3@aaa.ccc"
        o,r = root.AddUser(data, activate=0, generatePW=1, mail=None, groups="group:author", currentUser=user)
        self.assertTrue(o,r)
        l,r = root.Login("user3", o.data.password, raiseUnauthorized = 0)
        self.assertFalse(l,r)
        root.Logout("user3")
        
        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByName("user2", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByName("user3", activeOnly=0)))


    def test_user(self):
        a=self.app
        root=a.root
        user = User("test")
        # root
        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))
        data = {"password": "11111", "surname": "surname", "lastname": "lastname", "organistion": "organisation"}
        
        data["name"] = "user1"
        data["email"] = "user1@aaa.ccc"
        o,r = root.AddUser(data, activate=1, generatePW=0, mail=None, groups="", currentUser=user)

        self.assertTrue(o.SecureUpdate(data, user))
        self.assertTrue(o.UpdateGroups(["group:author"]))
        self.assertTrue(o.GetGroups()==("group:author",), o.GetGroups())
        self.assertTrue(o.AddGroup("group:editor"))
        self.assertTrue(o.GetGroups()==("group:author","group:editor"), o.GetGroups())
        self.assertTrue(o.InGroups("group:editor"))
        self.assertTrue(o.InGroups("group:author"))
    
        self.assertTrue(o.ReadableName()=="surname lastname")

        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))


    def test_user2(self):
        a=self.app
        root=a.root
        user = User("test")

        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByMail("user1@aaa.ccc", activeOnly=0)))
        data = {"password": "11111", "surname": "surname", "lastname": "lastname", "token": "12345"}
        data["name"] = "user1"
        data["email"] = "user1@aaa.ccc"
        o,r = root.AddUser(data, activate=0, generatePW=0, mail=None, groups="", currentUser=user)
        self.assertTrue(o,r)

        o.HashPassword()
        o.data["password"] = "12345"
        o.HashPassword()
        self.assertTrue(AuthEncoding.pw_validate(o.data.password, "12345"))

        o.data["surname"] = ""
        o.data["lastname"] = ""
        self.assertTrue(o.ReadableName()==o.data.name)
        o.data["surname"] = "surname"
        o.data["lastname"] = "lastname"
        self.assertTrue(o.ReadableName()=="surname lastname")

        self.assertTrue(o.Activate(currentUser=user))

        o.UpdatePassword("22222", user=user, resetActivation=True)
        self.assertTrue(AuthEncoding.pw_validate(o.data.password, "22222"))
        o.UpdatePassword("33333", user=user, resetActivation=False)
        self.assertTrue(AuthEncoding.pw_validate(o.data.password, "33333"))


    def test_reserved(self):
        self.assertTrue(IsReservedUserName(""))
        self.assertTrue(IsReservedUserName(None))
        self.assertTrue(IsReservedUserName("group:admin"))
        self.assertTrue(IsReservedUserName("group:aaaaaaaaaa"))
        self.assertFalse(IsReservedUserName("aaaaaaaaaaaa"))


    def test_usernamevalidator(self):
        a=self.app
        root=a.root
        user = User("test")

        class tf(object):
            context = root
        class tw(object):
            form = tf()
        class tn(object):
            widget = tw()
        node = tn()

        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByMail("user1@aaa.ccc", activeOnly=0)))
        UsernameValidator(node, "user1")

        data = {"password": "11111", "surname": "surname", "lastname": "lastname", "token": "12345"}
        data["name"] = "user1"
        data["email"] = "user1@aaa.ccc"
        o,r = root.AddUser(data, activate=0, generatePW=0, mail=None, groups="", currentUser=user)
        self.assertTrue(o,r)
        self.assertRaises(Invalid, UsernameValidator, node, "user1")
        self.assertRaises(Invalid, UsernameValidator, node, "user1@aaa.ccc")

        self.assertRaises(Invalid, UsernameValidator, node, "ua")
        self.assertRaises(Invalid, UsernameValidator, node, "#+§$%")
        self.assertRaises(Invalid, UsernameValidator, node, "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu")
        self.assertRaises(Invalid, UsernameValidator, node, "group:")
        self.assertRaises(Invalid, UsernameValidator, node, "group:test")


    def test_emailvalidator(self):
        a=self.app
        root=a.root
        user = User("test")

        class tf(object):
            context = root
        class tw(object):
            form = tf()
        class tn(object):
            widget = tw()
        node = tn()

        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByMail("user1@aaa.ccc", activeOnly=0)))
        EmailValidator(node, "user1@aaa.ccc")

        data = {"password": "11111", "surname": "surname", "lastname": "lastname", "token": "12345"}
        data["name"] = "user1"
        data["email"] = "user1@aaa.ccc"
        o,r = root.AddUser(data, activate=0, generatePW=0, mail=None, groups="", currentUser=user)
        self.assertTrue(o,r)
        self.assertRaises(Invalid, EmailValidator, node, "user1@aaa.ccc")
        self.assertRaises(Invalid, EmailValidator, node, "user1")

        self.assertRaises(Invalid, EmailValidator, node, "ua")
        self.assertRaises(Invalid, EmailValidator, node, "#+§$%")



    def test_activate(self):
        a=self.app
        root=a.root
        user = User("test")
        # root
        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByMail("user1@aaa.ccc", activeOnly=0)))
        data = {"password": "11111", "surname": "surname", "lastname": "lastname", "token": "12345"}

        data["name"] = "user1"
        data["email"] = "user1@aaa.ccc"
        o,r = root.AddUser(data, activate=0, generatePW=0, mail=None, groups="", currentUser=user)
        self.assertTrue(o,r)

        self.assertFalse(root.GetUserForToken("no id"))

        self.assertFalse(root.GetUserForToken("12345", activeOnly=True))
        u = root.GetUserForToken("12345", activeOnly=False)
        self.assertTrue(u)
        self.assertTrue(u.Activate(currentUser=user))

        self.assertFalse(root.GetUserForToken("12345", activeOnly=False))

        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))


    def test_mail_pass(self):
        a=self.app
        root=a.root
        user = User("test")
        # root
        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByMail("user1@aaa.ccc", activeOnly=0)))
        data = {"password": "11111", "surname": "surname", "lastname": "lastname"}
        data["name"] = "user1"
        data["email"] = "user1@aaa.ccc"
        o,r = root.AddUser(data, activate=1, generatePW=0, mail=None, groups="", currentUser=user, url="uu")
        self.assertTrue(o,r)

        root.MailResetPass("user1@aaa.ccc", currentUser=user, url="")
        self.assertTrue(root.GetUserByName("user1").data.token)
        o,r = root.MailResetPass("no mail", currentUser=user, url="")
        self.assertFalse(o,r)

        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))


    def test_reset_pass(self):
        a=self.app
        root=a.root
        user = User("test")
        # root
        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByMail("user1@aaa.ccc", activeOnly=0)))
        data = {"password": "11111", "surname": "surname", "lastname": "lastname", "token": "12345"}
        data["name"] = "user1"
        data["email"] = "user1@aaa.ccc"
        o,r = root.AddUser(data, activate=1, generatePW=0, mail=None, groups="", currentUser=user)
        self.assertTrue(o,r)

        self.assertTrue(root.GetUserForToken("12345", activeOnly=False))

        self.assertFalse(root.GetUserForToken("", activeOnly=False))

        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))


    def test_groups(self):
        a=self.app
        root=a.root
        user = User("test")
        # root
        root.DeleteUser(str(root.GetUserByName("user1", activeOnly=0)))
        root.DeleteUser(str(root.GetUserByMail("user1@aaa.ccc", activeOnly=0)))
        data = {"password": "11111", "surname": "surname", "lastname": "lastname", "token": "12345"}
        data["name"] = "user1"
        data["email"] = "user1@aaa.ccc"
        o,r = root.AddUser(data, activate=1, generatePW=0, mail=None, groups="", currentUser=user)
        self.assertTrue(o,r)

        o.UpdateGroups(["g1","g2","g3"])
        self.assertTrue(o.GetGroups()==("g1","g2","g3"))
        self.assertTrue(o.InGroups(("g1","g2","g3")))
        self.assertTrue(o.InGroups("g1"))
        self.assertFalse(o.InGroups(("zz","yy","xx")))
        self.assertFalse(o.InGroups("xx"))
        o.AddGroup("g4")
        self.assertTrue(o.InGroups("g4"))
        self.assertTrue(o.InGroups(("g1","g2","g3")))
        o.RemoveGroup("g4")
        self.assertFalse(o.InGroups("g4"))
        self.assertTrue(o.InGroups(("g1","g2","g3")))







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

    
    def test_login(self):
        user = User("test")
        a=self.app
        root=a.root
        root.identityField="name"
        root.DeleteUser("adminXXXXX")
        root.DeleteUser("admin")

        data = {"password": "11111", "surname": "surname", "lastname": "lastname", "organistion": "organisation"}
        data["name"] = "admin"
        data["email"] = "admin@aaa.cccXXXXX"
        o,r = root.AddUser(data, activate=1, generatePW=0, mail=None, groups="", currentUser=user)
        self.assertFalse(o,r)
        data["name"] = "adminXXXXX"
        data["email"] = "admin@aaa.ccc"
        o,r = root.AddUser(data, activate=1, generatePW=0, mail=None, groups="", currentUser=user)
        self.assertFalse(o,r)

        l,r = root.Login("admin", "11111", raiseUnauthorized = 0)
        self.assertTrue(l,r)
        self.assertTrue(root.Logout("admin"))
        l,r = root.Login("admin", "aaaaa", raiseUnauthorized = 0)
        self.assertFalse(l,r)
        l,r = root.Login("admin", "", raiseUnauthorized = 0)
        self.assertFalse(l,r)


