# Copyright 2012 - 2014 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

import copy

from nive.definitions import FieldConf, ViewConf, ViewModuleConf, Conf
from nive.definitions import ConfigurationError
from nive.definitions import IUser
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
    assets = (),
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
    ViewConf(name="updatemail2",    attr="updatemail2",renderer=t+"form.pt"),
    ViewConf(name="resetpass",      attr="resetpass",  renderer=t+"form.pt"),
    ViewConf(name="logout",         attr="logout"),
    ViewConf(name="contact",        attr="contact",    renderer=t+"form.pt",      permission="contactuser"),
    ViewConf(name="closefirstrun",  attr="closefirstrun",renderer="json",         permission="updateuser"),
    ViewConf(name="remove",         attr="remove",     renderer=t+"remove.pt",    permission="removeuser"),
]



# view and form implementation ------------------------------------------------------------------



class UserView(BaseView):
    """
    Views in this class can be used to build user profile handling.
    """


    def create(self):
        """
        Renders and executes a web form based on the items configuration values.
        Form form setup requires the `subset` or list of fields to be used. If
        nothing is given it defaults to `create`. `subset` is the form identifier
        used in the items configuration as `form`.

        **Settings**

        - *form*: (dict) form definition inlcuding fields and form settings used for the form.
        - *values*: (dict) default values stored for the new user not include in the form.
        - *title*: (string) title displayed above the form

        **Request parameter**

        - *assets*: You can call `create?assets=only` to get the required css+js assets only. The form
                    iteself will not be processed.

        **Return values**

        - *body*: This function returns rendered html code as body.
        - *X-Result header*: http header indicating whether the new item has been created or not.

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
        subset = values = None
        viewconf = self.GetViewConf()
        title = u""
        if viewconf and viewconf.get("settings"):
            subset = viewconf.settings.get("form")
            title = viewconf.settings.get("title")
            values = viewconf.settings.get("values")

        form, subset = self._loadForm(subset, viewconf=viewconf, defaultsubset="create")
        form.Setup(subset=subset)

        if self.GetFormValue("assets")=="only":
            self.AddHeader("X-Result", "true")
            return {"content": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets])}

        result, data, action = form.Process(url=self.Url()+"activate", values=values, renderSuccess=False)
        self.AddHeader("X-Result", str(result).lower())
        return {u"content": data,
                u"result": result,
                u"head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]),
                u"title": title}

    def update(self):
        """
        Renders and executes a web form based on the items configuration values.
        Form form setup requires the `subset` or list of fields to be used. If
        nothing is given it defaults to `create`. `subset` is the form identifier
        used in the items configuration as `form`.

        **Settings**

        - *form*: (dict) form definition inlcuding fields and form settings used for the form.
        - *values*: (dict) default values stored for the new user not include in the form.
        - *title*: (string) title displayed above the form

        **Request parameter**

        - *assets*: You can call `create?assets=only` to get the required css+js assets only. The form
                    iteself will not be processed.

        **Return values**

        - *body*: This function returns rendered html code as body.
        - *X-Result header*: http header indicating whether the new item has been created or not.

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
        subset = values = None
        title = u""
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            subset = viewconf.settings.get("form")
            title = viewconf.settings.get("title",u"")
            values = viewconf.settings.get("values")
        form, subset = self._loadForm(subset, viewconf=viewconf, defaultsubset="edit")

        if self.GetFormValue("assets")=="only":
            self.AddHeader("X-Result", "true")
            return {"content": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets])}

        if user and user.id == 0:
            self.AddHeader("X-Result", "false")
            return {u"content": _(u"Your current user can only be edited on file system level."),
                    u"result": False, u"head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]), u"title": title}
        form.Setup(subset=subset)
        try:
            result, data, action = form.Process(values=values)
            self.AddHeader("X-Result", str(result).lower())
            return {u"content": data,
                    u"result": result,
                    u"head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]),
                    u"title": title}
        except Unauthorized:
            self.AddHeader("X-Result", "false")
            return {u"content": _(u"User not found"),
                    u"result": False,
                    u"head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]),
                    u"title": title}
            
    def activate(self):
        """
        Activates a user account. Requires the token generated in `create`.

        **Settings**

        - *title*: (string) title displayed above the form

        **Return values**

        - *body*: This function returns rendered html code as body.
        - *X-Result header*: http header indicating whether the new item has been created or not.
        """
        title = u""
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            title = viewconf.settings.get("title",u"")
        form = self._loadSimpleForm()
        form.startEmpty = True
        form.Setup(subset="activate")
        result, data, action = form.Process(renderSuccess=False)
        self.AddHeader("X-Result", str(result).lower())
        return {u"content": data, 
                u"result": result, 
                u"head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]), 
                u"title": title}

    def resetpass(self):
        """
        Resets the users password and sends a randomly generated password to the users email.

        **Settings**

        - *title*: (string) title displayed above the form

        **Return values**

        - *body*: This function returns rendered html code as body.
        - *X-Result header*: http header indicating whether the new item has been created or not.
        """
        title = u""
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            title = viewconf.settings.get("title",u"")
        form = self._loadSimpleForm()
        form.startEmpty = True
        if self.context.app.configuration.loginByEmail:
            subset = "resetpassMail"
        else:
            subset = "resetpass"
        form.Setup(subset=subset)
        result, data, action = form.Process(renderSuccess=False)
        self.AddHeader("X-Result", str(result).lower())
        return {u"content": data, 
                u"result": result, 
                u"head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]), 
                u"title": title}

    def updatepass(self):
        """
        Update the users password. The user is forced to enter the current password to change it.

        **Settings**

        - *title*: (string) title displayed above the form

        **Return values**

        - *body*: This function returns rendered html code as body.
        - *X-Result header*: http header indicating whether the new item has been created or not.
        """
        title = u""
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            title = viewconf.settings.get("title",u"")
        form = self._loadSimpleForm()
        form.startEmpty = True
        form.Setup(subset="updatepass")
        result, data, action = form.Process(renderSuccess=False)
        self.AddHeader("X-Result", str(result).lower())
        return {u"content": data, 
                u"result": result, 
                u"head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]), 
                u"title": title}

    def updatemail1(self):
        """
        Change the users email. Sends a verification mail to the new email address. Use `updatemail2` to verify
        the email.

        **Settings**

        - *title*: (string) title displayed above the form

        **Return values**

        - *body*: This function returns rendered html code as body.
        - *X-Result header*: http header indicating whether the new item has been created or not.
        """
        title = u""
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            title = viewconf.settings.get("title",u"")
        form = self._loadSimpleForm()
        form.startEmpty = True
        form.Setup(subset="updatemail1")
        result, data, action = form.Process(url=self.Url()+"updatemail2", renderSuccess=False)
        self.AddHeader("X-Result", str(result).lower())
        return {u"content": data, 
                u"result": result, 
                u"head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]), 
                u"title": title}

    def updatemail2(self):
        """
        Change the users email. Verifies the new user email by processing the token generated in `updatemail1`.

        **Settings**

        - *title*: (string) title displayed above the form

        **Return values**

        - *body*: This function returns rendered html code as body.
        - *X-Result header*: http header indicating whether the new item has been created or not.
        """
        title = u""
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            title = viewconf.settings.get("title",u"")
        form = self._loadSimpleForm()
        form.startEmpty = True
        form.Setup(subset="updatemail2")
        result, data, action = form.Process(renderSuccess=False)
        self.AddHeader("X-Result", str(result).lower())
        return {u"content": data, 
                u"result": result, 
                u"head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]), 
                u"title": title}

    def contact(self):
        """
        Contact form with several configuration options. Can be used to send mails to other users or the system
        administrator.

        **Settings**

        - *title*: (string) title displayed above the form
        - *receiver*: (string/tuple/callback) send the email to this user. Can be a user id, a `(email, name)` tuple
                      or callback to dynamically lookup the receiver. The callback takes one parameter `form`.
        - *replyToSender*: (bool) sets the reply to adress to the authenticated sender.
        - *form*: (dict) the form setup including fields and form settings for the form setup.
        - *mail*: (nive.views.Mail) The template used to render the email. Form values are passed as `data` to the mail
                  template. Uses `nive_userdb:userview/mails/contact.pt` by default. See nive_userdb.application configuration.

        **Return values**

        - *body*: This function returns rendered html code as body.
        - *X-Result header*: http header indicating whether the new item has been created or not.
        """
        title = u""
        mail = receiver = None
        replyToSender = False
        subset = u"contact"
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            title = viewconf.settings.get("title",u"")
            receiver = viewconf.settings.get("receiver")
            replyToSender = viewconf.settings.get("replyToSender")
            subset = viewconf.settings.get("form")
            mail = viewconf.settings.get("mail")
        # get the receiver
        if isinstance(receiver, basestring):
            user = self.context.root().GetUser(receiver)
            receiver = ((user.data.get("email"), user.meta.get("title")),)
        elif IUser.providedBy(receiver):
            receiver = ((receiver.data.get("email"), receiver.meta.get("title")),)
        elif callable(receiver):
            receiver = receiver(self)
        form, subset = self._loadForm(subset, viewconf=viewconf, defaultsubset="contact")
        form.startEmpty = True
        form.Setup(subset=subset)
        result, data, action = form.Process(receiver=receiver, replyToSender=replyToSender, mail=mail, renderSuccess=False)
        self.AddHeader("X-Result", str(result).lower())
        return {u"content": data, 
                u"result": result, 
                u"head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]), 
                u"title": title}

    def login(self):
        """
        Login page for user authentication

        **Settings**

        - *title*: (string) title displayed above the form
        - *resetPasswordLink*: (bool) shows the reset password link on the default template if true.
        - *form*: (dict) the form setup including fields and form settings for the form setup.

        **Return values**

        - *body*: This function returns rendered html code as body.
        - *X-Result header*: http header indicating whether the new item has been created or not.
        """
        title = u""
        resetPasswordLink = False
        viewconf = self.GetViewConf()
        subset = "login"
        if viewconf and viewconf.get("settings"):
            subset = viewconf.settings.get("form")
            title = viewconf.settings.get("title",u"")
            resetPasswordLink = viewconf.settings.get("resetPasswordLink",resetPasswordLink)
        if self.context.app.configuration.loginByEmail:
            defaultsubset = "loginMail"
        else:
            defaultsubset = "login"
        form, subset = self._loadForm(subset, viewconf=viewconf, defaultsubset=defaultsubset)
        form.Setup(subset=subset)
        user = self.User()
        if not user:
            redirect = self.GetFormValue(u"redirect")
            if not redirect:
                try:
                    redirect = self.context.app.portal.configuration.loginSuccessUrl
                except:
                    redirect = self.request.url
                result, data, action = form.Process(redirectSuccess=redirect)
            else:
                # pass redirect to form as hidden field
                result, data, action = form.Process(defaultData={u"redirect":redirect}, redirectSuccess=redirect)
            self.AddHeader("X-Result", str(result).lower())
            return {u"content": data,
                    u"result": result,
                    u"head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]),
                    u"resetPasswordLink":resetPasswordLink,
                    u"title":title}
        return {u"content": u"",
                u"result": True,
                u"head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]),
                u"resetPasswordLink":resetPasswordLink,
                u"title":title}
            
    def logout(self):
        """
        Logout action
        """
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
    
    def logoutlink(self):
        return {}  #?

    def logouturl(self):
        try:
            return self.context.app.portal.configuration.logoutUrl
        except:
            return self.request.url


    def closefirstrun(self):
        """
        Resets the users first run state after signup
        """
        user = self.User(sessionuser=False)
        if user is None:
            return {"result": False}
        user.data["tempcache"] = u""
        user.Commit(user=user)
        return {"result": True}

    def remove(self):
        """
        This method gives the user a option to delete his user account through the web.

        **Settings**

        - *title*: (string) title displayed above the form
        - *description*: (string) adds a description 

        **Return values**

        - *body*: This function returns rendered html code as body.
        - *X-Result header*: http header indicating whether the new item has been created or not.
        """
        user=self.User(sessionuser=False)
        title = u""
        description = u""
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            title = viewconf.settings.get("title",u"")
            description = viewconf.settings.get("description",u"")
        values = {u"title": title, u"description": description, u"result":False}
        if user is None:
            return values
        remove = self.GetFormValue(u"remove", method="POST")==u"1"
        if remove:
            # delete the object, cache and sign out
            self.context.root().DeleteUser(user, currentUser=user)
            self.context.app.ForgetLogin(self.request)
            values[u"result"] = True
            self.AddHeader("X-Result", "true")
        return values


    def insertMessages(self):
        messages = self.request.session.pop_flash("")
        if not messages:
            return u""
        html = u"""<div class="alert alert-success">%s</div>"""
        return html % (u"</li><li>".join(messages))


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

    def _loadForm(self, subset, viewconf, defaultsubset):
        # form rendering settings
        # form setup
        typeconf=self.context.app.GetObjectConf("user")
        form = UserForm(view=self, context=self.context.root(), loadFromType=typeconf)
        defaultaction = form.subsets[defaultsubset]
        # sign up settings defined in user db configuration user in AddUser()
        form.settings = self.context.app.configuration.settings

        # load subset
        subset = subset or defaultsubset
        if isinstance(subset, basestring):
            # the subset is referenced as string -> look it up in typeconf.forms
            if not subset in form.subsets:
                cp = copy.deepcopy(typeconf.forms)
                form.subsets = cp
        else:
            form.ApplyOptions(subset)
            cp = copy.deepcopy(subset)
            form.subsets = {defaultsubset: cp}
            subset = defaultsubset

        if not subset in form.subsets:
            raise ConfigurationError("Unknown subset "+subset)

        # set up action
        if not "actions" in form.subsets[subset] and defaultaction:
            if "defaultAction" in defaultaction:
                form.subsets[subset]["defaultAction"] = defaultaction["defaultAction"]
            if "actions" in defaultaction:
                form.subsets[subset]["actions"] = defaultaction["actions"]

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


class UserForm(ObjectForm):
    """
    Extended User form used in `userview` functions
    """

    def __init__(self, view=None, loadFromType=None, context=None, request=None, app=None, **kw):
        ObjectForm.__init__(self, view=view, loadFromType=loadFromType, context=context, request=request, app=app, **kw)

        self.actions = [
            Conf(id="default",    method="StartForm", name=u"Initialize",    hidden=True),
            Conf(id="defaultEdit",method="LoadUser",  name=u"Initialize",    hidden=True),
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
                    FieldConf(id="password", name=_("Password"), datatype="password", settings={"single": True}),
                    FieldConf(id="redirect", datatype="string", size="500", name="redirect url", hidden=True),
                ],
                "actions": ["login"],
                "defaultAction": "default"
            },
            "loginMail":  {
                "fields":  [
                    FieldConf(id="name", name=_("Name or email"), datatype="string"),
                    FieldConf(id="password", name=_("Password"), datatype="password", settings={"single": True}),
                    FieldConf(id="redirect", datatype="string", size="500", name="redirect url", hidden=True),
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
                "actions": [Conf(id="resetpass", method="ResetPass", name=_(u"Reset password"), hidden=False)],
                "defaultAction": "default"
            },
            "resetpassMail": {
                "fields": [FieldConf(id="name", name=_("Email"), datatype="string")],
                "actions": [Conf(id="resetpass", method="ResetPass", name=_(u"Reset password"), hidden=False)],
                "defaultAction": "default"
            },
            "contact": {
                "fields": [FieldConf(id="message", name=_("Message"), datatype="text", required=True, size=3000)],
                "actions": [Conf(id="contact", method="Contact", name=_(u"Send message"), hidden=False)],
                "defaultAction": Conf(id="default", method="StartRequestPOST", name=_(u"Initialize"), hidden=True)
            },
        }

        self.css_class = "smallform"
        self.settings = {}


    def AddUser(self, action, **kw):
        """
        Form action: safely add a user

        Pass additional user data as `values` in keywords.
        """
        msgs = []
        result,data,errors = self.Validate(self.request)
        if result:
            opts = {}
            opts.update(kw)
            opts.update(self.settings)
            # add additional user values if passed in kws
            if kw.get("values"):
                data.update(kw["values"])
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

        Pass additional user data as `values` in keywords.
        """
        user = self.view.User(sessionuser=False)
        if not user:
            raise Unauthorized, "User not found."
        msgs = []
        result,data,errors = self.Validate(self.request)
        if result:
            # add additional user values if passed in kws
            if kw.get("values"):
                data.update(kw["values"])
            result = user.SecureUpdate(data, user)
            if result:
                msgs.append(_(u"OK."))

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
                msgs = [self.context.app.configuration.get("activationMessage") or _(u"OK.")]
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
                    result = True
        if not result:
            msgs = [_(u"The token is invalid. Please make sure it is complete.")]
        data = {"token": data or u""}
        return self._FinishFormProcessing(result, data, msgs, errors, **kw)


    def ResetPass(self, action, **kw):
        """
        Form action: generate a new password and mail to the user
        """
        data = self.GetFormValues(self.request)
        kw["form"] = self
        result, msgs = self.context.MailUserPass(data.get("name"),
                                                 currentUser=self.view.User(),
                                                 **kw)
        if result:
            data = {}
        return self._FinishFormProcessing(result, data, msgs, None, **kw)


    def Contact(self, action, **kw):
        """
        Sends a email to the user 'receiver'

        :param action:
        :param kw: mail, receiver, replyToSender
        :return:
        """
        result,data,errors = self.Validate(self.request)
        if not result:
            return result, self.Render(data, msgs=[], errors=errors)

        recv = kw.get("receiver")
        if not isinstance(recv, (list, tuple)):
            result = False
            msgs = (_(u"No receiver specified."),)
            return result, self.Render(data, msgs=msgs, errors=errors)

        replyTo = u""
        user = self.view.User()
        if kw.get("replyToSender")==True:
            replyTo=user.data.email

        mail = kw.get("mail") or self.context.app.configuration.mailContact
        title = mail.title
        body = mail(sender=user, data=data, form=self, **kw)
        tool = self.context.app.GetTool("sendMail")
        if not tool:
            raise ConfigurationError, "Mail tool 'sendMail' not found"

        result, value = tool(body=body, title=title, recvmails=recv, replyTo=replyTo, force=1)
        if not result:
            msgs=(_(u"The email could not be sent."),)
        else:
            msgs = (_(u"The email has been sent."),)
        return self._FinishFormProcessing(result, data, msgs, None, **kw)

