# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

from nive.definitions import FieldConf, ViewConf, ViewModuleConf, Conf

from nive.views import BaseView, Unauthorized, Mail
from nive.forms import ObjectForm

from nive_userdb.i18n import _
from nive_userdb.i18n import translator
from nive_userdb.app import EmailValidator, UsernameValidator


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
    template = "main.pt",
    permission = "view"
)
t = configuration.templates
configuration.views = [
    # User Views
    ViewConf(name="login",          attr="login",     renderer=t+"loginpage.pt"),
    ViewConf(name="signup",         attr="create",    renderer=t+"signup.pt",    permission="signup"),
    ViewConf(name="activate",       attr="activate",  renderer=t+"form.pt"),
    ViewConf(name="update",         attr="update",    renderer=t+"update.pt",    permission="updateuser"),
    ViewConf(name="updatepass",     attr="updatepass",renderer=t+"form.pt",      permission="updateuser"),
    ViewConf(name="updatemail1",    attr="updatemail1",renderer=t+"form.pt",     permission="updateuser"),
    ViewConf(name="updatemail2",    attr="updatemail2",renderer=t+"form.pt",     permission="updateuser"),
    ViewConf(name="resetpass",      attr="resetpass",  renderer=t+"form.pt"),
    ViewConf(name="logout",         attr="logout"),
]



# view and form implementation ------------------------------------------------------------------

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
            Conf(id="login",      method="Login",     name=_(u"Login"),         hidden=False),
        ]

        self.subsets = {
            "create": {
                # loads fields from user configuration
                "actions": ["create"],
                "defaultAction": "default"
            },
            "edit":   {
                # loads fields from user configuration
                "actions": ["defaultEdit", "edit"],
                "defaultAction": "defaultEdit"
            },

            "login":  {
                "fields":  [
                    FieldConf(id="name", name=_("Name"), datatype="string"),
                    FieldConf(id="password", name=_("Password"), datatype="password", settings={"single": True})
                ],
                "actions": ["login"],
                "defaultAction": "default"
            },

            "activate": {
                "fields": [FieldConf(id="token", datatype="string", size="500", name="Activation token", required=True, hidden=False)],
                "actions": [Conf(id="activate", method="Activate", name=_(u"Activate"), hidden=False)],
                "defaultAction": "activate"
            },
            "updatepass":{
                "fields": [
                    FieldConf(id="oldpassword",
                              datatype="password",
                              size=100,
                              default=u"",
                              required=1,
                              name=_(u"Old password"),
                              settings={"single":True}),
                    "password"
                ],
                "actions": [Conf(id="updatepass", method="UpdatePass", name=_(u"Reset password"), hidden=False)],
                "defaultAction": "default"
            },

            "updatemail1": {
                "fields": [FieldConf(id="newmail",
                           datatype="email",
                           size=255,
                           default=u"",
                           required=1,
                           name=_(u"New email"),
                           settings={"validator":EmailValidator})
                ],
                "actions": [Conf(id="updatemail", method="UpdateMail", name=_(u"Update email"), hidden=False)],
                "defaultAction": "default"
            },
            "updatemail2": {
                "fields": [FieldConf(id="token", datatype="string", size="500", name="reset token", required=True, hidden=True)],
                "actions": [Conf(id="updatemail_token", method="UpdateMailToken", name=_(u"Verify email"), hidden=False)],
                "defaultAction": "default"
            },

            "resetpass": {
                "fields": ["name"],
                "actions": [Conf(id="resetpass", method="ResetPass", name=_(u"Reset password"),hidden=False)],
                "defaultAction": "default"
            },
        }

        self.css_class = "smallform"
        self.settings = {}


    def AddUser(self, action, **kw):
        """
        Form action: safely add a user 
        """
        msgs = []
        result,data,errors = self.Validate(self.request)
        if result:
            opts = {}
            opts.update(kw)
            opts.update(self.settings)
            result, msgs = self.context.AddUser(data, 
                                                currentUser=self.view.User(),
                                                **opts)
            if result and self.context.app.configuration.get("welcomeMessage"):
                msgs = [self.context.app.configuration.get("welcomeMessage")]

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
        user = self.view.User(sessionuser=False)
        if not user:
            raise Unauthorized, "User not found."
        msgs = []
        result,data,errors = self.Validate(self.request)
        if result:
            result = user.SecureUpdate(data, user)
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
            self.context.app.RememberLogin(self.request, str(user))
            if self.view and redirectSuccess:
                self.view.Redirect(redirectSuccess)
                return
        errors=None
        return user, self.Render(data, msgs=msgs, errors=errors)
        

    def Activate(self, action, **kw):
        """
        Form action: activate the mail in tempcache if token matches
        """
        msgs = []
        self.method = "GET"
        result,data,errors = self.Validate(self.request)
        if result:
            token = data.get("token")
            user = self.context.GetUserForToken(token, active=False)
            if user:
                result = True
                user.Activate(currentUser=user)
                msgs = [_(u"OK. Your account has been activated.")]
            else:
                result = False
                msgs = [_(u"The token is invalid. Please make sure it is complete.")]
        return self._FinishFormProcessing(result, data, msgs, errors, **kw)


    def UpdatePass(self, action, **kw):
        """
        Form action: update password if current password matches
        """
        user = self.view.User(sessionuser=False)
        if user is None:
            raise Unauthorized, "User not found."
        msgs = []
        redirectSuccess = kw.get("redirectSuccess")
        result,data,errors = self.Validate(self.request)
        # check old password
        if data["oldpassword"] and not user.Authenticate(data["oldpassword"]):
            msgs = [_(u"The old password does not match.")]
            result = False
        if not result:
            return result, self.Render(data, msgs=msgs, errors=errors)

        result = user.UpdatePassword(data["password"], user)
        if result:
            msgs.append(_(u"OK. Password changed."))
            return result, self.Render(data, msgs=msgs, errors=None, messagesOnly=True)
        return result, self.Render(data)


    def UpdateMail(self, action, **kw):
        """
        Form action: trigger a mail to verify another mail address
        """
        user = self.view.User()
        if not user:
            raise Unauthorized, "User not found."
        msgs = []
        result,data,errors = self.Validate(self.request)
        if result:
            newmail = data["newmail"]
            result, msgs = self.context.MailVerifyNewEmail(user, newmail, currentUser=user, **kw)
        return self._FinishFormProcessing(result, data, msgs, errors, **kw)


    def UpdateMailToken(self, action, **kw):
        """
        Form action: activate the mail in tempcache if token matches
        """
        msgs = []
        self.method = "GET"
        result,data,errors = self.Validate(self.request)
        if result:
            token = data.get("token")
            user = self.context.GetUserForToken(token)
            if user:
                mail = user.data.tempcache
                user.data["email"] = mail
                user.data["tempcache"] = u""
                user.data["token"] = u""
                user.Commit(user=user)
                msgs = [_(u"OK. The new email address has been activated.")]
            else:
                result = False
                msgs = [_(u"The token is empty. Please copy the whole url.")]
        return self._FinishFormProcessing(result, data, msgs, errors, **kw)


    def ResetPass(self, action, **kw):
        """
        Form action: generate a new password and mail to the user
        """
        data = self.GetFormValues(self.request)
        result, msgs = self.context.MailUserPass(email=data.get("email"),
                                                 currentUser=self.view.User())
        if result:
            data = {}
        return self._FinishFormProcessing(result, data, msgs, None, **kw)




