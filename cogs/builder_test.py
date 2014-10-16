#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Fall 2014
# University of Colorado


import copy

import test_common

import auth
import structs


class BuilderTestCase(test_common.CogsTestCase):

    def setUp(self):

        # Call Parent
        super(BuilderTestCase, self).setUp()

        # Setup Auth
        self.auth = auth.Auth()

        # Setup Server
        self.srv = structs.Server()

        # Create User
        self.user = self.auth.create_user(test_common.USER_TESTDICT,
                                          username="testuser",
                                          password="testpass",
                                          authmod="test")

    def tearDown(self):

        # Cleanup
        self.user.delete()
        self.srv.close()

        # Call parent
        super(BuilderTestCase, self).tearDown()


class BuilderRunTestCase(BuilderTestCase):

    def setUp(self):

        # Call Parent
        super(BuilderRunTestCase, self).setUp()

        # Setup Assignment
        asn_dict = copy.copy(test_common.ASSIGNMENT_TESTDICT)
        asn_dict['env'] = "local"
        self.asn = self.srv.create_assignment(asn_dict, owner=self.user)

    def tearDown(self):

        # Cleanup
        self.asn.delete()

        # Call Parent
        super(BuilderRunTestCase, self).tearDown()
