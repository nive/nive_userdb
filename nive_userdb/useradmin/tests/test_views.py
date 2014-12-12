# -*- coding: utf-8 -*-

import time
import unittest

from nive.definitions import FieldConf, Conf
from nive.portal import Portal
from nive.views import ExceptionalResponse

from nive_userdb.tests.db_app import *
from nive_userdb.tests import __local

from nive_userdb.useradmin import view
from nive_userdb.useradmin import adminroot

from pyramid.httpexceptions import HTTPFound
from pyramid import testing
from pyramid.renderers import render



class tViews(__local.DefaultTestCase):

    def setUp(self):
        request = testing.DummyRequest()
        request._LOCALE_ = "en"
        self.request = request
        self.request.method = "POST"
        self.config = testing.setUp(request=request)
        self.config.include('pyramid_chameleon')
        self._loadApp()
        self.portal = Portal()
        self.portal.Register(self.app, "nive")
        self.app.Register(adminroot.configuration)
        self.app.Startup(self.config)
        self.root = self.app.root("usermanagement")
        self.request.context = self.root
        self.request.content_type = ""
    

    def tearDown(self):
        self.app.Close()
        testing.tearDown()


    def test_views(self):
        v = view.UsermanagementView(context=self.root, request=self.request)
        v.__configuration__ = lambda: view.configuration
        self.assert_(v.GetAdminWidgets())
        self.assert_(v.add())
        self.assert_(v.edit())
        self.assert_(v.delete())
        v.view()

    def test_templates(self):
        user = User(u"test")
        v = view.UsermanagementView(context=self.root, request=self.request)
        v.__configuration__ = lambda: view.configuration
        vrender = {"context":self.root, "view":v, "request": self.request}
        
        values = v.add()
        values.update(vrender)
        render("nive_userdb.useradmin:add.pt", values)
        u=self.root.Create("user",{"name":"testuser", "password":"test", "email":"test@aaa.com", "groups":("group:admin",)},user=user)
        v.context = u
        values = v.edit()
        values.update(vrender)
        values["context"] = u
        render("nive_userdb.useradmin:edit.pt", values)
        v.context = self.root
        values = v.view()
        values.update(vrender)
        render("nive_userdb.useradmin:root.pt", values)
        values = v.delete()
        values.update(vrender)
        render("nive_userdb.useradmin:delete.pt", values)
        
        self.root.Delete(u.id, user=user)


    def test_add(self):
        user = self.root.GetUserByName("testuser")
        if user:
            self.root.DeleteUser("testuser")
        v = view.UsermanagementView(context=self.root, request=self.request)
        v.__configuration__ = lambda: view.configuration
        r = v.add()
        self.assert_(r["result"])
        if self.root.GetUserByName("testuser"):
            self.assert_(False, "User should not exist")
        self.request.POST = {"name":"testuser", "password":"", "email":"test@aaa.com", "groups":("group:admin",)}
        r = v.add()
        self.assert_(r["result"])
        if self.root.GetUserByName("testuser"):
            self.assert_(False, "User should not exist")
        
        self.request.POST["create$"] = "create"
        r = v.add()
        self.assertFalse(r["result"])
        if self.root.GetUserByName("testuser"):
            self.assert_(False, "User should not exist")
        self.request.POST["password"] = "password"
        self.request.POST["password-confirm"] = "password"
        
        self.assertRaises(HTTPFound, v.add)
        self.assert_(self.root.GetUserByName("testuser"))
        
        self.root.DeleteUser("testuser")


    def test_edit(self):
        user = self.root.GetUserByName("testuser")
        if user:
            self.root.DeleteUser("testuser")
        v = view.UsermanagementView(context=self.root, request=self.request)
        v.__configuration__ = lambda: view.configuration
        self.request.POST = {"name":"testuser", "email":"test@aaa.com", "groups":("group:admin",)}
        self.request.POST["password"] = "password"
        self.request.POST["password-confirm"] = "password"
        self.request.POST["create$"] = "create"
        self.assertRaises(HTTPFound, v.add)
        user = self.root.GetUserByName("testuser")
        if not user:
            self.assert_(False, "User should exist")
        
        v = view.UsermanagementView(context=user, request=self.request)
        v.__configuration__ = lambda: view.configuration
        self.request.POST = {}
        r = v.edit()
        self.assert_(r["result"])

        self.request.POST = {"name":"testuser", "email":"test", "groups":("group:admin",)}
        self.request.POST["edit$"] = "edit"
        r = v.edit()
        self.assertFalse(r["result"])
        user = self.root.GetUserByName("testuser")
        self.assert_(user.data.email != "test")
        
        self.request.POST = {"name":"testuser", "email":"test@bbb.com", "groups":("group:admin",)}
        self.request.POST["edit$"] = "edit"
        r = v.edit()
        self.assert_(r["result"])
        user = self.root.GetUserByName("testuser")
        self.assert_(user.data.email == "test@bbb.com")
        
        self.root.DeleteUser("testuser")


    def test_delete(self):
        v = view.UsermanagementView(context=self.root, request=self.request)
        v.__configuration__ = lambda: view.configuration
        user = self.root.GetUserByName("testuser")
        if not user:
            self.request.POST = {"name":"testuser", "email":"test@aaa.com", "groups":("group:admin",)}
            self.request.POST["password"] = "password"
            self.request.POST["password-confirm"] = "password"
            self.request.POST["create$"] = "create"
            self.assertRaises(HTTPFound, v.add)
        user = self.root.GetUserByName("testuser")
        if not user:
            self.assert_(False, "User should exist")
            
        r = v.delete()
        self.assert_(r["result"])
        self.assertFalse(r["confirm"])

        ids = (user.id,)
        self.request.POST = {"ids":ids}

        r = v.delete()
        self.assert_(r["result"])
        self.assertFalse(r["confirm"])
        self.assert_(len(r["users"])==1)

        self.request.POST = {"ids":ids, "confirm": 1}
        self.assertRaises(HTTPFound, v.delete)
        self.assertFalse(self.root.GetUserByName("testuser"))
        