class UserView(BaseView):
    
    def __init__(self, context, request):
        super(UserView, self).__init__(context, request)
        # the viewModule is used for template/template directory lookup
        #self.viewModuleID = "userview"
        # form setup
        self.form = UserForm(view=self, loadFromType="user")
        self.form.settings = self.context.app.configuration.settings

        #            report.append(_(u"The token is empty. Please copy the whole url."))



    def create(self):
        self.form.Setup(subset="create")
        return self._render(url=self.Url()+"activate")

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
            
    def activate(self):
        self.form.startEmpty = True
        self.form.Setup(subset="activate")
        return self._render(renderSuccess=False)

    def resetpass(self):
        self.form.startEmpty = True
        self.form.Setup(subset="resetpass")
        return self._render()

    def updatepass(self):
        self.form.startEmpty = True
        self.form.Setup(subset="updatepass")
        return self._render()

    def updatemail1(self):
        self.form.startEmpty = True
        self.form.Setup(subset="updatemail1")
        return self._render(url=self.Url()+"updatemail2")

    def updatemail2(self):
        self.form.startEmpty = True
        self.form.Setup(subset="updatemail2")
        return self._render(renderSuccess=False)

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
        html = u"""<ul class="alert alert-success"><li>%s</li></ul>"""
        try:
            return html % (u"</li><li>".join(messages))
        except:
            return u""

    def _render(self,**kw):
        result, data, action = self.form.Process(**kw)
        return {u"content": data, u"result": result, u"head": self.form.HTMLHead()}
    
