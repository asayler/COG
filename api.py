#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import time

import flask
import flask.ext.httpauth

import redis

import cogs.auth
import cogs.structs

### Constants ###

_MSG_ROOT = "Welcome to the CU CS Online Grading System API\n"

_ASSIGNMENTS_KEY = "assignments"
_TESTS_KEY = "tests"
_SUBMISSIONS_KEY = "submissions"
_FILES_KEY = "files"
_RUNS_KEY = "runs"

_DEFAULT_AUTHMOD = 'moodle'

_REDIS_CONF= {'redis_host': "localhost",
              'redis_port': 6379,
              'redis_db': 3}

### Global Setup ###

app = flask.Flask(__name__)
auth = flask.ext.httpauth.HTTPBasicAuth()
redis_conf = _REDIS_CONF
db = redis.StrictRedis(host=redis_conf['redis_host'],
                       port=redis_conf['redis_port'],
                       db=redis_conf['redis_db'])
srv = cogs.structs.Server(db)

@auth.verify_password
def verify_login(username, password):

    flask.g.user = None

    # Username:Password Case
    if password:
        user = srv.auth_user(username, password)
        if user:
            flask.g.user = user
            return True
        elif user_uuid == False:
            return False
        else:
            try:
                user = srv._create_user({}, username=username, password=password)
            except cogs.auth.BadCredentialsError:
                return False
            else:
                flask.g.user = user
                return True
    # Token Case
    else:
        user = srv.auth_token(username)
        if user:
            flask.g.user = user
            return True
        else:
            return False

### Endpoints ###

## Root Endpoints ##


@app.route("/",
           methods=['GET'])
@auth.login_required
def get_root():
    res = _MSG_ROOT
    return res

## Access Control Endpoints ##


## Assignment Endpoints ##

@app.route("/assignments/",
           methods=['GET', 'POST'])
def process_assignments():

    # Process
    if flask.request.method == 'GET':
        # Get Assignments
        out = {_ASSIGNMENTS_KEY: list(srv.list_assignments())}
    elif flask.request.method == 'POST':
        # Create Assignment
        d = flask.request.get_json(force=True)
        try:
            asn = srv.create_assignment(d)
        except KeyError as e:
            err = { 'status': 400,
                    'message': str(e) }
            err_res = flask.jsonify(err)
            err_res.status_code = err['status']
            return err_res
        else:
            out = {_ASSIGNMENTS_KEY: list([str(asn.uuid)])}
    else:
        raise Exception("Unhandled Method")

    # Return Assignment List
    res = flask.jsonify(out)
    return res

@app.route("/assignments/<uuid_hex>/",
           methods=['GET', 'PUT', 'DELETE'])
def process_assignment(uuid_hex):

    # Get Assignment
    try:
        a = s.get_assignment(uuid_hex)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Process
    if flask.request.method == 'GET':
        # Get Assignment
        out = {str(a.uuid): a.get_dict()}
    elif flask.request.method == 'PUT':
        # Update Assignment
        d = flask.request.get_json(force=True)
        try:
            a.set_dict(d)
        except KeyError as e:
            err = { 'status': 400,
                    'message': str(e) }
            err_res = flask.jsonify(err)
            err_res.status_code = err['status']
            return err_res
        else:
            out = {str(a.uuid): a.get_dict()}
    elif flask.request.method == 'DELETE':
        # Delete Assignment
        out = {str(a.uuid): a.get_dict()}
        a.delete()
    else:
        raise Exception("Unhandled Method")

    # Return Assignment
    res = flask.jsonify(out)
    return res


## Test Endpoints ##

@app.route("/assignments/<asn_uuid>/tests/",
           methods=['GET', 'POST'])
def process_tests(asn_uuid):

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Process
    if flask.request.method == 'GET':
        # Get Tests
        out = {_TESTS_KEY: list(asn.list_tests())}
    elif flask.request.method == 'POST':
        # Create Test
        d = flask.request.get_json(force=True)
        try:
            tst = asn.create_test(d)
        except KeyError as e:
            err = { 'status': 400,
                    'message': str(e) }
            err_res = flask.jsonify(err)
            err_res.status_code = err['status']
            return err_res
        else:
            out = {_TESTS_KEY: list([str(tst.uuid)])}
    else:
        raise Exception("Unhandled Method")

    # Return Test List
    res = flask.jsonify(out)
    return res

@app.route("/assignments/<asn_uuid>/tests/<tst_uuid>/",
           methods=['GET', 'PUT', 'DELETE'])
