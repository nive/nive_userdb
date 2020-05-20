# Copyright 2012-2017 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

from nive.definitions import ViewConf, ViewModuleConf, Conf, FieldConf
from nive.definitions import IApplication, IUser

from nive.components.reform.widget import RadioChoiceWidget

from nive_userdb.i18n import _

# view module definition ------------------------------------------------------------------

#@nive_module
configuration = ViewModuleConf("nive.components.adminview.view",
    id = "useradmin",
    name = _("User management"),
    containment = IApplication,
    context = "nive_userdb.useradmin.adminroot.adminroot",
    view = "nive_userdb.useradmin.view.UsermanagementView",
    templates = "nive_userdb.useradmin:",
    template = "nive.components.adminview:index.pt",
    permission = "manage users",
    # user interface configuration
    adminLink = "app_folder_url/usermanagement",
    listfields = ("pool_state","name","email","groups","lastlogin","id"),
    addfields = ("name","password","email","groups"),
    editfields = (FieldConf(id="pool_state", name=_("Active"), datatype="bool",
                            widget=RadioChoiceWidget(values=(("true", _("Yes")),("false", _("No"))))),
                  "name",
                  FieldConf(id="password", name=_("Password"), datatype="password", settings={"update": True}),
                  "email","groups"),
    searchfields = ("name","email","groups")
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

from nive.components.reform.forms import ObjectForm, HTMLForm
from nive_userdb.app import UsernameValidator

from nive.components.adminview.view import AdminBasics
    

class UsermanagementView(AdminBasics):
    
    
    def GetAdminWidgets(self):
        url = self.FolderUrl(self.context.root)
        confs = [
            Conf(id="admin.root", viewmapper=url+"list", name=_("List")),
            Conf(id="admin.add", viewmapper=url+"add", name=_("Add"))
        ]
        return confs


    def view(self):
        flds = self.configuration.searchfields
        form = HTMLForm(loadFromType="user", view=self, autofill="off")
        form.actions = [
            Conf(id="default", method="StartForm", name="Initialize", hidden=True),
            Conf(id="search",  method="ReturnDataOnSuccess", name="Aktualisieren", css_class="btn btn-info", hidden=False),
        ]
        form.fields = flds
        #settings["widget.item_template"]
        form.Setup()
        result, formvalues = form.Extract(self.request, removeNull=True, removeEmpty=True)
        formhtml = dict()
        for f in flds:
            form = HTMLForm(loadFromType="user", view=self, autofill="off")
            form.actions = []
            form.fields = [f]
            form.widget.item_template = "field_nolabel"
            form.Setup()
            form._c_fields[0].settings["css_class"] = "form-control form-control-sm"
            formhtml[form._c_fields[0].id] = form.RenderBody(formvalues, msgs=None, errors=None, result=None)

        listfields = [self.context.app.configurationQuery.GetFld(f, 'user') for f in self.configuration.listfields]
        sort = self.EscapeSortField(self.configuration.listfields)
        asc = '1' if self.GetFormValue('ac', '1') == '1' else '0'
        start = self.GetFormValue('st', '0')
        users = self.context.search.SearchType("user",
                                               parameter=formvalues,
                                               operators=dict(groups="LIKE",name="LIKE",email="LIKE"),
                                               fields=listfields,
                                               sort=sort or "name",
                                               ascending=int(asc),
                                               start=start,
                                               max=100,
                                               skipRender=())

        searchvalues = dict(so=sort, st=start, ac=asc)
        return dict(formhtml=formhtml, formvalues=formvalues, fields=listfields, users=users, searchvalues=searchvalues)


    def add(self):
        name = self.context.app.configurationQuery.GetObjectFld("name", "user").copy()
        name.settings["validator"] = UsernameValidator
        form = ObjectForm(loadFromType="user", view=self, autofill="off")
        form.subsets = {
            "create": {"fields": self.configuration.addfields,
                       "actions": [
                           Conf(id="create", method="CreateObj", name=_("Add user"),     hidden=False, css_class="btn btn-primary"),
                       ],
                       "defaultAction": "default"}
        }
        form.Setup(subset="create")
        result, data, action = form.Process(pool_type="user", redirectSuccess="obj_url")
        return {"content": data, "result": result, "head": form.HTMLHead()}


    def edit(self):
        pwd = self.context.app.configurationQuery.GetObjectFld("password", "user").copy()
        pwd.settings["update"] = True
        pwd.required = False
        form = ObjectForm(loadFromType="user", subset="edit", view=self, autofill="off")
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
        result, data, action = form.Process(redirectSuccess="obj_url")
        return {"content": data, "result": result, "head": form.HTMLHead()}
            
    
    def delete(self):
        ids = self.GetFormValue("ids")
        confirm = self.GetFormValue("confirm")
        users = []
        msgs = []
        root = self.context.root
        if isinstance(ids, str):
            ids = (ids,)
        elif not ids:
            ids = ()
        for i in ids:
            u = root.GetUserByID(i, activeOnly=0)
            if not u:
                msgs.append(self.Translate(_("User not found. (id %(name)s)", mapping={"name": i})))
            else:
                users.append(u)
        result = True
        if confirm:
            for u in users:
                name = u.data.name
                if not root.Delete(id=u.id, obj=u, user=self.User()):
                    result = False
                    msgs.append(self.Translate(_("Delete failed: User '%(name)s'", mapping={"name": u.meta.title})))
            users=()
            if result:
                if len(ids)>1:
                    msgs.append(self.Translate(_("OK. Users deleted.")))
                else:
                    msgs.append(self.Translate(_("OK. User deleted.")))
            return self.Redirect(self.Url(root), msgs)
        return {"ids": ids, "users":users, "result": result, "msgs": msgs, "confirm": confirm} 
    

    def PageUrls(self, items, searchvalues):
        """
        if paged result the previous, next and set links
        """
        if items.get('total', 0) == 0:
            return ""

        sort = searchvalues.get("so")
        ascending = searchvalues.get("ac")

        # pages
        url = self.CurrentUrl()
        start = items.get("start")
        maxPage = items.get("max")
        total = items.get("total")
        pageCount = int(total / maxPage) + (total % maxPage != 0)
        pageHtml = ""

        if total <= maxPage:
            return ""

        cntstr = "%d - %d / %d"
        cnt = cntstr % (items.get('start')+1, items.get('start')+items.get('count'), items.get('total'))
        pageTmpl = """ <a href="%s?st=%s&so=%s&as=%s">%s</a> """
        prev = pageTmpl % (url, items.get("prev"), sort, ascending, "&laquo;")
        next = pageTmpl % (url, items.get("next"), sort, ascending, "&raquo;")
        pageTmpl1 = """ [%s] """

        if items.get("start")==0:
            prev = "&laquo;"
        if items.get("next")==0:
            next = "&raquo;"

        if pageCount > 1:
            current = int(start / maxPage)
            count = 10
            pages = [0]
            first = current - int(count / 2) + 1
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
            prev = ""
            next = ""

        html = """<div class="paging"><div>%s %s %s %s</div></div>""" % (cnt, prev, pageHtml, next)
        return html



    def EscapeSortField(self, fields):
        sort = self.GetFormValue("so","name")
        if not sort in [f if isinstance(f, str) else f.id for f in fields]:
            return "name"
        return sort




