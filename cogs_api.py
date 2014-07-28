#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import flask

import cogs.datatypes as datatypes

app = flask.Flask(__name__)

_MSG_ROOT = "Welcome to the CU CS Online Grading System API"

### Endpoints

@app.route("/", methods=['GET'])
def get_root():
    res = _MSG_ROOT
    return res

@app.route("/assignments/", methods=['GET'])
def get_assignments():
    s = datatypes.Server()
    assignments = s.assignments_list()
    out = {'assignments': list(assignments)}
    res = flask.jsonify(out)
    return res

@app.route("/assignments/", methods=['POST'])
def create_assignment():

    # Create Assignment
    d = flask.request.get_json(force=True)
    try:
        a = datatypes.Assignment.from_new(d)
    except KeyError as e:
        err = {
            'status': 400,
            'message': str(e)
        }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Return Assignment
    out = {repr(a): a.get_dict()}
    res = flask.jsonify(out)
    return res

@app.route("/assignments/<uuid_hex>/", methods=['GET'])
def get_assignment(uuid_hex):

    # Get Assignment
    try:
        a = datatypes.Assignment.from_existing(uuid_hex)
    except datatypes.UUIDRedisObjectDNE as e:
        err = {
            'status': 404,
            'message': str(e)
        }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Return Assignment
    out = {repr(a): a.get_dict()}
    res = flask.jsonify(out)
    return res

@app.route("/assignments/<uuid_hex>/", methods=['PUT'])
def set_assignment(uuid_hex):

    # Get Assignment
    try:
        a = datatypes.Assignment.from_existing(uuid_hex)
    except datatypes.UUIDRedisObjectDNE as e:
        err = {
            'status': 404,
            'message': str(e)
        }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Update Assignment
    d = flask.request.get_json(force=True)
    try:
        a.set_dict(d)
    except KeyError as e:
        err = {
            'status': 400,
            'message': str(e)
        }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Return Assignment
    out = {repr(a): a.get_dict()}
    res = flask.jsonify(out)
    return res

@app.route("/assignments/<uuid_hex>/", methods=['DELETE'])
def delete_assignment(uuid_hex):

    # Get Assignment
    try:
        a = datatypes.Assignment.from_existing(uuid_hex)
    except datatypes.UUIDRedisObjectDNE as e:
        err = {
            'status': 404,
            'message': str(e)
        }
        err_res = flask.jsonify(err)
        err_res.status_code = err['status']
        return err_res

    # Delete Assignment
    a.delete()

    # Return Null
    out = {}
    res = flask.jsonify(out)
    return res

### Exceptions

@app.errorhandler(400)
def bad_request(error=False):
    message = {
            'status': 400,
            'message': "Malformed request"
    }
    res = flask.jsonify(message)
    res.status_code = 400
    return res

@app.errorhandler(404)
def not_found(error=False):
    message = {
            'status': 404,
            'message': "Not Found: {:s}".format(request.url)
    }
    res = flask.jsonify(message)
    res.status_code = 404
    return res


if __name__ == "__main__":
    app.run(debug=True)
