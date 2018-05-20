# vim: ts=4 sw=4 sts=4 et ai

# The MIT License
#
# Copyright 2018 YOUNG HO CHA <ganadist<at>gmail<dot>com>. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


"""
Very thin gerrit REST API wrapper for python

Features:
    Works with Python 3.6
    No Error Handlers
    No Docs
    No Testcases
    Just ONE file

"""

import json
import os
import requests
from requests.utils import get_netrc_auth

GERRIT_MAGIC_JSON_PREFIX = ")]}\'\n"


class RestApi(object):
    def __init__(self, endPointSuffix = '', method = 'GET'):
        self.suffix = endPointSuffix
        self.method = method

    def __call__(self, f):
        def new_f(endpoint, *args, **kwds):
            url, session = endpoint.make_url(self.suffix, args)

            payload = kwds
            if self.method == 'GET':
                kwds = {}
                kwds['params'] = payload
            else:
                kwds = {}
                kwds['json'] = payload

            response = {
                    'GET': session.get,
                    'POST' : session.post,
                    'PUT': session.put,
                    'DELETE' : session.delete,
            }[self.method](url, **kwds)

            # copy from 
            # https://github.com/dpursehouse/pygerrit2/blob/master/pygerrit2/rest/__init__.py#L33
            content = response.content.strip()
            if response.encoding:
                content = content.decode(response.encoding)
            response.raise_for_status()
            content_type = response.headers.get('content-type', '')
            if content_type.split(';')[0] != 'application/json':
                return content
            if content.startswith(GERRIT_MAGIC_JSON_PREFIX):
                content = content[len(GERRIT_MAGIC_JSON_PREFIX):]
            try:
                return json.loads(content)
            except ValueError:
                raise

        return new_f


class EndpointBase(object):
    def __init__(self, parent, endpoint, *args):
        self.parent = parent
        self.url = parent.url
        self.session = parent.session
        self.endpoint = parent.endpoint + endpoint.format(*args)

    def make_url(self, suffix, args):
        if suffix:
            suffix = suffix.format(*args)
        return '{0}{1}{2}'.format(self.url, self.endpoint, suffix), self.session


class Project(EndpointBase):
    """
    Wrapper of https://gerrit-review.googlesource.com/Documentation/rest-api-projects.html#get-project
    """
    def __init__(self, parent, id):
        super().__init__(parent, '{0}/', id)

    @RestApi('description')
    def getDescription(self):
        pass

    @RestApi('description', method = 'PUT')
    def setDescription(self, description = '', commit_message = ''):
        pass

    @RestApi('description', method = 'DELETE')
    def deleteDescription(self):
        pass

    @RestApi('parent')
    def getParent(self):
        pass

    @RestApi('parent', method = 'PUT')
    def setParent(self, parent, **kwds):
        pass

    @RestApi('HEAD')
    def getHead(self):
        pass

    @RestApi('HEAD', method = 'PUT')
    def setHead(self, ref = ''):
        pass

    @RestApi('statistics.git')
    def getStatistics(self):
        pass

    @RestApi('config')
    def getConfig(self):
        pass

    @RestApi('config', method = 'PUT')
    def setConfig(self, description = '', **kwds ):
        pass

    @RestApi('gc', method = 'POST')
    def runGc(self, show_progress=False, aggressive=False, async=False):
        pass

    @RestApi('ban', method = 'PUT')
    def ban(self, commits = [], reason = ''):
        pass

    @RestApi('access')
    def getAccess(self):
        pass

    @RestApi('access', method = 'POST')
    def setAccess(self, **kwds):
        pass

    @RestApi('index', method = 'POST')
    def reindex(self):
        pass

    @RestApi('branches/')
    def listBranches(self):
        pass

    @RestApi('branches/{0}')
    def getBranch(self, name):
        pass

    @RestApi('branches/{0}', method = 'PUT')
    def createBranch(self, name, revision='HEAD'):
        pass

    @RestApi('branches/{0}', method = 'DELETE')
    def deleteBranch(self, name):
        pass

    @RestApi('branches:delete', method = 'POST')
    def deleteBranches(self, branches=[]):
        pass

    @RestApi('tags/')
    def listTags(self):
        pass

    @RestApi('tags/{0}', method = 'PUT')
    def createTag(self, name, revision='HEAD', **kwds):
        pass

    @RestApi('tags/{0}')
    def getTag(self, name):
        pass

    @RestApi('tags/{0}', method = 'DELETE')
    def deleteTag(self, name):
        pass

    @RestApi('tags:delete', method = 'POST')
    def deleteTags(self, tags = []):
        pass


class Projects(EndpointBase):
    """
    Wrapper of https://gerrit-review.googlesource.com/Documentation/rest-api-projects.html#list-projects
    """
    def __init__(self, parent):
        super().__init__(parent, '/projects/')

    @RestApi()
    def list(self, **kwds):
        pass

    @RestApi('{0}')
    def get(self, name):
        pass

    @RestApi('{0}', method = 'PUT')
    def create(self, name, parent = '', description = '',
            permissions_only = False, create_empty_commit = False ):
        pass

    def __getitem__(self, id):
        id = id.replace('/', '%2F')
        return Project(self, id)


