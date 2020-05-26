

import unittest
import time

from nive.helper import FormatConfTestFailure
from nive.definitions import Conf

from nive_userdb.extensions.sessionuser import SessionUser, SessionUserCache, ISessionUser, configuration
from nive_userdb.extensions.sessionuser import RootListener, UserListener, UserFound


class cq(object):
    def GetMetaFld(self, id):
        return True

class testobj(object):
    configuration = Conf()
    configurationQuery = cq()
    def Listen(self, name, fnc):
        pass

class Conftest(unittest.TestCase):
    
    def test_conf1(self):
        r=configuration.test()
        if not r:
            return
        self.fail(FormatConfTestFailure(r))



class CacheTest(unittest.TestCase):
    
    def setUp(self):
        self.cache = SessionUserCache(1234)
    
    def test_caching(self):
        user1 = SessionUser("user1", 1, Conf(), Conf())
        user2 = SessionUser("user2", 2, Conf(), Conf())
        user3 = SessionUser("user3", 3, Conf(), Conf())
        
        self.assertFalse(self.cache.Get("user1"))
        self.assertFalse(self.cache.GetAll())

        self.cache.Add(user1, "user1")
        self.assertTrue(self.cache.Get("user1"))
        self.assertTrue(len(self.cache.GetAll())==1)

        self.cache.Add(user1, "user1")
        self.assertTrue(self.cache.Get("user1"))
        self.assertTrue(len(self.cache.GetAll())==1)

        self.cache.Add(user2, "user2")
        self.assertTrue(self.cache.Get("user1"))
        self.assertTrue(self.cache.Get("user2"))
        self.assertTrue(len(self.cache.GetAll())==2)

        self.cache.Add(user3, "user3")
        self.assertTrue(self.cache.Get("user1"))
        self.assertTrue(self.cache.Get("user2"))
        self.assertTrue(self.cache.Get("user3"))
        self.assertTrue(len(self.cache.GetAll())==3)

        self.cache.Invalidate("user1")
        self.assertFalse(self.cache.Get("user1"))
        self.assertTrue(self.cache.Get("user2"))
        self.assertTrue(self.cache.Get("user3"))
        self.assertTrue(len(self.cache.GetAll())==2)

        self.cache.Purge()
        self.assertFalse(self.cache.Get("user1"))
        self.assertTrue(self.cache.Get("user2"))
        self.assertTrue(self.cache.Get("user3"))
        self.assertTrue(len(self.cache.GetAll())==2)

        self.cache.expires = 0
        self.cache.Purge()
        self.assertFalse(self.cache.Get("user1"))
        self.assertFalse(self.cache.Get("user2"))
        self.assertFalse(self.cache.Get("user3"))
        self.assertTrue(len(self.cache.GetAll())==0)

class ListenerTest(unittest.TestCase):
    
    def test_root(self):
        r = RootListener()
        r.app = testobj()
        r.app.usercache = SessionUserCache()
        user = r.LookupCache(ident="user1", activeOnly=None)
        self.assertFalse(user)
        r.app.usercache.Add(SessionUser("user1", 1, Conf(), Conf()), "user1")
        self.assertRaises(UserFound, r.LookupCache, ident="user1", activeOnly=None)

        u = UserListener()
        u.app = testobj()
        u.app.usercache = SessionUserCache()
        u.identity = "user1"
        u.data = Conf()
        u.meta = Conf()
        u.id = 1
        sessionuser = r.SessionUserFactory("user1", u)
        self.assertTrue(sessionuser)
        r.AddToCache(sessionuser)
        
    def test_user(self):
        u = UserListener()
        u.app = testobj()
        u.app.usercache = SessionUserCache()
        u.identity = "user1"
        u.data = Conf()
        u.id = 1
        u.InvalidateCache()
        
        
class SessionuserTest(unittest.TestCase):
    
    def setUp(self):
        values = {"name":"user1", 
                  "email": "user@nive.co", 
                  "surname": "The", 
                  "lastname": "User", 
                  "groups": ("here", "there"), 
                  "lastlogin": time.time()}
        values2 = {"id": 1, "pool_state": 1}
        self.user = SessionUser("user1", 1, Conf(**values), Conf(**values2))
        pass
    

    def test_iface(self):
        i = ISessionUser
        
    def test_user(self):
        self.assertTrue(self.user.lastlogin)
        self.assertTrue(self.user.currentlogin)
        self.assertTrue(self.user.data)
        self.assertTrue(self.user.data.name)
        self.assertTrue(self.user.data.email)
        self.assertTrue(self.user.data.groups)
        self.assertTrue(self.user.meta.id==1)
        self.assertTrue(self.user.meta.pool_state==1)
    
    def test_groups(self):
        grps = self.user.GetGroups()
        self.assertTrue(self.user.data.groups==grps)
        
    def test_ingroups(self):
        self.assertTrue(self.user.InGroups("here"))
        self.assertTrue(self.user.InGroups(["there", "ohno"]))
        self.assertFalse(self.user.InGroups(["ahaha", "ohno"]))
        
        
