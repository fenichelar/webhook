#!/usr/bin/env python


import os, sys, json, cgi, cgitb
from collections import namedtuple
from subprocess import Popen, PIPE


def main():
    cgitb.enable()

    config = getConfig('config.json')
    path, command = getAction(config)
    script = 'cd "' + path + '" && ' + command
    stdout, stderr = execute(script)

    if(stderr):
        respond(500, stderr)
    else:
        respond(200, stdout)


def getConfig(configFile):
    configDir = os.path.dirname(os.path.realpath(sys.argv[0]))
    configPath = os.path.join(configDir, configFile)

    try:
        configJSON = open(configPath).read()
    except:
        respond(500, 'Unable to load JSON configuration file: ' + configPath + '\n')

    try:
        configData = json.loads(configJSON)
        repositoryList = []
        for e in configData['repository']:
            repositoryList.append(namedtuple('repository', e.keys())(*e.values()))
    except:
        respond(500, 'Unable to parse JSON configuration file: ' + configPath + '\n')

    for repository in repositoryList:
        if(not hasattr(repository, 'name')):
            respond(500, 'Missing "name" string in JSON configuration for repository\n')

        if(not hasattr(repository, 'url')):
            respond(500, 'Missing "url" string in JSON configuration for repository: ' + repository.name + '\n')

        if(not hasattr(repository, 'path')):
            respond(500, 'Missing "path" string in JSON configuration for repository: ' + repository.name + '\n')

        if(not hasattr(repository, 'secret')):
            respond(500, 'Missing "secret" string in JSON configuration for repository: ' + repository.name + '\n')

        if(not hasattr(repository, 'method')):
            respond(500, 'Missing "method" array in JSON configuration for repository: ' + repository.name + '\n')

        if(not hasattr(repository, 'command')):
            espond(500, 'Missing "command" object in JSON configuration for repository: ' + repository.name + '\n')

        path = repository.path
        gitPath = os.path.join(path, '.git')

        if(not os.path.isdir(path)):
            respond(500, 'Unable to find directory: ' + path + '\n')
        if(not os.path.isdir(gitPath)):
            respond(500, 'Unable to find directory: ' + gitPath + '\n')

    return repositoryList


def getAction(config):
    method = os.environ['REQUEST_METHOD']

    if(method == 'POST'):
        jsonPayload = sys.stdin.read()
        payload = json.loads(jsonPayload)
        url = payload['repository']['url']
        repository = getRepository(config, '', url)
        #rawCommand = cgi.parse_header('X-GitHub-Event')
        rawCommand = 'pull'

    elif(method == 'GET'):
        form = cgi.FieldStorage()
        name = form.getvalue('repo')
        repository = getRepository(config, name, '')
        rawCommand = form.getvalue('cmd')

    if(method.lower() not in repository.method):
        respond(405, 'Invalid method.')

    command = getCommand(repository, rawCommand)
    path = repository.path

    return (path, command)


def getRepository(config, name, url):
    for repository in config:
        if(repository.name == name or repository.url == url):
            return repository

    respond(400, 'Invalid repository.')


def getCommand(repository, cmd):
    if(not cmd):
        cmd = 'default'

    if(cmd in repository.command):
        return repository.command[cmd]

    respond(400, 'Invalid command.')


def execute(script):
    process = Popen(script, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    return (stdout, stderr)


def respond(code, message):
    method = os.environ['REQUEST_METHOD']

    if(code >= 500):
        title = 'Server Error'
    elif(code >= 400):
        title = 'Client Error'
    elif(code >= 300):
        title = 'Redirection'
    elif(code >= 200):
        title = 'Success'
    else:
        title = 'Informational'

    if(method == 'GET'):
        sendMessage(title, message)
    elif(method == 'POST'):
        sendStatus(code, message)
    else:
        sendStatus(405, 'Method Not Allowed')

    if(code >= 200):
        sys.exit(message)
    else:
        sys.exit(0)


def sendStatus(code, message):
    responses = {
        100: 'Continue', 101: 'Switching Protocols',
        200: 'OK', 201: 'Created', 202: 'Accepted', 203: 'Non-Authoritative Information', 204: 'No Content', 205: 'Reset Content', 206: 'Partial Content',
        300: 'Multiple Choices', 301: 'Moved Permanently', 302: 'Found', 303: 'See Other', 304: 'Not Modified', 305: 'Use Proxy', 306: '(Unused)', 307: 'Temporary Redirect',
        400: 'Bad Request', 401: 'Unauthorized', 402: 'Payment Required', 403: 'Forbidden', 404: 'Not Found', 405: 'Method Not Allowed', 406: 'Not Acceptable', 407: 'Proxy Authentication Required', 408: 'Request Timeout', 409: 'Conflict', 410: 'Gone', 411: 'Length Required', 412: 'Precondition Failed', 413: 'Request Entity Too Large', 414: 'Request-URI Too Long', 415: 'Unsupported Media Type', 416: 'Requested Range Not Satisfiable', 417: 'Expectation Failed',
        500: 'Internal Server Error', 501: 'Not Implemented', 502: 'Bad Gateway', 503: 'Service Unavailable', 504: 'Gateway Timeout', 505: 'HTTP Version Not Supported',
    }

    status = 'Status: ' + str(code) + responses.get(code, 'Unknow Status Code')
    print status
    print
    print message


def sendMessage(title, message):
    print 'Content-type:text/html'
    print
    print '<h1>' + title + '</h1>'
    print '<p>' + message + '</p>'



main()
