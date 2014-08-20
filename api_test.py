#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado


import base64
import copy
import json
import unittest
import uuid
import os

import cogs.test_common

import api


class CogsApiTestCase(cogs.test_common.CogsTestCase):

    def setUp(self):

        # Call Parent
        super(CogsApiTestCase, self).setUp()

        # Set App to Testing Mode
        api.app.testing = True

        # Create Test Client
        self.app = api.app.test_client()

        # Setup Admin
        self.admin = api.auth.create_user(cogs.test_common.USER_TESTDICT,
                                          username=cogs.test_common.ADMIN_USERNAME,
                                          password=cogs.test_common.ADMIN_PASSWORD,
                                          authmod=cogs.test_common.ADMIN_AUTHMOD)
        self.admin_uuid = str(self.admin.uuid).lower()
        api.auth.add_admins([self.admin_uuid])

    def tearDown(self):

        # Remove User
        self.admin.delete()

        # Call Parent
        super(CogsApiTestCase, self).tearDown()

    ## Auth Helpers ##

    def open_auth(self, method, url, username=None, password=None, **kwargs):

        headers = kwargs.pop('headers', {})

        if username:
            if not password:
                password = ""
            auth_str = "{:s}:{:s}".format(username, password)
            b64_auth_str = base64.b64encode(auth_str)
            key = "Authorization"
            val = "Basic {:s}".format(b64_auth_str)
            headers[key] = val

        return self.app.open(url, method=method, headers=headers, **kwargs)

    def open_user(self, method, url, user=None, **kwargs):

        if user:
            username = user['token']
        else:
            username = None

        return self.open_auth(method, url, username=username, **kwargs)

