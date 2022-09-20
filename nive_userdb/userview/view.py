# Copyright 2012 - 2014 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

import copy

from nive.definitions import FieldConf, ViewConf, ViewModuleConf, Conf
from nive.definitions import ConfigurationError
from nive.definitions import IUser
from nive.views import BaseView, Unauthorized, Mail
from nive.components.reform.forms import ObjectForm

from nive_userdb.i18n import _
from nive_userdb.i18n import translator
from nive_userdb.app import EmailValidator, UsernameValidator, OldPwValidator
import collections


# view module definition ------------------------------------------------------------------

#@nive_module
configuration = ViewModuleConf(
    id = "userview",
    name = _("User signup"),
    static = "nive_userdb.userview:static",
    containment = "nive.definitions.IPortal",
    context = "nive_userdb.app.UserDB",
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
    ViewConf(name="resetpass1",     attr="resetpassToken",  renderer=t+"form.pt"),
    ViewConf(name="resetpass2",     attr="updatepassToken", renderer=t+"form.pt"),
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
        title = ""
        if viewconf and viewconf.get("settings"):
            subset = viewconf.settings.get("form")
            title = viewconf.settings.get("title")
            values = viewconf.settings.get("values")

        form, subset = self._loadForm(subset, context=self.context.root, viewconf=viewconf, defaultsubset="create")
        form.Setup(subset=subset)

        if self.GetFormValue("assets")=="only":
            self.AddHeader("X-Result", "true")
            return {"content": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets])}

        result, data, action = form.Process(url=self.Url()+"activate", values=values, renderSuccess=False)
        self.AddHeader("X-Result", str(result).lower())
        return {"content": data,
                "result": result,
                "head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]),
                "title": title}

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
        title = ""
        user = self.User(sessionuser=False)
        if user is None:
            self.AddHeader("X-Result", "false")
            return {"content": _("User not found."),
                    "result": False, "head": "", "title": title}

        subset = values = None
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            subset = viewconf.settings.get("form")
            title = viewconf.settings.get("title","")
            values = viewconf.settings.get("values")
        form, subset = self._loadForm(subset, context=user, viewconf=viewconf, defaultsubset="edit")

        if self.GetFormValue("assets")=="only":
            self.AddHeader("X-Result", "true")
            return {"content": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets])}

        if user and user.id == 0:
            self.AddHeader("X-Result", "false")
            return {"content": _("Your current user can only be edited on file system level."),
                    "result": False, "head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]), "title": title}
        form.Setup(subset=subset)
        try:
            result, data, action = form.Process(values=values, renderSuccess=True)
            self.AddHeader("X-Result", str(result).lower())
            return {"content": data,
                    "result": result,
                    "head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]),
                    "title": title}
        except Unauthorized:
            self.AddHeader("X-Result", "false")
            return {"content": _("User not found"),
                    "result": False,
                    "head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]),
                    "title": title}
            
    def activate(self):
        """
        Activates a user account. Requires the token generated in `create`.

        **Settings**

        - *title*: (string) title displayed above the form

        **Return values**

        - *body*: This function returns rendered html code as body.
        - *X-Result header*: http header indicating whether the new item has been created or not.
        """
        title = ""
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            title = viewconf.settings.get("title","")
        form = self._loadSimpleForm(context=self.context.root)
        form.startEmpty = True
        form.Setup(subset="activate")
        result, data, action = form.Process(renderSuccess=False)
        self.AddHeader("X-Result", str(result).lower())
        return {"content": data, 
                "result": result, 
                "head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]), 
                "title": title}

    def resetpass(self):
        """
        Resets the users password and sends a randomly generated password to the users email.

        **Settings**

        - *title*: (string) title displayed above the form

        **Return values**

        - *body*: This function returns rendered html code as body.
        - *X-Result header*: http header indicating whether the new item has been created or not.
        """
        title = ""
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            title = viewconf.settings.get("title","")
        form = self._loadSimpleForm(context=self.context.root)
        form.startEmpty = True
        if self.context.configuration.loginByEmail:
            subset = "resetpassMail"
        else:
            subset = "resetpass"
        form.Setup(subset=subset)
        result, data, action = form.Process(renderSuccess=False)
        self.AddHeader("X-Result", str(result).lower())
        return {"content": data, 
                "result": result, 
                "head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]), 
                "title": title}

    def updatepass(self):
        """
        Update the users password. The user is forced to enter the current password to change it.

        **Settings**

        - *title*: (string) title displayed above the form

        **Return values**

        - *body*: This function returns rendered html code as body.
        - *X-Result header*: http header indicating whether the new item has been created or not.
        """
        title = ""
        user = self.User(sessionuser=False)
        if user is None:
            self.AddHeader("X-Result", "false")
            return {"content": _("User not found."),
                    "result": False, "head": "", "title": title}

        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            title = viewconf.settings.get("title","")
        form = self._loadSimpleForm(context=user)
        form.startEmpty = True
        form.Setup(subset="updatepass")
        result, data, action = form.Process(renderSuccess=False)
        self.AddHeader("X-Result", str(result).lower())
        return {"content": data, 
                "result": result, 
                "head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]), 
                "title": title}

    def resetpassToken(self):
        """
        Resets the users password and sends a randomly generated password to the users email.

        **Settings**

        - *title*: (string) title displayed above the form

        **Return values**

        - *body*: This function returns rendered html code as body.
        - *X-Result header*: http header indicating whether the new item has been created or not.
        """
        title = ""
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            title = viewconf.settings.get("title","")
        form = self._loadSimpleForm(context=self.context.root)
        form.startEmpty = True
        form.Setup(subset="resetpass_mail")
        result, data, action = form.Process(renderSuccess=False)
        self.AddHeader("X-Result", str(result).lower())
        return {"content": data,
                "result": result,
                "head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]),
                "title": title}

    def updatepassToken(self):
        """
        Update the users password. The user is forced to enter the current password to change it.

        **Settings**

        - *title*: (string) title displayed above the form

        **Return values**

        - *body*: This function returns rendered html code as body.
        - *X-Result header*: http header indicating whether the new item has been created or not.
        """
        title = ""
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            title = viewconf.settings.get("title","")
        form = self._loadSimpleForm(context=self.context.root)
        token = self.GetFormValue("token")
        user = self.context.root.GetUserForToken(token)
        if user is None:
            form.Setup(subset="editpass_token2")
        else:
            form.Setup(subset="editpass_token")
        result, data, action = form.Process(renderSuccess=False)
        self.AddHeader("X-Result", str(result).lower())
        return {"content": data,
                "result": result,
                "head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]),
                "title": title}

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
        title = ""
        user = self.User(sessionuser=False)
        if user is None:
            self.AddHeader("X-Result", "false")
            return {"content": _("User not found."),
                    "result": False, "head": "", "title": title}

        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            title = viewconf.settings.get("title","")
        form = self._loadSimpleForm(context=user)
        form.startEmpty = True
        form.Setup(subset="updatemail1")
        result, data, action = form.Process(url=self.Url()+"updatemail2", renderSuccess=False)
        self.AddHeader("X-Result", str(result).lower())
        return {"content": data, 
                "result": result, 
                "head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]), 
                "title": title}

    def updatemail2(self):
        """
        Change the users email. Verifies the new user email by processing the token generated in `updatemail1`.

        **Settings**

        - *title*: (string) title displayed above the form

        **Return values**

        - *body*: This function returns rendered html code as body.
        - *X-Result header*: http header indicating whether the new item has been created or not.
        """
        title = ""
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            title = viewconf.settings.get("title","")
        form = self._loadSimpleForm(context=self.context.root)
        form.startEmpty = True
        form.Setup(subset="updatemail2")
        result, data, action = form.Process(renderSuccess=False)
        self.AddHeader("X-Result", str(result).lower())
        return {"content": data, 
                "result": result, 
                "head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]), 
                "title": title}

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
        - *senderConfirmationNote*: (string) sends a confirmation mail to sender and prepends the note to email copy. if empty or none
                                    the confirmation mail will be skipped.

        **Return values**

        - *body*: This function returns rendered html code as body.
        - *X-Result header*: http header indicating whether the new item has been created or not.
        """
        title = ""
        mail = receiver = senderConfirmationNote = None
        replyToSender = False
        subset = "contact"
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            title = viewconf.settings.get("title","")
            receiver = viewconf.settings.get("receiver")
            replyToSender = viewconf.settings.get("replyToSender")
            subset = viewconf.settings.get("form")
            mail = viewconf.settings.get("mail")
            senderConfirmationNote = viewconf.settings.get("senderConfirmationNote")

        # get the receiver
        if isinstance(receiver, str):
            user = self.context.root.GetUser(receiver)
            receiver = ((user.data.get("email"), user.meta.get("title")),)
        elif IUser.providedBy(receiver):
            receiver = ((receiver.data.get("email"), receiver.meta.get("title")),)
        elif isinstance(receiver, collections.abc.Callable):
            receiver = receiver(self)
        else: # use userAdmin as default
            receiver = (self.context.configuration.userAdmin,)
        form, subset = self._loadForm(subset, context=self.context.root, viewconf=viewconf, defaultsubset="contact")
        form.startEmpty = True
        form.Setup(subset=subset)
        result, data, action = form.Process(receiver=receiver, replyToSender=replyToSender, mail=mail, renderSuccess=False,
                                            senderConfirmationNote=senderConfirmationNote)
        self.AddHeader("X-Result", str(result).lower())
        return {"content": data, 
                "result": result, 
                "head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]), 
                "title": title}

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
        title = ""
        resetPasswordLink = False
        viewconf = self.GetViewConf()
        subset = "login"
        if viewconf and viewconf.get("settings"):
            subset = viewconf.settings.get("form")
            title = viewconf.settings.get("title","")
            resetPasswordLink = viewconf.settings.get("resetPasswordLink",resetPasswordLink)
        if self.context.app.configuration.loginByEmail:
            defaultsubset = "loginMail"
        else:
            defaultsubset = "login"
        form, subset = self._loadForm(subset, context=self.context.root, viewconf=viewconf, defaultsubset=defaultsubset)
        form.Setup(subset=subset)
        user = self.User()
        if not user:
            redirect = self.GetFormValue("redirect")
            if not redirect:
                try:
                    redirect = self.context.portal.configuration.loginSuccessUrl
                except:
                    redirect = self.request.url
                result, data, action = form.Process(redirectSuccess=redirect)
            else:
                # pass redirect to form as hidden field
                result, data, action = form.Process(defaultData={"redirect":redirect}, redirectSuccess=redirect)
            self.AddHeader("X-Result", str(result).lower())
            return {"content": data,
                    "result": result,
                    "head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]),
                    "resetPasswordLink":resetPasswordLink,
                    "title":title}
        return {"content": "",
                "result": True,
                "head": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets]),
                "resetPasswordLink":resetPasswordLink,
                "title":title}
            
    def logout(self):
        """
        Logout action
        """
        self.ResetFlashMessages()
        app = self.context
        user = self.UserName()
        a = self.context.root.Logout(user)
        app.ForgetLogin(self.request)
        redirect = self.GetFormValue("redirect")
        if not redirect:
            try:
                redirect = self.context.portal.configuration.logoutSuccessUrl
            except:
                redirect = self.context.portal.configuration.portalDefaultUrl
        if redirect:
            localizer = translator(self.request)
            self.Redirect(redirect, messages=[localizer(_("You have been logged out!"))])
        return {}
    
    def logoutlink(self):
        return {}  #?

    def logouturl(self):
        try:
            return self.context.portal.configuration.logoutUrl
        except:
            return self.request.url


    def closefirstrun(self):
        """
        Resets the users first run state after signup
        """
        user = self.User(sessionuser=False)
        if user is None:
            return {"result": False}
        user.data["tempcache"] = ""
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
        title = ""
        user = self.User(sessionuser=False)
        if user is None:
            self.AddHeader("X-Result", "false")
            return {"content": _("User not found."),
                    "result": False, "head": "", "title": title, "description": ""}

        description = ""
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            title = viewconf.settings.get("title","")
            description = viewconf.settings.get("description","")
        values = {"title": title, "description": description, "result":False}
        remove = self.GetFormValue("remove", method="POST")=="1"
        if remove:
            # delete the object, cache and sign out
            self.context.root.DeleteUser(user, currentUser=user)
            self.context.ForgetLogin(self.request)
            values["result"] = True
            self.AddHeader("X-Result", "true")
        return values


    def insertMessages(self):
        messages = self.request.session.pop_flash("")
        if not messages:
            return ""
        html = """<div class="alert alert-success">%s</div>"""
        return html % ("</li><li>".join(messages))


    def _loadSimpleForm(self, context=None):
        # form rendering settings
        # form setup
        context = context or self.User(sessionuser=False)
        form = UserForm(view=self, context=context, loadFromType="user")
        # sign up settings defined in user db configuration user in AddUser()
        form.settings = self.context.configuration.settings

        # customize form widget. values are applied to form.widget
        form.widget.item_template = "field_onecolumn"
        form.widget.action_template = "form_actions_onecolumn"
        #form.use_ajax = True
        form.action = self.request.url
        vm = self.configuration
        if vm:
            formsettings = vm.get("form")
            if isinstance(formsettings, dict):
                form.ApplyOptions(formsettings)
        return form

    def _loadForm(self, subset, viewconf, defaultsubset, context):
        # form rendering settings
        # form setup
        typeconf = self.context.app.configurationQuery.GetObjectConf("user")
        form = UserForm(view=self, context=context, loadFromType=typeconf)
        defaultaction = form.subsets[defaultsubset]
        # sign up settings defined in user db configuration user in AddUser()
        form.settings = self.context.configuration.settings

        # load subset
        subset = subset or defaultsubset
        if isinstance(subset, str):
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
        vm = self.configuration
        if vm:
            formsettings = vm.get("form")
            if isinstance(formsettings, dict):
                form.ApplyOptions(formsettings)
        return form, subset


class UserForm(ObjectForm):
    """
    Extended User form used in `userview` functions

    context = Userroot
    """

    def __init__(self, view=None, loadFromType=None, context=None, request=None, app=None, **kw):
        ObjectForm.__init__(self, view=view, loadFromType=loadFromType, context=context, request=request, app=app, **kw)

        self.actions = [
            Conf(id="default",    method="StartForm", name="Initialize",    hidden=True),
            Conf(id="defaultEdit",method="LoadUser",  name="Initialize",    hidden=True),
            Conf(id="create",     method="AddUser",   name=_("Signup"),        hidden=False, css_class="btn btn-primary"),
            Conf(id="edit",       method="Update",    name=_("Confirm"),       hidden=False, css_class="btn btn-primary"),
            Conf(id="login",      method="Login",     name=_("Login"),         hidden=False),
            Conf(id="loginmail",  method="LoginEmail",name=_("Login"),         hidden=False),
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
                    FieldConf(id="name", name=_("Name"), datatype="string", size="255", required=True),
                    FieldConf(id="password", name=_("Password"), datatype="password", required=True, settings={"single": True}),
                    FieldConf(id="redirect", datatype="string", size="500", name="redirect url", hidden=True),
                ],
                "actions": ["login"],
                "defaultAction": "default"
            },
            "loginMail":  {
                "fields":  [
                    FieldConf(id="email", name=_("Email"), datatype="string", size="255", required=True),
                    FieldConf(id="password", name=_("Password"), datatype="password", settings={"single": True}),
                    FieldConf(id="redirect", datatype="string", size="500", name="redirect url", hidden=True),
                ],
                "actions": ["loginmail"],
                "defaultAction": "default"
            },

            "activate": {
                "fields": [FieldConf(id="token", datatype="string", size="500", name=_("Token for activation or password reset"), required=True, hidden=False)],
                "actions": [Conf(id="activate", method="Activate", name=_("Activate"), hidden=False)],
                "defaultAction": "activate"
            },
            "updatepass":{
                "fields": [
                    FieldConf(id="oldpassword",
                              datatype="password",
                              size=100,
                              default="",
                              required=1,
                              name=_("Old password"),
                              settings={"single":True},
                              validator=OldPwValidator),
                    "password"
                ],
                "actions": [Conf(id="updatepass", method="UpdatePass", name=_("Update password"), hidden=False)],
                "defaultAction": "default"
            },
            "resetpass_mail": {
                "fields": [
                    FieldConf(id="email", name=_("Email"), datatype="string", size=255)
                ],
                "actions": [
                    Conf(id="resetpass", method="MailPassToken", name=_("Reset password"), hidden=False)
                ]
            },
            "editpass_token": {
                "fields": [
                    "password",
                    FieldConf(id="token", datatype="string", name=_("Token for activation or password reset"), size=500, required=True, hidden=True)
                ],
                "actions": [
                    Conf(id="editpass", method="UpdatePassToken", name=_("Update password"), hidden=False)
                ],
                "defaultAction": Conf(id="starteditpass", method="StartRequestGET", name="Start update password", hidden=True)
            },
            "editpass_token2":{
                "fields": [
                    FieldConf(id="token", datatype="string", name=_("Token for activation or password reset"), size=500, required=True, hidden=False),
                    "password"
                ],
                "actions": [
                    Conf(id="editpass", method="UpdatePassToken", name=_("Update password"), hidden=False, css_class="btn btn-primary")
                ],
                "defaultAction": Conf(id="starteditpass", method="StartRequestGET", name="Start update password", hidden=True)
            },

            "updatemail1": {
                "fields": [
                    FieldConf(id="newmail",
                           datatype="email",
                           size=255,
                           default="",
                           required=1,
                           name=_("New email"),
                           validator=EmailValidator)
                ],
                "actions": [Conf(id="updatemail", method="UpdateMail", name=_("Update email"), hidden=False)],
                "defaultAction": "default"
            },
            "updatemail2": {
                "fields": [FieldConf(id="token", datatype="string", size="500", name=_("Token for activation or password reset"), required=True, hidden=False)],
                "actions": [Conf(id="updatemail_token", method="UpdateMailToken", name=_("Verify email"), hidden=False)],
                "defaultAction": "updatemail_token"
            },

            "resetpass": {
                "fields": [FieldConf(id="name", name=_("Name"), datatype="string", size=255)],
                "actions": [Conf(id="resetpass", method="ResetPass", name=_("Reset password"), hidden=False)],
                "defaultAction": "default"
            },
            "resetpassMail": {
                "fields": [FieldConf(id="name", name=_("Email"), datatype="string", size=255)],
                "actions": [Conf(id="resetpass", method="ResetPass", name=_("Reset password"), hidden=False)],
                "defaultAction": "default"
            },
            "contact": {
                "fields": [FieldConf(id="message", name=_("Message"), datatype="text", required=True, size=3000)],
                "actions": [Conf(id="contact", method="Contact", name=_("Send message"), hidden=False)],
                "defaultAction": Conf(id="default", method="StartRequestPOST", name=_("Initialize"), hidden=True)
            },
        }

        self.css_class = "smallform"
        self.settings = {}


    def AddUser(self, action, **kw):
        """
        Form action: safely add a user

        context: root

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

        context: user
        """
        data = self.LoadObjData(self.context)
        try:
            del data["password"]
        except:
            pass
        return data!=None, self.Render(data)


    def Login(self, action, **kw):
        """
        Form action: user login

        context: root
        """
        redirectSuccess = kw.get("redirectSuccess")
        data = self.GetFormValues(self.request)
        user, msgs = self.context.Login(data.get("name"), data.get("password"), raiseUnauthorized=0)
        if user:
            self.context.app.RememberLogin(self.request, str(user))
            if self.view and redirectSuccess:
                self.view.Redirect(redirectSuccess)
                return
        errors=None
        return user, self.Render(data, msgs=msgs, errors=errors)


    def LoginEmail(self, action, **kw):
        """
        Form action: user login

        context: root
        """
        redirectSuccess = kw.get("redirectSuccess")
        data = self.GetFormValues(self.request)
        user, msgs = self.context.Login(None, data.get("password"), email=data.get("email"), raiseUnauthorized=0)
        if user is not None:
            self.context.app.RememberLogin(self.request, str(user))
            if self.view and redirectSuccess:
                self.view.Redirect(redirectSuccess)
                return
        errors=None
        return user, self.Render(data, msgs=msgs, errors=errors)


    def Activate(self, action, **kw):
        """
        Form action: activate the mail in tempcache if token matches

        context: root
        """
        msgs = []
        errors = []
        result = False
        data = self.GetFormValue("token",method="ALL")
        if data:
            if data.find("token=")!=-1:
                data = data.split("token=")[-1]
            user = self.context.GetUserForToken(data, activeOnly=False)
            if user is not None:
                result = True
                user.Activate(currentUser=user)
                msgs = [self.context.app.configuration.get("activationMessage") or _("OK.")]
            else:
                result = False
        if not result:
            msgs = [_("The token is invalid. Please make sure it is complete.")]
        data = {"token": data or ""}
        return self._FinishFormProcessing(result, data, msgs, errors, **kw)


    def Update(self, action, **kw):
        """
        Form action: safely update a user

        context: user

        Pass additional user data as `values` in keywords.
        """
        msgs = []
        result,data,errors = self.Validate(self.request)
        if result:
            # add additional user values if passed in kws
            if kw.get("values"):
                data.update(kw["values"])
            password = data.get("password")
            email = data.get("email")
            result = self.context.SecureUpdate(data, self.view.user)
            if result:
                if password:
                    result = self.context.UpdatePassword(password, self.view.user)
                if email:
                    result = self.context.UpdateEmail(email, self.view.user)
                msgs.append(_("OK."))
            data["email"] = email

        return self._FinishFormProcessing(result, data, msgs, errors, **kw)


    def UpdatePass(self, action, **kw):
        """
        Form action: update password if current password matches

        context: user

        """
        msgs = []
        result,data,errors = self.Validate(self.request)
        if not result:
            return result, self.Render(data, msgs=msgs, errors=errors)

        result = self.context.UpdatePassword(data["password"], self.view.user)
        if result:
            msgs.append(_("OK. Password changed."))
            return result, self.Render(data, msgs=msgs, errors=None, messagesOnly=True)
        return result, self.Render(data)


    def UpdateMail(self, action, **kw):
        """
        Form action: trigger a mail to verify another mail address
        """
        msgs = []
        result,data,errors = self.Validate(self.request)
        if result:
            newmail = data["newmail"]
            result, msgs = self.context.root.MailVerifyNewEmail(self.context, newmail, currentUser=self.view.user, **kw)
        return self._FinishFormProcessing(result, data, msgs, errors, **kw)


    def UpdateMailToken(self, action, **kw):
        """
        Form action: activate the mail in tempcache if token matches

        context: root
        """
        msgs = []
        errors = []
        result = False
        data = self.GetFormValue("token",method="ALL")
        if data:
            if data.find("token=")!=-1:
                data = data.split("token=")[-1]
            user = self.context.GetUserForToken(data)
            if user:
                mail = user.data.tempcache
                if mail.startswith("verifymail:"):
                    mail = mail.replace("verifymail:","")
                    user.data["email"] = mail
                    user.data["tempcache"] = ""
                    user.data["token"] = ""
                    user.Commit(user=user)
                    msgs = [_("OK. The new email address has been activated.")]
                    result = True
        if not result:
            msgs = [_("The token is invalid. Please make sure it is complete.")]
        data = {"token": data or ""}
        return self._FinishFormProcessing(result, data, msgs, errors, **kw)


    def ResetPass(self, action, **kw):
        """
        Form action: generate a new password and mail to the user

        context: root
        """
        data = self.GetFormValues(self.request)
        kw["form"] = self
        result, msgs = self.context.MailUserPass(data.get("name"),
                                                 currentUser=self.view.User(),
                                                 **kw)
        if result:
            data = {}
        return self._FinishFormProcessing(result, data, msgs, None, **kw)


    def MailPassToken(self, action, **kw):
        """
        Form action: safely update a user

        context: root

        kw parameter:
        - mail
        - redirectSuccess
        """
        msgs = []
        redirectSuccess = kw.get("redirectSuccess")
        result,data,errors = self.Validate(self.request)
        if result:
            result, msgs = self.context.MailResetPass(name=None,
                                                      email=data.get("email"),
                                                      currentUser=self.view.User(),
                                                      **kw)
            if result:
                errors=None
                #msgs.append(_("You can now sign in with the new password."))
                if self.view and redirectSuccess:
                    self.view.Redirect(redirectSuccess, messages=msgs)
                    return
                return result, self.Render(data, msgs=msgs, errors=errors, messagesOnly=True)
        return result, self.Render(data, msgs=msgs, errors=errors)


    def UpdatePassToken(self, action, **kw):
        """
        Form action: safely update a user

        context: root

        kw parameter:
        - redirectSuccess
        """
        msgs = []
        redirectSuccess = kw.get("redirectSuccess")
        result,data,errors = self.Validate(self.request)
        if result and data.get("token"):
            user = self.context.root.GetUserForToken(data["token"])
            if not user:
                return result, self.Render(data, msgs=[_("The token is invalid. Please make sure it is complete.")], errors=None)
            result = user.UpdatePassword(data["password"], self.view.User())
            if result:
                msgs.append(_("OK. Password changed."))
                errors=None
                if self.view and redirectSuccess:
                    self.view.Redirect(redirectSuccess, messages=msgs)
                    return
                return result, self.Render(data, msgs=msgs, errors=errors, messagesOnly=True)
        if not data.get("t"):
            msgs=[_("The token is invalid. Please make sure it is complete.")]
        return result, self.Render(data, msgs=msgs, errors=errors)


    def Contact(self, action, **kw):
        """
        Sends a email to the user 'receiver'

        context: root

        :param action:
        :param kw: mail, receiver, replyToSender, senderConfirmationNote
        :return:
        """
        result,data,errors = self.Validate(self.request)
        if not result:
            return result, self.Render(data, msgs=[], errors=errors)

        recv = kw.get("receiver")
        if not isinstance(recv, (list, tuple)):
            result = False
            msgs = (_("No receiver specified."),)
            return result, self.Render(data, msgs=msgs, errors=errors)

        replyTo = ""
        user = self.view.User()
        if kw.get("replyToSender")==True:
            replyTo=user.data.email

        mail = kw.get("mail") or self.context.app.configuration.settings.contactMail
        title = mail.title
        body = mail(sender=user, data=data, form=self, **kw)
        tool = self.context.app.GetTool("sendMail")
        if not tool:
            raise ConfigurationError("Mail tool 'sendMail' not found")

        stream, result = tool(body=body, title=title, recvmails=recv, replyTo=replyTo, force=1)
        if not result:
            msgs=(_("The email could not be sent."),)
        else:
            msgs = (_("The email has been sent."),)

        if kw.get("senderConfirmationNote"):
            sender = self.view.User(sessionuser=False)
            recv = ((sender.data.email, sender.meta.title),)
            title = kw.get("senderConfirmationNote") + title
            tool(body=body, title=title, recvmails=recv, force=1)

        return self._FinishFormProcessing(result, data, msgs, None, **kw)

