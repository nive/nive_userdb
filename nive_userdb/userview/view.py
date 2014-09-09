# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

from nive_userdb.i18n import _
from nive_userdb.i18n import translator
from nive.definitions import FieldConf, ViewConf, ViewModuleConf, Conf

# view module definition ------------------------------------------------------------------

#@nive_module
configuration = ViewModuleConf(
    id = "userview",
    name = _(u"User signup"),
    static = "nive_userdb.userview:static",
    containment = "nive_userdb.app.UserDB",
    context = "nive_userdb.root.root",
    view = "nive_userdb.userview.view.UserView",
    templates = "nive_userdb.userview:",
    permission = "view"
)
t = configuration.templates
configuration.views = [
    # User Views
    ViewConf(name="login",    attr="login",    renderer=t+"loginpage.pt"),
    ViewConf(name="signup",   attr="create",   renderer=t+"signup.pt", permission="signup"),
    ViewConf(name="update",   attr="update",   renderer=t+"update.pt", permission="updateuser"),
    ViewConf(name="resetpass",attr="resetpass",renderer=t+"resetpass.pt"),
    ViewConf(name="logout",   attr="logout"),
    # disabled
    #ViewConf(name="mailpass", attr="mailpass", renderer=t+"mailpass.pt"),
]



# view and form implementation ------------------------------------------------------------------

from nive.views import BaseView, Unauthorized, Mail
from nive.forms import ObjectForm


class UserForm(ObjectForm):
    """
    Extended User form 
    """

    def __init__(self, view=None, loadFromType=None, context=None, request=None, app=None, **kw):
        ObjectForm.__init__(self, view=view, loadFromType=loadFromType)
        
        self.actions = [
            Conf(id="default",    method="StartForm", name=_(u"Initialize"),    hidden=True),
            Conf(id="defaultEdit",method="LoadUser",  name=_(u"Initialize"),    hidden=True),
            Conf(id="create",     method="AddUser",   name=_(u"Signup"),        hidden=False, options={"renderSuccess":False}),
            Conf(id="edit",       method="Update",    name=_(u"Confirm"),       hidden=False),
            Conf(id="mailpass",   method="MailPass",  name=_(u"Mail password"), hidden=False),
            Conf(id="resetpass",  method="ResetPass", name=_(u"Reset password"), hidden=False),
            Conf(id="login",      method="Login",     name=_(u"Login"),         hidden=False),
        ]
    
        self.subsets = {
            "create": {"fields":  ["name", "password", "email", "surname", "lastname"], 
                       "actions": ["create"],
                       "defaultAction": "default"},
            "create2":{"fields":  ["name", "email"], 
                       "actions": ["create"],
                       "defaultAction": "default"},
            "edit":   {"fields":  ["email", 
                                   FieldConf(id="password", name=_("Password"), datatype="password", required=False, settings={"update": True}),
                                   "surname", "lastname"], 
                       "actions": ["defaultEdit", "edit"],
                       "defaultAction": "defaultEdit"},
            "login":  {"fields":  ["name", FieldConf(id="password", name=_("Password"), datatype="password", settings={"single": True})], 
                       "actions": ["login"],
                       "defaultAction": "default"},
            "mailpass":{"fields": ["email"], 
                        "actions": ["mailpass"],
                        "defaultAction": "default"},
            "resetpass":{"fields": ["email"], 
                        "actions": ["resetpass"],
                        "defaultAction": "default"},
        }

        self.activate = 1
        self.generatePW = 0
        self.notify = True
        self.mail = None
        self.mailpass = None
        self.groups = ""
        self.css_class = "smallform"


    def AddUser(self, action, **kw):
        """
        Form action: safely add a user 
        """
        msgs = []
        result,data,errors = self.Validate(self.request)
        if result:
            result, msgs = self.context.AddUser(data, 
                                                activate=self.activate, 
                                                generatePW=self.generatePW, 
                                                mail=self.mail, 
                                                groups=self.groups, 
                                                notify=self.notify, 
                                                currentUser=self.view.User())

        return self._FinishFormProcessing(result, data, msgs, errors, **kw)
        
        
    def LoadUser(self, action, **kw):
        """
        Initially load data from obj. 
        context = obj
        """
        user = self.view.User()
        if not user:
            raise Unauthorized, "User not found."
        data = self.LoadObjData(user)
        try:
            del data["password"]
        except:
            pass
        return data!=None, self.Render(data)


    def Update(self, action, **kw):
        """
        Form action: safely update a user 
        """
        user = self.view.User()
        if not user:
            raise Unauthorized, "User not found."
        msgs = []
        result,data,errors = self.Validate(self.request)
        if result:
            uobj = self.context.LookupUser(id=user.id)
            result = uobj.SecureUpdate(data, user)
            if result:
                msgs.append(_(u"OK"))

        return self._FinishFormProcessing(result, data, msgs, errors, **kw)
        
    
    def Login(self, action, **kw):
        """
        Form action: user login 
        """
        redirectSuccess = kw.get("redirectSuccess")
        data = self.GetFormValues(self.request)
        user, msgs = self.context.Login(data.get("name"), data.get("password"), 0)
        if user:
            self.context.app.RememberLogin(self.request, user.data.get("name"))
            if self.view and redirectSuccess:
                self.view.Redirect(redirectSuccess)
                return
        errors=None
        return user, self.Render(data, msgs=msgs, errors=errors)
        

    def MailPass(self, action, **kw):
        """
        """
        redirectSuccess = kw.get("redirectSuccess")
        return self.ResetPass(action, createNewPasswd=False, **kw)


    def ResetPass(self, action, createNewPasswd=True, **kw):
        """
        """
        #result, data, e = self.Validate(self.request)
        data = self.GetFormValues(self.request)
        result, msgs = self.context.MailUserPass(email=data.get("email"), mailtmpl=self.mailpass, createNewPasswd=createNewPasswd, currentUser=self.view.User())
        if result:
            data = {}
        return self._FinishFormProcessing(result, data, msgs, None, **kw)




