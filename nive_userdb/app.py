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
import copy

from nive.definitions import AppConf, FieldConf, GroupConf
from nive.definitions import implements, IUserDatabase, ILocalGroups
from nive.definitions import AllMetaFlds
from nive.security import Allow, Deny, Everyone, ALL_PERMISSIONS, remember, forget
from nive.components.objects.base import ApplicationBase
from nive_userdb.i18n import _

#@nive_module
configuration = AppConf(
    id = "userdb",
    title = _(u"Users"),
    context = "nive_userdb.app.UserDB",
    loginByEmail = False
)

# configuration.systemAdmin = (u"email", u"display name")
# configuration.admin = {"name": "admin", "password": "adminpass", "email": "admin@domain.com"}

configuration.modules = [
    "nive_userdb.root", 
    "nive_userdb.user", 
    # session user cache
    "nive_userdb.extensions.sessionuser",
    # user administration
    "nive_userdb.useradmin", 
    # tools
    "nive.tools.dbStructureUpdater", 
    # administration and persistence
    "nive.adminview",
    #"nive_userdb.persistence.dbPersistenceConfiguration"
]

configuration.acl= [
    (Allow, Everyone, 'view'),
    (Allow, Everyone, 'updateuser'),
    (Allow, "group:useradmin", 'signup'), 
    (Allow, "group:useradmin", 'manage users'),
    (Allow, "group:admin", ALL_PERMISSIONS),
]

configuration.groups = [ 
    GroupConf(id="group:useradmin", name="group:useradmin"),
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




    def AuthenticatedUser(self, request):
        # bw 0.9.6. removed in next version.
        name = self.UserName(request)
        return self.GetRoot().GetUserByName(name)

    def AuthenticatedUserName(self, request):
        # bw 0.9.6. removed in next version.
        return authenticated_userid(request)    