class CogsApiObjectBase(object):

    ## Object Helpers ##

    def create_objects(self, url, key, data, json_data=True, user=None):
        if json_data:
            data = json.dumps(data)
        res = self.open_user('POST', url, user=user, data=data)
        self.assertEqual(res.status_code, 200)
        res_obj = json.loads(res.data)
        self.assertTrue(res_obj)
        res_keys = res_obj.keys()
        self.assertEqual(len(res_keys), 1)
        self.assertEqual(res_keys[0], key)
        res_lst = res_obj[key]
        self.assertEqual(len(res_lst), 1)
        res_uuid = res_lst[0]
        self.assertTrue(res_uuid)
        return res_uuid

    def lst_objects(self, url, key, user=None):
        res = self.open_user('GET', url, user=user)
        self.assertEqual(res.status_code, 200)
        res_obj = json.loads(res.data)
        self.assertTrue(res_obj)
        res_keys = res_obj.keys()
        self.assertEqual(len(res_keys), 1)
        self.assertEqual(res_keys[0], key)
        res_lst = res_obj[key]
        return set(res_lst)

    def get_object(self, url, obj_uuid, user=None):
        res = self.open_user('GET', '{:s}{:s}/'.format(url, obj_uuid), user=user)
        if (res.status_code == 200):
            self.assertEqual(res.status_code, 200)
            res_obj = json.loads(res.data)
            self.assertTrue(res_obj)
            res_keys = res_obj.keys()
            self.assertEqual(len(res_keys), 1)
            self.assertEqual(res_keys[0], obj_uuid)
            res_hash = res_obj[obj_uuid]
            self.assertTrue(res_hash)
            return res_hash
        elif (res.status_code == 404):
            return None
        else:
            self.fail("Bad HTTP status code {:d}".format(res.status_code))

    def set_object(self, url, obj_uuid, data, json_data=True, user=None):
        if json_data:
            data = json.dumps(data)
        res = self.open_user('PUT', '{:s}{:s}/'.format(url, obj_uuid), user=user, data=data)
        if (res.status_code == 200):
            self.assertEqual(res.status_code, 200)
            res_obj = json.loads(res.data)
            self.assertTrue(res_obj)
            res_keys = res_obj.keys()
            self.assertEqual(len(res_keys), 1)
            self.assertEqual(res_keys[0], obj_uuid)
            res_hash = res_obj[obj_uuid]
            self.assertTrue(res_hash)
            return res_hash
        elif (res.status_code == 404):
            return None
        else:
            self.fail("Bad HTTP status code {:d}".format(res.status_code))

    def delete_object(self, url, obj_uuid, user=None):
        res = self.open_user('DELETE', '{:s}{:s}/'.format(url, obj_uuid), user=user)
        if (res.status_code == 200):
            self.assertEqual(res.status_code, 200)
            res_obj = json.loads(res.data)
            self.assertTrue(res_obj)
            res_keys = res_obj.keys()
            self.assertEqual(len(res_keys), 1)
            self.assertEqual(res_keys[0], obj_uuid)
            res_hash = res_obj[obj_uuid]
            self.assertTrue(res_hash)
            return res_hash
        elif (res.status_code == 404):
            return None
        else:
            self.fail("Bad HTTP status code {:d}".format(res.status_code))

    ## Object Tests ##

    def test_create_object(self):

        # Set URLs
        url = getattr(self, 'url', None)
        url_lst = getattr(self, 'url_lst', url)
        url_obj = getattr(self, 'url_obj', url)

        # Create Object
        obj_uuid = self.create_objects(url_lst, self.key, self.data,
                                       json_data=self.json_data, user=self.user)
        self.assertTrue(obj_uuid)

        # Delete Object
        obj = self.delete_object(url_obj, obj_uuid, user=self.user)
        self.assertIsNotNone(obj)

    def test_list_objects(self):

        objects_in = set([])

        # Set URLs
        url = getattr(self, 'url', None)
        url_lst = getattr(self, 'url_lst', url)
        url_obj = getattr(self, 'url_obj', url)

        # Get Object List (Empty)
        objects_out = self.lst_objects(url_lst, self.key, user=self.user)
        self.assertEqual(objects_in, objects_out)

        # Create Objects
        for i in range(10):
            obj_uuid = self.create_objects(url_lst, self.key, self.data,
                                           json_data=self.json_data, user=self.user)
            objects_in.add(obj_uuid)

        # Get Object List
        objects_out = self.lst_objects(url_lst, self.key, user=self.user)
        self.assertEqual(objects_in, objects_out)

        # Delete Some Objects
        for i in range(5):
            obj_uuid = objects_in.pop()
            obj = self.delete_object(url_obj, obj_uuid, user=self.user)
            self.assertIsNotNone(obj)

        # Get Object List
        objects_out = self.lst_objects(url_lst, self.key, user=self.user)
        self.assertEqual(objects_in, objects_out)

        # Delete Remaining Objects
        for obj_uuid in list(objects_in):
            objects_in.remove(obj_uuid)
            obj = self.delete_object(url_obj, obj_uuid, user=self.user)
            self.assertIsNotNone(obj)

        # Get Object List
        objects_out = self.lst_objects(url_lst, self.key, user=self.user)
        self.assertEqual(objects_in, objects_out)

    def test_get_object(self):

        # Set URLs
        url = getattr(self, 'url', None)
        url_lst = getattr(self, 'url_lst', url)
        url_obj = getattr(self, 'url_obj', url)

        # Create Object
        obj_uuid = self.create_objects(url_lst, self.key, self.data,
                                       json_data=self.json_data, user=self.user)

        # Get Object
        obj = self.get_object(url_obj, obj_uuid, user=self.user)
        self.assertSubset(self.data, obj)

        # Delete Object
        obj = self.delete_object(url_obj, obj_uuid, user=self.user)
        self.assertIsNotNone(obj)

    def test_set_object(self):

        # Set URLs
        url = getattr(self, 'url', None)
        url_lst = getattr(self, 'url_lst', url)
        url_obj = getattr(self, 'url_obj', url)

        # Create Object
        obj_uuid = self.create_objects(url_lst, self.key, self.data,
                                       json_data=self.json_data, user=self.user)

        # Update Object
        data = copy.copy(self.data)
        if data:
            for key in data:
                data[key] = data[key] + "_updated"
            self.assertNotEqual(self.data, data)
        obj = self.set_object(url_obj, obj_uuid, data,
                              json_data=self.json_data, user=self.user)
        self.assertSubset(data, obj)

        # Get Object
        obj = self.get_object(url_obj, obj_uuid, user=self.user)
        self.assertSubset(data, obj)

        # Delete Object
        obj = self.delete_object(url_obj, obj_uuid, user=self.user)
        self.assertIsNotNone(obj)

    def test_delete_object(self):

        # Set URLs
        url = getattr(self, 'url', None)
        url_lst = getattr(self, 'url_lst', url)
        url_obj = getattr(self, 'url_obj', url)

        # Create Object
        obj_uuid = self.create_objects(url_lst, self.key, self.data,
                                       json_data=self.json_data, user=self.user)

        # Get Object
        obj = self.get_object(url_obj, obj_uuid, user=self.user)
        self.assertIsNotNone(obj)

        # Delete Object
        obj = self.delete_object(url_obj, obj_uuid, user=self.user)
        self.assertIsNotNone(obj)

        # Get Object
        obj = self.get_object(url_lst, obj_uuid, user=self.user)
        self.assertIsNone(obj)


## Root Tests ##
class CogsApiRootTestCase(CogsApiTestCase):

    def setUp(self):
        super(CogsApiRootTestCase, self).setUp()

    def tearDown(self):
        super(CogsApiRootTestCase, self).tearDown()

    def test_root_get(self):
        res = self.open_user('GET', '/', user=self.admin)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, api._MSG_ROOT)


