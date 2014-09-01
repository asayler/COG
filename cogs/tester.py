# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado


import abc


class Tester(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, env, tst, run):
        self.env = env
        self.tst = tst
        self.run = run

    def _format_msg(self, msg):
        return "{:s}: {:s}".format(repr(self.run), msg)

    @abc.abstractmethod
    def test(self):

        # Set Vars
        ret = -1
        score = "0"
        stderr = "Dummer Tester Test()"

        # Return
        return ret, score, stderr
