# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
Root for public user functions
-------------------------------------------
Provides functionality to safely add users with several activation and 
mailing options.
"""

import base64, random
import uuid
import json

from nive.definitions import RootConf, Conf, StagUser, IUser
from nive.definitions import ConfigurationError
from nive.security import User, AdminUser, IAdminUser, UserFound, Unauthorized
from nive.components.objects.base import RootBase
from nive_userdb.i18n import _


class root(RootBase):
    """
    """
    
    # field used as unique user identity internally in sessions and cache
    identityField = u"name"
    
    # User account handling ------------------------------------------------------------------------------------------------------

    def AddUser(self, data, activate=None, generatePW=None, generateName=None, mail="default", notifyMail="default", groups=None, currentUser=None, **kw):
        """
        Create a new user with groups for login with name/password ::

            data: user data as dictionary. groups and pool_state are removed. 
            activate: directly activate the user for login (pool_state=1)
            generatePW: generate a random password to be send by mail
            generateName: generate a unique id to be used as username
            mail: mail object template for confirmation mail
            notifyMail: mail object template for notify mail
            groups: initially assign groups to the user
            currentUser: the currently logged in user for pool_createdby and workflow
    
        returns tuple: the user object if succeeds and report list
        """
        report = []

        if generateName is None:
            generateName = self.app.configuration.settings.generateName
        if generateName:
            # generate a short uuid name
            name = self.GenerateID(15)
            exists = self.GetUserByName(name, activeOnly=0)
            while exists:
                name = self.GenerateID(15)
                exists = self.GetUserByName(name, activeOnly=0)
            data["name"] = name
        else:
            name = data.get("name")
        
        if not name or name == "":
            report.append(_(u"Please enter your username"))
            return None, report

        # check user with name exists
        user = self.GetUserByName(name, activeOnly=0)
        if user:
            report.append(_(u"Username '${name}' already in use. Please choose a different name.", mapping={u"name":name}))
            return None, report
        email = data.get("email")
        if email and self.app.configuration.get("loginByEmail"):
            user = self.GetUserByMail(email, activeOnly=0)
            if user:
                report.append(_(u"Email '${name}' already in use. ", mapping={'name':email}))
                return None, report
        
        if generatePW is None:
            generatePW = self.app.configuration.settings.generatePW
        if groups is None:
            groups = self.app.configuration.settings.groups
        if activate is None:
            activate = self.app.configuration.settings.activate

        if generatePW:
            pw = self.GeneratePassword()
            data["password"] = pw

        if groups:
            data["groups"] = groups

        if not "token" in data:
            token = self.GenerateID(30)
            data["token"] = token

        data["pool_type"] = u"user"
        data["pool_state"] = int(activate)
        data["pool_stag"] = StagUser

        if not currentUser:
            currentUser = User(name)
        obj = self.Create("user", data=data, user=currentUser)
        if not obj:
            report.append(_(u"Sorry. Account could not be created."))
            return None, report
        #obj.Commit(currentUser)
        
        app = self.app
        if mail=="default":
            mail = app.configuration.mailSignup
        if mail:
            title = mail.title
            body = mail(user=obj, **kw)
            tool = app.GetTool("sendMail")
            if not tool:
                raise ConfigurationError, "Mail tool 'sendMail' not found"
            result, value = tool(body=body, title=title, recvids=[str(obj)], force=1)
            if not result:
                report.append(_(u"The email could not be sent."))
                return None, report

        sysadmin = app.configuration.get("userAdmin")
        if sysadmin:
            if notifyMail=="default":
                notifyMail = self.app.configuration.mailNotify
            if notifyMail:
                title = notifyMail.title
                body = notifyMail(user=obj)
                tool = app.GetTool("sendMail")
                if not tool:
                    raise ConfigurationError, "Mail tool 'sendMail' not found"
                result, value = tool(body=body, title=title, recvmails=[sysadmin], force=1)

        report.append(_(u"Account created."))
        return obj, report


    # Login/logout and user sessions ------------------------------------------------------------------------------------------------------

    def Login(self, name, password, raiseUnauthorized = 1):
        """
        returns user/none and report list
        """
        report = []

        # session login
        user = self.GetUserByName(name)
        if not user:
            if raiseUnauthorized:
                raise Unauthorized, "Login failed"
            report.append(_(u"Sign in failed. Please check your username and password."))
            return None, report
            
        if not user.Authenticate(password):
            if raiseUnauthorized:
                raise Unauthorized, "Login failed"
            report.append(_(u"Sign in failed. Please check your username and password."))
            return None, report

        # call user
        user.Login()
        report.append(_(u"You are now signed in."))
        return user, report


    def Logout(self, ident):
        """
        Logout and delete session data
        """
        if not ident:
            return False
        user = self.GetUser(ident)
        if not user:
            return False
        if not IUser.providedBy(user):
            user = self.LookupUser(id=user.id)
        if user:
            user.Logout()
        return True


    # changing credentials --------------------------------------------------------------------

    def MailVerifyNewEmail(self, name, newmail, mail="default", currentUser=None, **kw):
        """
        returns status and report list
        """
        report=[]

        if not newmail:
            report.append(_(u"Please enter your new email address."))
            return False, report

        if isinstance(name, basestring):
            obj = self.GetUserByName(name)
            if not obj:
                report.append(_(u"No matching account found."))
                return False, report
        else:
            obj = name

        recv = [(newmail, obj.meta.get("title"))]

        token = self.GenerateID(20)
        obj.data["token"] = token
        obj.data["tempcache"] = "verifymail:"+newmail
        obj.Commit(user=currentUser)

        app = self.app
        if mail=="default":
            mail = self.app.configuration.mailVerifyMail
        title = mail.title
        body = mail(user=obj, **kw)
        tool = app.GetTool("sendMail")
        if not tool:
            raise ConfigurationError, "Mail tool 'sendMail' not found"
        result, value = tool(body=body, title=title, recvmails=recv, force=1)
        if not result:
            report.append(_(u"The email could not be sent."))
            return None, report

        report.append(_(u"The link to verify your new email has been sent by mail."))
        return obj, report


    def MailUserPass(self, name, mail="default", newPassword=None, currentUser=None, **kw):
        """
        Mails a new password or the current password in plain text.

        returns status and report list
        """
        report=[]

        if not name:
            report.append(_(u"Please enter your email address or username."))
            return False, report

        if isinstance(name, basestring):
            obj = self.GetUserByName(name)
            if not obj:
                report.append(_(u"No matching account found. Please try again."))
                return False, report
        else:
            obj = name

        email = obj.data.get("email")
        title = obj.meta.get("title")
        if email == "":
            report.append(_("No email address found."))
            return False, report
        recv = [(email, title)]

        if not newPassword:
            pwd = self.GenerateID(5)
        else:
            pwd = newPassword
        obj.data["password"] = pwd

        if mail=="default":
            try:
                mail = self.app.configuration.mailSendPass
            except AttributeError, e:
                raise ConfigurationError, str(e)

        title = mail.title
        body = mail(user=obj, password=pwd, **kw)
        tool = self.app.GetTool("sendMail")
        if not tool:
            raise ConfigurationError, "Mail tool 'sendMail' not found"
        result, value = tool(body=body, title=title, recvmails=recv, force=1)
        if not result:
            report.append(_(u"The email could not be sent."))
            return False, report

        obj.Commit(user=currentUser)

        report.append(_(u"The new password has been sent to your email address. Please sign in and change it."))
        return True, report


    def MailResetPass(self, name, mail="default", currentUser=None, **kw):
        """
        returns status and report list
        """
        report=[]

        if not name:
            report.append(_(u"Please enter your sign in name or email address."))
            return None, report

        if isinstance(name, basestring):
            obj = self.GetUserByName(name)
            if not obj:
                report.append(_(u"No matching account found."))
                return None, report
        else:
            obj = name

        email = obj.data.get("email")
        if not email:
            report.append(_("No email address found."))
            return None, report
        recv = [(email, obj.meta.title)]

        token = self.GenerateID(25)
        obj.data["token"] = token
        obj.Commit(user=currentUser)

        app = self.app
        if mail=="default":
            try:
                mail = self.app.configuration.mailResetPass
            except AttributeError, e:
                raise ConfigurationError, str(e)
        if not mail:
            raise ConfigurationError("Required  mailtemplate is required")
        title = mail.title
        body = mail(user=obj, **kw)
        tool = app.GetTool("sendMail")
        if not tool:
            raise ConfigurationError, "Mail tool 'sendMail' not found"
        result, value = tool(body=body, title=title, recvmails=recv, force=1)
        if not result:
            report.append(_(u"The email could not be sent."))
            return None, report

        report.append(_(u"The link to reset your password has been sent to your email address."))
        return obj, report


    def DeleteUser(self, ident, currentUser=None):
        """
        returns status and report list
        """
        report = []
        if not ident:
            report.append(_(u"Invalid user."))
            return False, report
        elif isinstance(ident, basestring):
            if not ident:
                report.append(_(u"Invalid user."))
                return False, report

            user = self.LookupUser(ident=ident, activeOnly=0)
            if not user:
                report.append(_(u"Invalid username."))
                return False, report
        else:
            user = ident

        if IAdminUser.providedBy(user):
            report.append(_(u"You cannot delete the admin user."))
            return False, report

        self.Logout(user)
        if not self.Delete(user.id, obj=user, user=currentUser):
            report.append(_(u"Sorry. An error occurred."))
            return False, report

        report.append(_(u"User deleted."))
        return True, report


    # Password, token ------------------------------------------------------------------------------------------------------

    def GenerateID(self, length=20, repl="-"):
        # generates a id
        return str(uuid.uuid4()).replace(repl,"")[:length]
        

    def GeneratePassword(self, mincount=5, maxcount=5):
        # generates a password
        vowels = u"aeiou0123456789#*"
        consonants = u"bcdfghjklmnpqrstvwxyz"
        password = u""

        for x in range(1,random.randint(mincount+1,maxcount+1)):
            if random.choice([1,0]):
                consonant = consonants[random.randint(1,len(consonants)-1)]
                if random.choice([1,0]):
                    consonant = consonant.upper()
                password=password + consonant
            else:
                vowel = vowels[random.randint(1,len(vowels)-1)]
                password=password + vowel

        return password


    # user lookup ------------------------------------------------------------------------------------------------------

    def GetUser(self, ident, activeOnly=1):
        """
        Lookup user by *user identity* as used in session cookies for example.
        Returns the cached session user if available, not the 'real' user object.
        Use `LookupUser()` to make sure the user is actually looked in the database.
        
        events: 
        - getuser(ident, activeOnly)
        - loaduser(user)
        """
        try:
            self.Signal("getuser", ident=ident, activeOnly=activeOnly)
        except UserFound, user:
            return user.user
        user = self.LookupUser(ident=ident, activeOnly=activeOnly)
        if user:
            self.Signal("loaduser", user=user)
        return user
    

    def GetUserByName(self, name, activeOnly=1):
        """ """
        return self.LookupUser(name=name, activeOnly=activeOnly)


    def GetUserByMail(self, email, activeOnly=1):
        """ """
        return self.LookupUser(email=email, activeOnly=activeOnly)


    def GetUserByID(self, id, activeOnly=1):
        """ """
        return self.LookupUser(id=id, activeOnly=activeOnly)


    def GetUserByFilename(self, filename, activeOnly=1):
        """
        Look up a user by filename (meta.pool_filename). Use this function only if your application explicitly manages
        unique user filenames. By default filenames are not used at all.
        """
        ident = self.Select(pool_type=u"user", parameter={"pool_filename":filename}, fields=[u"id"], max=2)
        if len(ident)>1:
            raise ValueError, "Filename is not unique"
        if not len(ident):
            return None
        return self.LookupUser(id=ident[0][0], activeOnly=activeOnly)


    def LookupUser(self, id=None, ident=None, name=None, email=None, activeOnly=1, reloadFromDB=0):
        """ 
        reloadFromDB deprecated. will be removed in the future
        """
        if not id:
            loginByEmail = self.app.configuration.get("loginByEmail", True)
            # lookup adminuser
            admin = self.app.configuration.get("admin")
            if admin:
                if ident and ident == admin.get(self.identityField):
                    return AdminUser(admin, admin[self.identityField])
                elif name and name == admin["name"]:
                    return AdminUser(admin, admin.get(self.identityField))
                elif loginByEmail and email and email == admin["email"]:
                    return AdminUser(admin, admin.get(self.identityField))
            # lookup id for name, email or ident
            param = {}
            if activeOnly:
                param[u"pool_state"] = 1
            if name:
                param[u"name"] = name
            elif email:
                param[u"email"] = email
            elif ident:
                if not self.identityField:
                    raise ValueError, "user identity field not set"
                param[self.identityField] = ident

            user = self.Select(pool_type=u"user", parameter=param, fields=[u"id"], max=2)
            
            # check multiple identity fields
            if len(user)==0 and loginByEmail:
                if name:
                    del param[u"name"]
                    param[u"email"] = name
                    user = self.Select(pool_type=u"user", parameter=param, fields=[u"id"], max=2)
                elif email:
                    del param[u"email"]
                    param[u"name"] = email
                    user = self.Select(pool_type=u"user", parameter=param, fields=[u"id"], max=2)
                else:
                    return None

            if len(user)!=1:
                return None
            id = user[0][0]
            
        user = self.GetObj(id)
        if not user or (activeOnly and not user.meta.get("pool_state")==1):
            return None
        return user
    

    def GetUserForToken(self, token, activeOnly=True):
        """
        Looks up the user for the token
        requires fld token in user record
        returns tuple: the user object or None
        """
        if not token:
            return None

        p = {"token": token}
        if activeOnly:
            p["pool_state"] = 1
        users = self.Select(pool_type=u"user",
                            parameter=p,
                            fields=[u"id"],
                            max=2)
        if len(users) != 1:
            return None
        id = users[0][0]
        obj = self.GetObj(id)
        return obj


    # user infos -----------------------------------------------------------------------

    def GetUsers(self, **kw):
        """
        """
        fields = [u"id", u"name", u"email", u"title", u"groups", u"lastlogin"]
        if not self.identityField in fields:
            fields.append(self.identityField)
        return self.SearchType(u"user", {u"pool_state":1}, fields)


    def GetUserInfos(self, userids, fields=None, activeOnly=True):
        """
        """
        param = {self.identityField:userids}
        if activeOnly:
            param[u"pool_state"] = 1
        if not fields:
            fields = [u"id", u"name", u"email", u"title", u"groups", u"lastlogin"]
        if not self.identityField in fields:
            fields = list(fields)
            fields.append(self.identityField)
        return self.SelectDict(pool_type=u"user", 
                               parameter=param, fields=fields, operators={self.identityField:u"IN"})

    
    def GetUsersWithGroup(self, group, fields=None, activeOnly=True):
        """
        """
        param = {u"groups":group}
        if activeOnly:
            param[u"pool_state"] = 1
        operators = {u"groups": "LIKE"}
        if not fields:
            fields = [u"name",u"groups"]
        elif not u"groups" in fields:
            fields = list(fields)
            fields.append(u"groups")
        users = self.SelectDict(pool_type=u"user", parameter=param, fields=fields, operators=operators)
        # verify groups
        verified = []
        for u in users:
            try:
                g = json.loads(u["groups"])
            except ValueError:
                continue
            if group in g:
                verified.append(u)
        return verified


    # to be removed ------------------------------------------------------
    def GetUserGroups(self, name, activeOnly=1):
        """
        """
        user = self.GetUser(name, activeOnly=activeOnly)
        if not user:
            return None
        return user.data.groups

    def Encrypt(self, string):
        try:
            return base64.encodestring(string)
        except:
            return string

    def Decrypt(self, string):
        try:
            return base64.decodestring(string)
        except:
            return string




# Root definition ------------------------------------------------------------------

#@nive_module
configuration = RootConf(
    id = "udb",
    context = "nive_userdb.root.root",
    template = "root.pt",
    default = 1,
    subtypes = "*",
    name = _(u"User account"),
    description = __doc__
)

