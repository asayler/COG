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
    def from_existing(cls, key=None):
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

    def __init__(self, base_cls, prefix=None, db=None, srv=None):

        # Setup DB
        if not db:
            db = redis.StrictRedis(host=_REDIS_CONF_DEFAULT['redis_host'],
                                   port=_REDIS_CONF_DEFAULT['redis_port'],
                                   db=_REDIS_CONF_DEFAULT['redis_db'])

        # Call Parent
        super(Factory, self).__init__(base_cls, prefix=prefix, db=db, srv=srv)

    def list_family(self):
        """List Factory Objects"""
        if self.pre_key:
            p = "{:s}{:s}".format(self.pre_key, backend._FIELD_SEP)
        else:
            p = ""
        q = "{:s}*".format(p)
        fam_lst = self.db.keys(q)
        obj_keys = set([])
        for itm in fam_lst:
            full_key = itm[len(p): ]
            typ_key = full_key[0:full_key.find(backend._TYPE_SEP)]
            obj_key = full_key[(len(typ_key) + 1): ]
            if typ_key.lower() == self.cls_name.lower():
                obj_keys.add(obj_key)
        return obj_keys


class UUIDFactory(Factory):

    def from_new(self, *args, **kwargs):
        key = uuid.uuid4()
        obj = super(UUIDFactory, self).from_new(*args, key=key, **kwargs)
        obj.uuid = key
        return obj

    def from_custom(self, uuid_str, *args, **kwargs):
        key = uuid.UUID(str(uuid_str))
        obj = super(UUIDFactory, self).from_new(*args, key=key, **kwargs)
        obj.uuid = key
        return obj

    def from_existing(self, uuid_str, *args, **kwargs):
        key = uuid.UUID(str(uuid_str))
        obj = super(UUIDFactory, self).from_existing(*args, key=key, **kwargs)
        obj.uuid = key
        return obj

    def from_raw(self, uuid_str, *args, **kwargs):
        key = uuid.UUID(str(uuid_str))
        obj = super(UUIDFactory, self).from_raw(*args, key=key, **kwargs)
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
                raise KeyError("Key {:s} not valid in {:s}".format(str(k), self.schema))

        ret = self.db.hget(self.full_key, k)
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
        return ret

    def set_dict(self, d):
        """Set Full Dict"""

        # Check Input
        if not d:
            raise ObjectError("Input dict must not be None or empty")

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
    def from_new(cls, dictionary, key=None):
        """New Constructor"""

        # Set Times
        data = copy.copy(dictionary)
        t = str(time.time())
        data['created_time'] = t
        data['modified_time'] = t

        # Call Parent
        obj = super(TSHashBase, cls).from_new(data, key=key)

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


class OwnedTSHashBase(TSHashBase):
    """
    Owned and Time-stamped Hash Base Class
    """

    @classmethod
    def from_new(cls, dictionary, key=None, user=None):
        """New Constructor"""

        # Set Owner
        data = copy.copy(dictionary)
        if user:
            data['owner'] = str(user.uuid).lower()
        else:
            data['owner'] = ""

        # Call Parent
        obj = super(OwnedTSHashBase, cls).from_new(data, key=key)

        # Return Run
        return obj


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
