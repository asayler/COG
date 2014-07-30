# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import os
import uuid

import redis

_ENCODING = 'utf-8'

_REDIS_HOST = "localhost"
_REDIS_PORT = 6379
_REDIS_DB   = 3

_ASSIGNMENTS_SCHEMA  = ['name', 'contact']
ASSIGNMENT_TESTDICT  = {'name': "Test_Assignment",
                        'contact': "Andy Sayler"}

_TESTS_SCHEMA = ['name', 'contact', 'type', 'maxscore']
TEST_TESTDICT = {'name': "Test_Assignment",
                 'contact': "Andy Sayler",
                 'type': "script",
                 'maxscore': "10"}

_SUBMISSION_SCHEMA = ['author', 'date']

_FILES_SCHEMA = ['name', 'contact', 'type']
_FILES_PATH = "./files/"

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

    schema = []

    def __init__(self, uuid_obj):
        """Base Constructor"""
        super(UUIDRedisObject, self).__init__()
        self.uuid = uuid_obj
        self.obj_key = "{:s}:{:s}".format(self.base_key, repr(self)).lower()

    @classmethod
    def get_factory(cls, parent_str):
        cls.db = redis.StrictRedis(host=_REDIS_HOST, port=_REDIS_PORT, db=_REDIS_DB)
        if parent_str == None:
            cls.base_key = "{:s}".format(cls.__name__).lower()
        else:
            cls.base_key = "{:s}:{:s}".format(parent_str, cls.__name__).lower()
        return cls

    @classmethod
    def list_objs(cls):
        """List Class Objects"""
        objs_in = cls.db.keys("{:s}:{:s}".format(cls.base_key, _UUID_GLOB))
        objs_out = []
        for obj in objs_in:
            objs_out.append(obj.split(':')[-1])
        return set(objs_out)

    @classmethod
    def from_new(cls, d):
        """New Constructor"""

        # Create New Object
        uuid_obj = uuid.uuid4()
        obj = cls(uuid_obj)

        # Check dict
        if (set(d.keys()) != set(obj.schema)):
            raise KeyError("Keys {:s} do not match schema {:s}".format(d, obj.schema))

        # Add Object Data to DB
        if not obj.db.hmset(obj.obj_key, d):
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
        d = self.db.hgetall(self.obj_key)
        return d

    def set_dict(self, d):
        """Set Dict"""

        # Check dict
        if (set(d.keys()) != set(self.schema)):
            raise KeyError("Keys {:s} do not match schema {:s}".format(d, self.schema))

        # Set dict
        self.db.hmset(self.obj_key, d)


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
    def list_assignments(self):
        return self.AssignmentFactory.list_objs()


class Assignment(UUIDRedisObject):
    """
    COGS Assignment Class

    """

    schema = _ASSIGNMENTS_SCHEMA

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
    def list_tests(self):
        return self.TestFactory.list_objs()

    # Submission Methods
    def create_submission(self, d):
        return self.SubmissionFactory.from_new(d)
    def get_submission(self, uuid_hex):
        return self.SubmissionFactory.from_existing(uuid_hex)
    def list_submissions(self):
        return self.SubmissionFactory.list_objs()


class Test(UUIDRedisObject):
    """
    COGS Test Class

    """

    schema = _TESTS_SCHEMA

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
    def list_files(self):
        return self.FileFactory.list_objs()

class Submission(UUIDRedisObject):
    """
    COGS Submission Class

    """

    schema = _SUBMISSION_SCHEMA

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
    def list_files(self):
        return self.FileFactory.list_objs()


class File(UUIDRedisObject):
    """
    COGS File Class

    """

    schema = _FILES_SCHEMA

    # Override from_new
    @classmethod
    def from_new(cls, d, file_obj):
        """New Constructor"""

        # Setup Dict
        d['name'] = file_obj.filename
        d['type'] = None

        # Create File
        fle = super(File, cls).from_new(d)

        # Save File
        fle.path = _FILES_PATH + repr(fle)
        try:
            file_obj.save(fle.path)
        except IOError:
            # Clean up on failure
            fle.delete(force=True)
            raise

        # Return File
        return fle

    # Override from_existing
    @classmethod
    def from_existing(cls, uuid_hex):
        """Existing Constructor"""

        # Get File
        fle = super(File, cls).from_existing(uuid_hex)

        # Setup path
        fle.path = _FILES_PATH + repr(fle)

        # Return File
        return fle

    # Override Delete
    def delete(self, force=False):
        """Delete"""

        # Delete File
        try:
            os.remove(self.path)
        except OSError:
            if force:
                pass
            else:
                raise

        # Delete Self
        super(File, self).delete()
