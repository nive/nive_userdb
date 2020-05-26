# -*- coding: utf-8 -*-

import unittest

from nive.helper import FormatConfTestFailure

from nive_userdb import app, root, user




class TestConf(unittest.TestCase):

    def test_conf1(self):
        r=app.configuration.test()
        if not r:
            return
        self.fail(FormatConfTestFailure(r))


    def test_conf2(self):
        r=root.configuration.test()
        if not r:
            return
        self.fail(FormatConfTestFailure(r))


    def test_conf3(self):
        r=user.configuration.test()
        if not r:
            return
        self.fail(FormatConfTestFailure(r))


