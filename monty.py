'''
Background:

We have designed a distributed, domain driven microservice platform. Every communication between the domains happen through events.

An event records context and any interesting change that happened in a domain.

event = {
"id" : "<GUID>",
"name": "<EVENT_NAME>",
"context" : {
     <List of Request cookies>
},
"data": {
     <Data describing current event">
},
"time":"<TIMESTAMP>"
}



Question 1:

Build a microservice using your favorite language that serves the following endpoints:

1. GET /health-check

    Return HTTP/204

2. GET /store/<file_name>

Return HTTP/200 with a stream of data stored in <file_name> if file_name is found in

    the local repository (file system for now but extensible to any other storage like s3 in the future)

         HTTP/404 if the file_name is not present in local repository

3. GET /stats

Return HTTP/200 with stats like current QPS, QPM and total number of operations

     handled by the service since it last started by category (call type like create, delete, health check etc)

Also make the service log appropriate events at every relevant moment.



Question 2:

Design a system that collects all the events generated by every microservice in the platform and make it available such that the event data can be played back  to any other subsystem within the platform.

It should be possible to specify the start and end time for the replay, only the events within the start and end time should be replayed. Optimize for speed and reliability.

Thank you,

Ryan
'''
from datetime import datetime as dt
from datetime import timedelta as td
import io
import uuid
import os

from flask import Response, Flask, request

app = Flask(__name__)
app.log = []


# # HELPER METHODS


def qps(log):
    '''
    get # of queries in the last second
    '''
    return len(list(lambda:
                    i for i in log if i['timestamp'] > int((dt.now() - td(seconds=1)).timestamp())))


def qpm(log):
    '''
    get # of queries in the last minute
    '''
    return len(list(lambda:
                    i for i in log if i['timestamp'] > int((dt.now() - td(seconds=60)).timestamp())))


def qpt(logs):
    '''
    get a list of queries by request path
    '''
    path_list = []
    for log in logs:
        if not log['path'] in path_list:
            path_list.append(log['path'])
    c = {}
    for path in path_list:
        c[path] = len(list(lambda:
                           i for i in logs if i['path'] == path))
    return c


# # ROUTES


@app.before_request
def before():
    '''
    before each request, logs are added
    '''
    app.log.append({
        'id': str(uuid.uuid4()),
        'type': request.method,
        'path': request.path,
        'timestamp': int(dt.now().timestamp())
    })


@app.route('/health-check', methods=['GET'])
def health_check():
    '''
    1. GET /health-check

        Return HTTP/204
    '''
    return "", 204


@app.route('/store/<filename>', methods=['GET'])
def store(filename):
    '''
    2. GET /store/<file_name>

    Return HTTP/200 with a stream of data stored in <file_name> if file_name is found in

        the local repository (file system for now but extensible to any other storage like s3 in the future)

            HTTP/404 if the file_name is not present in local repository

    '''
    def stream():
        with open(filename) as data:
            for line in data:
                yield str(line)

    if os.path.exists(os.getcwd() + '/' + filename):
        with io.StringIO(filename) as data:
            return Response(stream())

    else:
        return "File not Found", 404


@app.route('/stats')
def stats():
    '''
    3. GET /stats

    Return HTTP/200 with stats like current QPS, QPM and total number of operations

        handled by the service since it last started by category (call type like create, delete, health check etc)

    Also make the service log appropriate events at every relevant moment.
    '''
    return {
        'Requests in last second': qps(app.log),
        'Requests in last minute': qpm(app.log),
        'Requests by path since init': qpt(app.log)
    }


if __name__ == '__main__':
    app.run(debug=True)
