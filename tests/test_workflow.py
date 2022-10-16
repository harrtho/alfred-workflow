#!/usr/bin/env python3
# encoding: utf-8
#
# Copyright (c) 2022 Thomas Harr <xDevThomas@gmail.com>
# Copyright (c) 2019 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2014-03-01
#

"""Unit tests for :mod:`workflow.Workflow`."""

import json
import logging
import os
import sys
from io import StringIO
from unicodedata import normalize

import pytest
from workflow import ICON_WARNING, Variables, Workflow

from tests.conftest import env
from tests.test_util import MockCall


def test_args(alfred4):
    """ARGV"""
    args = ['arg1', 'arg2', 'füntíme']
    oargs = sys.argv[:]
    sys.argv = [oargs[0]] + [s.encode('utf-8') for s in args]
    wf = Workflow()
    try:
        assert wf.args == args
    finally:
        sys.argv = oargs[:]


def test_arg_normalisation(alfred4):
    """ARGV normalisation"""
    def nfdme(s):
        """NFD-normalise string"""
        return normalize('NFD', s)

    args = [nfdme(s) for s in ['arg1', 'arg2', 'füntíme']]
    oargs = sys.argv[:]
    sys.argv = [oargs[0]] + [s.encode('utf-8') for s in args]

    wf = Workflow(normalization='NFD')
    try:
        assert wf.args == args
    finally:
        sys.argv = oargs[:]


def test_magic_args(alfred4):
    """Magic args"""
    # cache original sys.argv
    oargs = sys.argv[:]

    # delsettings
    sys.argv = [oargs[0]] + [b'workflow:delsettings']
    try:
        wf = Workflow(default_settings={'arg1': 'value1'})
        assert wf.settings['arg1'] == 'value1'
        assert os.path.exists(wf.settings_path)
        with pytest.raises(SystemExit):
            wf.args
        assert not os.path.exists(wf.settings_path)
    finally:
        sys.argv = oargs[:]

    # delcache
    sys.argv = [oargs[0]] + [b'workflow:delcache']

    def somedata():
        return {'arg1': 'value1'}

    try:
        wf = Workflow()
        cachepath = wf.cachefile('somedir')
        os.makedirs(cachepath)
        wf.cached_data('test', somedata)
        assert os.path.exists(wf.cachefile('test.pickle'))
        with pytest.raises(SystemExit):
            wf.args
        assert not os.path.exists(wf.cachefile('test.pickle'))
    finally:
        sys.argv = oargs[:]


def test_logger(wf):
    """Logger"""
    assert isinstance(wf.logger, logging.Logger)
    logger = logging.Logger('')
    wf.logger = logger
    assert wf.logger == logger


def test_icons():
    """Icons"""
    import workflow
    for name in dir(workflow):
        if name.startswith('ICON_'):
            path = getattr(workflow, name)
            print(name, path)
            assert os.path.exists(path)


def test_debugging(alfred4):
    """Debugging"""
    tests = [
        ('', False),
        ('0', False),
        ('1', True),
    ]
    for s, wanted in tests:
        with env(alfred_debug=s):
            wf = Workflow()
            assert wf.debugging == wanted, "unexpected debugging"


def test_required_optional(infopl):
    """Item: Required and optional values."""
    wf = Workflow()
    it = wf.add_item('Title')
    assert it.title == 'Title'
    o = it.obj
    assert o['title'] == 'Title'
    assert o['valid'] is False
    assert o['subtitle'] == ''
    assert set(o.keys()) == {'title', 'valid', 'subtitle'}


def test_optional(infopl):
    """Item: Optional values."""
    wf = Workflow()
    it = wf.add_item('Title', 'Subtitle',
                     arg='argument',
                     uid='uid',
                     valid=True,
                     autocomplete='auto',
                     match='match',
                     largetext='large',
                     copytext='copy',
                     quicklookurl='http://www.deanishe.net/alfred-workflow',
                     type='file',
                     icon='icon.png')

    o = it.obj
    assert o['title'] == 'Title'
    assert o['valid'] is True
    assert o['autocomplete'] == 'auto'
    assert o['match'] == 'match'
    assert o['uid'] == 'uid'
    assert o['text']['copy'] == 'copy'
    assert o['text']['largetype'] == 'large'
    assert o['icon']['path'] == 'icon.png'
    assert o['quicklookurl'] == 'http://www.deanishe.net/alfred-workflow'
    assert o['type'] == 'file'


