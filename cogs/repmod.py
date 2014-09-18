# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado


import abc


class ReporterError(Exception):
    """Base class for Reporter Exceptions"""

    def __init__(self, *args, **kwargs):

        # Call Parent
        super(ReporterError, self).__init__(*args, **kwargs)


class Reporter(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, rpt, run):
        self._rpt = rpt
        self._run = run

    def _format_msg(self, msg):
        return "{:s}: {:s}".format(str(self._run), msg)

    @abc.abstractmethod
    def file_report(self, usr, grade, comment):
        pass
