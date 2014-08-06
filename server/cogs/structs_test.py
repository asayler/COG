#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import copy
import unittest

import structs
import test_common


class TypesTestCase(test_common.CogsTestCase):

    def setUp(self):
        super(TypesTestCase, self).setUp()

    def tearDown(self):
        super(TypesTestCase, self).tearDown()


class ServerTestCase(TypesTestCase):

    def setUp(self):
        super(ServerTestCase, self).setUp()
        self.s = structs.Server(db=self.db)

    def tearDown(self):
        del(self.s)
        super(ServerTestCase, self).tearDown()

    def test_list_assignments(self):

        assignments_in = set([])

        # List Assignments (Empty DB)
        assignments_out = self.s.list_assignments()
        self.assertEqual(assignments_in, assignments_out)

        # Generate 10 Assingments
        for i in range(10):
            d = copy.deepcopy(test_common.ASSIGNMENT_TESTDICT)
            for k in d:
                d[k] = "{:s}_test_{:02d}".format(d[k], i)
            assignments_in.add(str(self.s.create_assignment(d).uuid))

        # List Assignments
        assignments_out = self.s.list_assignments()
        self.assertEqual(assignments_in, assignments_out)


class AssignmentTestCase(TypesTestCase):

    def setUp(self):
        super(AssignmentTestCase, self).setUp()
        self.srv = structs.Server(self.db)

    def tearDown(self):
        super(AssignmentTestCase, self).tearDown()

    def test_create_assignment(self):

        # Test Empty Dict
        d = {}
        self.assertRaises(KeyError, self.srv.create_assignment, d)

        # Test Bad Dict
        d = {'test': "test"}
        self.assertRaises(KeyError, self.srv.create_assignment, d)

        # Test Sub Dict
        d = copy.deepcopy(test_common.ASSIGNMENT_TESTDICT)
        d.pop(d.keys()[0])
        self.assertRaises(KeyError, self.srv.create_assignment, d)

        # Test Super Dict
        d = copy.deepcopy(test_common.ASSIGNMENT_TESTDICT)
        d['test'] = "test"
        self.assertRaises(KeyError, self.srv.create_assignment, d)

        # Test Valid
        d = copy.deepcopy(test_common.ASSIGNMENT_TESTDICT)
        asn = self.srv.create_assignment(d)
        self.assertSubset(d, asn.get_dict())

    def test_get_assignment(self):

        # Test Invalid UUID
        self.assertRaises(structs.ObjectDNE,
                          self.srv.get_assignment,
                          'eb424026-6f54-4ef8-a4d0-bb658a1fc6cf')

        # Test Valid UUID
        d = copy.deepcopy(test_common.ASSIGNMENT_TESTDICT)
        asn1 = self.srv.create_assignment(d)
        asn1_uuid = asn1.uuid
        asn2 = self.srv.get_assignment(asn1_uuid)
        self.assertEqual(asn1, asn2)

class TestTestCase(TypesTestCase):

    def setUp(self):
        super(TestTestCase, self).setUp()
        self.srv = structs.Server(self.db)
        self.asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT)

    def tearDown(self):
        super(TestTestCase, self).tearDown()

    def test_create_test(self):

        # Test Empty Dict
        d = {}
        self.assertRaises(KeyError, self.asn.create_test, d)

        # Test Bad Dict
        d = {'test': "test"}
        self.assertRaises(KeyError, self.asn.create_test, d)

        # Test Sub Dict
        d = copy.deepcopy(test_common.TEST_TESTDICT)
        d.pop(d.keys()[0])
        self.assertRaises(KeyError, self.asn.create_test, d)

        # Test Super Dict
        d = copy.deepcopy(test_common.TEST_TESTDICT)
        d['test'] = "test"
        self.assertRaises(KeyError, self.asn.create_test, d)

        # Test Valid
        d = copy.deepcopy(test_common.TEST_TESTDICT)
        tst = self.asn.create_test(d)
        self.assertSubset(d, tst.get_dict())

    def test_get_test(self):

        # Test Invalid UUID
        self.assertRaises(structs.ObjectDNE,
                          self.asn.get_test,
                          'eb424026-6f54-4ef8-a4d0-bb658a1fc6cf')

        # Test Valid UUID
        d = copy.deepcopy(test_common.TEST_TESTDICT)
        tst1 = self.asn.create_test(d)
        tst1_uuid = tst1.uuid
        tst2 = self.asn.get_test(tst1_uuid)
        self.assertEqual(tst1, tst2)


# Main
if __name__ == '__main__':
    unittest.main()
