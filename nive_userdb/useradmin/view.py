# Copyright 2012-2017 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

from nive.definitions import ViewConf, ViewModuleConf, Conf, FieldConf
from nive.definitions import IApplication, IUser

from nive.components.reform.widget import RadioChoiceWidget

from nive_userdb.i18n import _

# view module definition ------------------------------------------------------------------

#@nive_module
configuration = ViewModuleConf("nive.adminview.view",
    id = "useradmin",
    name = _(u"User management"),
    containment = IApplication,
    context = "nive_userdb.useradmin.adminroot.adminroot",
    view = "nive_userdb.useradmin.view.UsermanagementView",
    templates = "nive_userdb.useradmin:",
    template = "nive.adminview:index.pt",
    permission = "manage users",
    # user interface configuration
    listfields = ("pool_state","name","email","groups","lastlogin","id"),
    addfields = ("name","password","email","groups"),
    editfields = (FieldConf(id="pool_state", name=_("Active"), datatype="bool",
                            widget=RadioChoiceWidget(values=((u"true", _(u"Yes")),(u"false", _(u"No"))))),
                  "name",
                  FieldConf(id="password", name=_("Password"), datatype="password", settings={"update": True}),
                  "email","groups")
)
t = configuration.templates
configuration.views = [
    # User Management Views
    ViewConf(name="",       attr="view",   renderer=t+"root.pt"),
    ViewConf(name="list",   attr="view",   renderer=t+"root.pt"),
    ViewConf(name="add",    attr="add",    renderer=t+"add.pt"),
    ViewConf(name="delete", attr="delete", renderer=t+"delete.pt"),
    ViewConf(name="",       attr="edit",   context=IUser, containment="nive_userdb.useradmin.adminroot.adminroot", renderer=t+"edit.pt"),
]


        
    
# view and form implementation ------------------------------------------------------------------

from nive.forms import ObjectForm
from nive_userdb.app import UsernameValidator

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
            "create": {"fields": self.configuration.addfields,
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
            "edit":   {"fields": self.configuration.editfields,
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
    

    def PageUrls(self, items, sort, ascending):
        """
        if paged result the previous, next and set links
        """
        if items.get('total', 0) == 0:
            return u""

        # pages
        url = self.CurrentUrl()
        start = items.get("start")
        maxPage = items.get("max")
        total = items.get("total")
        pageCount = total / maxPage + (total % maxPage != 0)
        pageHtml = u""

        if total <= maxPage:
            return u""

        cntstr = u"%d - %d / %d"
        cnt = cntstr % (items.get('start')+1, items.get('start')+items.get('count'), items.get('total'))
        pageTmpl = u""" <a href="%s?st=%s&so=%s&as=%s">%s</a> """
        prev = pageTmpl % (url, items.get("prev"), sort, ascending, "&laquo;")
        next = pageTmpl % (url, items.get("next"), sort, ascending, "&raquo;")
        pageTmpl1 = u""" [%s] """

        if items.get("start")==0:
            prev = u"&laquo;"
        if items.get("next")==0:
            next = u"&raquo;"

        if pageCount > 1:
            current = int(start / maxPage)
            count = 10
            pages = [0]
            first = current - count / 2 + 1
            if first < 1:
                first = 1
            elif pageCount < count:
                first = 1
                count = pageCount
            elif first + count > pageCount - 1:
                first = pageCount - count
            for i in range(count - 1):
                p = first + i
                if p == pageCount - 1:
                    break
                pages.append(p)
            pages.append(pageCount - 1)

            # loop pages
            for i in pages:
                # check curent page
                if start >= maxPage * i and start <= maxPage * i:
                    pageHtml = pageHtml + pageTmpl1 % (str(i + 1))
                else:
                    pageHtml = pageHtml + pageTmpl % (url, maxPage * i, sort, ascending, str(i + 1))
        else:
            prev = u""
            next = u""

        html = u"""<div class="paging"><div>%s %s %s %s</div></div>""" % (cnt, prev, pageHtml, next)
        return html


    def EscapeSortField(self, fields):
        sort = self.GetFormValue("so","name")
        if not sort in fields:
            return "name"
        return sort




