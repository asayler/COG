#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import copy
import unittest
import os
import functools

import auth
import test_common
import test_common_backend

_COGS_MOODLE_USERNAME = os.environ['COGS_MOODLE_USERNAME']
_COGS_MOODLE_PASSWORD = os.environ['COGS_MOODLE_PASSWORD']

class BaseTestCase(test_common.CogsTestCase):

    def setUp(self):

        # Call Parent
        super(BaseTestCase, self).setUp()

        # Setup Server
        self.auth = auth.Auth(db=self.db)

    def tearDown(self):

        # Call parent
        super(BaseTestCase, self).tearDown()


class AuthTestCase(test_common_backend.SubMixin, BaseTestCase):

    def setUp(self):
        super(AuthTestCase, self).setUp()

    def tearDown(self):
        super(AuthTestCase, self).tearDown()

    def test_users(self):
        self.subHashDirectHelper(self.auth.create_user,
                                 self.auth.get_user,
                                 self.auth.list_users,
                                 test_common.USER_TESTDICT,
                                 base_kwargs={'username': 'username',
                                              'password': 'password'},
                                 extra_kwargs={'authmod': 'test'})

    def test_groups(self):
        self.subHashDirectHelper(self.auth.create_group,
                                 self.auth.get_group,
                                 self.auth.list_groups,
                                 test_common.GROUP_TESTDICT,
                                 extra_objs=[auth.SPECIAL_GROUP_ADMIN])

    def test_admins(self):

        # Create Test Users
        users = set([])
        for i in range(10):
            username = "user_{:02d}".format(i)
            password = "password_{:02d}"
            user = self.auth.create_user(test_common.USER_TESTDICT,
                                        username=username, password=password,
                                        authmod='test')
            users.add(str(user.uuid))

        # Test Admin Methods
        self.subSetReferenceHelper(self.auth.add_admins,
                                   self.auth.rem_admins,
                                   self.auth.list_admins,
                                   users)

        # Remove Test Users
        for user_uuid in users:
            user = self.auth.get_user(user_uuid)
            user.delete()

    def test_allowed_groups(self):

        # Create Test Groups
        groups = set([])
        for i in range(10):
            group = self.auth.create_group(test_common.GROUP_TESTDICT)
            groups.add(str(group.uuid))

        # Bind Partial Methods
        method = "GET"
        path = "/test"
        add_allowed_groups = functools.partial(self.auth.add_allowed_groups, method, path)
        rem_allowed_groups = functools.partial(self.auth.rem_allowed_groups, method, path)
        list_allowed_groups = functools.partial(self.auth.list_allowed_groups, method, path)

        # Test Allowed Group Methods
        self.subSetReferenceHelper(add_allowed_groups,
                                   rem_allowed_groups,
                                   list_allowed_groups,
                                   groups)

        # Remove Test Groups
        for group_uuid in groups:
            group = self.auth.get_group(group_uuid)
            group.delete()




class UserTestCase(test_common_backend.UUIDHashMixin, BaseTestCase):

    def setUp(self):
        self.username = 'testuser'
        self.password = 'testpass'
        self.authmod = 'test'
        super(UserTestCase, self).setUp()

    def tearDown(self):
        super(UserTestCase, self).tearDown()

    def test_create_user(self):
        self.hashCreateHelper(self.auth.create_user,
                              test_common.USER_TESTDICT,
                              extra_kwargs={'username': self.username,
                                            'password': self.password,
                                            'authmod': self.authmod})

    def test_get_user(self):
        self.hashGetHelper(self.auth.create_user,
                           self.auth.get_user,
                           test_common.USER_TESTDICT,
                              extra_kwargs={'username': self.username,
                                            'password': self.password,
                                            'authmod': self.authmod})

    def test_update_user(self):
        self.hashUpdateHelper(self.auth.create_user,
                              test_common.USER_TESTDICT,
                              extra_kwargs={'username': self.username,
                                            'password': self.password,
                                            'authmod': self.authmod})

    def test_delete_user(self):
        self.hashDeleteHelper(self.auth.create_user,
                              test_common.USER_TESTDICT,
                              extra_kwargs={'username': self.username,
                                            'password': self.password,
                                            'authmod': self.authmod})


class AuthmodUserTestCase(UserTestCase):

    def setUp(self):
        self.username = _COGS_MOODLE_USERNAME
        self.password = _COGS_MOODLE_PASSWORD
        self.authmod = 'moodle'
        super(UserTestCase, self).setUp()

    def tearDown(self):
        super(UserTestCase, self).tearDown()

    def test_create_user(self):
        self.hashCreateHelper(self.auth.create_user,
                              test_common.USER_TESTDICT,
                              extra_kwargs={'username': self.username,
                                            'password': self.password,
                                            'authmod': self.authmod})

    def test_get_user(self):
        self.hashGetHelper(self.auth.create_user,
                           self.auth.get_user,
                           test_common.USER_TESTDICT,
                              extra_kwargs={'username': self.username,
                                            'password': self.password,
                                            'authmod': self.authmod})

    def test_update_user(self):
        self.hashUpdateHelper(self.auth.create_user,
                              test_common.USER_TESTDICT,
                              extra_kwargs={'username': self.username,
                                            'password': self.password,
                                            'authmod': self.authmod})

    def test_delete_user(self):
        self.hashDeleteHelper(self.auth.create_user,
                              test_common.USER_TESTDICT,
                              extra_kwargs={'username': self.username,
                                            'password': self.password,
                                            'authmod': self.authmod})


class GroupTestCase(test_common_backend.SubMixin, test_common_backend.UUIDHashMixin, BaseTestCase):

    def setUp(self):

        # Call Parent
        super(GroupTestCase, self).setUp()

        # Setup Users
        self.users = set([])
        for i in range(10):
            username = "user_{:02d}".format(i)
            password = "password_{:02d}"
            user = self.auth.create_user(test_common.USER_TESTDICT,
                                        username=username, password=password,
                                        authmod='test')
            self.users.add(str(user.uuid))

    def tearDown(self):

        # Remove Users
        for user_uuid in self.users:
            user = self.auth.get_user(user_uuid)
            user.delete()

        # Call Parent
        super(GroupTestCase, self).tearDown()

    def test_create_group(self):
        self.hashCreateHelper(self.auth.create_group,
                              test_common.GROUP_TESTDICT)

    def test_get_group(self):
        self.hashGetHelper(self.auth.create_group,
                           self.auth.get_group,
                           test_common.GROUP_TESTDICT)

    def test_delete_group(self):
        self.hashDeleteHelper(self.auth.create_group,
                              test_common.GROUP_TESTDICT)

    def test_update_group(self):
        self.hashUpdateHelper(self.auth.create_group,
                              test_common.GROUP_TESTDICT)

    def test_members(self):
        grp = self.auth.create_group(test_common.GROUP_TESTDICT)
        self.subSetReferenceHelper(grp.add_users, grp.rem_users, grp.list_users,
                                   self.users)

# Main
if __name__ == '__main__':
    unittest.main()
