# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import uuid

import redis

_ENCODING = 'utf-8'

_REDIS_HOST = "localhost"
_REDIS_PORT = 6379
_REDIS_DB   = 3

_KEY_ASSIGNMENTS = "assignments"

# assignment:
#     name
#     contact
#     permissions <Future>


# Exceptions

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

# Objects

class RedisObject(object):
    """
    Redis Object Base Class

    """

    def __init__(self):
        """Base Constructor"""
        super(RedisObject, self).__init__()
        self.db = redis.StrictRedis(host=_REDIS_HOST, port=_REDIS_PORT, db=_REDIS_DB)


class UUIDRedisObject(RedisObject):
    """
    UUID Redis Object Base Class

    """

    def __init__(self, uuid_obj):
        """Base Constructor"""
        super(UUIDRedisObject, self).__init__()
        self.uuid = uuid_obj

    @classmethod
    def from_new(cls):
        """New Constructor"""
        uuid_obj = uuid.uuid4()
        return cls(uuid_obj)

    @classmethod
    def from_existing(cls, uuid_hex):
        """Exisiting Constructor"""
        uuid_obj = uuid.UUID(uuid_hex)
        return cls(uuid_obj)

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


class Server(RedisObject):
    """
    COGS Server Class

    """

    def __init__(self):
        """Base Constructor"""
        super(Server, self).__init__()

    def assignments_list(self):
        return self.db.smembers(_KEY_ASSIGNMENTS)

class Assignment(UUIDRedisObject):
    """
    COGS Assignment Class

    """

    def __init__(self, uuid_obj):
        """Base Constructor"""
        super(Assignment, self).__init__(uuid_obj)
        self.key = "{:s}:{:s}".format(_KEY_ASSIGNMENTS, repr(self))

    @classmethod
    def from_new(cls, a_dict):
        """New Constructor"""

        # Create Assignment
        asn = super(Assignment, cls).from_new()

        # Create Atomic Pipeline
        p = asn.db.pipeline(transaction=True)
        # Add Assingment ID to Set
        p.sadd(_KEY_ASSIGNMENTS, repr(asn))
        # Add Assignment Data to DB
        p.hmset(asn.key, a_dict)
        # Execute Pipeline
        if not all(p.execute()):
            raise UUIDRedisObjectError("Create Failed")

        # Return Assignment
        return asn

    @classmethod
    def from_existing(cls, uuid_hex):
        """Existing Constructor"""

        # Create Assignment
        asn = super(Assignment, cls).from_existing(uuid_hex)

        # Verify Assignment ID in Set
        if not asn.db.sismember(_KEY_ASSIGNMENTS, repr(asn)):
            raise UUIDRedisObjectDNE(asn)

        # Return Assignment
        return asn

    def delete(self):
        """Delete Assignment"""

        # Create Atomic Pipeline
        p = self.db.pipeline(transaction=True)
        # Delete Assignment Data from DB
        p.delete(self.key)
        # Remove Assingment ID from Set
        p.srem(_KEY_ASSIGNMENTS, repr(self))
        # Execute Pipeline
        if not all(p.execute()):
            return False
        else:
            return True
