# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

from nive.definitions import FieldConf, ViewConf, ViewModuleConf, Conf

from nive.views import BaseView, Unauthorized, Mail
from nive.forms import ObjectForm

from nive_userdb.i18n import _
from nive_userdb.i18n import translator
from nive_userdb.app import EmailValidator, UsernameValidator, OldPwValidator


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
    permission = "view",
    # form settings: additional slot to configure the forms used in the views
    form = {}
)
t = configuration.templates
configuration.views = [
    # User Views
    ViewConf(name="login",          attr="login",      renderer=t+"loginpage.pt"),
    ViewConf(name="signup",         attr="create",     renderer=t+"signup.pt",    permission="signup"),
    ViewConf(name="activate",       attr="activate",   renderer=t+"form.pt"),
    ViewConf(name="update",         attr="update",     renderer=t+"update.pt",    permission="updateuser"),
    ViewConf(name="updatepass",     attr="updatepass", renderer=t+"form.pt",      permission="updateuser"),
    ViewConf(name="updatemail1",    attr="updatemail1",renderer=t+"form.pt",      permission="updateuser"),
    ViewConf(name="updatemail2",    attr="updatemail2",renderer=t+"form.pt",      permission="updateuser"),
    ViewConf(name="resetpass",      attr="resetpass",  renderer=t+"form.pt"),
    ViewConf(name="logout",         attr="logout"),
]



# view and form implementation ------------------------------------------------------------------


