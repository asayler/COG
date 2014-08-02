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
import werkzeug

import environment
import tester_script

_ENCODING = 'utf-8'

_SUF_BASE = 'Base'

_BASE_SCHEMA           = ['created_time', 'modified_time']
_USER_SCHEMA           = ['username', 'first', 'last', 'type']
_GROUP_SCHEMA          = ['name', 'members']
_COL_PERMISSION_SCHEMA = ['create', 'list']
_OBJ_PERMISSION_SCHEMA = ['read', 'write', 'delete']
_ASSIGNMENTS_SCHEMA    = ['name', 'contact', 'permissions']
_TESTS_SCHEMA          = ['name', 'contact', 'type', 'maxscore']
_SUBMISSIONS_SCHEMA    = ['author']
_RUNS_SCHEMA           = ['test', 'status', 'score', 'output']
_FILES_SCHEMA          = ['key', 'name', 'type', 'encoding', 'path']

_FILES_DIR = "./files/"

_UUID_GLOB = '????????-????-????-????-????????????'

_REDIS_CONF_DEFAULT = {'redis_host': "localhost",
                       'redis_port': 6379,
                       'redis_db': 3}

### Exceptions

class DatatypesError(Exception):
    """Base class for Datatypes Exceptions"""

    def __init__(self, *args, **kwargs):
        super(DatatypesError, self).__init__(*args, **kwargs)

class UUIDRedisFactoryError(DatatypesError):
    """Base class for UUID Redis Object Exceptions"""

    def __init__(self, *args, **kwargs):
        super(UUIDRedisFactoryError, self).__init__(*args, **kwargs)

class UUIDRedisObjectError(DatatypesError):
    """Base class for UUID Redis Object Exceptions"""

    def __init__(self, *args, **kwargs):
        super(UUIDRedisObjectError, self).__init__(*args, **kwargs)

class UUIDRedisObjectDNE(UUIDRedisObjectError):
    """UUID Redis Object Does Not Exist"""

    def __init__(self, obj):
        msg = "{:s} does not exist.".format(obj)
        super(UUIDRedisObjectDNE, self).__init__(msg)


### Objects

class UUIDObject(object):

    def __init__(self, uuid_obj):
        """Base Constructor"""
        super(UUIDObject, self).__init__()
        self.uuid = uuid_obj

    @classmethod
    def from_new(cls):
        """New Constructor"""

        # Create New Object
        uuid_obj = uuid.uuid4()
        obj = cls(uuid_obj)

        # Return Object
        return obj

    @classmethod
    def from_existing(cls, uuid_hex):
        """Existing Constructor"""

        # Create Existing Object
        uuid_obj = uuid.UUID(uuid_hex)
        obj = cls(uuid_obj)

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


class UUIDRedisObjectBase(UUIDObject):

    def __init__(self, uuid_obj):
        """Base Constructor"""
        super(UUIDRedisObjectBase, self).__init__(uuid_obj)

        self.obj_key = "{:s}:{:s}".format(self.base_key, repr(self)).lower()

    @classmethod
    def from_existing(cls, uuid_hex):
        """Existing Constructor"""

        # Call Parent
        obj = super(UUIDRedisObjectBase, cls).from_existing(uuid_hex)

        # Verify Object ID in Set
        if not obj.db.exists(obj.obj_key):
            raise UUIDRedisObjectDNE(obj)

        # Return Object
        return obj

    def delete(self):
        """Delete Object"""

        # Delete Object Data from DB
        if not self.db.delete(self.obj_key):
            raise UUIDRedisObjectError("Delete Failed")


class UUIDRedisHashBase(UUIDRedisObjectBase):
    """
    UUID Redis Object Base Class

    """

    schema = _BASE_SCHEMA

    def __init__(self, uuid_obj):
        """Base Constructor"""
        super(UUIDRedisHashBase, self).__init__(uuid_obj)
        self.obj_key = "{:s}:{:s}".format(self.base_key, repr(self)).lower()

    @classmethod
    def from_new(cls, d):
        """New Constructor"""

        # Call Parent
        obj = super(UUIDRedisHashBase, cls).from_new()

        # Set Times
        data = copy.deepcopy(d)
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

    def __copy__(self):
        return self.copy()

    def __deepcopy__(self):
        return self.copy()

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

    def copy(self):
        """ Copy Constructor """

        return self.from_new(self.get_dict)

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


