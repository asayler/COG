#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import flask
import time

import cogs.datatypes as datatypes

app = flask.Flask(__name__)

_MSG_ROOT = "Welcome to the CU CS Online Grading System API"

_ASSIGNMENTS_KEY = "assignments"
_TESTS_KEY = "tests"
_SUBMISSIONS_KEY = "submissions"
_FILES_KEY = "files"
_RUNS_KEY = "runs"

### Endpoints

## Root Endpoints

@app.route("/",
           methods=['GET'])
def get_root():
    res = _MSG_ROOT
    return res

## Assignment Endpoints ##

@app.route("/assignments/",
           methods=['GET', 'POST'])
def process_assignments():

    # Create Server
    srv = datatypes.Server()

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
            out = {_ASSIGNMENTS_KEY: list([repr(asn)])}
    else:
        raise Exception("Unhandled Method")

    # Return Assignment List
    res = flask.jsonify(out)
    return res

@app.route("/assignments/<uuid_hex>/",
           methods=['GET', 'PUT', 'DELETE'])
def process_assignment(uuid_hex):

    # Create Server
    s = datatypes.Server()

    # Get Assignment
    try:
        a = s.get_assignment(uuid_hex)
    except datatypes.UUIDRedisObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Process
    if flask.request.method == 'GET':
        # Get Assignment
        out = {repr(a): a.get_dict()}
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
            out = {repr(a): a.get_dict()}
    elif flask.request.method == 'DELETE':
        # Delete Assignment
        out = {repr(a): a.get_dict()}
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

    # Create Server
    srv = datatypes.Server()

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
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
            out = {_TESTS_KEY: list([repr(tst)])}
    else:
        raise Exception("Unhandled Method")

    # Return Test List
    res = flask.jsonify(out)
    return res

@app.route("/assignments/<asn_uuid>/tests/<tst_uuid>/",
           methods=['GET', 'PUT', 'DELETE'])
def process_test(asn_uuid, tst_uuid):

    # Create Server
    srv = datatypes.Server()

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get Test
    try:
        tst = asn.get_test(tst_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Process
    if flask.request.method == 'GET':
        # Get Assignment
        out = {repr(tst): tst.get_dict()}
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
            out = {repr(tst): tst.get_dict()}
    elif flask.request.method == 'DELETE':
        # Delete Assignment
        out = {repr(tst): tst.get_dict()}
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

    # Create Server
    srv = datatypes.Server()

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get Test
    try:
        tst = asn.get_test(tst_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
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
             fle_lst.append(repr(fle))
    else:
        raise Exception("Unhandled Method")

    # Return Test File List
    out = {_FILES_KEY: fle_lst}
    res = flask.jsonify(out)
    return res

@app.route("/assignments/<asn_uuid>/tests/<tst_uuid>/files/<fle_uuid>/",
           methods=['GET', 'DELETE'])
def process_test_file(asn_uuid, tst_uuid, fle_uuid):

    # Create Server
    srv = datatypes.Server()

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get Test
    try:
        tst = asn.get_test(tst_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get File
    try:
        fle = tst.get_file(fle_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Process
    if flask.request.method == 'GET':
        # Get File
        out = {repr(fle): fle.get_dict()}
    elif flask.request.method == 'DELETE':
        # Delete File
        out = {repr(fle): fle.get_dict()}
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

    # Create Server
    srv = datatypes.Server()

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
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
            out = {_SUBMISSIONS_KEY: list([repr(sub)])}
    else:
        raise Exception("Unhandled Method")

    # Return Submission List
    res = flask.jsonify(out)
    return res

@app.route("/assignments/<asn_uuid>/submissions/<sub_uuid>/",
           methods=['GET', 'PUT', 'DELETE'])
def process_submission(asn_uuid, sub_uuid):

    # Create Server
    srv = datatypes.Server()

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get Submission
    try:
        sub = asn.get_submission(sub_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Process
    if flask.request.method == 'GET':
        # Get Assignment
        out = {repr(sub): sub.get_dict()}
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
            out = {repr(sub): sub.get_dict()}
    elif flask.request.method == 'DELETE':
        # Delete Assignment
        out = {repr(sub): sub.get_dict()}
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

    # Create Server
    srv = datatypes.Server()

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get Submission
    try:
        sub = asn.get_submission(sub_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
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
             fle_lst.append(repr(fle))
    else:
        raise Exception("Unhandled Method")

    # Return Test File List
    out = {_FILES_KEY: fle_lst}
    res = flask.jsonify(out)
    return res

@app.route("/assignments/<asn_uuid>/submissions/<sub_uuid>/files/<fle_uuid>/",
           methods=['GET', 'DELETE'])
def process_submission_file(asn_uuid, sub_uuid, fle_uuid):

    # Create Server
    srv = datatypes.Server()

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get Submission
    try:
        sub = asn.get_submission(sub_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get File
    try:
        fle = sub.get_file(fle_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Process
    if flask.request.method == 'GET':
        # Get File
        out = {repr(fle): fle.get_dict()}
    elif flask.request.method == 'DELETE':
        # Delete File
        out = {repr(fle): fle.get_dict()}
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

    # Create Server
    srv = datatypes.Server()

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get Submission
    try:
        sub = asn.get_submission(sub_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
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
                run = sub.execute_run(tst)
            except KeyError as e:
                err = { 'status': 400,
                        'message': str(e) }
                err_res = flask.jsonify(err)
                err_res.status_code = err['status']
                return err_res
            else:
                run_lst.append(repr(run))
    else:
        raise Exception("Unhandled Method")

    # Return Run List
    out = {_RUNS_KEY: run_lst}
    res = flask.jsonify(out)
    return res

@app.route("/assignments/<asn_uuid>/submissions/<sub_uuid>/runs/<run_uuid>/",
           methods=['GET', 'DELETE'])
def process_run(asn_uuid, sub_uuid, run_uuid):

    # Create Server
    srv = datatypes.Server()

    # Get Assignment
    try:
        asn = srv.get_assignment(asn_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get Submission
    try:
        sub = asn.get_submission(sub_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Get Run
    try:
        run = sub.get_run(run_uuid)
    except datatypes.UUIDRedisObjectDNE as e:
        err = { 'status': 404,
                'message': str(e) }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Process
    if flask.request.method == 'GET':
        # Get Run
        out = {repr(run): run.get_dict()}
    elif flask.request.method == 'DELETE':
        # Delete Assignment
        out = {repr(run): run.get_dict()}
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