class UserForm(ObjectForm):
    """
    Extended User form 
    """

    def __init__(self, view=None, loadFromType=None, context=None, request=None, app=None, **kw):
        ObjectForm.__init__(self, view=view, loadFromType=loadFromType, context=context, request=request, app=app, **kw)
        
        self.actions = [
            Conf(id="default",    method="StartForm", name=_(u"Initialize"),    hidden=True),
            Conf(id="defaultEdit",method="LoadUser",  name=_(u"Initialize"),    hidden=True),
            Conf(id="create",     method="AddUser",   name=_(u"Signup"),        hidden=False),
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
                "actions": ["edit"],
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
            "loginMail":  {
                "fields":  [
                    FieldConf(id="name", name=_("Email"), datatype="string"),
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
                              settings={"single":True},
                              validator=OldPwValidator),
                    "password"
                ],
                "actions": [Conf(id="updatepass", method="UpdatePass", name=_(u"Update password"), hidden=False)],
                "defaultAction": "default"
            },

            "updatemail1": {
                "fields": [
                    FieldConf(id="newmail",
                           datatype="email",
                           size=255,
                           default=u"",
                           required=1,
                           name=_(u"New email"),
                           validator=EmailValidator)
                ],
                "actions": [Conf(id="updatemail", method="UpdateMail", name=_(u"Update email"), hidden=False)],
                "defaultAction": "default"
            },
            "updatemail2": {
                "fields": [FieldConf(id="token", datatype="string", size="500", name="Activation token", required=True, hidden=False)],
                "actions": [Conf(id="updatemail_token", method="UpdateMailToken", name=_(u"Verify email"), hidden=False)],
                "defaultAction": "updatemail_token"
            },

            "resetpass": {
                "fields": [FieldConf(id="name", name=_("Name"), datatype="string")],
                "actions": [Conf(id="resetpass", method="ResetPass", name=_(u"Reset password"),hidden=False)],
                "defaultAction": "default"
            },
            "resetpassMail": {
                "fields": [FieldConf(id="name", name=_("Email"), datatype="string")],
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
        user = self.view.User(sessionuser=False)
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
        errors = []
        result = False
        data = self.GetFormValue("token",method="ALL")
        if data:
            if data.find(u"token=")!=-1:
                data = data.split(u"token=")[-1]
            user = self.context.GetUserForToken(data, activeOnly=False)
            if user is not None:
                result = True
                user.Activate(currentUser=user)
                msgs = [_(u"OK.")]
            else:
                result = False
        if not result:
            msgs = [_(u"The token is invalid. Please make sure it is complete.")]
        data = {"token": data or u""}
        return self._FinishFormProcessing(result, data, msgs, errors, **kw)


    def UpdatePass(self, action, **kw):
        """
        Form action: update password if current password matches
        """
        user = self.view.User(sessionuser=False)
        if user is None:
            raise Unauthorized, "User not found."
        msgs = []
        result,data,errors = self.Validate(self.request)
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
        user = self.view.User(sessionuser=False)
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
        errors = []
        result = False
        data = self.GetFormValue("token",method="ALL")
        if data:
            if data.find(u"token=")!=-1:
                data = data.split(u"token=")[-1]
            user = self.context.GetUserForToken(data)
            if user:
                mail = user.data.tempcache
                if mail.startswith(u"verifymail:"):
                    mail = mail.replace(u"verifymail:",u"")
                    user.data["email"] = mail
                    user.data["tempcache"] = u""
                    user.data["token"] = u""
                    user.Commit(user=user)
                    msgs = [_(u"OK. The new email address has been activated.")]
            else:
                result = False
        if not result:
            msgs = [_(u"The token is invalid. Please make sure it is complete.")]
        data = {"token": data or u""}
        return self._FinishFormProcessing(result, data, msgs, errors, **kw)


    def ResetPass(self, action, **kw):
        """
        Form action: generate a new password and mail to the user
        """
        data = self.GetFormValues(self.request)
        result, msgs = self.context.MailUserPass(data.get("email"),
                                                 currentUser=self.view.User(),
                                                 **kw)
        if result:
            data = {}
        return self._FinishFormProcessing(result, data, msgs, None, **kw)




class UserView(BaseView):

    def _loadSimpleForm(self):
        # form rendering settings
        # form setup
        form = UserForm(view=self, context=self.context.root(), loadFromType="user")
        # sign up settings defined in user db configuration user in AddUser()
        form.settings = self.context.app.configuration.settings

        # customize form widget. values are applied to form.widget
        form.widget.item_template = "field_onecolumn"
        form.widget.action_template = "form_actions_onecolumn"
        #form.use_ajax = True
        form.action = self.request.url
        vm = self.viewModule
        if vm:
            formsettings = self.viewModule.get("form")
            if isinstance(formsettings, dict):
                form.ApplyOptions(formsettings)
        return form

    def _loadForm(self, subset, viewconf, defaultsubset, defaultaction=None):
        # form rendering settings
        # form setup
        typeconf=self.context.app.GetObjectConf("user")
        form = UserForm(view=self, loadFromType=typeconf)
        # sign up settings defined in user db configuration user in AddUser()
        form.settings = self.context.app.configuration.settings

        # load subset
        subset = subset or defaultsubset
        if isinstance(subset, basestring):
            # the subset is referenced as string -> look it up in typeconf.forms
            form.subsets = typeconf.forms
        else:
            form.subsets = {defaultsubset: subset}
            subset = defaultsubset

        if not subset in form.subsets:
            raise ConfigurationError("Unknown subset "+subset)

        # set up action
        if not "actions" in form.subsets[subset] and defaultaction:
            form.subsets[subset].update(defaultaction)

        # customize form widget. values are applied to form.widget
        form.widget.item_template = "field_onecolumn"
        form.widget.action_template = "form_actions_onecolumn"
        #form.use_ajax = True
        form.action = self.request.url
        vm = self.viewModule
        if vm:
            formsettings = self.viewModule.get("form")
            if isinstance(formsettings, dict):
                form.ApplyOptions(formsettings)
        return form, subset

    def create(self):
        """
        Renders and executes a web form based on the items configuration values.
        Form form setup requires the `subset` or list of fields to be used. If
        nothing is given it defaults to `create`. `subset` is the form identifier
        used in the items configuration as `form`.

        Form configuration lookup order :

        1) Customized `create` view ::

            create = ViewConf(
                name="create",
                attr="create",
                ...
                settings={"form": {"fields": ("email", "name", "password")}}
            )

        2) The types' ObjectConf.forms settings for `newItem`  ::

            user = ObjectConf(
                id = "user",
                ...
                forms = {
                    "create": {"fields": ("email", "name", "password")},
                    "edit":   {"fields": ("surname", "lastname")}
                },
                ...
            )

        defines the `newItem` form in both cases with 3 form fields and to use ajax submissions ::

            {"fields": ("email", "name", "password"), "use_ajax": True}

        """
        subset = None
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            subset = viewconf.settings.get("form")
        form, subset = self._loadForm(subset, viewconf=viewconf, defaultsubset="create", defaultaction=UserForm.subsets["create"])
        form.Setup(subset=subset)
        return self._render(form=form, url=self.Url()+"activate", renderSuccess=False)

    def update(self):
        """
        Renders and executes a web form based on the items configuration values.
        Form form setup requires the `subset` or list of fields to be used. If
        nothing is given it defaults to `create`. `subset` is the form identifier
        used in the items configuration as `form`.

        Form configuration lookup order :

        1) Customized `create` view ::

            update = ViewConf(
                name="update",
                attr="update",
                ...
                settings={"form": {"fields": ("surname", "lastname")}}
            )

        2) The types' ObjectConf.forms settings for `newItem`  ::

            user = ObjectConf(
                id = "user",
                ...
                forms = {
                    "create": {"fields": ("email", "name", "password")},
                    "edit":   {"fields": ("surname", "lastname")}
                },
                ...
            )

        defines the `newItem` form in both cases with 2 form fields and to use ajax submissions ::

            {"fields": ("surname", "lastname"), "use_ajax": True}

        """
        user=self.User(sessionuser=False)
        subset = None
        title = u""
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            subset = viewconf.settings.get("form")
            title = viewconf.settings.get("title",u"")
        form, subset = self._loadForm(subset, viewconf=viewconf, defaultsubset="edit", defaultaction=UserForm.subsets["edit"])
        if user and user.id == 0:
            return {u"content": _(u"Your current user can only be edited on file system level."), u"result": False, u"head": form.HTMLHead()}
        form.Setup(subset=subset)
        try:
            result, data, action = form.Process()
            return {u"content": data, u"result": result, u"head": form.HTMLHead(), u"title": title}
        except Unauthorized:
            return {u"content": _(u"User not found"), u"result": False, u"head": form.HTMLHead(), u"title": title}
            
    def activate(self):
        form = self._loadSimpleForm()
        form.startEmpty = True
        form.Setup(subset="activate")
        return self._render(form=form, renderSuccess=False)

    def resetpass(self):
        form = self._loadSimpleForm()
        form.startEmpty = True
        if self.context.app.configuration.loginByEmail:
            subset = "resetpassMail"
        else:
            subset = "resetpass"
        form.Setup(subset=subset)
        return self._render(form=form, renderSuccess=False)

    def updatepass(self):
        form = self._loadSimpleForm()
        form.startEmpty = True
        form.Setup(subset="updatepass")
        return self._render(form=form, renderSuccess=False)

    def updatemail1(self):
        form = self._loadSimpleForm()
        form.startEmpty = True
        form.Setup(subset="updatemail1")
        return self._render(form=form, url=self.Url()+"updatemail2",renderSuccess=False)

    def updatemail2(self):
        form = self._loadSimpleForm()
        form.startEmpty = True
        form.Setup(subset="updatemail2")
        return self._render(form=form, renderSuccess=False)

    def login(self):
        if self.context.app.configuration.loginByEmail:
            subset = "loginMail"
        else:
            subset = "login"
        showPasswordLink = False
        form = self._loadSimpleForm()
        form.Setup(subset=subset)
        form.widget.item_template = "field_onecolumn"
        user = self.User()
        if not user:
            form.startEmpty = True
            redirect = self.GetFormValue(u"redirect")
            if not redirect:
                try:
                    redirect = self.context.app.portal.configuration.loginSuccessUrl
                except:
                    redirect = self.request.url
            result, data, action = form.Process(redirectSuccess=redirect)
            return {u"content": data, u"result": result, u"head": form.HTMLHead(), "showPasswordLink":showPasswordLink}
        return {u"content": u"", u"result": True, u"head": form.HTMLHead(), "showPasswordLink":showPasswordLink}
            
    def logoutlink(self):
        return {}

    def logout(self):
        self.ResetFlashMessages()
        app = self.context.app
        user = self.UserName()
        a = self.context.root().Logout(user)
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
        html = u"""<div class="alert alert-success">%s</div>"""
        return html % (u"</li><li>".join(messages))

    def _render(self,form,**kw):
        result, data, action = form.Process(**kw)
        return {u"content": data, u"result": result, u"head": form.HTMLHead()}
    
