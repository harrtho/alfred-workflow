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


import hashlib
import logging
import os
import plistlib
import shutil
import stat
import time
from datetime import timedelta

import pytest
from workflow import Workflow, notify

from tests.conftest import BUNDLE_ID, WORKFLOW_NAME
from tests.util import FakePrograms, WorkflowMock

CACHEDIR = os.path.expanduser(
    '~/Library/Caches/com.runningwithcrayons.Alfred/'
    'Workflow Data/' + BUNDLE_ID)
APP_PATH = os.path.join(CACHEDIR, f'Notificator for {WORKFLOW_NAME}.app')
APPLET_PATH = os.path.join(APP_PATH, 'Contents/MacOS/applet')
ICON_PATH = os.path.join(APP_PATH, 'Contents/Resources/applet.icns')
INFO_PATH = os.path.join(APP_PATH, 'Contents/Info.plist')

# Alfred-PyWorkflow icon (present in source distribution)
PNG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        'icon.png')


@pytest.fixture
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
    assert APPLET_PATH == notify.notificator_program(), "unexpected applet path"
    assert ICON_PATH == notify.notificator_icon_path(), "unexpected icon path"


def test_install(infopl, alfred4, applet):
    """Notificator.app is installed correctly"""
    assert os.path.exists(APP_PATH) is False, "APP_PATH exists"
    notify.install_notificator()
    for p in (APP_PATH, APPLET_PATH, ICON_PATH, INFO_PATH):
        assert os.path.exists(p) is True, "path not found"
    # Ensure applet is executable
    assert (os.stat(APPLET_PATH).st_mode & stat.S_IXUSR), \
        "applet not executable"
    # Verify bundle ID was not changed
    with open(INFO_PATH, 'rb') as fp:
        data = plistlib.load(fp)
    bid = data.get('CFBundleIdentifier')
    assert bid == BUNDLE_ID, "bundle IDs identical"


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
    assert notify.notify(title='Test Title', message='Test Message') is True
    # A notification should appear now, but there's no way of
    # checking whether it worked
    assert os.path.exists(APP_PATH) is True


def test_notificatorapp_recreated(infopl, alfred4):
    """Notificator.app older 30 days"""
    # Create a Notificator.app
    notify.install_notificator()
    assert os.path.exists(APP_PATH) is True
    curr = time.time()
    mod = os.path.getmtime(APPLET_PATH)
    diff = curr - mod
    assert timedelta(seconds=diff).days == 0
    # Date the Notificator.app back 31 days (86400 sec/day)
    curr = time.time()
    old = int(curr - 86400*31)
    os.utime(APPLET_PATH, (old, old))
    mod = os.path.getmtime(APPLET_PATH)
    diff = curr - mod
    assert timedelta(seconds=diff).days == 31
    # Check if the Notificator.app has been updated
    assert notify.notify(title='Test Title', message='Test Message') is True
    assert os.path.exists(APP_PATH) is True
    curr = time.time()
    mod = os.path.getmtime(APPLET_PATH)
    diff = curr - mod
    assert timedelta(seconds=diff).days == 0


def test_notificatorapp_called(infopl, alfred4):
    """Notificator.app is called"""
    c = WorkflowMock()
    notify.install_notificator()
    with c:
        assert notify.notify(title='Test Title', message='Test Message') is False
        assert c.cmd[0] == APPLET_PATH


def test_iconutil_fails(infopl, alfred4, tempdir):
    """`iconutil` throws RuntimeError"""
    with FakePrograms('iconutil'):
        icns_path = os.path.join(tempdir, 'icon.icns')
        with pytest.raises(RuntimeError):
            notify.png_to_icns(PNG_PATH, icns_path)


def test_sips_fails(infopl, alfred4, tempdir):
    """`sips` throws RuntimeError"""
    with FakePrograms('sips'):
        icon_path = os.path.join(tempdir, 'icon.png')
        with pytest.raises(RuntimeError):
            notify.convert_image(PNG_PATH, icon_path, 64)


def test_image_conversion(infopl, alfred4, tempdir, applet):
    """PNG to ICNS conversion"""
    assert os.path.exists(APP_PATH) is False
    notify.install_notificator()
    assert os.path.exists(APP_PATH) is True
    icns_path = os.path.join(tempdir, 'icon.icns')
    assert os.path.exists(icns_path) is False
    notify.png_to_icns(PNG_PATH, icns_path)
    assert os.path.exists(icns_path) is True
    with open(icns_path, 'rb') as fp:
        h1 = hashlib.md5(fp.read())
    with open(ICON_PATH, 'rb') as fp:
        h2 = hashlib.md5(fp.read())
    assert h1.digest() == h2.digest()


if __name__ == '__main__':  # pragma: no cover
    pytest.main([__file__])
