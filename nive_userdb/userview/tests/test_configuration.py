# -*- coding: utf-8 -*-

import unittest

from nive.helper import FormatConfTestFailure

from nive_userdb.userview import view




class TestConf(unittest.TestCase):

    def test_conf1(self):
        r=view.configuration.test()
        if not r:
            return
        self.fail(FormatConfTestFailure(r))


