#!/usr/bin/env python3
# encoding: utf-8
#
# Copyright (c) 2022 Thomas Harr <xDevThomas@gmail.com>
# Copyright (c) 2016 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2016-02-22
#

"""Unit tests for notifications."""


import logging
import os
import plistlib
import shutil
import stat

import pytest
from workflow import Workflow, notify

from tests.conftest import BUNDLE_ID, WORKFLOW_NAME
from tests.util import WorkflowMock

CACHEDIR = os.path.expanduser(
    '~/Library/Caches/com.runningwithcrayons.Alfred'
    '/Workflow Data/' + BUNDLE_ID)
NOTIFICATOR_PATH = os.path.join(os.path.dirname(
    os.path.dirname(__file__)), 'workflow/notificator.sh')
APP_PATH = os.path.join(CACHEDIR, f'Notificator for {WORKFLOW_NAME}.app')
APPLET_PATH = os.path.join(APP_PATH, 'Contents/MacOS/applet')
ICON_PATH = os.path.join(APP_PATH, 'Contents/Resources/applet.icns')
INFO_PATH = os.path.join(APP_PATH, 'Contents/Info.plist')

# Alfred-Workflow icon (present in source distribution)
PNG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        'icon.png')


@ pytest.fixture
def applet():
    """Ensure applet doesn't exist."""
    if os.path.exists(APP_PATH):
        shutil.rmtree(APP_PATH)
    yield
    if os.path.exists(APP_PATH):
        shutil.rmtree(APP_PATH)


def test_log_wf(infopl, alfred4):
    """Workflow and Logger objects correct"""
    wf = notify.wf()
    assert isinstance(wf, Workflow), "not Workflow"
    # Always returns the same objects
    wf2 = notify.wf()
    assert wf is wf2, "not same Workflow"

    log = notify.log()
    assert isinstance(log, logging.Logger), "not Logger"
    log2 = notify.log()
    assert log is log2, "not same Logger"


def test_paths(infopl, alfred4):
    """Module paths are correct"""
    assert CACHEDIR == notify.wf().cachedir, "unexpected cachedir"
    assert APPLET_PATH == notify.wf().cachefile(
        f'Notificator for {WORKFLOW_NAME}.app/Contents/MacOS/applet'), "unexpected applet path"
    assert ICON_PATH == notify.wf().cachefile(
        f'Notificator for {WORKFLOW_NAME}.app/Contents/Resources/applet.icns'), "unexpected icon path"


def test_install(infopl, alfred4, applet):
    """Notify.app is installed correctly"""
    assert os.path.exists(APP_PATH) is False, "APP_PATH exists"
    notify.notify('Test Title', 'Test Message')
    for p in (APP_PATH, APPLET_PATH, ICON_PATH, INFO_PATH):
        assert os.path.exists(p) is True, "path not found"
    # Ensure applet is executable
    assert (os.stat(APPLET_PATH).st_mode & stat.S_IXUSR), \
        "applet not executable"
    # Verify bundle ID was changed
    with open(INFO_PATH, 'rb') as fp:
        data = plistlib.load(fp)
    bid = data.get('CFBundleIdentifier')
    assert bid != BUNDLE_ID, "bundle IDs identical"
    assert bid.startswith(BUNDLE_ID) is True, "bundle ID not prefix"


def test_sound():
    """Good sounds work, bad ones fail"""
    # Good values
    for s in ('basso', 'GLASS', 'Purr', 'tink'):
        sound = notify.validate_sound(s)
        assert sound is not None
        assert sound == s.title(), "unexpected title"
    # Bad values
    for s in (None, 'SPOONS', 'The Hokey Cokey', ''):
        sound = notify.validate_sound(s)
        assert sound is None


def test_invalid_notifications(infopl, alfred4):
    """Invalid notifications"""
    with pytest.raises(ValueError):
        notify.notify()
    # Is not installed yet
    assert os.path.exists(APP_PATH) is False
    assert notify.notify('Test Title', 'Test Message') is True
    # A notification should appear now, but there's no way of
    # checking whether it worked
    assert os.path.exists(APP_PATH) is True


def test_notifyapp_called(infopl, alfred4):
    """Notify.app is called"""
    c = WorkflowMock()
    with c:
        assert notify.notify('Test Title', 'Test Message') is False
        assert c.cmd[0] == NOTIFICATOR_PATH


def test_image_conversion(infopl, alfred4, applet):
    """PNG to ICNS conversion"""
    assert os.path.exists(APP_PATH) is False
    assert os.path.exists(ICON_PATH) is False
    notify.notify('Test Title', 'Test Message')
    assert os.path.exists(APP_PATH) is True
    assert os.path.exists(ICON_PATH) is True


if __name__ == '__main__':  # pragma: no cover
    pytest.main([__file__])
