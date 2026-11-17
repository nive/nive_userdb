# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
Root for context to run adminview 
"""

from nive.definitions import RootConf
from nive_userdb.root import Userroot
from nive_userdb.i18n import _

class Adminroot(Userroot):
	"""
	"""



# Root definition ------------------------------------------------------------------
#@nive_module
configuration = RootConf(
	id = "management",
	context = "nive_userdb.useradmin.adminroot.Adminroot",
	default = False,
	subtypes = "*",
	name = _("User listing"),
	description = ""
)
