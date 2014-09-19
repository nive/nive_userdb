# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

import hashlib
from datetime import datetime

from nive_userdb.i18n import _
from nive.definitions import implements, IUser

from nive.components.objects.base import ObjectBase



def Sha(password):
    return hashlib.sha224(password).hexdigest()


class user(ObjectBase):
    """
    User object with groups and login possibility. 
    """
    implements(IUser)
    
    @property
    def identity(self):
        return self.data.get(self.parent.identityField,str(self.id))

    def __str__(self):
        return str(self.identity)
    
    def Init(self):
        self.groups = tuple(self.data.get("groups",()))
        self.ListenEvent("commit", "OnCommit")


    def Authenticate(self, password):
        return Sha(password) == self.data["password"]

    
    def Activate(self, currentUser):
        """
        Activate user and remove activation id
        calls workflow commit, if possible

        signals event: activate
        """
        wf = self.GetWf()
        if wf:
            result = wf.Action("activate", self, user=currentUser)
        else:
            self.meta.set("pool_state", 1)
            self.data.set("token", "")
            self.data.set("tempcache", "firstrun")
            result = True
        if result:
            self.Signal("activate")
            self.Commit(currentUser)
        return result


    def Login(self):
        """
        events: login(lastlogin)
        """
        lastlogin = self.data.get("lastlogin")
        date = datetime.now()
        self.data.set("lastlogin", date)
        self.Commit(self)
        self.Signal("login", lastlogin=lastlogin)


    def Logout(self):
        """
        events: logout()
        """
        self.Signal("logout")
        self.Commit(self)


    def OnCommit(self):
        self.HashPassword()
        t = self.ReadableName()
        if t != self.meta["title"]:
            self.meta["title"] = t


    def HashPassword(self):
        if not self.data.HasTempKey("password"):
            return
        pw = Sha(self.data.password)
        self.data["password"] = pw


    def ReadableName(self):
        if self.data.surname or self.data.lastname: 
            return u" ".join([self.data.surname, self.data.lastname])
        return self.data.name


    def SecureUpdate(self, data, user):
        """
        Update existing user data.
        name, groups, pool_state cannot be changed
        """
        readonly = ("name","email","groups","pool_state","pool_wfa","token")
        for f in readonly:
            if f in data:
                del data[f]

        if not self.Update(data, user):
            return False, [_(u"Update failed.")]
        
        self.Commit(user)
        return True, []


    def UpdatePassword(self, password, user, resetActivation=True):
        """
        Update existing user data.
        name, groups, pool_state cannot be changed
        """
        self.data["password"] = password
        if resetActivation:
            self.data["token"] = u""
        self.Commit(user)
        return True, []


    def UpdateGroups(self, groups):
        """
        update groups of user
        """
        self.groups = tuple(groups)
        self.data["groups"] = self.groups
        return True


    def AddGroup(self, group, user=None):
        """
        add user to this group
        
        event: securityCahnged()
        """
        #bw 0.9.12 removed 'user' parameter and commit
        if group in self.groups:
            return True
        g = list(self.groups)
        g.append(group)
        self.groups = tuple(g)
        self.data["groups"] = g
        return True


    def RemoveGroup(self, group):
        """
        add user to this group
        
        event: securityCahnged()
        """
        if group not in self.groups:
            return True
        g = list(self.groups)
        g.remove(group)
        self.groups = tuple(g)
        self.data["groups"] = g
        return True


    def GetGroups(self, context=None):
        """
        Returns the users gloabal groups as tuple.
        Local assignments are not supported, `context` is currently unused.
        """
        return self.groups


    def InGroups(self, groups):
        """
        check if user has one of these groups
        """
        if isinstance(groups, basestring):
            return groups in self.groups
        for g in groups:
            if g in self.groups:
                return True
        return False


# user definition ------------------------------------------------------------------
from nive.definitions import StagUser, ObjectConf, FieldConf
from nive_userdb.app import UsernameValidator, EmailValidator

#@nive_module
configuration = ObjectConf(
    id = "user",
    name = _(u"User"),
    dbparam = "users",
    context = "nive_userdb.user.user",
    template = "user.pt",
    selectTag = StagUser,
    container = False,
    description = __doc__
)

configuration.data = (
    FieldConf(id="name",     datatype="string",      size= 30, default=u"", required=1, name=_(u"User ID"), description=u"",
              settings={"validator": UsernameValidator}),
    FieldConf(id="email",    datatype="email",       size=255, default=u"", required=1, name=_(u"Email"), description=u"",
              settings={"validator": EmailValidator}),
    FieldConf(id="password", datatype="password",    size=100, default=u"", required=1, name=_(u"Password"), description=u"",),
    FieldConf(id="groups",   datatype="mcheckboxes", size=255, default=u"", name=_(u"Groups"), settings={"codelist":"groups"}, description=u""),
    
    FieldConf(id="notify",   datatype="bool",        size= 4,  default=True, name=_(u"Activate email notifications"), description=u""),
    
    FieldConf(id="surname",  datatype="string",      size=100, default=u"", name=_(u"Surname"), description=u""),
    FieldConf(id="lastname", datatype="string",      size=100, default=u"", name=_(u"Lastname"), description=u""),
    FieldConf(id="organisation", datatype="string",  size=255, default=u"", name=_(u"Organisation"), description=u""),
    
    FieldConf(id="lastlogin",datatype="datetime",    size=0,   default=u"", name=_(u"Last login"), description=u""),
    FieldConf(id="token",    datatype="string",      size=30,  default=u"", name=_(u"Token for activation or password reset")),
    FieldConf(id="tempcache",datatype="string",      size=255, default=u"", name=_(u"Temp cache for additional verification data")),
)

configuration.forms = {
    "create": {"fields": ["name", "email", "password", "surname", "lastname"]},
    "edit":   {"fields": [FieldConf(id="password", name=_("Password"), datatype="password", required=False, settings={"update": True}),
                          "surname", "lastname"]},
}
