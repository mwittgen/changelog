#!/usr/bin/env python

from rubin_changelog.changelog import ChangeLog
from rubin_changelog.changelog import Type

import logging

logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
log = logging.getLogger("changelog")
log.setLevel(logging.INFO)
ChangeLog.create_changelog(Type.Weekly)
