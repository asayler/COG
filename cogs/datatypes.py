# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import copy
import os
import uuid
import time
import mimetypes

import redis

import environment
import tester_script

_ENCODING = 'utf-8'

_REDIS_HOST = "localhost"
_REDIS_PORT = 6379
_REDIS_DB   = 3

_BASE_SCHEMA = ['created_time', 'modified_time']

_ASSIGNMENTS_SCHEMA  = ['name', 'contact']
ASSIGNMENT_TESTDICT  = {'name': "Test_Assignment",
                        'contact': "Andy Sayler"}

_TESTS_SCHEMA = ['name', 'contact', 'type', 'maxscore']
TEST_TESTDICT = {'name': "Test_Assignment",
                 'contact': "Andy Sayler",
                 'type': "script",
                 'maxscore': "10"}

_SUBMISSIONS_SCHEMA = ['author']

_RUNS_SCHEMA = ['test', 'status', 'score', 'output']

_FILES_SCHEMA = ['key', 'name', 'type', 'encoding', 'path']
_FILES_DIR = "./files/"

_UUID_GLOB = '????????-????-????-????-????????????'

### Exceptions

class RedisObjectError(Exception):
    """Base class for Redis Object Exceptions"""

    def __init__(self, *args, **kwargs):
        super(RedisObjectError, self).__init__(*args, **kwargs)

class UUIDRedisObjectError(RedisObjectError):
    """Base class for UUID Redis Object Exceptions"""

    def __init__(self, *args, **kwargs):
        super(UUIDRedisObjectError, self).__init__(*args, **kwargs)

class UUIDRedisObjectDNE(UUIDRedisObjectError):
    """UUID Redis Object Does Not Exist"""

    def __init__(self, obj):
        msg = "{:s} does not exist.".format(obj)
        super(UUIDRedisObjectDNE, self).__init__(msg)

class UUIDRedisObjectMissing(UUIDRedisObjectError):
    """UUID Redis Object Is Missing"""

    def __init__(self, obj):
        msg = "{:s} exists, but is missing.".format(obj)
        super(UUIDRedisObjectMissing, self).__init__(msg)


### Objects

class RedisObject(object):
    """
    Redis Object Base Class

    """

    def __init__(self):
        """Base Constructor"""
        super(RedisObject, self).__init__()
        self.db = redis.StrictRedis(host=_REDIS_HOST, port=_REDIS_PORT, db=_REDIS_DB)