class UUIDRedisFactory(object):

    def __init__(self, redis_db, base_cls, prefix=None):

        # Call Super
        super(UUIDRedisFactory, self).__init__()

        # Check Input
        if not issubclass(base_cls, UUIDRedisObjectBase):
            raise UUIDRedisFactoryError("cls must be subclass of UUIDRedisObjectBase")
        base_name = base_cls.__name__
        if not base_name.endswith(_SUF_BASE):
            raise UUIDRedisFactoryError("cls name must end with '{:s}'".format(_SUF_BASE))

        # Setup Class Name
        cls_name = base_name[0:base_name.rfind(_SUF_BASE)]

        # Setup DB
        self.db = redis_db

        # Setup Base Key
        if prefix == None:
            self.base_key = "{:s}".format(cls_name).lower()
        else:
            self.base_key = "{:s}:{:s}".format(prefix, cls_name).lower()

        # Setup Class
        class cls(base_cls):

            base_key = self.base_key
            db = self.db

        cls.__name__ = cls_name
        self.cls = cls

    def list_objs(self):
        """List Factory Objects"""
        obj_lst = self.db.keys("{:s}:{:s}".format(self.base_key, _UUID_GLOB))
        obj_uuids = []
        for obj_key in obj_lst:
            obj_uuid = obj_key.split(':')[-1]
            obj_uuids.append(obj_uuid)
        return set(obj_uuids)

    def get_objs(self):
        """Get Factory Objects"""
        obj_lst = self.db.keys("{:s}:{:s}".format(self.base_key, _UUID_GLOB))
        objs = []
        for obj_key in obj_lst:
            obj_uuid = obj_key.split(':')[-1]
            obj = cls.from_existing(obj_uuid)
            objs.append(obj)
        return objs

    def from_new(self, *args, **kwargs):
        return self.cls.from_new(*args, **kwargs)

    def from_existing(self, *args, **kwargs):
        return self.cls.from_existing(*args, **kwargs)


class Server(object):
    """
    COGS Server Class

    """

    # Override Constructor
    def __init__(self, redis_db=None):
        """Base Constructor"""

        # Call Parent Construtor
        super(Server, self).__init__()

        # Setup DB
        if not redis_db:
            redis_conf = _REDIS_CONF_DEFAULT
            self.db = redis.StrictRedis(host=redis_conf['redis_host'],
                                        port=redis_conf['redis_port'],
                                        db=redis_conf['redis_db'])
        else:
            self.db = redis_db

        # Setup Factories
        self.AssignmentFactory = UUIDRedisFactory(self.db, AssignmentBase, None)
        self.UserFactory = UUIDRedisFactory(self.db, UserBase, None)

    # Assignment Methods
    def create_assignment(self, d):
        return self.AssignmentFactory.from_new(d)
    def get_assignment(self, uuid_hex):
        return self.AssignmentFactory.from_existing(uuid_hex)
    def get_assignments(self):
        return self.AssignmentFactory.get_objs()
    def list_assignments(self):
        return self.AssignmentFactory.list_objs()

    # User Methods
    def create_user(self, d):
        return self.UserFactory.from_new(d)
    def get_user(self, uuid_hex):
        return self.UserFactory.from_existing(uuid_hex)
    def get_users(self):
        return self.UserFactory.get_objs()
    def list_users(self):
        return self.UserFactory.list_objs()

class UserBase(UUIDRedisHashBase):
    """
    COGS User Class

    """

    schema = _BASE_SCHEMA + _USER_SCHEMA


class AssignmentBase(UUIDRedisHashBase):
    """
    COGS Assignment Class

    """

    schema = _BASE_SCHEMA + _ASSIGNMENTS_SCHEMA

    # Override Constructor
    def __init__(self, uuid_obj):
        """Base Constructor"""
        super(AssignmentBase, self).__init__(uuid_obj)
        self.TestFactory = UUIDRedisFactory(self.db, TestBase, self.obj_key)
        self.SubmissionFactory = UUIDRedisFactory(self.db, SubmissionBase, self.obj_key)

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
        super(AssignmentBase, self).delete()

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


