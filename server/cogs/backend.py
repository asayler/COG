# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import abc

_ENCODING = 'utf-8'
_FIELD_SEP = ':'
_TYPE_SEP = '+'

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

        super(ObjectBase, self).__init__()

        if key:
            if _FIELD_SEP in str(key):
                raise ObjectError("Key may not contain '{:s}'".format(_FIELD_SEP))
            if _TYPE_SEP in str(key):
                raise ObjectError("Key may not contain '{:s}'".format(_TYPE_SEP))

        if key:
            self.obj_key = str(key)
        else:
            self.obj_key = ""
        self.obj_rid = str(self)

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
