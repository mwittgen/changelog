#!/usr/bin/env python

import logging

from rubin_changelog.eups import EupsData

logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
log = logging.getLogger("changelog")
log.setLevel(logging.INFO)
eups_data = EupsData()
for p in eups_data.get_releases('w_')['products']:
    print(p)
