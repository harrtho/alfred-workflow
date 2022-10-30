#!/usr/bin/env python3
# encoding: utf-8
#
# Copyright (c) 2022 Thomas Harr <xDevThomas@gmail.com>
# Copyright (c) 2019 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2019-05-05
#
"""Unit tests for Workflow.run."""

import json
import sys
from io import StringIO

import pytest
from workflow import Workflow

from tests.conftest import env


def test_run_fails(infopl):
    """Run fails"""
    wf = Workflow()

    def cb(wf2):
        assert wf2 is wf
        raise ValueError('Have an error')

    wf.help_url = 'https://xdevcloud.de/alfred-pyworkflow/'
    ret = wf.run(cb)
    assert ret == 1

    # read name from info.plist
    with env(alfred_workflow_name=None):
        wf = Workflow()
        wf.name
        ret = wf.run(cb)
        assert ret == 1

        # named after bundleid
        wf = Workflow()
        wf.bundleid
        ret = wf.run(cb)
        assert ret == 1

    wf.reset()


def test_run_fails_with_json_output(wf):
    """Run fails with JSON output"""
    error_text = 'Have an error'
    stdout = sys.stdout
    buf = StringIO()
    sys.stdout = buf

    def cb(wf2):
        assert wf2 is wf
        raise ValueError(error_text)

    ret = wf.run(cb)

    sys.stdout = stdout
    output = buf.getvalue()
    buf.close()

    assert ret == 1
    assert error_text in output
    assert type(json.loads(output)) == type(dict())


def test_run_fails_with_plain_text_output(wf):
    """Run fails with plain text output"""
    error_text = 'Have an error'
    stdout = sys.stdout
    buf = StringIO()
    sys.stdout = buf

    def cb(wf2):
        assert wf2 is wf
        raise ValueError(error_text)

    ret = wf.run(cb, text_errors=True)

    sys.stdout = stdout
    output = buf.getvalue()
    buf.close()

    assert ret == 1
    assert error_text in output
    assert '"items":' not in output


def test_run_fails_borked_settings(wf):
    """Run fails with borked settings.json"""
    # Create invalid settings.json file
    with open(wf.settings_path, 'w') as fp:
        fp.write('')

    def fake(wf):
        wf.settings

    ret = wf.run(fake)
    assert ret == 1


def test_run_okay(wf):
    """Run okay"""
    def cb(wf2):
        assert wf2 is wf

    ret = wf.run(cb)
    assert ret == 0


if __name__ == '__main__':  # pragma: no cover
    pytest.main([__file__])
