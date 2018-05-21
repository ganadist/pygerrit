# vim: ts=4 sw=4 sts=4 et ai

# The MIT License
#
# Copyright 2018 YOUNG HO CHA <ganadist at gmail dot com>. All rights reserved.
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
    Works with Python 2.7/3.6
    No Error Handlers
    No Docs
    No Testcases
    Just ONE file

"""
import json
import os
import requests
import sys

from requests.utils import get_netrc_auth
from requests.compat import urlparse, cookielib, quote_plus

PY2 = sys.version_info.major == 2
if PY2:
    from types import FunctionType
    _builtin_super = super
    # copy from
    # https://github.com/PythonCharmers/python-future/blob/master/src/future/builtins/newsuper.py#L45
    def super():
        f = sys._getframe(1)
        typ = object
        type_or_obj = f.f_locals[f.f_code.co_varnames[0]]
        try:
            mro = type_or_obj.__mro__
        except (AttributeError, RuntimeWarning):
            mro = type_or_obj.__class__.__mro__

        for typ in mro:
            for meth in typ.__dict__.values():
                try:
                    while not isinstance(meth, FunctionType):
                        if isinstance(meth, property):
                            meth = meth.fget
                        else:
                            try:
                                meth = meth.__func__
                            except AttributeError:
                                meth = meth.__get__(type_or_obj, typ)
                except (AttributeError, TypeError):
                    continue
                if meth.func_code is f.f_code:
                    break
            else:
                continue
            break
        else:
            raise RuntimeError('super() called outside a method')

        return _builtin_super(typ, type_or_obj)


GERRIT_AUTH_SUFFIX = "/a"
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


class EndpointBase(dict):
    def __init__(self, parent, endpoint, arg = {}, key = 'id'):
        super().__init__(arg)

        self.parent = parent
        self.url = parent.url
        self.session = parent.session
        if arg:
            endpoint = endpoint.format(arg[key])
        self.endpoint = parent.endpoint + endpoint

    def make_url(self, suffix, args):
        if suffix:
            suffix = suffix.format(*args)
        return '{0}{1}{2}'.format(self.url, self.endpoint, suffix), self.session

    def __str__(self):
        return 'Endpoint({0}{1}) :{2}'.format(self.url, self.endpoint, dict.__str__(self))


class ProjectBranch(EndpointBase):
    def __init__(self, parent, branch):
        # XXX
        ref = branch['ref']
        assert ref.startswith('refs/heads/')
        branch['id'] = ref[len('refs/heads/'):]

        super().__init__(parent, '/branches/{0}', branch)

    @RestApi(method = 'DELETE')
    def delete(self):
        pass


class ProjectTag(EndpointBase):
    def __init__(self, parent, tag):
        # XXX
        ref = tag['ref']
        assert ref.startswith('refs/tags/')
        tag['id'] = ref[len('refs/tags/'):]

        super().__init__(parent, '/tags/{0}', tag)

    @RestApi(method = 'DELETE')
    def delete(self):
        pass


class Project(EndpointBase):
    """
    Wrapper of https://gerrit-review.googlesource.com/Documentation/rest-api-projects.html#get-project
    """
    def __init__(self, parent, project):
        super().__init__(parent, '/{0}', project)

    @RestApi('/description')
    def getDescription(self):
        pass

    @RestApi('/description', method = 'PUT')
    def setDescription(self, description = '', commit_message = ''):
        pass

    @RestApi('/description', method = 'DELETE')
    def deleteDescription(self):
        pass

    @RestApi('/parent')
    def getParent(self):
        pass

    @RestApi('/parent', method = 'PUT')
    def setParent(self, parent, **kwds):
        pass

    @RestApi('/HEAD')
    def getHead(self):
        pass

    @RestApi('/HEAD', method = 'PUT')
    def setHead(self, ref = ''):
        pass

    @RestApi('/statistics.git')
    def getStatistics(self):
        pass

    @RestApi('/config')
    def getConfig(self):
        pass

    @RestApi('/config', method = 'PUT')
    def setConfig(self, description = '', **kwds ):
        pass

    @RestApi('/gc', method = 'POST')
    def runGc(self, show_progress=False, aggressive=False, async=False):
        pass

    @RestApi('/ban', method = 'PUT')
    def ban(self, commits = [], reason = ''):
        pass

    @RestApi('/access')
    def getAccess(self):
        pass

    @RestApi('/access', method = 'POST')
    def setAccess(self, **kwds):
        pass

    @RestApi('/index', method = 'POST')
    def reindex(self):
        pass

    @RestApi('/branches/')
    def listBranches(self, **kwds):
        pass

    @RestApi('/branches/{0}')
    def getBranch(self, name):
        pass

    def branch(self, name):
        return ProjectBranch(self, self.getBranch(name))

    def branches(self, **kwds):
        for br in self.listBranches(**kwds):
            ref = br['ref']
            if ref.startswith('refs/heads/'):
                yield ProjectBranch(self, br)

    @RestApi('/branches/{0}', method = 'PUT')
    def createBranch(self, name, revision='HEAD'):
        pass

    @RestApi('/branches:delete', method = 'POST')
    def deleteBranches(self, branches=[]):
        pass

    @RestApi('/tags/')
    def listTags(self, **kwds):
        pass

    @RestApi('/tags/{0}')
    def getTag(self, name):
        pass

    def tag(self, name):
        return ProjectTag(self, self.getTag(name))

    def tags(self, **kwds):
        for tag in self.listTags(**kwds):
            ref = tag['ref']
            if ref.startswith('refs/tags/'):
                yield ProjectTag(self, tag)

    @RestApi('/tags/{0}', method = 'PUT')
    def createTag(self, name, revision='HEAD', **kwds):
        pass

    @RestApi('/tags:delete', method = 'POST')
    def deleteTags(self, tags = []):
        pass

class Projects(EndpointBase):
    """
    Wrapper of https://gerrit-review.googlesource.com/Documentation/rest-api-projects.html#list-projects
    """
    def __init__(self, parent):
        super().__init__(parent, '/projects')

    @RestApi('/')
    def _list(self, **kwds):
        pass

    def list(self, **kwds):
        for project in self._list(**kwds).values():
            yield Project(self, project)

    @RestApi('/{0}', method = 'PUT')
    def create(self, name, parent = '', description = '',
            permissions_only = False, create_empty_commit = False ):
        pass

    @RestApi('/{0}')
    def getProject(self, name):
        pass

    def __getitem__(self, name):
        name = quote_plus(name)
        return Project(self, self.getProject(name))

    def __iter__(self):
        return self.list()


class Account(EndpointBase):
    """
    Wrapper of https://gerrit-review.googlesource.com/Documentation/rest-api-accounts.html#get-detail
    """
    def __init__(self, parent, id):
        super().__init__(parent, '/{0}', id, key = '_account_id')

    @RestApi('/detail')
    def getDetail(self):
        pass

    @RestApi('/name')
    def getName(self):
        pass

    @RestApi('/name', method = 'PUT')
    def setName(self, **kwds):
        pass

    @RestApi('/name', method = 'DELETE')
    def delete(self):
        pass

    @RestApi('/status')
    def getStatus(self):
        pass

    @RestApi('/status', method = 'PUT')
    def setStatus(self, **kwds):
        pass

    @RestApi('/username')
    def getUsername(self):
        pass
        
    @RestApi('/username', method = 'PUT')
    def setUsername(self, **kwds):
        pass
 
    @RestApi('/active')
    def getActive(self):
        pass

    @RestApi('/active', method = 'PUT')
    def setActive(self):
        pass

    @RestApi('/active', method = 'DELETE')
    def deleteActive(self):
        pass


class Accounts(EndpointBase):
    """
    Wrapper of https://gerrit-review.googlesource.com/Documentation/rest-api-accounts.html#query-account
    """
    def __init__(self, parent):
        super().__init__(parent, '/accounts')

    @RestApi('/')
    def _query(self, q = '', **kwds):
        pass

    def query(self, q, **kwds):
        for item in self._query(q = q, **kwds):
            yield Account(self, item)

    @RestApi('/{0}', method = 'PUT')
    def create(self, account, name = '', email = '', groups = []):
        pass

    @RestApi('/{0}')
    def getAccount(self, name):
        pass

    def __getitem__(self, name):
        return Account(self, self.getAccount(name))


class Revision(EndpointBase):
    """
    Wrapper of https://gerrit-review.googlesource.com/Documentation/rest-api-changes.html#revision-endpoints
    """
    def __init__(self, parent, revision):
        super().__init__(parent, '/revisions/{0}', revision)

    @RestApi('/commit')
    def getCommit(self):
        pass

    @RestApi('/description')
    def getDescription(self):
        pass

    @RestApi('/description', method = 'PUT')
    def setDescription(self, description = ''):
        pass

    @RestApi('/review')
    def getReview(self):
        pass

    @RestApi('/review', method = 'POST')
    def setReview(self, labels = {}, **kwds):
        pass

    @RestApi('/related')
    def getRelated(self):
        pass

    @RestApi('/submit', method = 'POST')
    def submit(self):
        pass

    @RestApi('/rebase', method = 'POST')
    def rebase(self):
        pass


class Change(EndpointBase):
    def __init__(self, parent, name):
        super().__init__(parent, '/{0}', name)

    @RestApi('/detail')
    def getDetail(self):
        pass

    @RestApi('/message', method = 'PUT')
    def setMessage(self, **kwds):
        pass

    @RestApi('/topic')
    def getTopic(self):
        pass

    @RestApi('/topic', method = 'PUT')
    def setTopic(self, topic = ''):
        pass

    @RestApi('/topic', method = 'DELETE')
    def deleteTopic(self):
        pass

    @RestApi('/submit', method = 'POST')
    def submit(self, **kwds):
        pass

    def current(self):
        rev = self.get('current_revision')
        if rev:
            return Revision(self, rev)

    def revisions(self):
        for rev in self.get('revisions', []):
            yield Revision(self, rev)


class Changes(EndpointBase):
    """
    Wrapper of https://gerrit-review.googlesource.com/Documentation/rest-api-changes.html#change-endpoints
    """
    def __init__(self, parent):
        super().__init__(parent, '/changes')

    @RestApi('/')
    def _query(self, q = '', **kwds):
        pass

    def query(self, q, **kwds):
        o = kwds.setdefault('o', [])
        o += ['CURRENT_REVISION', 'ALL_REVISIONS']

        for item in self._query(q = q, **kwds):
            yield Change(self, item)

    @RestApi('/{0}')
    def getChange(self, change, **kwds):
        pass

    def __getitem__(self, id):
        change = self.getChange(id, o = ['CURRENT_REVISION', 'ALL_REVISIONS'])
        return Change(self, change)

class Accesses(EndpointBase):
    def __init__(self, parent):
        super().__init__(parent, '/access')

    @RestApi('/?project={0}')
    def list(self, project):
        pass

class Gerrit(EndpointBase):
    def __init__(self, url):
        self.url = url.rstrip('/')
        self.session = requests.session()
        self.endpoint = ''

        hostname = urlparse(self.url).netloc
        HAVE_AUTH = False

        # load gitcookies
        gitcookies = os.path.expanduser('~/.gitcookies')
        if os.path.isfile(gitcookies):
            cookiejar = cookielib.MozillaCookieJar()
            cookiejar.load(gitcookies, ignore_discard=True, ignore_expires=True)
            HAVE_AUTH = any(filter(lambda x: x.domain == hostname, cookiejar))
            if HAVE_AUTH:
                self.session.cookies = cookiejar

        # load netrc
        auth = get_netrc_auth(self.url)
        if auth:
            username, password = auth
            self.session.auth = requests.auth.HTTPBasicAuth(username, password)
            HAVE_AUTH = True

        if HAVE_AUTH and not self.url.endswith(GERRIT_AUTH_SUFFIX):
            self.url += GERRIT_AUTH_SUFFIX

        super().__init__(self, '')

        self.projects = Projects(self)
        self.changes = Changes(self)
        self.accounts = Accounts(self)
        self.accesses = Accesses(self)

    def query(self, q, **kwds):
        return self.changes.query(q, **kwds)


if __name__ == '__main__':
    #g = Gerrit('http://sel-gerrit2018.wrs.com/r')
    g = Gerrit('https://android-review.googlesource.com')

    for project in g.projects:
        print(project)
    for branch in g.projects['platform/manifest'].branches():
        print(branch)

    for item in g.query('is:open owner:ganadist@gmail.com'):
        print(item)

    print()
    print(g.changes[55205])
    print(g.accounts['ganadist@gmail.com'])