def test_icontype(infopl):
    """Item: Icon type."""
    wf = Workflow()
    it = wf.add_item('Title', icon='icon.png', icontype='filetype')
    o = it.obj
    assert o['icon']['path'] == 'icon.png'
    assert o['icon']['type'] == 'filetype'


def test_feedback(infopl):
    """Workflow: Feedback."""
    wf = Workflow()
    for i in range(10):
        wf.add_item('Title {0:2d}'.format(i + 1))

    orig = sys.stdout
    stdout = StringIO()
    try:
        sys.stdout = stdout
        wf.send_feedback()
    finally:
        sys.stdout = orig

    s = stdout.getvalue()

    assert len(s) > 0

    o = json.loads(s)

    assert isinstance(o, dict)

    items = o['items']

    assert len(items) == 10
    for i in range(10):
        assert items[i]['title'] == 'Title {0:2d}'.format(i + 1)


def test_warn_empty(infopl):
    """Workflow: Warn empty."""
    wf = Workflow()
    it = wf.warn_empty('My warning')

    assert it.title == 'My warning'
    assert it.subtitle == ''
    assert it.valid is False
    assert it.icon == ICON_WARNING

    o = wf.obj

    assert len(o['items']) == 1
    assert o['items'][0] == it.obj

    # Non-empty feedback
    wf = Workflow()
    wf.add_item('Real item')
    it = wf.warn_empty('Warning')

    assert it is None

    o = wf.obj

    assert len(o['items']) == 1


def test_arg_multiple(infopl):
    """Item: multiple args."""
    wf = Workflow()
    arg = ['one', 'two']
    it = wf.add_item('Title', arg=arg)

    o = it.obj
    assert o['arg'] == arg

    o = wf.obj
    assert len(o['items']) == 1
    o = o['items'][0]
    assert o['arg'] == arg


def test_arg_variables(infopl):
    """Item: Variables in arg."""
    wf = Workflow()
    it = wf.add_item('Title')
    it.setvar('key1', 'value1')
    o = it.obj
    assert 'variables' in o
    assert 'config' not in o
    assert o['variables']['key1'] == 'value1'


def test_feedback_variables(infopl):
    """Workflow: feedback variables."""
    wf = Workflow()

    o = wf.obj
    assert 'variables' not in o

    wf.setvar('prevar', 'preval')
    it = wf.add_item('Title', arg='something')
    wf.setvar('postvar', 'postval')

    assert wf.getvar('prevar') == 'preval'
    assert wf.getvar('postvar') == 'postval'
    assert it.getvar('prevar') == 'preval'
    assert it.getvar('postvar') is None

    o = wf.obj
    assert 'variables' in o
    assert o['variables']['prevar'] == 'preval'
    assert o['variables']['postvar'] == 'postval'

    o = it.obj
    assert 'variables' in o
    assert o['variables']['prevar'] == 'preval'
    assert 'postval' not in o['variables']


def test_persistent_variables(alfred4):
    """Persistent variables Alfred 4+"""
    _test_persistent_variables('com.runningwithcrayons.Alfred')


def _test_persistent_variables(appname):
    wf = Workflow()
    o = wf.obj
    assert 'variables' not in o

    name = 'testvar'
    value = 'testval'

    # Without persistence
    with MockCall() as m:
        wf.setvar(name, value)
        assert m.cmd is None

    # With persistence
        script = (
            'Application("' + appname + '")'
            '.setConfiguration("testvar", '
            '{"exportable": false, '
            '"inWorkflow": "de.xdevcloud.alfred-workflow", '
            '"toValue": "testval"});'
        )

    cmd = ['/usr/bin/osascript', '-l', 'JavaScript', '-e', script]
    with MockCall() as m:
        wf.setvar(name, value, True)
        assert m.cmd == cmd


def test_rerun(infopl):
    """Workflow: rerun."""
    wf = Workflow()
    o = wf.obj
    assert 'rerun' not in o
    assert wf.rerun == 0

    wf.rerun = 1

    o = wf.obj
    assert 'rerun' in o
    assert o['rerun'] == 1
    assert wf.rerun == 1