## File Tests ##
class CogsApiFileTestCase(CogsApiObjectBase, CogsApiTestCase):

    def setUp(self):
        super(CogsApiFileTestCase, self).setUp()
        self.user = self.admin
        self.url = '/files/'
        self.key = 'files'
        self.file_name = "test.txt"
        self.file_path = "{:s}/{:s}".format(cogs.test_common.TEST_INPUT_PATH, self.file_name)
        self.file_key = "test_file"
        self.data = {self.file_key: (self.file_path, self.file_name)}
        self.json_data = False

    def tearDown(self):
        super(CogsApiFileTestCase, self).tearDown()

    # Override default test_get_object
    def test_get_object(self):

        # Create Object
        obj_uuid = self.create_objects(self.url, self.key, self.data,
                                       json_data=self.json_data, user=self.user)

        # Get Object
        obj = self.get_object(self.url, obj_uuid, user=self.user)
        self.assertEqual(self.file_key, obj['key'])
        self.assertEqual(self.file_name, obj['name'])
        self.assertEqual(str(self.user.uuid), obj['owner'])

        # Delete Object
        obj = self.delete_object(self.url, obj_uuid, user=self.user)
        self.assertIsNotNone(obj)

    # Override default test_set_object
    def test_set_object(self):

        # Create Object
        obj_uuid = self.create_objects(self.url, self.key, self.data,
                                       json_data=self.json_data, user=self.user)

        # Update Object (Not Allowed on Files - Should Fail with a 405 Error)
        try:
            obj = self.set_object(self.url, obj_uuid, self.data,
                                  json_data=self.json_data, user=self.user)
        except AssertionError as e:
            if int(str(e).split()[-1]) != 405:
                raise

        # Delete Object
        obj = self.delete_object(self.url, obj_uuid, user=self.user)
        self.assertIsNotNone(obj)


## Reporter Tests ##
class CogsApiReporterTestCase(CogsApiObjectBase, CogsApiTestCase):

    def setUp(self):
        super(CogsApiReporterTestCase, self).setUp()
        self.user = self.admin
        self.url = '/reporters/'
        self.key = 'reporters'
        self.data = copy.copy(cogs.test_common.REPORTER_TESTDICT)
        self.data['mod'] = "moodle"
        self.data['asn_id'] = cogs.test_common.REPMOD_MOODLE_ASN
        self.json_data = True

    def tearDown(self):
        super(CogsApiReporterTestCase, self).tearDown()


## Assignment Tests ##
class CogsApiAssignmentTestCase(CogsApiObjectBase, CogsApiTestCase):

    def setUp(self):
        super(CogsApiAssignmentTestCase, self).setUp()
        self.user = self.admin
        self.url = '/assignments/'
        self.key = 'assignments'
        self.data = copy.copy(cogs.test_common.ASSIGNMENT_TESTDICT)
        self.json_data = True

    def tearDown(self):
        super(CogsApiAssignmentTestCase, self).tearDown()


## Test Tests ##
class CogsApiTestTestCase(CogsApiObjectBase, CogsApiTestCase):

    def setUp(self):

        # Call Parent
        super(CogsApiTestTestCase, self).setUp()

        # Set User
        self.user = self.admin

        # Create Assignment
        self.asn_uuid = self.create_objects('/assignments/', 'assignments',
                                            cogs.test_common.ASSIGNMENT_TESTDICT,
                                            json_data=True, user=self.user)

        # Set Params
        self.url_lst = '/assignments/{:s}/tests/'.format(self.asn_uuid)
        self.url_obj = '/tests/'
        self.key = 'tests'
        self.data = copy.copy(cogs.test_common.TEST_TESTDICT)
        self.json_data = True

    def tearDown(self):

        # Delete Assignment
        self.delete_object('/assignments/', self.asn_uuid, user=self.user)

        # Call Parent
        super(CogsApiTestTestCase, self).tearDown()


## Submission Tests ##
class CogsApiSubmissionTestCase(CogsApiObjectBase, CogsApiTestCase):

    def setUp(self):

        # Call Parent
        super(CogsApiSubmissionTestCase, self).setUp()

        # Set User
        self.user = self.admin

        # Create Assignment
        self.asn_uuid = self.create_objects('/assignments/', 'assignments',
                                            cogs.test_common.ASSIGNMENT_TESTDICT,
                                            json_data=True, user=self.user)

        # Set Params
        self.url_lst = '/assignments/{:s}/submissions/'.format(self.asn_uuid)
        self.url_obj = '/submissions/'
        self.key = 'submissions'
        self.data = copy.copy(cogs.test_common.SUBMISSION_TESTDICT)
        self.json_data = True

    def tearDown(self):

        # Delete Assignment
        self.delete_object('/assignments/', self.asn_uuid, user=self.user)

        # Call Parent
        super(CogsApiSubmissionTestCase, self).tearDown()


### Main
if __name__ == '__main__':
    unittest.main()
