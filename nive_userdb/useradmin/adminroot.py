# -*- coding: utf-8 -*-
# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
Root for context to run adminview 
"""

from nive.definitions import RootConf
from nive_userdb.root import root
from nive_userdb.i18n import _

class adminroot(root):
	"""
	"""



# Root definition ------------------------------------------------------------------
#@nive_module
configuration = RootConf(
	id = "usermanagement",
	context = "nive_userdb.useradmin.adminroot.adminroot",
    default = False,
	subtypes = "*",
	name = _(u"User listing"),
	description = ""
)
