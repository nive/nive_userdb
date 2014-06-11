
from nive.definitions import ModuleConf

configuration = ModuleConf(
    id="useradmin-module",
    name="Meta package for useradmin components",
    modules=(
        "nive_userdb.useradmin.adminroot",
        "nive_userdb.useradmin.view",
        "nive.components.reform.reformed"
    ),
)

