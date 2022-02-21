#!/usr/bin/env python

from rubin_changelog.changelog import ChangeLog
from rubin_changelog.eups import EupsData
from rubin_changelog.jira import JiraData
from rubin_changelog.rst import Writer

import logging

logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
log = logging.getLogger("change_log")
log.setLevel(logging.DEBUG)
log.info("Fetching EUPS data")
eups = EupsData()
eups_data = eups.get_releases("w_")
change_log = ChangeLog(eups_data)
package_diff = change_log.get_package_diff()
products = eups_data['products']
log.info("Fetching JIRA ticket data")
jira = JiraData()
jira_data = jira.get_tickets()
log.info("Fetching GitHub repo data")
repos = change_log.get_package_repos(products, "w.")
log.info("Processing changelog data")
repo_data = change_log.get_merged_tickets(repos)
log.info("Writing RST files")
writer = Writer("source/weekly")
writer.write(jira_data, repo_data, eups_data)

# pprint(result)
