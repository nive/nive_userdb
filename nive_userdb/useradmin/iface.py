
from nive.definitions import FieldConf, Conf
from nive.definitions import IObject, IRoot

from nive.components.iface.definitions import IFaceConf
from nive.components.reform.widget import RadioChoiceWidget
from nive_userdb.i18n import _


# iface configuration------------------------------------------------------------------

configuration = IFaceConf(
    sections=   (
        Conf(id="root.viewlist", ref="users", name=_("Listing")),
        Conf(id="root.add?pool_type=user", ref="add", name=_("Add")),
    ),

    acl=None,
    backlink = Conf(id="root.",         name="Start"),
    headlink = Conf(id="/userdb/logout",name="Abmelden"),
    headoptions = [],
    tmpl_macro = "main_object_full",
    currentSection = "users",
    slogan = _("User management"),
    static="nive.components.iface:static/",
    path = False
)

# navigation
configuration.navigation = ()

# object defaults. can be replaced on type base.
configuration.tabs = (
    Conf(id="context.edit", name=_("Edit"), permission="manage users", interfaces=[IObject]),
    Conf(id="context.options", name=_("Options"), permission="manage users", interfaces=[IObject]),
    Conf(id="context.meta", name=_("System"), permission="manage users", interfaces=[IObject])
)

configuration.settings = ()
configuration.shortcuts = ()


# fields ------------------------------------------------------------------

stateField =    FieldConf(id="pool_state",    datatype="list",        size=  5, default="", name=_("Active"),
                          listItems=[{"id":"","name":""},{"id":"1","name":"Yes"},{"id":"0","name":"No"}])
nameField =     FieldConf(id="name",          datatype="string",      size=255, default="", name=_("Name"))
emailField =    FieldConf(id="email",         datatype="string",      size=255, default="", name=_("Email"))
groupsField =   FieldConf(id="groups",        datatype="list",        size=255, default="", name=_("Groups"),
                          settings={"codelist":"groups", "addempty":True})
activationField = FieldConf(id="token",       datatype="string",      size= 30, default="", name=_("Token"))
password_update = FieldConf(id="password",    datatype="password",    size=100, default="", name=_("Password"),
                            required=False, settings={"update": True})
companyField    = FieldConf(id="company",     datatype="string",      size=50,  default="", name=_("Name"))
lastloginField  = FieldConf(id="lastlogin",   datatype="string",      size=50,  default="", name=_("Last login"))
pool_createField= FieldConf(id="pool_create", datatype="string",      size=255, default="", name=_("Create"))
idField         = FieldConf(id="id",          datatype="number",      size=255, default="", name=_("Id"))

# object fields
configuration.addflds = Conf(
    user=Conf(fields=[
        "name", "email", "password", "groups",
        "surname", "lastname", "company",
    ], interfaces=[IObject])
)

configuration.editflds = Conf(
    user=Conf(fields=[
                FieldConf(id="pool_state", name=_("Active"), datatype="number",
                        widget=RadioChoiceWidget(values=(("1", _("Yes")), ("0", _("No"))))),
                "email",
                FieldConf(id="password", name=_("Password"), datatype="password", settings={"update": True}),
                "name", "groups", "notify",
                "surname", "lastname", "company",
    ],
              interfaces=[IObject]
    )
)
configuration.metaflds = Conf(default=Conf(fields=[
   "pool_state", "id", "reference", "pool_create", "pool_change", "pool_createdby", "pool_changedby", "token", "tempcache"
], interfaces=[IObject]))
configuration.dataflds = Conf(default=Conf(fields=[
    "name", "email", "groups", "notify", "surname", "lastname", "company", "lastlogin"
], interfaces=[IObject]))

# search types
user = Conf(
    type = "user",
    listoptions = ["delete"],
    form = [stateField, emailField, nameField, groupsField, lastloginField, pool_createField],
    fields = ["pool_state", "email", "name", "groups", "lastlogin", "pool_create"],
    operators = dict(groups="LIKE", email="LIKE", name="LIKE"),
)
configuration.searchconf = Conf(user=user)
        