def test_session_id(infopl):
    """Workflow: session_id."""
    wf = Workflow()
    o = wf.obj
    assert 'variables' not in o

    sid = wf.session_id
    assert sid

    o = wf.obj
    assert 'variables' in o
    assert '_WF_SESSION_ID' in o['variables']
    assert o['variables']['_WF_SESSION_ID'] == sid

    # load from environment variable
    sid = 'thisisatest'
    with env(_WF_SESSION_ID=sid):
        wf = Workflow()
        o = wf.obj
        assert 'variables' in o
        assert '_WF_SESSION_ID' in o['variables']
        assert o['variables']['_WF_SESSION_ID'] == sid
        assert wf.session_id == sid


def test_session_cache(infopl):
    """Workflow: session-scoped caching."""
    wf1 = Workflow()
    wf2 = Workflow()
    data1 = {'foo': 'bar'}
    data2 = {'bar': 'foo'}
    # sid = wf.session_id
    wf1.cache_data('data', data1, session=True)
    wf2.cache_data('data', data2, session=True)
    assert wf1.cached_data('data', session=True) == data1
    assert wf2.cached_data('data', session=True) == data2


def test_clear_session_cache(infopl):
    """Workflow: session-scoped caching."""
    wf = Workflow()
    data = {'foo': 'bar'}
    wf.clear_cache()

    assert len(os.listdir(wf.cachedir)) == 0

    # save session and non-session data
    wf.cache_data('data', data, session=True)
    wf.cache_data('data', data, session=False)

    def _sessfiles():
        return [n for n in os.listdir(wf.cachedir)
                if n.startswith('_wfsess-')]

    assert len(_sessfiles()) > 0

    wf.clear_session_cache()

    # current session files kept
    assert len(_sessfiles()) == 1
    assert len(os.listdir(wf.cachedir)) > 0
    assert wf.cached_data('data', session=True) == data
    assert wf.cached_data('data', session=False) == data

    # also clear data for current session
    wf.clear_session_cache(True)

    # sessions files are gone, but other cache files are not
    assert len(_sessfiles()) == 0
    assert len(os.listdir(wf.cachedir)) > 0
    assert wf.cached_data('data', session=True) is None
    assert wf.cached_data('data', session=False) == data


def test_modifiers(infopl):
    """Item: Modifiers."""
    wf = Workflow()
    wf.setvar('wfprevar', 'wfpreval')

    it = wf.add_item('Title', 'Subtitle', arg='value', valid=False)
    it.setvar('prevar', 'preval')
    mod = it.add_modifier('cmd', subtitle='Subtitle2',
                          arg='value2', valid=True)
    it.setvar('postvar', 'postval')
    wf.setvar('wfpostvar', 'wfpostval')
    mod.setvar('modvar', 'hello')

    # assert wf.getvar('prevar') == 'preval'
    # Test variable inheritance
    assert it.getvar('prevar') == 'preval'
    assert mod.getvar('prevar') == 'preval'
    assert it.getvar('postvar') == 'postval'
    assert mod.getvar('postvar') is None

    assert it.getvar('wfprevar') == 'wfpreval'
    assert mod.getvar('wfprevar') == 'wfpreval'
    assert it.getvar('wfpostvar') is None
    assert mod.getvar('wfpostvar') is None

    o = it.obj
    assert 'mods' in o
    assert set(o['mods'].keys()) == {'cmd'}

    m = o['mods']['cmd']
    assert m['valid'] is True
    assert m['subtitle'] == 'Subtitle2'

    assert m['arg'] == 'value2'
    assert m['variables']['prevar'] == 'preval'
    assert m['variables']['modvar'] == 'hello'


def test_modifier_multiple_args(infopl):
    """Item: Modifier multiple args."""
    wf = Workflow()
    arg = ['one', 'two']
    marg = ['three', 'four']
    it = wf.add_item('Title', arg=arg)
    mod = it.add_modifier('cmd', arg=marg)

    o = it.obj
    assert o['arg'] == arg

    assert o['mods']['cmd']['arg'] == marg

    assert mod.arg == marg
    assert mod.obj['arg'] == marg


def test_modifier_icon(infopl):
    """Item: Modifier icon."""
    wf = Workflow()
    it = wf.add_item('Title', 'Subtitle')
    mod = it.add_modifier('cmd', subtitle='Subtitle2',
                          icon='icon.png')
    o = mod.obj
    assert 'icon' in o
    assert o['icon'] == {'path': 'icon.png'}

    mod = it.add_modifier('cmd', subtitle='Subtitle2',
                          icon='/Applications/Safari.app',
                          icontype='fileicon')
    o = mod.obj
    assert 'icon' in o
    assert o['icon'] == {
        'path': '/Applications/Safari.app',
        'type': 'fileicon',
    }


