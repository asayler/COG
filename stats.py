#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Spring 2015
# University of Colorado

import sys
import cogs.structs

srv = cogs.structs.Server()

def assignment_stats(uuid):

    asn = srv.get_assignment(uuid)
    print(asn)

if __name__ == "__main__":

    for asn_uuid in srv.list_assignments():
        assignment_stats(asn_uuid)