class Account(EndpointBase):
    """
    Wrapper of https://gerrit-review.googlesource.com/Documentation/rest-api-accounts.html#get-detail
    """
    def __init__(self, parent, id):
        super().__init__(parent, '{0}/', id)

    @RestApi('detail')
    def getDetail(self):
        pass

    @RestApi('name')
    def getName(self):
        pass

    @RestApi('name', method = 'PUT')
    def setName(self, **kwds):
        pass

    @RestApi('name', method = 'DELETE')
    def delete(self):
        pass

    @RestApi('status')
    def getStatus(self):
        pass

    @RestApi('status', method = 'PUT')
    def setStatus(self, **kwds):
        pass

    @RestApi('username')
    def getUsername(self):
        pass
        
    @RestApi('username', method = 'PUT')
    def setUsername(self, **kwds):
        pass
 
    @RestApi('active')
    def getActive(self):
        pass

    @RestApi('active', method = 'PUT')
    def setActive(self):
        pass

    @RestApi('active', method = 'DELETE')
    def deleteActive(self):
        pass


class Accounts(EndpointBase):
    """
    Wrapper of https://gerrit-review.googlesource.com/Documentation/rest-api-accounts.html#query-account
    """
    def __init__(self, parent):
        super().__init__(parent, '/accounts/')

    @RestApi('{0}')
    def get(self, account):
        pass

    @RestApi('{0}', method = 'PUT')
    def create(self, account, name = '', email = '', groups = []):
        pass

    def __getitem__(self, id):
        return Account(self, id)

class Revision(EndpointBase):
    """
    Wrapper of https://gerrit-review.googlesource.com/Documentation/rest-api-changes.html#revision-endpoints
    """
    def __init__(self, parent, revision):
        super().__init__(parent, 'revision/{0}/', revision)

    @RestApi('commit')
    def getCommit(self):
        pass

    @RestApi('description')
    def getDescription(self):
        pass

    @RestApi('description', method = 'PUT')
    def setDescription(self, description = ''):
        pass

    @RestApi('review')
    def getReview(self):
        pass

    @RestApi('review', method = 'POST')
    def setReview(self, labels = {}, **kwds):
        pass

    @RestApi('related')
    def getRelated(self):
        pass

    @RestApi('submit', method = 'POST')
    def submit(self):
        pass

    @RestApi('rebase', method = 'POST')
    def rebase(self):
        pass


class Change(EndpointBase):
    def __init__(self, parent, name):
        super().__init__(parent, '{0}/', name)

    @RestApi('detail')
    def getDetail(self):
        pass

    @RestApi('message', method = 'PUT')
    def setMessage(self, **kwds):
        pass

    @RestApi('topic')
    def getTopic(self):
        pass

    @RestApi('topic', method = 'PUT')
    def setTopic(self, topic = ''):
        pass

    @RestApi('topic', method = 'DELETE')
    def deleteTopic(self):
        pass

    @RestApi('submit', method = 'POST')
    def submit(self, **kwds):
        pass

    def _getitem__(self, revision):
        return Revision(self, revision)


class Changes(EndpointBase):
    """
    Wrapper of https://gerrit-review.googlesource.com/Documentation/rest-api-changes.html#change-endpoints
    """
    def __init__(self, parent):
        super().__init__(parent, '/changes/')

    @RestApi()
    def query(self, q = '', **kwds):
        pass

    @RestApi('{0}')
    def get(self, name):
        pass

    def __getitem__(self, id):
        return Change(self, id)

class Accesses(EndpointBase):
    def __init__(self, parent):
        super().__init__(parent, '/access/')

    @RestApi('?project={0}')
    def list(self, project):
        pass

class Gerrit(EndpointBase):
    def __init__(self, url):
        self.url = url.rstrip('/')
        self.session = requests.session()
        self.endpoint = ''

        super().__init__(self, '')

        # load gitcookies
        gitcookies = os.path.expanduser('~/.gitcookies')
        if os.path.isfile(gitcookies):
            from http.cookiejar import MozillaCookieJar
            cookiejar = MozillaCookieJar()
            cookiejar.load(gitcookies, ignore_discard=True, ignore_expires=True)
            self.session.cookies = cookiejar

        # load netrc
        auth = get_netrc_auth(self.url)
        if auth:
            username, password = auth
            self.session.auth = requests.auth.HTTPBasicAuth(username, password)


    def projects(self):
        return Projects(self)

    def changes(self):
        return Changes(self)

    def accounts(self):
        return Accounts(self)

    def accesses(self):
        return Accesses(self)


if __name__ == '__main__':
    #g = Gerrit('http://sel-gerrit2018.wrs.com/r/a')
    g = Gerrit('https://android-review.googlesource.com')
    p = g.projects()
    print(p.list())
    print(p['platform/manifest'].listBranches())
    c = g.changes()
    print(c.query(q = 'is:open owner:ganadist@gmail.com'))
