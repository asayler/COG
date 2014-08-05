# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import abc

_ENCODING = 'utf-8'
_FIELD_SEP = ':'
_TYPE_SEP = '+'
_SUF_BASE = 'Base'

assert(_FIELD_SEP != _TYPE_SEP)

### Exceptions ###

class BackendError(Exception):
    """Base class for Backend Exceptions"""

    def __init__(self, *args, **kwargs):
        super(BackendError, self).__init__(*args, **kwargs)

class FactoryError(BackendError):
    """Backend Factory Exceptions"""

    def __init__(self, *args, **kwargs):
        super(FactoryError, self).__init__(*args, **kwargs)

class ObjectError(BackendError):
    """Backend Object Exceptions"""

    def __init__(self, *args, **kwargs):
        super(ObjectError, self).__init__(*args, **kwargs)

class ObjectDNE(ObjectError):
    """Backend Object Exceptions"""

    def __init__(self, obj):
        msg = "{:s} does not exist.".format(obj)
        super(ObjectDNE, self).__init__(msg)


### Helpers ###

class abstractstaticmethod(staticmethod):
    __slots__ = ()
    def __init__(self, function):
        super(abstractstaticmethod, self).__init__(function)
        function.__isabstractmethod__ = True
    __isabstractmethod__ = True


class abstractclassmethod(classmethod):
    __slots__ = ()
    def __init__(self, function):
        super(abstractclassmethod, self).__init__(function)
        function.__isabstractmethod__ = True
    __isabstractmethod__ = True


### Objects ###

class ObjectBase(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, key=None):
        """Base Constructor"""

        # Call Parent
        super(ObjectBase, self).__init__()

        # Input Check Key
        if key:
            if _FIELD_SEP in str(key):
                raise ObjectError("Key may not contain '{:s}'".format(_FIELD_SEP))
            if _TYPE_SEP in str(key):
                raise ObjectError("Key may not contain '{:s}'".format(_TYPE_SEP))

        # Save Object Key
        if key:
            self.obj_key = str(key)
        else:
            self.obj_key = ""
        self.obj_rid = str(self)

        # Compute Full Key
        if self.pre_key and self.obj_key:
            self.full_key = "{:s}{:s}{:s}".format(self.pre_key, _FIELD_SEP, self.obj_rid).lower()
        elif self.pre_key:
            self.full_key = "{:s}".format(self.pre_key).lower()
        elif self.obj_key:
            self.full_key = "{:s}".format(self.obj_rid).lower()
        else:
            raise ObjectError("Either pre_key or full_key required")

    def __unicode__(self):
        """Return Unicode Representation"""
        u = u"{:s}".format(type(self).__name__)
        if self.obj_key:
            u += u"{:s}{:s}".format(_TYPE_SEP, self.obj_key)
        return u

    def __str__(self):
        """Return String Representation"""
        s = unicode(self).encode(_ENCODING)
        return s

    def __repr__(self):
        """Return Unique Representation"""
        r = "{:s}".format(self.full_key)
        return r

    def __hash__(self):
        """Return Hash"""
        return hash(repr(self))

    def __eq__(self, other):
        """Test Equality"""
        return (repr(self) == repr(other))

    def key(self):
        """Return Object Key"""
        return self.obj_key

    @abstractclassmethod
    def from_new(cls, key=None):
        """New Constructor"""
        return cls(key)

    @abstractclassmethod
    def from_existing(cls, key):
        """Existing Constructor"""
        return cls(key)

    @abc.abstractmethod
    def delete(self):
        """Delete Object"""
        pass


class Factory(object):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, base_cls, prefix=None, db=None):

        # Call Parent
        super(Factory, self).__init__()

        # Check Input
        if not issubclass(base_cls, ObjectBase):
            raise FactoryError("cls must be subclass of ObjectBase")
        base_name = base_cls.__name__
        if not base_name.endswith(_SUF_BASE):
            raise FactoryError("cls name must end with '{:s}'".format(_SUF_BASE))

        # Setup Class Name
        cls_name = base_name[0:base_name.rfind(_SUF_BASE)]

        # Setup DB
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

    @abc.abstractmethod
    def list_family(self):
        """List Factory Objects"""
        pass

    def list_siblings(self):
        """List Factory Objects"""
        fam_keys = self.list_family()
        sib_keys = set([])
        for fam_key in fam_keys:
            if _FIELD_SEP not in fam_key:
                sib_keys.add(fam_key)
        return sib_keys

    def list_children(self):
        """List Factory Objects"""
        fam_keys = self.list_family()
        chd_keys = set([])
        for fam_key in fam_keys:
            if _FIELD_SEP in fam_key:
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


class UUIDFactory(Factory):

    def from_new(self, *args, **kwargs):
        k = uuid.uuid4()
        return super(UUIDFactory, self).from_new(*args, key=k, **kwargs)


class HashBase(ObjectBase):
    """
    Hash Base Class

    """

    schema = None

    @abstractclassmethod
    def from_new(cls, d, key=None):
        """New Constructor"""
        pass

    @abc.abstractmethod
    def __getitem__(self, k):
        """Get Dict Item"""
        pass

    @abc.abstractmethod
    def __setitem__(self, k, v):
        """Set Dict Item"""
        pass

    @abc.abstractmethod
    def get_dict(self):
        """Get Full Dict"""
        pass

    @abc.abstractmethod
    def set_dict(self, d):
        """Set Full Dict"""
        pass


class SetBase(ObjectBase):
    """
    Set Base Class

    """

    @classmethod
    def from_new(cls, v, key=None):
        """New Constructor"""
        pass

    def get_set(self):
        """Get All Vals from Set"""
        pass

    def add_vals(self, v):
        """Add Vals to Set"""
        pass

    def del_vals(self, v):
        """Remove Vals from Set"""
        pass
