#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

### Imports ###

import time
import os

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


### Global Setup ###

app = flask.Flask(__name__)
httpauth = flask.ext.httpauth.HTTPBasicAuth()
srv = cogs.structs.Server()
auth = cogs.auth.Auth()


### Functions ###

## Authentication Functions ##

@httpauth.verify_password
def verify_login(username, password):

    flask.g.user = None

    # Username:Password Case
    if password:
        user = auth.auth_userpass(username, password)
        if user:
            flask.g.user = user
            return True
        elif user == False:
            return False
        else:
            try:
                user = auth.create_user({}, username=username, password=password)
            except cogs.auth.BadCredentialsError:
                return False
            else:
                flask.g.user = user
                return True
    # Token Case
    else:
        user = auth.auth_token(username)
        if user:
            flask.g.user = user
            return True
        else:
            return False

## Helper Functions ##

def error_response(e, status):

    err = { 'status': status,
            'message': str(e) }
    err_res = flask.jsonify(err)
    err_res.status_code = err['status']
    return err_res

def create_stub_json(func_create):

    data = flask.request.get_json(force=True)
    obj = func_create(data, owner=flask.g.user)
    obj_lst = list([str(obj.uuid)])
    return obj_lst

def create_stub_file(func_create):

    obj_lst = []
    files = flask.request.files
    for key in files:
        data = {}
        data['key'] = str(key)
        file_obj = files[key]
        obj = func_create(data, file_obj=file_obj, owner=flask.g.user)
        obj_lst.append([str(obj.uuid)])
    return lst

def update_stub_json(obj):

    data = flask.request.get_json(force=True)
    obj.set_dict(data)
    obj_dict = obj.get_dict()
    return obj_dict

def process_objects(func_list, func_create, key, create_stub=create_stub_json):

    # List Objects
    if flask.request.method == 'GET':

        obj_lst = list(func_list())

    # Create Object
    elif flask.request.method == 'POST':
        try:
            obj_lst = create_stub(func_create)
        except KeyError as e:
            return error_response(e, 400)

    # Bad Method
    else:
        raise Exception("Unhandled Method")

    # Return Object List
    out = {key: obj_lst}
    return flask.jsonify(out)

def process_object(func_get, obj_uuid, update_stub=update_stub_json):

    # Lookup Object
    try:
        obj = func_get(obj_uuid)
    except cogs.structs.ObjectDNE as e:
        return error_response(e, 404)

    # Get Object
    if flask.request.method == 'GET':
        obj_dict = obj.get_dict()

    # Update Object
    elif flask.request.method == 'PUT':
        try:
            obj_dict = update_stub(obj)
        except KeyError as e:
            return error_response(e, 400)

    # Delete Object
    elif flask.request.method == 'DELETE':
        obj_dict = obj.get_dict()
        obj.delete()

    # Bad Method
    else:
        raise Exception("Unhandled Method")

    # Return Object
    out = {str(obj.uuid): obj_dict}
    return flask.jsonify(out)


### Endpoints ###

## Root Endpoints ##

@app.route("/",
           methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def get_root():

    res = _MSG_ROOT
    return res

## Access Control Endpoints ##

# ToDo: All of Them...

## Assignment Endpoints ##

@app.route("/assignments/", methods=['GET', 'POST'])
@httpauth.login_required
@auth.requires_auth_route()
def process_assignments():
    return process_objects(srv.list_assignments, srv.create_assignment, _ASSIGNMENTS_KEY)

@app.route("/assignments/<obj_uuid>/", methods=['GET', 'PUT', 'DELETE'])
@httpauth.login_required
@auth.requires_auth_route()
def process_assignment(obj_uuid):
    return process_object(srv.get_assignment, obj_uuid)

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

@app.errorhandler(cogs.auth.UserNotAuthorizedError)
def not_authorized(error):
    err = { 'status': 401,
            'message': str(error) }
    res = flask.jsonify(err)
    res.status_code = err['status']
    return res

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
