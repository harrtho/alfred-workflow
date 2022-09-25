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
"""Unit tests for serializers."""

import pytest


def test_unicode_paths(wf):
    """Workflow paths are Unicode"""
    b = b'test.txt'
    s = 'über.txt'
    assert isinstance(wf.datadir, str)
    assert isinstance(wf.datafile(b), str)
    assert isinstance(wf.datafile(s), str)
    assert isinstance(wf.cachedir, str)
    assert isinstance(wf.cachefile(b), str)
    assert isinstance(wf.cachefile(s), str)
    assert isinstance(wf.workflowdir, str)
    assert isinstance(wf.workflowfile(b), str)
    assert isinstance(wf.workflowfile(s), str)


if __name__ == '__main__':  # pragma: no cover
    pytest.main([__file__])
