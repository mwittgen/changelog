#!/usr/bin/env python

import logging

from rubin_changelog.changelog import ChangeLog
from rubin_changelog.tag import *

logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
log = logging.getLogger("changelog")
log.setLevel(logging.INFO)
ChangeLog.create_changelog(ReleaseType.WEEKLY, 1)
ChangeLog.create_changelog(ReleaseType.REGULAR,1 )
