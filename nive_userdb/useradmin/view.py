# Copyright 2012-2017 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

from nive_userdb.i18n import _
from nive.definitions import ViewModuleConf, ViewConf
from nive.components.iface.view import IFaceView
from nive.definitions import IUserDatabase
from nive.views import HTTPNotFound
from nive.components.adminview import view as adminview

from .iface import configuration as ifaceConf

# views configuration -------------------------------------------------
#@nive_module
configuration = ViewModuleConf("nive.components.iface.view.configuration",
    id = "useradmin",
    name = _("User management"),
    context = "nive_userdb.useradmin.adminroot.Adminroot",
    containment = IUserDatabase,
    view ="nive_userdb.useradmin.view.UsermanagementView",
    permission = "manage users",
    adminLink = "root_url",
    static = (
        {"path":"nive.components.iface:static/","name":"s-iface"}
    ),
    ifaceConf = ifaceConf,
    template = "nive.components.iface:templates/index.pt",
    assetsCustom = [ ]

)
b = "nive.components.iface:templates/"
t = "nive_userdb.useradmin:templates/"
configuration.views = [
    # Root views --------------------------------------------------------------------------------------
    ViewConf(name="", attr="default"),
    ViewConf(name="open", attr="open"),
    ViewConf(name="add", attr="add", renderer=b+"add.pt", permission="add"),
    ViewConf(name="@delete", attr="deletelist", renderer=b+"delete.pt", permission="delete"),
    ViewConf(name="viewlist", attr="view", renderer=t+"root.pt"),

    ViewConf(name="", attr="default", context="nive_userdb.user.Userobject"),
    ViewConf(name="view", attr="view", context="nive_userdb.user.Userobject", renderer=b+"view.pt"),
    ViewConf(name="edit", attr="edit", context="nive_userdb.user.Userobject", renderer=b+"edit.pt", permission="edit"),
    ViewConf(name="meta", attr="meta", context="nive_userdb.user.Userobject", renderer=b+"meta.pt"),
    ViewConf(name="options", attr="options", context="nive_userdb.user.Userobject", renderer=t+"options.pt"),
    ViewConf(name="deleteo", attr="delete", context="nive_userdb.user.Userobject", renderer=b+"delete.pt", permission="delete"),
]


class UsermanagementView(IFaceView):
    viewModuleID = "useradmin"

    def open(self):
        id = self.GetFormValue("id")
        obj = self.context.root.GetObj(id)
        if obj is None:
            return HTTPNotFound()
        url = self.FolderUrl(obj)+"edit"
        self.Redirect(url)