def process_test(asn_uuid, tst_uuid):

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get Test
    try:
        tst = asn.get_test(tst_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Process
    if flask.request.method == 'GET':
        # Get Assignment
        out = {str(tst.uuid): tst.get_dict()}
    elif flask.request.method == 'PUT':
        # Update Assignment
        d = flask.request.get_json(force=True)
        try:
            tst.set_dict(d)
        except KeyError as e:
            err = { 'status': 400,
                    'message': str(e) }
            err_res = flask.jsonify(err)
            err_res.status_code = err['status']
            return err_res
        else:
            out = {str(tst.uuid): tst.get_dict()}
    elif flask.request.method == 'DELETE':
        # Delete Assignment
        out = {str(tst.uuid): tst.get_dict()}
        tst.delete()
    else:
        raise Exception("Unhandled Method")

    # Return Test
    res = flask.jsonify(out)
    return res

## Test File Endpoints ##

@app.route("/assignments/<asn_uuid>/tests/<tst_uuid>/files/",
           methods=['GET', 'POST'])
def process_test_files(asn_uuid, tst_uuid):

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get Test
    try:
        tst = asn.get_test(tst_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Process
    if flask.request.method == 'GET':
        # Get Test Files
        fle_lst = list(tst.list_files())
    elif flask.request.method == 'POST':
        # Create Test File
        d = {}
        fle_lst = []
        files = flask.request.files
        for f in files:
            f_data = files[f]
            d['key'] = str(f)
            try:
                fle = tst.create_file(d, f_data)
            except KeyError as e:
                err = { 'status': 400,
                        'message': str(e) }
                err_res = flask.jsonify(err)
                err_res.status_code = err['status']
                return err_res
            else:
             fle_lst.append(str(fle.uuid))
    else:
        raise Exception("Unhandled Method")

    # Return Test File List
    out = {_FILES_KEY: fle_lst}
    res = flask.jsonify(out)
    return res

@app.route("/assignments/<asn_uuid>/tests/<tst_uuid>/files/<fle_uuid>/",
           methods=['GET', 'DELETE'])
def process_test_file(asn_uuid, tst_uuid, fle_uuid):

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get Test
    try:
        tst = asn.get_test(tst_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get File
    try:
        fle = tst.get_file(fle_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Process
    if flask.request.method == 'GET':
        # Get File
        out = {str(fle.uuid): fle.get_dict()}
    elif flask.request.method == 'DELETE':
        # Delete File
        out = {str(fle.uuid): fle.get_dict()}
        fle.delete()
    else:
        raise Exception("Unhandled Method")

    # Return Test
    res = flask.jsonify(out)
    return res

## Submission Endpoints ##

@app.route("/assignments/<asn_uuid>/submissions/",
           methods=['GET', 'POST'])
def process_submissions(asn_uuid):

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Process
    if flask.request.method == 'GET':
        # Get Submissions
        out = {_SUBMISSIONS_KEY: list(asn.list_submissions())}
    elif flask.request.method == 'POST':
        # Create Submission
        d = flask.request.get_json(force=True)
        try:
            sub = asn.create_submission(d)
        except KeyError as e:
            err = { 'status': 400,
                    'message': str(e) }
            err_res = flask.jsonify(err)
            err_res.status_code = err['status']
            return err_res
        else:
            out = {_SUBMISSIONS_KEY: list([str(sub.uuid)])}
    else:
        raise Exception("Unhandled Method")

    # Return Submission List
    res = flask.jsonify(out)
    return res

@app.route("/assignments/<asn_uuid>/submissions/<sub_uuid>/",
           methods=['GET', 'PUT', 'DELETE'])
def process_submission(asn_uuid, sub_uuid):

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get Submission
    try:
        sub = asn.get_submission(sub_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Process
    if flask.request.method == 'GET':
        # Get Assignment
        out = {str(sub.uuid): sub.get_dict()}
    elif flask.request.method == 'PUT':
        # Update Assignment
        d = flask.request.get_json(force=True)
        try:
            sub.set_dict(d)
        except KeyError as e:
            err = { 'status': 400,
                    'message': str(e) }
            err_res = flask.jsonify(err)
            err_res.status_code = err['status']
            return err_res
        else:
            out = {str(sub.uuid): sub.get_dict()}
    elif flask.request.method == 'DELETE':
        # Delete Assignment
        out = {str(sub.uuid): sub.get_dict()}
        sub.delete()
    else:
        raise Exception("Unhandled Method")

    # Return Test
    res = flask.jsonify(out)
    return res

## Submission File Endpoints ##

@app.route("/assignments/<asn_uuid>/submissions/<sub_uuid>/files/",
           methods=['GET', 'POST'])
def process_submission_files(asn_uuid, sub_uuid):

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get Submission
    try:
        sub = asn.get_submission(sub_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Process
    if flask.request.method == 'GET':
        # Get Submission Files
        fle_lst = list(sub.list_files())
    elif flask.request.method == 'POST':
        # Create Test File
        d = {}
        fle_lst = []
        files = flask.request.files
        for f in files:
            f_data = files[f]
            d['key'] = str(f)
            try:
                fle = sub.create_file(d, f_data)
            except KeyError as e:
                err = { 'status': 400,
                        'message': str(e) }
                err_res = flask.jsonify(err)
                err_res.status_code = err['status']
                return err_res
            else:
             fle_lst.append(str(fle.uuid))
    else:
        raise Exception("Unhandled Method")

    # Return Test File List
    out = {_FILES_KEY: fle_lst}
    res = flask.jsonify(out)
    return res

@app.route("/assignments/<asn_uuid>/submissions/<sub_uuid>/files/<fle_uuid>/",
           methods=['GET', 'DELETE'])
def process_submission_file(asn_uuid, sub_uuid, fle_uuid):

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get Submission
    try:
        sub = asn.get_submission(sub_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get File
    try:
        fle = sub.get_file(fle_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Process
    if flask.request.method == 'GET':
        # Get File
        out = {str(fle.uuid): fle.get_dict()}
    elif flask.request.method == 'DELETE':
        # Delete File
        out = {str(fle.uuid): fle.get_dict()}
        fle.delete()
    else:
        raise Exception("Unhandled Method")

    # Return Test
    res = flask.jsonify(out)
    return res

## Run Endpoints ##

@app.route("/assignments/<asn_uuid>/submissions/<sub_uuid>/runs/",
           methods=['GET', 'POST'])
def process_runs(asn_uuid, sub_uuid):

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get Submission
    try:
        sub = asn.get_submission(sub_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Process
    if flask.request.method == 'GET':
        # Get Runs
        run_lst = list(sub.list_runs())
    elif flask.request.method == 'POST':
        # Execute Runs
        run_lst = []
        for tst_uuid in asn.list_tests():
            tst = asn.get_test(tst_uuid)
            try:
                run = sub.execute_run(tst, sub)
            except KeyError as e:
                err = { 'status': 400,
                        'message': str(e) }
                err_res = flask.jsonify(err)
                err_res.status_code = err['status']
                return err_res
            else:
                run_lst.append(str(run.uuid))
    else:
        raise Exception("Unhandled Method")

    # Return Run List
    out = {_RUNS_KEY: run_lst}
    res = flask.jsonify(out)
    return res

@app.route("/assignments/<asn_uuid>/submissions/<sub_uuid>/runs/<run_uuid>/",
           methods=['GET', 'DELETE'])
def process_run(asn_uuid, sub_uuid, run_uuid):

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get Submission
    try:
        sub = asn.get_submission(sub_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get Run
    try:
        run = sub.get_run(run_uuid)
    except cogs.structs.ObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Process
    if flask.request.method == 'GET':
        # Get Run
        out = {str(run.uuid): run.get_dict()}
    elif flask.request.method == 'DELETE':
        # Delete Assignment
        out = {str(run.uuid): run.get_dict()}
        run.delete()
    else:
        raise Exception("Unhandled Method")

    # Return Test
    res = flask.jsonify(out)
    return res


### Exceptions

@app.errorhandler(400)
def bad_request(error=False):
    err = { 'status': 400,
                'message': "Malformed request" }
    res = flask.jsonify(err)
    res.status_code = err['status']
    return res

@app.errorhandler(404)
def not_found(error=False):
    err = { 'status': 404,
            'message': "Not Found: {:s}".format(flask.request.url) }
    res = flask.jsonify(err)
    res.status_code = err['status']
    return res

@app.errorhandler(405)
def bad_method(error=False):
    err = { 'status': 405,
            'message': "Bad Method: {:s} {:s}".format(flask.request.method, flask.request.url) }
    res = flask.jsonify(err)
    res.status_code = err['status']
    return res

if __name__ == "__main__":

    app.run(debug=True)
