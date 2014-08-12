#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import copy
import unittest
import werkzeug
import os

import auth
import test_common
import test_common_backend

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


class UserTestCase(test_common_backend.UUIDHashMixin, BaseTestCase):

    def setUp(self):
        super(UserTestCase, self).setUp()

    def tearDown(self):
        super(UserTestCase, self).tearDown()

    def test_create_user(self):
        self.hashCreateHelper(self.auth.create_user,
                              test_common.USER_TESTDICT,
                              extra_kwargs={'username': 'testuser',
                                            'password': 'testpass',
                                            'authmod': 'test'})

    def test_get_user(self):
        self.hashGetHelper(self.auth.create_user,
                           self.auth.get_user,
                           test_common.USER_TESTDICT,
                              extra_kwargs={'username': 'testuser',
                                            'password': 'testpass',
                                            'authmod': 'test'})

    def test_update_user(self):
        self.hashUpdateHelper(self.auth.create_user,
                              test_common.USER_TESTDICT,
                              extra_kwargs={'username': 'testuser',
                                            'password': 'testpass',
                                            'authmod': 'test'})

    def test_delete_user(self):
        self.hashDeleteHelper(self.auth.create_user,
                              test_common.USER_TESTDICT,
                              extra_kwargs={'username': 'testuser',
                                            'password': 'testpass',
                                            'authmod': 'test'})


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