class UUIDRedisObject(object):
    """
    UUID Redis Object Base Class

    """

    schema = _BASE_SCHEMA

    def __init__(self, uuid_obj):
        """Base Constructor"""
        super(UUIDRedisObject, self).__init__()
        self.uuid = uuid_obj
        self.obj_key = "{:s}:{:s}".format(self.base_key, repr(self)).lower()

    @classmethod
    def get_factory(cls, parent_str):

        class new_cls(cls):

            db = redis.StrictRedis(host=_REDIS_HOST, port=_REDIS_PORT, db=_REDIS_DB)
            if parent_str == None:
                base_key = "{:s}".format(cls.__name__).lower()
            else:
                base_key = "{:s}:{:s}".format(parent_str, cls.__name__).lower()

        return new_cls

    @classmethod
    def list_objs(cls):
        """List Class Objects"""
        obj_lst = cls.db.keys("{:s}:{:s}".format(cls.base_key, _UUID_GLOB))
        obj_uuids = []
        for obj_key in obj_lst:
            obj_uuid = obj_key.split(':')[-1]
            obj_uuids.append(obj_uuid)
        return set(obj_uuids)

    @classmethod
    def get_objs(cls):
        """List Class Objects"""
        obj_lst = cls.db.keys("{:s}:{:s}".format(cls.base_key, _UUID_GLOB))
        objs = []
        for obj_key in obj_lst:
            obj_uuid = obj_key.split(':')[-1]
            obj = cls.from_existing(obj_uuid)
            objs.append(obj)
        return objs

    @classmethod
    def from_new(cls, d):
        """New Constructor"""

        # Create New Object
        data = copy.deepcopy(d)
        uuid_obj = uuid.uuid4()
        obj = cls(uuid_obj)

        # Set Times
        data['created_time'] = str(time.time())
        data['modified_time'] = str(time.time())

        # Check dict
        if (set(data.keys()) != set(obj.schema)):
            raise KeyError("Keys {:s} do not match schema {:s}".format(data.keys(), obj.schema))

        # Add Object Data to DB
        if not obj.db.hmset(obj.obj_key, data):
            raise UUIDRedisObjectError("Create Failed")

        # Return Object
        return obj

    @classmethod
    def from_existing(cls, uuid_hex):
        """Existing Constructor"""

        # Create Existing Object
        uuid_obj = uuid.UUID(uuid_hex)
        obj = cls(uuid_obj)

        # Verify Object ID in Set
        if not obj.db.exists(obj.obj_key):
            raise UUIDRedisObjectDNE(obj)

        # Return Object
        return obj

    def __unicode__(self):
        u = u"{:s}_{:012x}".format(type(self).__name__, self.uuid.node)
        return u

    def __str__(self):
        s = unicode(self).encode(_ENCODING)
        return s

    def __repr__(self):
        r = "{:s}".format(self.uuid)
        return r

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        return (repr(self) == repr(other))

    def __getitem__(self, k):
        if k in self.schema:
            return self.db.hget(self.obj_key, k)
        else:
            raise KeyError("Key {:s} not valid in {:s}".format(k, self))

    def __setitem__(self, k, v):
        if k in self.schema:
            return self.db.hset(self.obj_key, k, v)
        else:
            raise KeyError("Key {:s} not valid in {:s}".format(k, self))

    def delete(self):
        """Delete"""

        # Delete Object Data from DB
        if not self.db.delete(self.obj_key):
            raise UUIDRedisObjectError("Delete Failed")

    def get_dict(self):
        """Get Dict"""
        data = self.db.hgetall(self.obj_key)
        return data

    def set_dict(self, d):
        """Set Dict"""

        # Create New Object
        data = copy.deepcopy(d)

        # Set Time
        data['modified_time'] = str(time.time())

        # Check dict
        if not set(data.keys()).issubset(set(self.schema)):
            raise KeyError("Keys {:s} do not match schema {:s}".format(data.keys(), self.schema))

        # Set dict
        self.db.hmset(self.obj_key, data)


class Server(RedisObject):
    """
    COGS Server Class

    """

    # Override Constructor
    def __init__(self):
        """Base Constructor"""
        super(Server, self).__init__()
        self.AssignmentFactory = Assignment.get_factory(None)

    # Assignment Methods
    def create_assignment(self, d):
        return self.AssignmentFactory.from_new(d)
    def get_assignment(self, uuid_hex):
        return self.AssignmentFactory.from_existing(uuid_hex)
    def get_assignments(self):
        return self.AssignmentFactory.get_objs()
    def list_assignments(self):
        return self.AssignmentFactory.list_objs()


class Assignment(UUIDRedisObject):
    """
    COGS Assignment Class

    """

    schema = _BASE_SCHEMA + _ASSIGNMENTS_SCHEMA

    # Override Constructor
    def __init__(self, uuid_obj):
        """Base Constructor"""
        super(Assignment, self).__init__(uuid_obj)
        self.TestFactory = Test.get_factory(self.obj_key)
        self.SubmissionFactory = Submission.get_factory(self.obj_key)

    # Override Delete
    def delete(self):
        """Delete"""

        # Delete Tests
        for t_uuid in self.list_tests():
            tst = self.get_test(t_uuid)
            tst.delete()

        # Delete Submissions
        for s_uuid in self.list_submissions():
            sub = self.get_submission(s_uuid)
            sub.delete()

        # Delete Self
        super(Assignment, self).delete()

    # Test Methods
    def create_test(self, d):
        return self.TestFactory.from_new(d)
    def get_test(self, uuid_hex):
        return self.TestFactory.from_existing(uuid_hex)
    def get_tests(self):
        return self.TestFactory.get_objs()
    def list_tests(self):
        return self.TestFactory.list_objs()

    # Submission Methods
    def create_submission(self, d):
        return self.SubmissionFactory.from_new(d)
    def get_submission(self, uuid_hex):
        return self.SubmissionFactory.from_existing(uuid_hex)
    def get_submissions(self):
        return self.SubmissionFactory.get_objs()
    def list_submissions(self):
        return self.SubmissionFactory.list_objs()


