# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

# pylint: disable=no-member

import copy
import time
import uuid

import redis

import backend
from backend import BackendError, FactoryError, ObjectError, ObjectDNE


_REDIS_CONF_DEFAULT = {'redis_host': "localhost",
                       'redis_port': 6379,
                       'redis_db': 4}


### Objects ###

class ObjectBase(backend.ObjectBase):

    @classmethod
    def from_new(cls, key=None):
        """New Constructor"""

        obj = super(ObjectBase, cls).from_new(key)
        if obj.db.exists(obj.full_key):
            raise ObjectError("Key already exists in DB")
        return obj

    @classmethod
    def from_existing(cls, key):
        """Existing Constructor"""

        obj = super(ObjectBase, cls).from_existing(key)
        if not obj.db.exists(obj.full_key):
            raise ObjectDNE(obj)
        return obj

    def delete(self):
        """Delete Object"""

        super(ObjectBase, self).delete()

        if not self.db.delete(self.full_key):
            raise ObjectError("Delete Failed")


class Factory(backend.Factory):

    def __init__(self, base_cls, prefix=None, db=None):

        # Setup DB
        if not db:
            db = redis.StrictRedis(host=_REDIS_CONF_DEFAULT['redis_host'],
                                   port=_REDIS_CONF_DEFAULT['redis_port'],
                                   db=_REDIS_CONF_DEFAULT['redis_db'])

        # Call Parent
        super(Factory, self).__init__(base_cls, prefix=prefix, db=db)

    def list_family(self):
        """List Factory Objects"""
        if self.pre_key:
            p = "{:s}{:s}".format(self.pre_key, backend._FIELD_SEP)
        else:
            p = ""
        q = "{:s}*".format(p)
        fam_lst = self.db.keys(q)
        fam_keys = set([])
        for full_key in fam_lst:
            fam_id = full_key[len(p): ]
            fam_key = fam_id[(fam_id.find(backend._TYPE_SEP) + 1): ]
            fam_keys.add(fam_key)
        return fam_keys


class UUIDFactory(Factory):

    def from_new(self, *args, **kwargs):
        key = uuid.uuid4()
        obj = super(UUIDFactory, self).from_new(*args, key=key, **kwargs)
        obj.uuid = key
        return obj

    def from_existing(self, uuid_str, *args, **kwargs):
        key = uuid.UUID(str(uuid_str))
        obj = super(UUIDFactory, self).from_existing(key, *args, **kwargs)
        obj.uuid = key
        return obj


class HashBase(ObjectBase):
    """
    Redis Hash Base Class

    """

    schema = None

    @classmethod
    def from_new(cls, d, key=None):
        """New Constructor"""

        # Check Input
        if not d:
            raise ObjectError("Input dict must not be None or empty")

        # Call Parent
        obj = super(HashBase, cls).from_new(key)

        # Check dict
        if obj.schema:
            s = set(d.keys())
            if (s != obj.schema):
                raise KeyError("Keys {:s} do not match schema {:s}".format(s, obj.schema))

        # Add Object Data to DB
        if not obj.db.hmset(obj.full_key, d):
            raise ObjectError("Create Failed")

        # Return Object
        return obj

    def __getitem__(self, k):
        """Get Dict Item"""

        if self.schema is not None:
            if k not in self.schema:
                raise KeyError("Key {:s} not valid in {:s}".format(k, self))

        ret = self.db.hget(self.full_key, k)
        if not ret:
            raise KeyError("Key {:s} not found in {:s}".format(k, self))

        return ret

    def __setitem__(self, k, v):
        """Set Dict Item"""

        if self.schema is not None:
            if k not in self.schema:
                raise KeyError("Key {:s} not valid in {:s}".format(k, self))

        ret = self.db.hset(self.full_key, k, v)

        return ret

    def get_dict(self):
        """Get Full Dict"""

        ret = self.db.hgetall(self.full_key)
        if not ret:
            raise ObjectError("Get Failed")

        return ret

    def set_dict(self, d):
        """Set Full Dict"""

        if self.schema is not None:
            s = set(d.keys())
            if not s.issubset(self.schema):
                raise KeyError("Keys {:s} do not match schema {:s}".format(s, self.schema))

        ret = self.db.hmset(self.full_key, d)
        if not ret:
            raise ObjectError("Set Failed")


class TSHashBase(HashBase):
    """
    Time-stamped Hash Base Class
    """

    @classmethod
    def from_new(cls, d, key=None):
        """New Constructor"""

        # Set Times
        data = copy.deepcopy(d)
        t = str(time.time())
        data['created_time'] = t
        data['modified_time'] = t

        # Call Parent
        obj = super(TSHashBase, cls).from_new(data, key)

        # Return Object
        return obj

    def __setitem__(self, k, v):
        """Set Item"""

        # Set Time
        data = {}
        data['modified_time'] = str(time.time())

        # Set Value
        data[k] = v

        # Call Parent
        ret = super(TSHashBase, self).set_dict(data)

        # Return
        return ret

    def set_dict(self, d):
        """Set Dict"""

        # Set Time
        data = copy.deepcopy(d)
        data['modified_time'] = str(time.time())

        # Call Parent
        ret = super(TSHashBase, self).set_dict(data)

        # Return
        return ret


class SetBase(ObjectBase):
    """
    Redis Set Base Class

    """

    @classmethod
    def from_new(cls, v, key=None):
        """New Constructor"""

        # Check Input
        if not v:
            raise ObjectError("Input set must not be None or empty")

        # Call Parent
        obj = super(SetBase, cls).from_new(key)

        # Add lst to DB
        if not obj.db.sadd(obj.full_key, *v):
            raise ObjectError("Create Failed")

        # Return Object
        return obj

    def get_set(self):
        """Get All Vals from Set"""

        return self.db.smembers(self.full_key)

    def add_vals(self, v):
        """Add Vals to Set"""

        return self.db.sadd(self.full_key, *v)

    def del_vals(self, v):
        """Remove Vals from Set"""

        return self.db.srem(self.full_key, *v)
