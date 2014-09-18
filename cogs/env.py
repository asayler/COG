# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado


import abc


class Env(object):

    __metaclass__ = abc.ABCMeta

    def _format_msg(self, msg):
        return "{:s}: {:s}".format(str(self._run), msg)

    @abc.abstractmethod
    def __init__(self, asn, sub, tst, run):

        # Public Vars
        self.wd = ""
        self.wd_tst = ""
        self.wd_sub = ""
        self.tst_files = []
        self.sub_files = []

        # Private Vars
        self._asn = asn
        self._run = sub
        self._tst = tst
        self._run = run

    @abc.abstractmethod
    def copy_fle(self, fle, dst_dir):
        pass
        # return new_fle

    @abc.abstractmethod
    def run_cmd(self, user_cmd, stdin=None):
        pass
        # return retval, stdout, stdin

    @abc.abstractmethod
    def close(self):
        pass
