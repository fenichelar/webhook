#!/usr/bin/env python


import os, sys, json, cgi, cgitb
from collections import namedtuple
from subprocess import Popen, PIPE


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

    if(not hasattr(repository, 'command')):
      respond(500, 'Missing "command" object in JSON configuration for repository: ' + repository.name + '\n')

    path = repository.path
    gitPath = os.path.join(path, '.git')

    if(not os.path.isdir(path)):
      respond(500, 'Unable to find directory: ' + path + '\n')
    if(not os.path.isdir(gitPath)):
      respond(500, 'Unable to find directory: ' + gitPath + '\n')

  return repositoryList


def getRepository(config, name, url):
  for repository in config:
    if(repository.name == name or repository.url == url):
      return repository

  respond(400, 'Invalid repository.')


def respond(code, message):
  print 'Content-type:text/html'
  print 'Status: ' + str(code) + ' ' + ('Success' if code < 300 else message)
  print
  print '<h1>' + ('Success' if code < 300 else 'Error') + '</h1>'
  print '<p>' + message + '</p>'

  if(code < 300):
    sys.exit(0)
  else:
    sys.exit(message)


cgitb.enable()

config = getConfig('config.json')

method = os.environ['REQUEST_METHOD']
if(method == 'POST'):
  jsonPayload = sys.stdin.read()
  payload = json.loads(jsonPayload)
  url = payload['repository']['url']
  name = payload['repository']['name']
  repository = getRepository(config, name, url)
  rawCommand = 'default'
elif(method == 'GET'):
  form = cgi.FieldStorage()
  name = form.getvalue('repo')
  repository = getRepository(config, name, '')
  rawCommand = form.getvalue('cmd')
else:
  respond(400, 'Invalid method.')

if(not rawCommand):
  rawCommand = 'default'

if(rawCommand in repository.command):
  command = repository.command[rawCommand]
else:
  respond(400, 'Invalid command.')

path = repository.path
script = 'cd "' + path + '" && ' + command
process = Popen(script, shell=True, stdout=PIPE, stderr=PIPE)
stdout, stderr = process.communicate()

if(stderr):
  respond(400, stderr)
else:
  respond(200, stdout)
