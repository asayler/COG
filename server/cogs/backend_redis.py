# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

# pylint: disable=no-member

import uuid

import redis

import backend

_ENCODING = 'utf-8'
_SUF_BASE = 'Base'
_REDIS_CONF_DEFAULT = {'redis_host': "localhost",
                       'redis_port': 6379,
                       'redis_db': 4}


### Objects

class ObjectBase(backend.ObjectBase):

    @classmethod
    def from_new(cls, key=None):
        """New Constructor"""

        obj = super(ObjectBase, cls).from_new(key)
        if obj.db.exists(obj.full_key):
            raise backend.ObjectError("Key already exists in DB")
        return obj

    @classmethod
    def from_existing(cls, key):
        """Existing Constructor"""

        obj = super(ObjectBase, cls).from_existing(key)
        if not obj.db.exists(obj.full_key):
            raise backend.ObjectDNE(obj)
        return obj

    def delete(self):
        """Delete Object"""

        super(ObjectBase, self).delete()

        if not self.db.delete(self.full_key):
            raise backend.ObjectError("Delete Failed")


class RedisFactory(object):

    def __init__(self, base_cls, prefix=None, db=None):

        # Call Super
        super(RedisFactory, self).__init__()

        # Check Input
        if not issubclass(base_cls, ObjectBase):
            raise RedisFactoryError("cls must be subclass of ObjectBase")
        base_name = base_cls.__name__
        if not base_name.endswith(_SUF_BASE):
            raise RedisFactoryError("cls name must end with '{:s}'".format(_SUF_BASE))

        # Setup Class Name
        cls_name = base_name[0:base_name.rfind(_SUF_BASE)]

        # Setup DB
        if not db:
            self.db = redis.StrictRedis(host=_REDIS_CONF_DEFAULT['redis_host'],
                                        port=_REDIS_CONF_DEFAULT['redis_port'],
                                        db=_REDIS_CONF_DEFAULT['redis_db'])
        else:
            self.db = db

        # Setup Base Key
        if prefix:
            self.pre_key = str(prefix)
        else:
            self.pre_key = ""

        # Setup Class
        class cls(base_cls):

            pre_key = self.pre_key
            db = self.db

        cls.__name__ = cls_name
        self.cls = cls

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

    def list_siblings(self):
        """List Factory Objects"""
        fam_keys = self.list_family()
        sib_keys = set([])
        for fam_key in fam_keys:
            if backend._FIELD_SEP not in fam_key:
                sib_keys.add(fam_key)
        return sib_keys

    def list_children(self):
        """List Factory Objects"""
        fam_keys = self.list_family()
        chd_keys = set([])
        for fam_key in fam_keys:
            if backend._FIELD_SEP in fam_key:
                chd_keys.add(fam_key)
        return chd_keys

    def get_siblings(self):
        """Get Sibling Objects"""
        siblings = self.list_siblings()
        objs = []
        for sib in siblings:
            objs.append(self.from_existing(sib))
        return objs

    def from_new(self, *args, **kwargs):
        return self.cls.from_new(*args, **kwargs)

    def from_existing(self, *args, **kwargs):
        return self.cls.from_existing(*args, **kwargs)


class RedisUUIDFactory(RedisFactory):

    def from_new(self, *args, **kwargs):
        k = uuid.uuid4()
        return super(RedisUUIDFactory, self).from_new(*args, key=k, **kwargs)


class RedisHashBase(ObjectBase):
    """
    Redis Hash Base Class

    """

    schema = None

    @classmethod
    def from_new(cls, d, key=None):
        """New Constructor"""

        # Check Input
        if not d:
            raise backend.ObjectError("Input dict must not be None or empty")

        # Call Parent
        obj = super(RedisHashBase, cls).from_new(key)

        # Check dict
        if obj.schema:
            s = set(d.keys())
            if (s != obj.schema):
                raise KeyError("Keys {:s} do not match schema {:s}".format(s, obj.schema))

        # Add Object Data to DB
        if not obj.db.hmset(obj.full_key, d):
            raise backend.ObjectError("Create Failed")

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
            raise backend.ObjectError("Get Failed")

        return ret

    def set_dict(self, d):
        """Set Full Dict"""

        if self.schema is not None:
            s = set(d.keys())
            if not s.issubset(self.schema):
                raise KeyError("Keys {:s} do not match schema {:s}".format(s, self.schema))

        ret = self.db.hmset(self.full_key, d)
        if not ret:
            raise backend.ObjectError("Set Failed")


class RedisSetBase(ObjectBase):
    """
    Redis Set Base Class

    """

    @classmethod
    def from_new(cls, v, key=None):
        """New Constructor"""

        # Check Input
        if not v:
            raise backend.ObjectError("Input set must not be None or empty")

        # Call Parent
        obj = super(RedisSetBase, cls).from_new(key)

        # Add lst to DB
        if not obj.db.sadd(obj.full_key, *v):
            raise backend.ObjectError("Create Failed")

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
