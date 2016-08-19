COG: Computerized Online Grading
================================

By [Andy Sayler](https://www.andysayler.com)
University of Colorado, Boulder

About
-----

COG is a modular and scalable grading framework for student
programming assignments designed to support a wide range of use cases
and development techniques. COG aims to provide a versatile set of
abstractions capable of accommodating a range of automated grading use
cases. COG provides a Python-based grading backend, a RESTfull API,
and multiple user frontends (see below). It also supports plugins for
interfacing with external systems like Moodle, etc. COG is Free
Software, licensed under the terms of the AGPL.

Status
------

COG is currently running in Beta in production using v2 of the
API. Bug reports, patches, and comments welcome.

[![Build Status](https://travis-ci.org/asayler/COG.svg?branch=master)](https://travis-ci.org/asayler/COG)

Setup
-----

Pull submodules:

```
$ make git
```

Install apt reqs:

```
$ sudo apt-get install -y libffi-dev libssl-dev dos2unix
$ sudo apt-get install -y redis-server
```

Install pip reqs:

```
$ make reqs
```
*Note: It is probably best to use
 [virtualenvs](http://docs.python-guide.org/en/latest/dev/virtualenvs/)
 to setup a local COG environment. But if you're looking to setup COG
 without virtualenvs, you'll need to append `sudo` to the command
 above.*

Setup conf:

```
$ sudo make conf
```

Testing
-------

The unit tests currently rely on an external Moodle test server for
testing Moodle API functionality. This server lives at
https://moodle-test.cs.colorado.edu. You'll need accounts on that
server to run the tests. Alternatively, spin up your own Moodle test
server and use that (and the appropriate credentials) instead.

To run the unit tests, first setup the necessary environment
variables:

```
$ export COGS_TEST_MOODLE_HOST='https://moodle-test.cs.colorado.edu'
$ export COGS_TEST_AUTHMOD_MOODLE_STUDENT_USERNAME='<Moodle Student Username>'
$ export COGS_TEST_AUTHMOD_MOODLE_STUDENT_PASSWORD='<Moodle Student Password>'
$ export COGS_TEST_REPMOD_MOODLE_USERNAME='<Moodle Instructor Username>'
$ export COGS_TEST_REPMOD_MOODLE_PASSWORD='<Moodle Instructor Password>'
$ export COGS_ENV_LOCAL_LIMIT_TIME_CPU=0.1
$ export COGS_ENV_LOCAL_LIMIT_TIME_WALL=1
```

Then, launch the tests (these can take 15 to 20 minutes to run
depending on the speed of your machine):

```
$ make tests
```

*Note: A race condition will occur if multiple sets of unit tests are
 run simultaneously. This is due to the fact that multiple tests all
 depend on modifying a single set of common Moodle assignments, and if
 multiple tests are thus run in parallel, they will thrash each
 other's modifications. To avoid these issues, run the tests
 sequentially and avoid launching multiple unit tests at the same time
 (including via the CI system).*

Related
-------

 * [COG-Web](https://github.com/asayler/COG-Web): Web Front-end
 * [COG-CLI](https://github.com/asayler/COG-CLI): CLI Front-end

Licensing
---------

Copyright 2014, 2015 by Andy Sayler

This file is part of COG.

COG is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

COG is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
License for more details.

You should have received a copy of the GNU Affero General Public
License along with COG (see COPYING).  If not, see
http://www.gnu.org/licenses/.

<!---
LocalWords:  RESTfull Moodle AGPL reqs libffi dev libssl virtualenvs
LocalWords:  submodules unix AUTHMOD REPMOD ENV Affero
LocalWords:  MERCHANTABILITY
-->
