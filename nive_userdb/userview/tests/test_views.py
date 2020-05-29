# -*- coding: utf-8 -*-

import unittest

from nive_userdb.userview.view import UserForm, UserView
from nive_userdb.userview.view import configuration as view_configuration
from nive.views import BaseView
from nive.security import User

from nive_userdb.tests import __local
from nive_userdb.tests import db_app

from pyramid.httpexceptions import HTTPFound
from pyramid import testing
from pyramid.renderers import render


class TestView(UserView):
    
    def User(self, sessionuser=None):
        return self.context.GetUserByName("testuser")
    

class tViews(__local.DefaultTestCase):

    def setUp(self):
        request = testing.DummyRequest()
        request._LOCALE_ = "en"
        self.request = request
        self.request.content_type = ""
        self.request.method = "POST"
        self.config = testing.setUp(request=request)
        self.config.include('pyramid_chameleon')
        self._loadApp()
        self.app.Startup(self.config)
        self.root = self.app.root
        user = User("test")
        user.groups.append("group:admin")
        self.request.context = self.root
        self.request.content_type = ""
        self.app.Query("delete from pool_meta")
        self.app.Query("delete from users")

    def tearDown(self):
        db_app.emptypool(self.app)
        self.app.Close()
        testing.tearDown()


    
    def test_views(self):
        view = UserView(context=self.app, request=self.request)
        view.__configuration__ = lambda: view_configuration
        view.create()
        view.update()
        view.updatepass()
        view.resetpass()
        view.updatemail1()
        view.updatemail2()
        view.contact()
        view.login()
        view.logoutlink()
        self.assertRaises(HTTPFound, view.logout)
        view.logouturl()
        view.closefirstrun()
        view.remove()


    def test_templates(self):    
        view = UserView(context=self.app, request=self.request)
        view.__configuration__ = lambda: view_configuration
        vrender = {"context":self.app, "view":view, "request": self.request}
        
        values = view.login()
        values.update(vrender)
        render("nive_userdb.userview:loginpage.pt", values)
        
        values = view.updatepass()
        values.update(vrender)
        render("nive_userdb.userview:form.pt", values)

        values = view.updatemail1()
        values.update(vrender)
        render("nive_userdb.userview:form.pt", values)

        values = view.updatemail2()
        values.update(vrender)
        render("nive_userdb.userview:form.pt", values)

        values = view.resetpass()
        values.update(vrender)
        render("nive_userdb.userview:form.pt", values)
        
        values = view.create()
        values.update(vrender)
        render("nive_userdb.userview:signup.pt", values)

        values = view.update()
        values.update(vrender)
        render("nive_userdb.userview:update.pt", values)

        values = view.contact()
        values.update(vrender)
        render("nive_userdb.userview:form.pt", values)

        values = view.remove()
        values.update(vrender)
        render("nive_userdb.userview:remove.pt", values)

        render("nive_userdb.userview:main.pt", values)
    
    
    def test_mails(self):
        user = User("test")
        user.data["token"] = "123"
        values = {"user": user, "url":"uu", "password": "12345"}
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
        self.assertTrue(r, r)

        form = UserForm(loadFromType="user", context=view.User(), request=self.request, view=view, app=self.app)
        form.Setup(subset="edit")
        self.request.POST = {"surname": "12345", "email": "testuser@domain.net", "password": "12345", "password-confirm": "12345"}
        self.request.GET = {}

        r,v = form.LoadUser("action", redirectSuccess="")
        self.assertTrue(r)
        r,v = form.Update("action", redirectSuccess="")
        self.assertTrue(r,v)
        self.request.POST = {"name": "testuser123", "email": "testuser@domain.net", "surname": "12345", "password": "12345"}
        r,v = form.Update("action", redirectSuccess="")
        self.assertFalse(r)

        view = BaseView(context=self.root, request=self.request)
        form = UserForm(loadFromType="user", context=self.root, request=self.request, view=view, app=self.app)
        form.Setup(subset="login")
        self.request.POST = {"name": "testuser", "password": "12345"}
        self.request.GET = {}
        r,v = form.Login("action", redirectSuccess="")
        self.assertTrue(r)

        # activate -----------------------------------------------------------------------------------------------------
        u = self.root.LookupUser(name="testuser", reloadFromDB=1)
        u.meta["pool_state"] = 0
        u.data["token"] = "1111111111"
        u.Commit(user=u)

        view = BaseView(context=self.root, request=self.request)
        form = UserForm(loadFromType="user", context=self.root, request=self.request, view=view, app=self.app)
        form.Setup(subset="activate")
        form.method = "GET"
        self.request.POST = {}
        self.request.GET = {"token": "aaaa"}
        r,v = form.Activate("action", redirectSuccess="")
        self.assertFalse(r)

        self.request.GET = {"token": "1111111111"}
        r,v = form.Activate("action", redirectSuccess="")
        self.assertTrue(r)
        u = self.root.LookupUser(name="testuser", reloadFromDB=1)
        self.assertTrue(u.meta["pool_state"])
        self.assertFalse(u.data["token"])


    def test_form2(self):
        view = TestView(context=self.root, request=self.request)
        form = UserForm(loadFromType="user", context=self.root, request=self.request, view=view, app=self.app)
        form.settings["mail"] = None
        form.Setup(subset="create")
        self.request.GET = {}
        self.request.POST = {"name": "testuser", "email": "testuser@domain.net", "password": "12345", "password-confirm": "12345"}
        r,v = form.AddUser("action", redirectSuccess="")
        self.assertTrue(r, r)

        # UpdatePass -----------------------------------------------------------------------------------------------------

        view = TestView(context=self.root, request=self.request)
        form = UserForm(loadFromType="user", context=view.User(), request=self.request, view=view, app=self.app)
        form.Setup(subset="updatepass")
        self.request.POST = {"oldpassword": "12345", "password": "34567", "password-confirm": "67890"}
        self.request.GET = {}
        r, v = form.UpdatePass("action", redirectSuccess="")
        self.assertFalse(r)

        form = UserForm(loadFromType="user", context=view.User(), request=self.request, view=view, app=self.app)
        form.Setup(subset="updatepass")
        self.request.POST = {"oldpassword": "12345", "password": "67890", "password-confirm": "67890"}
        self.request.GET = {}
        r, v = form.UpdatePass("action", redirectSuccess="")
        self.assertTrue(r)

        form = UserForm(loadFromType="user", context=view.User(), request=self.request, view=view, app=self.app)
        form.Setup(subset="updatepass")
        self.request.POST = {"oldpassword": "67890", "password": "12345", "password-confirm": "12345"}
        self.request.GET = {}
        r, v = form.UpdatePass("action", redirectSuccess="")
        self.assertTrue(r)


        # UpdateMail -----------------------------------------------------------------------------------------------------

        form = UserForm(loadFromType="user", context=view.User(), request=self.request, view=view, app=self.app)
        form.Setup(subset="updatemail1")
        self.request.POST = {"newmail": "testuser"}
        self.request.GET = {}
        r, v = form.UpdateMail("action", redirectSuccess="")
        self.assertFalse(r)

        form = UserForm(loadFromType="user", context=view.User(), request=self.request, view=view, app=self.app)
        form.Setup(subset="updatemail1")
        self.request.POST = {"newmail": "testuser@domain.net"}
        self.request.GET = {}
        r, v = form.UpdateMail("action", redirectSuccess="", url="")
        self.assertTrue(r, v)

        form = UserForm(loadFromType="user", context=view.User(), request=self.request, view=view, app=self.app)
        form.Setup(subset="updatemail1")
        self.request.POST = {"newmail": "newuser@domain.net"}
        self.request.GET = {}
        form.UpdateMail("action", redirectSuccess="", url="")
        m = self.root.LookupUser(name="testuser", reloadFromDB=1).data.tempcache
        self.assertTrue(m=="verifymail:newuser@domain.net", m)


        # UpdateMailToken -----------------------------------------------------------------------------------------------------

        form = UserForm(loadFromType="user", context=self.root, request=self.request, view=view, app=self.app)
        form.Setup(subset="updatemail2")
        self.request.GET = {"token": "000"}
        r, v = form.UpdateMailToken("action", redirectSuccess="")
        self.assertFalse(r)

        form = UserForm(loadFromType="user", context=self.root, request=self.request, view=view, app=self.app)
        form.Setup(subset="updatemail2")
        self.request.GET = {"token": self.root.LookupUser(name="testuser", reloadFromDB=1).data.token}
        form.UpdateMailToken("action", redirectSuccess="")
        self.assertTrue(self.root.GetUser("testuser").data.email=="newuser@domain.net")

        form = UserForm(loadFromType="user", context=self.root, request=self.request, view=view, app=self.app)
        form.Setup(subset="updatemail2")
        self.request.POST = {"token": self.root.LookupUser(name="testuser", reloadFromDB=1).data.token}
        self.request.GET = {}
        r, v = form.UpdateMailToken("action", redirectSuccess="")
        self.assertFalse(r)


        # ResetPass -----------------------------------------------------------------------------------------------------

        view = BaseView(context=self.root, request=self.request)
        form = UserForm(loadFromType="user", context=self.root, request=self.request, view=view, app=self.app)
        form.Setup(subset="resetpass")
        self.request.POST = {"email": "testuser@domain.net"}
        self.request.GET = {}
        form.ResetPass("action", redirectSuccess="")

        # Contact -----------------------------------------------------------------------------------------------------

        view = BaseView(context=self.root, request=self.request)
        form = UserForm(loadFromType="user", context=self.root, request=self.request, view=view, app=self.app)
        form.Setup(subset="contact")
        self.request.POST = {"receiver": str(self.root.LookupUser(name="testuser", reloadFromDB=1))}
        self.request.GET = {}
        form.Contact("action", redirectSuccess="")


    def test_form3(self):
        view = TestView(context=self.root, request=self.request)
        form = UserForm(loadFromType="user", context=self.root, request=self.request, view=view, app=self.app)
        form.settings["mail"] = None
        form.Setup(subset="create")
        self.request.GET = {}
        self.request.POST = {"name": "testuser", "email": "testuser@domain.net", "password": "12345", "password-confirm": "12345"}
        r,v = form.AddUser("action", redirectSuccess="")
        self.assertTrue(r, r)

        # resetpass
        form = UserForm(loadFromType="user", context=self.root, request=self.request, view=view, app=self.app)
        form.Setup(subset="resetpass_mail")
        form.mail = None
        self.request.POST = {"email": "testuser@domain.net"}
        self.request.GET = {}

        u = self.root.GetUserByName("testuser")
        u.data["token"] = ""
        u.Commit(user=view.User())

        r, v = form.MailPassToken("action", redirectSuccess="", url="")
        self.assertTrue(r, v)
        u = self.root.GetUserByName("testuser")
        self.assertTrue(u.data.token)

        self.request.POST = {"email": "not a email@ net"}
        r, v = form.MailPassToken("action", redirectSuccess="")
        self.assertFalse(r, v)

        # editpass token
        form = UserForm(loadFromType="user", context=self.root, request=self.request, view=view, app=self.app)
        form.Setup(subset="editpass_token")
        self.request.GET = {}

        testuser = self.root.GetUserByName("testuser")
        testuser.data["token"] = ""
        testuser.Commit(user=view.User())
        self.request.POST = {"password": "55555", "password-confirm": "33333", "token": "invalid"}
        r, v = form.UpdatePassToken("action", redirectSuccess="")
        self.assertFalse(r)

        testuser.data["token"] = "12345"
        testuser.Commit(user=view.User())
        self.request.POST = {"password": "abcde", "password-confirm": "abcde", "token": "12345"}
        r, v = form.UpdatePassToken("action", redirectSuccess="")
        self.assertTrue(r, v)

        u = self.root.GetUserByName("testuser")
        self.assertFalse(u.data.token)
