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
    adminLink = "root_folder_url",
    static = (
        {"path":"nive.components.iface:static/","name":"s-iface"}
    ),
    ifaceConf = ifaceConf,
    template = "nive.components.iface:templates/index.pt",
    assetsCustom = [ ]

)

t = "nive_userdb.useradmin:templates/"
configuration.views += [
    ViewConf(name="",        attr="default"),
    ViewConf(name="viewlist",attr="view", renderer=t+"root.pt"),
    ViewConf(name="options", attr="options", context="nive_userdb.user.Userobject", renderer=t+"options.pt"),
]


class UsermanagementView(IFaceView):
    viewModuleID = "useradmin"

    headoptions = adminview.headoptions

    #??? name.settings["validator"] = UsernameValidator

    def open(self):
        id = self.GetFormValue("id")
        obj = self.context.root.GetObj(id)
        if obj is None:
            return HTTPNotFound()
        url = self.FolderUrl(obj)+"edit"
        self.Redirect(url)

