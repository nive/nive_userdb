# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
nive user database 
--------------------

You can specify a admin user on configuration level as `admin`. The admin user works without 
database connection.

The system admin for notification mails can be specified as `systemAdmin`.
::

    configuration.admin = {"name": "admin", "password": "adminpass", "email": "admin@domain.com"}
    configuration.systemAdmin = ("email", "display name")

"""
import hashlib

from nive.definitions import AppConf, GroupConf, Conf
from nive.definitions import implementer, IUserDatabase, ILocalGroups, IRoot
from nive.security import Allow, Deny, Everyone, Authenticated, ALL_PERMISSIONS, remember, forget
from nive.application import Application
from nive.views import Mail
from nive.components.reform.schema import Invalid
from nive.components.reform.schema import Email
from nive.components.reform.schema import Literal, Length

from nive_userdb.i18n import _

#@nive_module
configuration = AppConf(
    id = "userdb",
    title = _("Users"),

    loginByEmail = True,
    identityFallbackAlternative = True, # tries both: name and email as identity fields
    cookieAuthMaxAge=0, # e.g. 60*60*24*7 one week

    # signup settings
    settings = Conf(
        groups=(),
        activate=1,
        generatePW=0,
        generateName=False,
        # mails
        signupMail = Mail(_("Signup confirmation"), "nive_userdb:userview/mails/signup.pt"),
        notifyMail = Mail(_("Signup notification"), "nive_userdb:userview/mails/notify.pt"),
        sendPasswordMail = Mail(_("Your password"), "nive_userdb:userview/mails/mailpass.pt"),
        verifyPasswordMail = Mail(_("Verify your new e-mail"), "nive_userdb:userview/mails/verifymail.pt"),
        resetPasswordMail = Mail(_("Your new password"), "nive_userdb:userview/mails/resetpass.pt"),
        contactMail = Mail(_("Contact form"), "nive_userdb:userview/mails/contact.pt"),
    ),
    # contact system information
    userAdmin = ("admin@mymail.com", "Admin"),
    # non-db admin login
    #admin = {"name": "adminusername", "password": "adminpass", "email": ""admin@mymail.com""},

    # messages customizations
    welcomeMessage = "",
    activationMessage = "",

    # sessionuser field cache
    sessionuser = ("name", "email", "surname", "lastname", "groups", "notify", "lastlogin"),

    # system
    context = "nive_userdb.app.UserDB",
    translations="nive_userdb:locale/"
)

configuration.modules = [
    "nive_userdb.root", 
    "nive_userdb.user", 
    # session user cache
    "nive_userdb.extensions.sessionuser",
    # tools
    "nive.components.reform.reformed",
    "nive.tools.dbStructureUpdater",
    "nive.extensions.persistence.dbPersistenceConfiguration",
    # system administration
    "nive.components.adminview"

    # user actions
    # "nive_userdb.userview.view", -> removed default userviews by default.
    # user administration
    #"nive_userdb.useradmin.adminroot", -> removed system views by default.
    #"nive_userdb.useradmin", -> removed system views by default.
]

configuration.acl= [
    #(Allow, Everyone,         "signup"), # signup is disabled by default
    (Allow, Everyone,          "view"),
    (Allow, Authenticated,     "updateuser"),
    (Allow, "group:useradmin", "contactuser"),
    (Allow, "group:useradmin", "removeuser"),
    (Allow, "group:useradmin", "signup"),
    (Allow, "group:useradmin", "manage users"),
    (Allow, "group:admin",     ALL_PERMISSIONS),
    (Deny,  Everyone,          ALL_PERMISSIONS),
]

configuration.groups = [ 
    GroupConf(id="group:useradmin", name="group:useradmin"),
    GroupConf(id="group:admin", name="group:admin")
]

StagUser = 22


@implementer(IUserDatabase)
class UserDB(Application):
    """
    """

    def Groupfinder(self, userid, request=None, context=None):
        """
        returns the list of groups assigned to the user 
        """
        if request:
            try:
                user = request.environ["authenticated_user"]
            except (AttributeError, KeyError):
                user = self.root.GetUser(userid)
                if not hasattr(request, "environ"):
                    request.environ = dict()
                request.environ["authenticated_user"] = user
                def remove_user(request):
                    if "authenticated_user" in request.environ:
                        del request.environ["authenticated_user"]
                request.add_finished_callback(remove_user)
        else:
            user = self.root.GetUser(userid)

        if user is None:
            return None

        # users groups or empty list
        groups = user.groups or ()

        # lookup context for local roles
        if context is None and hasattr(request, "context"):
            context = request.context
        if context and ILocalGroups.providedBy(context):
            local = context.GetLocalGroups(userid, user=user)
            if not groups:
                return local
            return tuple(list(groups)+list(local))
        return groups


    def RememberLogin(self, request, user):
        """
        add login info to cookies or session. 
        """
        if not hasattr(request.response, "headerlist"):
            request.response.headerlist = []
        maxAge = self.configuration.cookieAuthMaxAge
        headers = remember(request, user, max_age=maxAge if maxAge else None)
        request.response.headerlist += list(headers)


    def ForgetLogin(self, request, url=None):
        """
        removes login info from cookies and session
        """
        if not hasattr(request.response, "headerlist"):
            setattr(request.response, "headerlist", [])
        headers = forget(request)
        request.response.headerlist += list(headers)
        #request.authenticate



def IsReservedUserName(name):
    """
    Check if name can be used for users
    """
    if not name:
        return True
    name = name.strip()
    if not name:
        return True
    name = name.lower()
    if name.startswith("group:"):
        return True
    return False


def UsernameValidator(node, value):
    """
    Validator which succeeds if the username does not exist.
    Can be used for the name input field in a sign up form.
    """
    Literal()(node, value)
    Length(min=5,max=40)(node, value)
    if IsReservedUserName(value):
        err = _("Username '${name}' already in use. Please choose a different name.", mapping={'name':value})
        raise Invalid(node, err)
    # lookup name in database
    c = node.widget.form.context
    if not IRoot.providedBy(c):
        root = c.root
    else:
        root = c
    u = root.search.Select(pool_type="user", parameter={"name": value}, fields=["id","name","email"], max=2, operators={"name":"="})
    if not u:
        u = root.search.Select(pool_type="user", parameter={"email": value}, fields=["id","name","email"], max=2, operators={"email":"="})
    if u:
        # check if its the current user
        ctx = node.widget.form.context
        if len(u)==1 and ctx.id == u[0][0]:
            return
        err = _("Username '${name}' already in use. Please choose a different name.", mapping={'name':value})
        raise Invalid(node, err)

def EmailValidator(node, value):
    """
    Validator which succeeds if the email does not exist.
    Can be used for the email input field in a sign up form.
    """
    # validate email format
    Email()(node, value)
    if IsReservedUserName(value):
        err = _("Email '${name}' already in use. Please choose a different email.", mapping={'name':value})
        raise Invalid(node, err)
    # lookup email in database
    c = node.widget.form.context
    if not IRoot.providedBy(c):
        root = c.root
    else:
        root = c
    u = root.search.Select(pool_type="user", parameter={"email": value}, fields=["id","name","email"], max=2, operators={"email":"="})
    if not u:
        u = root.search.Select(pool_type="user", parameter={"name": value}, fields=["id","name","email"], max=2, operators={"name":"="})
    if u:
        # check if its the current user
        ctx = node.widget.form.context
        if len(u)==1 and ctx.id == u[0][0]:
            return
        err = _("Email '${name}' already in use. Please choose a different email.", mapping={'name':value})
        raise Invalid(node, err)

def PasswordValidator(node, value):
    """
    Validator which succeeds if the username does not exist.
    Can be used for the name input field in a sign up form.
    """
    Length(min=5,max=30)(node, value)
    chars = ''.join(set(value))
    if len(chars)<5:
        err = _("Password is too simple. It should have at least 5 different characters.")
        raise Invalid(node, err)

def OldPwValidator(node, value):
    """
    Validator which succeeds if the current password matches.
    """
    user = node.widget.form.view.User(sessionuser=False)
    if not user.Authenticate(value):
        err = _("The old password does not match.")
        raise Invalid(node, err)

def AcceptValidator(node, value):
    """
    Validator which succeeds if the checkbox is ticked (true).
    """
    if not value==True:
        err = _("Please accept the terms and conditions.")
        raise Invalid(node, err)



from AuthEncoding import AuthEncoding
from binascii import b2a_base64

class SHA512DigestScheme:

    def encrypt(self, pw):
        return b2a_base64(hashlib.sha512(pw).digest())[:-1]

    def validate(self, reference, attempt):
        compare = b2a_base64(hashlib.sha512(attempt.encode("utf-8")).digest())[:-1]
        return AuthEncoding.constant_time_compare(compare, reference)

AuthEncoding.registerScheme("SHA512", SHA512DigestScheme())
