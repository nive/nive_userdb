# -*- coding: utf-8 -*-

from nive_userdb.tests import __local
from nive_userdb.tests import db_app

from nive_userdb.useradmin import view
from nive_userdb.useradmin import adminroot

from nive.security import DummySecurityPolicy
from nive.security import User
from nive.portal import Portal

from pyramid.httpexceptions import HTTPFound
from pyramid import testing
from pyramid.renderers import render

class TestView(view.UsermanagementView):
    __configuration__ = lambda a: view.configuration
    def User(self, sessionuser=None):
        return User("testuser")

class tViews(__local.DefaultTestCase):

    def setUp(self):
        request = testing.DummyRequest()
        request._LOCALE_ = "en"
        self.request = request
        self.request.method = "POST"
        self.config = testing.setUp(request=request)
        self.config.registry.registerUtility(DummySecurityPolicy("test"))
        self.config.include('pyramid_chameleon')
        self._loadApp()
        self.portal = Portal()
        self.portal.Register(self.app, "userdb")
        self.app.Register(adminroot.configuration)
        self.app.Startup(self.config)
        self.root = self.app.GetRoot("management")
        self.request.context = self.root
        self.request.content_type = ""


    def tearDown(self):
        self._closeApp(True, True)
        testing.tearDown()


    def test_templates(self):
        user = User("test")
        v = TestView(context=self.root, request=self.request)
        vrender = {"context":self.root, "view":v, "request": self.request}
        
        values = v.options()
        values.update(vrender)
        render("nive_userdb.useradmin:templates/options.pt", values)
        u=self.root.Create("user",{"name":"testuser", "password":"test", "email":"test@aaa.com", "groups":("group:admin",)},user=user)
        v.context = u
        values = v.viewlist()
        values.update(vrender)
        values["context"] = u
        render("nive_userdb.useradmin:templates/root.pt", values)

        self.root.Delete(u.id, user=user)


    def test_add(self):
        user = self.root.GetUserByName("testuser")
        #if user is not None:
        self.root.DeleteUser("testuser")
        v = TestView(context=self.root, request=self.request)
        r = v.add()
        self.assertFalse(r["result"])
        user = self.root.GetUserByName("testuser")
        self.assertFalse(user, "User should not exist")
        self.request.POST = {"pool_type": "user", "name":"testuser", "password":"", "email":"test@aaa.com", "groups":("group:admin",)}
        r = v.add()
        self.assertTrue(r["result"])
        user = self.root.GetUserByName("testuser")
        self.assertFalse(user, "User should not exist")
        
        self.request.POST["create$"] = "create"
        r = v.add()
        self.assertFalse(r["result"])
        user = self.root.GetUserByName("testuser")
        self.assertFalse(user, "User should not exist")
        self.request.POST["password"] = "password"
        self.request.POST["password-confirm"] = "password"
        
        self.assertRaises(HTTPFound, v.add)
        self.assertTrue(self.root.GetUserByName("testuser"))
        
        self.root.DeleteUser("testuser")


    def test_edit(self):
        user = self.root.GetUserByName("testuser")
        if user:
            self.root.DeleteUser("testuser")
        v = TestView(context=self.root, request=self.request)
        self.request.POST = {"pool_type": "user", "name":"testuser", "email":"test@aaa.com", "groups":("group:admin",)}
        self.request.POST["password"] = "password"
        self.request.POST["password-confirm"] = "password"
        self.request.POST["create$"] = "create"
        self.assertRaises(HTTPFound, v.add)
        user = self.root.GetUserByName("testuser")
        if user is None:
            self.assertTrue(False, "User should exist")
        
        v = TestView(context=user, request=self.request)
        self.request.POST = {}
        r = v.edit()
        self.assertTrue(r["result"])

        self.request.POST = {"name":"testuser", "email":"test", "groups":("group:admin",)}
        self.request.POST["edit$"] = "edit"
        r = v.edit()
        self.assertFalse(r["result"])
        user = self.root.GetUserByName("testuser")
        self.assertTrue(user.data.email != "test")
        
        self.request.POST = {"name":"testuser", "email":"test@bbb.com", "groups":("group:admin",)}
        self.request.POST["edit$"] = "edit"
        self.assertRaises(HTTPFound, v.edit)
        #self.assertTrue(r["result"])
        user = self.root.GetUserByName("testuser")
        self.assertTrue(user.data.email == "test@bbb.com")
        
        self.root.DeleteUser("testuser")


    def test_delete(self):
        v = TestView(context=self.root, request=self.request)
        user = self.root.GetUserByName("testuser")
        if user is None:
            self.request.POST = {"pool_type": "user", "name":"testuser", "email":"test@aaa.com", "groups":("group:admin",)}
            self.request.POST["password"] = "password"
            self.request.POST["password-confirm"] = "password"
            self.request.POST["create$"] = "create"
            self.assertRaises(HTTPFound, v.add)
        user = self.root.GetUserByName("testuser")
        if user is None:
            self.assertTrue(False, "User should exist")
            
        v.context = user
        r = v.delete()
        self.assertFalse(r["result"])
        self.assertTrue(r["objsToDelete"])

        ids = (user.id,)
        self.request.POST = {"ids":ids, "delete": "0"}

        r = v.delete()
        self.assertFalse(r["result"])
        self.assertTrue(len(r["objsToDelete"])==1)

        self.request.POST = {"ids":ids, "delete": "1"}
        self.assertRaises(HTTPFound, v.delete)
        self.assertFalse(self.root.GetUserByName("testuser"))
        

