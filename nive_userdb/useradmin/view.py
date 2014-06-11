# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#


from pyramid.renderers import get_renderer, render, render_to_response

from nive_userdb.i18n import _
from nive.definitions import ViewConf, ViewModuleConf, Conf
from nive.definitions import IApplication, IUser


# view module definition ------------------------------------------------------------------

#@nive_module
configuration = ViewModuleConf(
    id = "useradmin",
    name = _(u"User management"),
    static = "",
    containment = "nive_userdb.useradmin.adminroot.adminroot",
    context = "nive_userdb.useradmin.adminroot.adminroot",
    view = "nive_userdb.useradmin.view.UsermanagementView",
    templates = "nive_userdb.useradmin:",
    permission = "manage users"
)
t = configuration.templates
configuration.views = [
    # User Management Views
    ViewConf(name = "",       attr = "view",   containment=IApplication, renderer = t+"root.pt"),
    ViewConf(name = "list",   attr = "view",   containment=IApplication, renderer = t+"root.pt"),
    ViewConf(name = "add",    attr = "add",    containment=IApplication, renderer = t+"add.pt"),
    ViewConf(name = "delete", attr = "delete", containment=IApplication, renderer = t+"delete.pt"),
    ViewConf(name = "",       attr = "edit",   context = IUser, renderer = t+"edit.pt"),
]


        
    
# view and form implementation ------------------------------------------------------------------

from nive.views import BaseView, Unauthorized, Mail
from nive.forms import ObjectForm, ValidationError
from nive_userdb.root import UsernameValidator

from nive.adminview.view import AdminBasics
    

class UsermanagementView(AdminBasics):
    
    
    def GetAdminWidgets(self):
        url = self.FolderUrl(self.context.dataroot)
        confs = [
            Conf(id="admin.root", viewmapper=url+"list", name=_(u"List users")),
            Conf(id="admin.add", viewmapper=url+"add", name=_(u"Add user"))
        ]
        return confs


    def view(self):
        return {}


    def add(self):
        name = self.context.app.GetObjectFld("name", "user").copy()
        name.settings["validator"] = UsernameValidator
        form = ObjectForm(loadFromType="user", view=self)
        form.subsets = {
            "create": {"fields":  [name, "password", "email", "groups", "surname", "lastname"], 
                       "actions": ["create"],
                       "defaultAction": "default"}
        }
        form.Setup(subset="create")
        result, data, action = form.Process(redirectSuccess="obj_url", pool_type="user")
        return {u"content": data, u"result": result, u"head": form.HTMLHead()}


    def edit(self):
        pwd = self.context.app.GetObjectFld("password", "user").copy()
        pwd.settings["update"] = True
        pwd.required = False
        form = ObjectForm(loadFromType="user", subset="edit", view=self)
        def removepasswd(data, obj):
            try:
                del data["password"]
            except:
                pass
        form.ListenEvent("loadDataObj", removepasswd)
        form.subsets = {
            "edit":   {"fields":  [pwd, "email", "groups", "surname", "lastname"], 
                       "actions": ["edit"],
                       "defaultAction": "defaultEdit"},
        }        
        form.Setup(subset="edit")
        result, data, action = form.Process()#, redirectSuccess="obj_url")
        return {u"content": data, u"result": result, u"head": form.HTMLHead()}
            
    
    def delete(self):
        ids = self.GetFormValue("ids")
        confirm = self.GetFormValue("confirm")
        users = []
        msgs = []
        root = self.context.dataroot
        if isinstance(ids, basestring):
            ids = (ids,)
        elif not ids:
            ids = ()
        for i in ids:
            u = root.GetUserByID(i, activeOnly=0)
            if not u:
                msgs.append(self.Translate(_(u"User not found. (id %(name)s)", mapping={"name": i})))
            else:
                users.append(u)
        result = True
        if confirm:
            for u in users:
                name = u.data.name
                if not root.Delete(id=u.id, obj=u, user=self.User()):
                    result = False
                    msgs.append(self.Translate(_(u"Delete failed: User '%(name)s'", mapping={"name": u.meta.title})))
            users=()
            if result:
                if len(ids)>1:
                    msgs.append(self.Translate(_(u"OK. Users deleted.")))
                else:
                    msgs.append(self.Translate(_(u"OK. User deleted.")))
            return self.Redirect(self.Url(root), msgs)
        return {"ids": ids, "users":users, "result": result, "msgs": msgs, "confirm": confirm} 
    







