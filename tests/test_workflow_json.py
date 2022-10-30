#!/usr/bin/env python3
# encoding: utf-8
#
# Copyright (c) 2022 Thomas Harr <xDevThomas@gmail.com>
# Copyright (c) 2019 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2017-05-06
#

"""Unit tests for Workflow's JSON feedback generation."""

import json
import sys
from contextlib import contextmanager
from io import StringIO

import pytest
from workflow import Workflow


@pytest.fixture(scope='function')
def wf(infopl):
    """Create a :class:`~workflow.Workflow` object."""
    yield Workflow()


@contextmanager
def stdout():
    """Capture output to STDOUT."""
    old = sys.stdout
    sio = StringIO()
    sys.stdout = sio
    yield sio
    sio.close()
    sys.stdout = old


def test_item_creation(wf):
    """JSON generation"""
    wf.add_item(
        'title', 'subtitle', arg='arg',
        autocomplete='autocomplete',
        valid=True, uid='uid', icon='icon.png',
        icontype='fileicon',
        type='file', largetext='largetext',
        copytext='copytext',
        quicklookurl='https://xdevcloud.de/alfred-pyworkflow')
    with stdout() as sio:
        wf.send_feedback()
        output = sio.getvalue()

    feedback = json.loads(output)
    feedback_item = feedback['items'][0]
    assert feedback_item['uid'] == 'uid'
    assert feedback_item['autocomplete'] == 'autocomplete'
    assert feedback_item['valid'] is True
    assert feedback_item['uid'] == 'uid'
    assert feedback_item['title'] == 'title'
    assert feedback_item['subtitle'] == 'subtitle'
    assert feedback_item['arg'] == 'arg'
    assert feedback_item['quicklookurl'] == 'https://xdevcloud.de/alfred-pyworkflow'
    feedback_text = feedback_item['text']
    assert feedback_text['largetype'] == 'largetext'
    assert feedback_text['copy'] == 'copytext'
    feedback_icon = feedback_item['icon']
    assert feedback_icon['path'] == 'icon.png'
    assert feedback_icon['type'] == 'fileicon'


def test_item_creation_with_modifiers(wf):
    """JSON generation (with modifiers)."""
    item = wf.add_item('title', 'subtitle', arg='arg',
                       autocomplete='autocomplete',
                       valid=True, uid='uid', icon='icon.png',
                       icontype='fileicon',
                       type='file')
    for mod in ('cmd', 'ctrl', 'alt', 'shift', 'fn'):
        item.add_modifier(mod, mod)
    with stdout() as sio:
        wf.send_feedback()
        output = sio.getvalue()

    feedback = json.loads(output)
    feedback_item = feedback['items'][0]
    assert feedback_item['uid'] == 'uid'
    assert feedback_item['autocomplete'] == 'autocomplete'
    assert feedback_item['valid'] is True
    assert feedback_item['uid'] == 'uid'
    assert feedback_item['title'] == 'title'
    assert feedback_item['subtitle'] == 'subtitle'
    assert feedback_item['arg'] == 'arg'
    feedback_mods = feedback_item['mods']
    assert feedback_mods['cmd']['subtitle'] == 'cmd'
    assert feedback_mods['ctrl']['subtitle'] == 'ctrl'
    assert feedback_mods['alt']['subtitle'] == 'alt'
    assert feedback_mods['shift']['subtitle'] == 'shift'
    assert feedback_mods['fn']['subtitle'] == 'fn'
    feedback_icon = feedback_item['icon']
    assert feedback_icon['path'] == 'icon.png'
    assert feedback_icon['type'] == 'fileicon'


def test_item_creation_no_optionals(wf):
    """JSON generation (no optionals)"""
    wf.add_item('title')
    with stdout() as sio:
        wf.send_feedback()
        output = sio.getvalue()

    feedback = json.loads(output)
    feedback_item = feedback['items'][0]
    for key in ['uid', 'arg', 'autocomplete', 'icon']:
        assert key not in feedback_item.keys()

    assert feedback_item['valid'] is False
    assert feedback_item['title'] == 'title'
    assert feedback_item['subtitle'] == ''


if __name__ == '__main__':  # pragma: no cover
    pytest.main([__file__])