def test_item_config(infopl):
    """Item: Config."""
    wf = Workflow()
    it = wf.add_item('Title')
    it.config['var1'] = 'val1'

    m = it.add_modifier('cmd')
    m.config['var1'] = 'val2'

    o = it.obj

    assert 'config' in o
    assert set(o['config'].keys()) == {'var1'}
    assert o['config']['var1'] == 'val1'

    assert 'mods' in o
    assert 'cmd' in o['mods']
    assert 'config' in o['mods']['cmd']

    o2 = m.obj
    c = o2['config']
    assert c['var1'] == 'val2'


def _test_default_directories(data, cache):
    wf3 = Workflow()
    assert wf3.datadir.startswith(data), "unexpected data directory"
    assert wf3.cachedir.startswith(cache), "unexpected cache directory"


def test_default_directories(alfred4):
    """Default directories (Alfred 4+)"""
    from os.path import expanduser
    _test_default_directories(
        expanduser('~/Library/Application Support/Alfred/Workflow Data/'),
        expanduser('~/Library/Caches/com.runningwithcrayons.Alfred/'
                   'Workflow Data/'))

    with env(alfred_workflow_data=None, alfred_workflow_cache=None):
        _test_default_directories(
            expanduser('~/Library/Application Support/Alfred/Workflow Data/'),
            expanduser('~/Library/Caches/com.runningwithcrayons.Alfred/'
                       'Workflow Data/'))


def test_run_fails_with_json_output(infopl):
    """Run fails with JSON output"""
    error_text = 'Have an error'

    def cb(wf):
        raise ValueError(error_text)

    # named after bundleid
    wf = Workflow()
    wf.bundleid

    stdout = sys.stdout
    buf = StringIO()
    sys.stdout = buf
    ret = wf.run(cb)
    sys.stdout = stdout
    output = buf.getvalue()
    buf.close()

    assert ret == 1
    assert error_text in output
    assert '{' in output


def test_run_fails_with_plain_text_output(infopl):
    """Run fails with plain text output"""
    error_text = 'Have an error'

    def cb(wf):
        raise ValueError(error_text)

    # named after bundleid
    wf = Workflow()
    wf.bundleid

    stdout = sys.stdout
    buf = StringIO()
    sys.stdout = buf
    ret = wf.run(cb, text_errors=True)
    sys.stdout = stdout
    output = buf.getvalue()
    buf.close()

    assert ret == 1
    assert error_text in output
    assert '{' not in output


def test_variables_plain_arg():
    """Arg-only returns string, not JSON."""
    v = Variables(arg='test')
    assert bytes(v) == b'test'
    assert str(v) == 'test'


def test_variables_multiple_args(infopl):
    """Variables: multiple args."""
    arg = ['one', 'two']
    js = '{"alfredworkflow": {"arg": ["one", "two"]}}'
    v = Variables(arg=arg)
    assert v.obj == {'alfredworkflow': {'arg': arg}}
    assert bytes(v) == js.encode('utf-8')
    assert str(v) == js


def test_variables_empty():
    """Empty Variables returns empty string."""
    v = Variables()
    assert bytes(v) == b''
    assert str(v) == ''


def test_variables():
    """Set variables correctly."""
    v = Variables(a=1, b=2)
    assert v.obj == {'alfredworkflow': {'variables': {'a': 1, 'b': 2}}}


def test_variables_config():
    """Set config correctly."""
    v = Variables()
    v.config['var'] = 'val'
    assert v.obj == {'alfredworkflow': {'config': {'var': 'val'}}}


def test_variables_unicode():
    """Unicode handled correctly."""
    v = Variables(arg='fübar', englisch='englisch')
    v['französisch'] = 'französisch'
    v.config['über'] = 'über'
    d = {
        'alfredworkflow':
            {
                'arg': 'fübar',
                'variables': {
                    'englisch': 'englisch',
                    'französisch': 'französisch',
                },
                'config': {'über': 'über'}
            }
    }
    print(repr(v.obj))
    print(repr(d))
    assert v.obj == d

    # Round-trip to JSON and back
    d2 = json.loads(str(v))
    assert d2 == d


if __name__ == '__main__':  # pragma: no cover
    pytest.main([__file__])