class TestBase(UUIDRedisHashBase):
    """
    COGS Test Class

    """

    schema = _BASE_SCHEMA + _TESTS_SCHEMA

    # Override Constructor
    def __init__(self, uuid_obj):
        """Base Constructor"""
        super(TestBase, self).__init__(uuid_obj)
        self.FileFactory = UUIDRedisFactory(self.db, FileBase, self.obj_key)

    # Override Delete
    def delete(self):
        """Delete"""

        # Delete Files
        for f_uuid in self.list_files():
            fle = self.get_file(f_uuid)
            fle.delete(force=True)

        # Delete Self
        super(TestBase, self).delete()

    # File Methods
    def create_file(self, d, file_obj):
        return self.FileFactory.from_new(d, file_obj)
    def get_file(self, uuid_hex):
        return self.FileFactory.from_existing(uuid_hex)
    def get_files(self):
        return self.FileFactory.get_objs()
    def list_files(self):
        return self.FileFactory.list_objs()

class SubmissionBase(UUIDRedisHashBase):
    """
    COGS Submission Class

    """

    schema = _BASE_SCHEMA + _SUBMISSIONS_SCHEMA

    # Override Constructor
    def __init__(self, uuid_obj):
        """Base Constructor"""
        super(SubmissionBase, self).__init__(uuid_obj)
        self.FileFactory = UUIDRedisFactory(self.db, FileBase, self.obj_key)
        self.RunFactory = UUIDRedisFactory(self.db, RunBase, self.obj_key)

    # Override Delete
    def delete(self):
        """Delete"""

        # Delete Files
        for f_uuid in self.list_files():
            fle = self.get_file(f_uuid)
            fle.delete(force=True)

        # Delete Runs
        for r_uuid in self.list_runs():
            run = self.get_run(r_uuid)
            run.delete()

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

class RunBase(UUIDRedisHashBase):
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
        run = super(RunBase, cls).from_new(data)

        # Get Files
        tst_fls = tst.get_files()
        sub_fls = sub.get_files()

        # Grade Run
        env = environment.Env(run, tst_fls, sub_fls)
        tester = tester_script.Tester(env)
        ret, score, output = tester.test()
        env.close()

        # Set Results
        run['status'] = str(ret)
        run['score'] = str(score)
        run['output'] = str(output)

        # Return Run
        return run


class FileBase(UUIDRedisHashBase):
    """
    COGS File Class

    """

    schema = _BASE_SCHEMA + _FILES_SCHEMA

    # Override from_new
    @classmethod
    def from_new(cls, d, file_obj=None, dst=None):
        """New Constructor"""

        # Create New Object
        data = copy.deepcopy(d)

        # Setup file_obj
        if file_obj is None:
            src_path = os.path.abspath("{:s}".format(data['path']))
            src_file = open(src_path, 'rb')
            file_obj = werkzeug.datastructures.FileStorage(stream=src_file, filename=data['name'])
        else:
            data['name'] = str(file_obj.filename)
            data['path'] = ""

        # Get Type
        typ = mimetypes.guess_type(file_obj.filename)
        data['type'] = str(typ[0])
        data['encoding'] = str(typ[1])

        # Create File
        fle = super(FileBase, cls).from_new(data)

        # Set Path
        if dst is None:
            fle['path'] = os.path.abspath("{:s}/{:s}".format(_FILES_DIR, repr(fle)))
        else:
            fle['path'] = os.path.abspath("{:s}".format(dst))

        # Save File
        try:
            file_obj.save(fle['path'])
            file_obj.close()
        except IOError:
            # Clean up on failure
            fle.delete(force=True)
            raise

        # Return File
        return fle

    # Override Copy
    def copy(self, dst=None):
        """Copy Constructor"""
        return self.from_new(self.get_dict(), None, dst)

    # Override Delete
    def delete(self, force=False):
        """Delete Object"""

        # Delete File
        try:
            os.remove(self['path'])
        except OSError:
            if force:
                pass
            else:
                raise

        # Delete Self
        super(FileBase, self).delete()
