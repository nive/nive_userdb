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
    configuration.systemAdmin = (u"email", u"display name")

"""
import hashlib


from nive.definitions import AppConf, GroupConf, Conf
from nive.definitions import implements, IUserDatabase, ILocalGroups
from nive.security import Allow, Deny, Everyone, ALL_PERMISSIONS, remember, forget
from nive.components.objects.base import ApplicationBase
from nive.views import Mail
from nive.components.reform.schema import Invalid
from nive.components.reform.schema import Email
from nive.components.reform.schema import Literal, Length

from nive_userdb.i18n import _

#@nive_module
configuration = AppConf(
    id = "userdb",
    title = _(u"Users"),

    # signup settings
    loginByEmail = True,
    settings = Conf(
        groups=(),
        activate=1,
        generatePW=0
    ),
    #userAdmin = (u"admin@mymail.com", u"Admin"),  # contact system information
    #admin = {"name": "adminusername", "password": "adminpass", "email": "u"admin@mymail.com""}, # admin login

    # mails
    mailSignup = Mail(_(u"Signup confirmed"), "nive_userdb:userview/mails/signup.pt"),
    mailNotify = Mail(_(u"Signup notification"), "nive_userdb:userview/mails/notify.pt"),
    mailVerifyMail = Mail(_(u"Verify your new e-mail"), "nive_userdb:userview/mails/verifymail.pt"),
    mailResetPass = Mail(_(u"Your new password"), "nive_userdb:userview/mails/resetpass.pt"),
    mailSendPass = Mail(_(u"Your password"), "nive_userdb:userview/mails/mailpass.pt"),

    # messages customizations
    #welcomeMessage = u"",

    # sessionuser field cache
    sessionuser = ("name", "email", "surname", "lastname", "groups", "notify", "lastlogin"),

    # system
    context = "nive_userdb.app.UserDB",
    translations="nive_userdb:locale/"
)

# configuration.systemAdmin = (u"email", u"display name")
# configuration.admin = {"name": "admin", "password": "adminpass", "email": "admin@domain.com"}

configuration.modules = [
    "nive_userdb.root", 
    "nive_userdb.user", 
    # session user cache
    "nive_userdb.extensions.sessionuser",
    # user actions
    "nive_userdb.userview.view",
    # user administration
    "nive_userdb.useradmin", 
    # tools
    "nive.tools.dbStructureUpdater", 
    # administration and persistence
    "nive.adminview",
    "nive.extensions.persistence.dbPersistenceConfiguration"
]

configuration.acl= [
    (Allow, Everyone, 'signup'),
    (Allow, Everyone, 'view'),
    (Allow, Everyone, 'updateuser'),
    (Allow, "group:useradmin", 'signup'), 
    (Allow, "group:useradmin", 'manage users'),
    (Allow, "group:admin", ALL_PERMISSIONS),
]

configuration.groups = [ 
    GroupConf(id="group:useradmin", name="group:useradmin"),
    GroupConf(id="group:admin", name="group:admin")
]


class UserDB(ApplicationBase):
    """
    """
    implements(IUserDatabase)


        
    def Groupfinder(self, userid, request=None, context=None):
        """
        returns the list of groups assigned to the user 
        """
        if request:
            try:
                user = request.environ["authenticated_user"]
            except:
                user = self.root().GetUser(userid)
                request.environ["authenticated_user"] = user
                def remove_user(request):
                    if "authenticated_user" in request.environ:
                        del request.environ["authenticated_user"]
                request.add_finished_callback(remove_user)
        else:
                user = self.root().GetUser(userid)
        if not user:
            return None

        # users groups or empty list
        groups = user.groups or ()

        # lookup context for local roles
        if not context and hasattr(request, "context"):
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
        headers = remember(request, user)
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
    if name.startswith(u"group:"):
        return True
    return False


def UsernameValidator(node, value):
    """
    Validator which succeeds if the username does not exist.
    Can be used for the name input field in a sign up form.
    """
    Literal()(node, value)
    Length(min=5,max=30)(node, value)
    if IsReservedUserName(value):
        err = _(u"Username '${name}' already in use. Please choose a different name.", mapping={'name':value})
        raise Invalid(node, err)
    # lookup name in database
    r = node.widget.form.context.root()
    u = r.Select(pool_type=u"user", parameter={u"name": value}, fields=[u"id",u"name",u"email"], max=2, operators={u"name":u"="})
    if not u:
        u = r.Select(pool_type=u"user", parameter={u"email": value}, fields=[u"id",u"name",u"email"], max=2, operators={u"email":u"="})
    if u:
        # check if its the current user
        ctx = node.widget.form.context
        if len(u)==1 and ctx.id == u[0][0]:
            return
        err = _(u"Username '${name}' already in use. Please choose a different name.", mapping={'name':value})
        raise Invalid(node, err)

def EmailValidator(node, value):
    """
    Validator which succeeds if the email does not exist.
    Can be used for the email input field in a sign up form.
    """
    # validate email format
    Email()(node, value)
    if IsReservedUserName(value):
        err = _(u"Email '${name}' already in use. Please use the sign in form if you already have a account.", mapping={'name':value})
        raise Invalid(node, err)
    # lookup email in database
    r = node.widget.form.context.root()
    u = r.Select(pool_type=u"user", parameter={u"email": value}, fields=[u"id",u"name",u"email"], max=2, operators={u"email":u"="})
    if not u:
        u = r.Select(pool_type=u"user", parameter={u"name": value}, fields=[u"id",u"name",u"email"], max=2, operators={u"name":u"="})
    if u:
        # check if its the current user
        ctx = node.widget.form.context
        if len(u)==1 and ctx.id == u[0][0]:
            return
        err = _(u"Email '${name}' already in use. Please use the sign in form if you already have a account.", mapping={'name':value})
        raise Invalid(node, err)


def Sha(password):
    return hashlib.sha224(password).hexdigest()

def Md5(password):
    return hashlib.md5(password).hexdigest()

