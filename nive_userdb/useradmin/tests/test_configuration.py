# -*- coding: utf-8 -*-

import unittest

from nive.helper import FormatConfTestFailure

from nive_userdb.useradmin import view
from nive_userdb.useradmin import adminroot




class TestConf(unittest.TestCase):

    def test_conf1(self):
        r=view.configuration.test()
        if not r:
            return
        self.fail(FormatConfTestFailure(r))


    def test_conf2(self):
        r=adminroot.configuration.test()
        if not r:
            return
        self.fail(FormatConfTestFailure(r))