class Test(UUIDRedisObject):
    """
    COGS Test Class

    """

    schema = _BASE_SCHEMA + _TESTS_SCHEMA

    # Override Constructor
    def __init__(self, uuid_obj):
        """Base Constructor"""
        super(Test, self).__init__(uuid_obj)
        self.FileFactory = File.get_factory(self.obj_key)

    # Override Delete
    def delete(self):
        """Delete"""

        # Delete Files
        for f_uuid in self.list_files():
            fle = self.get_file(f_uuid)
            fle.delete(force=True)

        # Delete Self
        super(Test, self).delete()

    # File Methods
    def create_file(self, d, file_obj):
        return self.FileFactory.from_new(d, file_obj)
    def get_file(self, uuid_hex):
        return self.FileFactory.from_existing(uuid_hex)
    def get_files(self):
        return self.FileFactory.get_objs()
    def list_files(self):
        return self.FileFactory.list_objs()

class Submission(UUIDRedisObject):
    """
    COGS Submission Class

    """

    schema = _BASE_SCHEMA + _SUBMISSIONS_SCHEMA

    # Override Constructor
    def __init__(self, uuid_obj):
        """Base Constructor"""
        super(Submission, self).__init__(uuid_obj)
        self.FileFactory = File.get_factory(self.obj_key)
        self.RunFactory = Run.get_factory(self.obj_key)

    # Override Delete
    def delete(self):
        """Delete"""

        # Delete Files
        for f_uuid in self.list_files():
            fle = self.get_file(f_uuid)
            fle.delete(force=True)

        # Delete Self
        super(Submission, self).delete()

    # File Methods
    def create_file(self, d, file_obj):
        return self.FileFactory.from_new(d, file_obj)
    def get_file(self, uuid_hex):
        return self.FileFactory.from_existing(uuid_hex)
    def get_files(self):
        return self.FileFactory.get_objs()
    def list_files(self):
        return self.FileFactory.list_objs()

    # Run Methods
    def execute_run(self, tst, sub):
        return self.RunFactory.from_new(tst, sub)
    def get_run(self, uuid_hex):
        return self.RunFactory.from_existing(uuid_hex)
    def get_runs(self):
        return self.RunFactory.get_objs()
    def list_runs(self):
        return self.RunFactory.list_objs()

class Run(UUIDRedisObject):
    """
    COGS Run Class

    """

    schema = _BASE_SCHEMA + _RUNS_SCHEMA

    # Override from_new
    @classmethod
    def from_new(cls, tst, sub):
        """New Constructor"""

        # Create New Object
        data = {}

        # Setup Dict
        data['test'] = repr(tst)
        data['status'] = ""
        data['score'] = ""
        data['output'] = ""

        # Create Run
        run = super(Run, cls).from_new(data)

        tst_fls = tst.get_files()
        sub_fls = sub.get_files()

        env = environment.Env(run, tst_fls, sub_fls)
        tester = tester_script.Tester(env)
        ret, score, output = tester.test()

        run['status'] = str(ret)
        run['score'] = str(score)
        run['output'] = str(output)

        # env.close()

        # Return Run
        return run


class File(UUIDRedisObject):
    """
    COGS File Class

    """

    schema = _BASE_SCHEMA + _FILES_SCHEMA

    # Override from_new
    @classmethod
    def from_new(cls, d, file_obj):
        """New Constructor"""

        # Create New Object
        data = copy.deepcopy(d)

        # Setup Dict
        data['name'] = str(file_obj.filename)
        typ = mimetypes.guess_type(file_obj.filename)
        data['type'] = str(typ[0])
        data['encoding'] = str(typ[1])
        data['path'] = ""

        # Create File
        fle = super(File, cls).from_new(data)

        # Save File
        fle['path'] = os.path.abspath("{:s}/{:s}".format(_FILES_DIR, repr(fle)))
        try:
            file_obj.save(fle['path'])
        except IOError:
            # Clean up on failure
            fle.delete(force=True)
            raise

        # Return File
        return fle

    # Override Delete
    def delete(self, force=False):
        """Delete"""

        # Delete File
        try:
            os.remove(self['path'])
        except OSError:
            if force:
                pass
            else:
                raise

        # Delete Self
        super(File, self).delete()
