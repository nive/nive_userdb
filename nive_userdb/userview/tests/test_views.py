# -*- coding: utf-8 -*-

import time
import unittest

from nive.definitions import Conf, ConfigurationError
from nive_userdb.userview.view import UserForm, UserView
from nive.views import BaseView
from nive.security import User

from nive_userdb.tests import __local

from pyramid.httpexceptions import HTTPFound
from pyramid import testing 
from pyramid.renderers import render


class TestView(BaseView):
    
    def User(self, sessionuser=None):
        return self.context.root().GetUserByName("testuser")
    

class tViews(__local.DefaultTestCase):

    def setUp(self):
        request = testing.DummyRequest()
        request._LOCALE_ = "en"
        self.request = request
        self.config = testing.setUp(request=request)
        self.config.include('pyramid_chameleon')
        self._loadApp()
        self.app.Startup(self.config)
        self.root = self.app.root()
        user = User(u"test")
        user.groups.append("group:admin")
        self.root.DeleteUser("testuser")
        self.root.DeleteUser("testuser123")
        self.request.context = self.root
        self.request.content_type = ""

    def tearDown(self):
        self.app.Close()
        testing.tearDown()


    
    def test_views(self):
        view = UserView(context=self.root, request=self.request)
        view.create()
        view.update()
        view.mailpass()
        view.resetpass()
        view.login()
        view.logoutlink()
        self.assertRaises(HTTPFound, view.logout)
        view.logouturl()
        
        
    def test_templates(self):    
        view = UserView(context=self.root, request=self.request)
        view.__configuration__ = lambda: Conf(template="nive_userdb.userview:main.pt",templates="",assets=[])
        vrender = {"context":self.root, "view":view, "request": self.request}
        
        values = view.login()
        values.update(vrender)
        render("nive_userdb.userview:loginpage.pt", values)
        
        values = view.mailpass()
        values.update(vrender)
        render("nive_userdb.userview:mailpass.pt", values)
        values = view.resetpass()
        values.update(vrender)
        render("nive_userdb.userview:resetpass.pt", values)
        
        values = view.create()
        values.update(vrender)
        render("nive_userdb.userview:signup.pt", values)

        values = view.update()
        values.update(vrender)
        render("nive_userdb.userview:update.pt", values)
        render("nive_userdb.userview:main.pt", values)
    
    
    def test_mails(self):
        user = User(u"test")
        user.data["token"] = "123"
        values = {"user": user, "url":"uuu", "password": "12345"}
        render("nive_userdb.userview:mails/notify.pt", values)
        render("nive_userdb.userview:mails/signup.pt", values)
        render("nive_userdb.userview:mails/verifymail.pt", values)
        render("nive_userdb.userview:mails/mailpass.pt", values)
        render("nive_userdb.userview:mails/resetpass.pt", values)
    
    
    def test_form(self):
        view = TestView(context=self.root, request=self.request)
        form = UserForm(loadFromType="user", context=self.root, request=self.request, view=view, app=self.app)
        form.settings["mail"] = None
        form.Setup(subset="create")
        self.request.GET = {}
        self.request.POST = {"name": "testuser", "email": "testuser@domain.net"}

        r,v = form.AddUser("action", redirectSuccess="")
        self.assertFalse(r)

        self.request.POST = {"name": "", "email": "testuser@domain.net", "password": "12345", "password-confirm": "12345"}
        r,v = form.AddUser("action", redirectSuccess="")
        self.assertFalse(r)

        self.request.POST = {"name": "testuser", "email": "testuser@domain.net", "password": "12345", "password-confirm": "12345"}
        r,v = form.AddUser("action", redirectSuccess="")
        self.assert_(r)

        form = UserForm(loadFromType="user", context=self.root, request=self.request, view=view, app=self.app)
        form.Setup(subset="edit")
        self.request.POST = {"surname": "12345", "password": "12345", "password-confirm": "12345"}
        self.request.GET = {}

        r,v = form.LoadUser("action", redirectSuccess="")
        self.assert_(r)
        r,v = form.Update("action", redirectSuccess="")
        self.assert_(r,v)
        self.request.POST = {"name": "testuser123", "email": "testuser@domain.net", "surname": "12345", "password": "12345"}
        r,v = form.Update("action", redirectSuccess="")
        self.assertFalse(r)

        view = BaseView(context=self.root, request=self.request)
        form = UserForm(loadFromType="user", context=self.root, request=self.request, view=view, app=self.app)
        form.Setup(subset="login")
        self.request.POST = {"name": "testuser", "password": "12345"}
        self.request.GET = {}

        r,v = form.Login("action", redirectSuccess="")
        self.assert_(r)

        form = UserForm(loadFromType="user", context=self.root, request=self.request, view=view, app=self.app)
        form.Setup(subset="mailpass")
        self.request.POST = {"email": "testuser@domain.net"}
        self.request.GET = {}

        try:
            form.MailPass("action", redirectSuccess="")
        except ConfigurationError:
            pass