class UserView(BaseView):
    
    def __init__(self, context, request):
        BaseView.__init__(self, context, request)
        self.form = UserForm(view=self, loadFromType="user")
        self.form.groups = ""
        self.publicSignup = False


    def create(self):
        self.form.activate=1
        self.form.generatePW=0
        self.form.Setup(subset="create")
        return self._render()

    def createNotActive(self):
        self.form.activate=0
        self.form.generatePW=0
        self.form.Setup(subset="create")
        return self._render()

    def createPassword(self):
        self.form.activate=1
        self.form.generatePW=1
        self.form.Setup(subset="create2")
        return self._render()

    def update(self):
        user=self.User()
        if user and user.id == 0:
            return {u"content": _(u"Your current user can only be edited on file system level."), u"result": False, u"head": self.form.HTMLHead()}
        self.form.Setup(subset="edit")
        try:
            result, data, action = self.form.Process()
            return {u"content": data, u"result": result, u"head": self.form.HTMLHead()}
        except Unauthorized:
            return {u"content": _(u"User not found"), u"result": False, u"head": self.form.HTMLHead()}
            
    def mailpass(self):
        self.form.startEmpty = True
        self.form.mail = Mail(_(u"Your password"), "nive_userdb:userview/mailpassmail.pt")
        self.form.Setup(subset="mailpass")
        return self._render()

    def resetpass(self):
        self.form.startEmpty = True
        self.form.mail = Mail(_(u"Your new password"), "nive_userdb:userview/resetpassmail.pt")
        self.form.Setup(subset="resetpass")
        return self._render()

    def login(self):
        self.form.Setup(subset="login")
        user = self.UserName()
        if not user:
            self.form.startEmpty = True
            #self.form.renderOneColumn = True
            redirect = self.GetFormValue(u"redirect")
            if not redirect:
                try:
                    redirect = self.context.app.portal.configuration.loginSuccessUrl
                except:
                    redirect = self.request.url
            result, data, action = self.form.Process(redirectSuccess=redirect)
            return {u"content": data, u"result": result, u"head": self.form.HTMLHead()}
        return {u"content": u"", u"result": True, u"head": self.form.HTMLHead()}
            
    def logoutlink(self):
        return {}

    def logout(self):
        self.ResetFlashMessages()
        app = self.context.app
        user = self.UserName()
        a = self.context.Logout(user)
        app.ForgetLogin(self.request)
        redirect = self.GetFormValue(u"redirect")
        if not redirect:
            try:
                redirect = self.context.app.portal.configuration.logoutSuccessUrl
            except:
                redirect = self.context.app.portal.configuration.portalDefaultUrl
        if redirect:
            localizer = translator(self.request)
            self.Redirect(redirect, messages=[localizer(_(u"You have been logged out!"))])
        return {}
    
    def logouturl(self):
        try:
            return self.context.app.portal.configuration.logoutUrl
        except:
            return self.request.url
    
    def insertMessages(self):
        messages = self.request.session.pop_flash("")
        if not messages:
            return u""
        html = u"""<ul class="boxOK"><li>%s</li></ul>"""
        try:
            return html % (u"</li><li>".join(messages))
        except:
            return u""

    def _render(self):
        result, data, action = self.form.Process()
        return {u"content": data, u"result": result, u"head": self.form.HTMLHead()}
    
