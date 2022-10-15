#!/usr/bin/env python3
# encoding: utf-8
#
# Copyright (c) 2022 Thomas Harr <xDevThomas@gmail.com>
# Copyright (c) 2019 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2015-11-26
#

"""
Post notifications via the macOS Notification Center.

This feature is only available on Mountain Lion (10.8) and later.
It will silently fail on older systems.

The main API is a single function, :func:`~workflow.notify.notify`.

It works by copying a simple application to your workflow's cache
directory. It replaces the application's icon with your workflow's
icon and then calls the application to post notifications.

This module uses ``Notificator`` created by Vítor Galvão
https://github.com/vitorgalvao/notificator
"""

import os
import subprocess

import workflow

_wf = None
_log = None


#: Available system sounds from System Preferences > Sound > Sound Effects (location: ``/System/Library/Sounds``)
SOUNDS = (
    'Basso',
    'Blow',
    'Bottle',
    'Frog',
    'Funk',
    'Glass',
    'Hero',
    'Morse',
    'Ping',
    'Pop',
    'Purr',
    'Sosumi',
    'Submarine',
    'Tink',
)


def wf():
    """Return Workflow object for this module.

    Returns:
        workflow.Workflow: Workflow object for current workflow.
    """
    global _wf
    if _wf is None:
        _wf = workflow.Workflow()
    return _wf


def log():
    """Return logger for this module.

    Returns:
        logging.Logger: Logger for this module.
    """
    global _log
    if _log is None:
        _log = wf().logger
    return _log


def validate_sound(sound):
    """Coerce ``sound`` to valid sound name.

    Returns ``None`` for invalid sounds. Sound names can be found
    in ``System Preferences > Sound > Sound Effects``
    or located at ``/System/Library/Sounds``.

    Args:
        sound (str): Name of system sound.

    Returns:
        str: Proper name of sound or ``None``.
    """
    if not sound:
        return None

    # Case-insensitive comparison of `sound`
    if sound.lower() in [s.lower() for s in SOUNDS]:
        # Title-case is correct for all system sounds as of macOS 10.11
        return sound.title()
    return None


def notify(title='', text='', sound=None):
    """Post notification via notificator helper from Vítor Galvão.

    Args:
        title (str, optional): Notification title.
        text (str, optional): Notification body text.
        sound (str, optional): Name of sound to play.

    Raises:
        ValueError: Raised if both ``title`` and ``text`` are empty.

    Returns:
        bool: ``True`` if notification was posted, else ``False``.
    """
    if title == text == '':
        raise ValueError('Empty notification')

    sound = validate_sound(sound) or ''

    notificator = os.path.join(os.path.dirname(__file__), 'notificator.sh')

    cmd = [notificator, '--title', title, '--message', text, '--sound', sound]
    retcode = subprocess.call(cmd)
    if retcode == 0:
        return True

    log().error('notificator exited with status {0}.'.format(retcode))
    return False
