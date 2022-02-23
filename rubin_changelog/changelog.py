import concurrent
import datetime
import logging
from concurrent.futures.thread import ThreadPoolExecutor
from copy import deepcopy
from pprint import pprint

from dateutil.parser import parse
from sortedcontainers import SortedDict, SortedList

from rubin_changelog.eups import EupsData
from rubin_changelog.github import GitHubData
from rubin_changelog.jira import JiraData
from rubin_changelog.rst import Writer

from .tag import *

log = logging.getLogger("changelog")


class ChangeLog:
    def __init__(self, eups_data: SortedDict, max_workers: int = 5):
        self.eups_data = eups_data
        self._max_workers = max_workers

    def get_package_diff(self) -> SortedDict:
        result = SortedDict()
        releases = self.eups_data['releases']
        last_release = None
        for r in releases:
            if last_release is not None:
                previous_pkgs = [sub['package'] for sub in last_release]
                pkgs = [sub['package'] for sub in releases[r]]
                removed = SortedList(set(previous_pkgs) - set(pkgs))
                added = SortedList(set(pkgs) - set(previous_pkgs))
                result[r] = {'added': added, 'removed': removed}
            last_release = releases[r]
        return result

    @staticmethod
    def _fetch(repo: str, tag: ReleaseType) -> dict:
        log.info("Fetching %s", repo)
        gh = GitHubData()
        result = dict()
        pulls = gh.get_pull_requests(repo)
        tags = gh.get_tags(repo, tag)
        result["repo"] = repo
        result["pulls"] = pulls
        result["tags"] = tags
        del gh
        return result

    def get_package_repos(self, products: SortedList, tag: ReleaseType) -> SortedDict:
        result = SortedDict()
        result['pulls'] = SortedDict()
        result["tags"] = SortedDict()
        gh = GitHubData()
        repos = gh.get_repos()
        del gh
        repo_list = SortedList()
        for product in products:
            if product in repos:
                repo_list.add(product)
        with ThreadPoolExecutor(
                max_workers=self._max_workers) as executor:
            futures = {executor.submit(self._fetch, repo, tag): repo for repo in repo_list}
            for future in concurrent.futures.as_completed(futures):
                try:
                    data = future.result()
                except Exception:
                    log.error("Fetch failed")
                else:
                    repo = data["repo"]
                    result["pulls"][repo] = data["pulls"]
                    result["tags"][repo] = data["tags"]
        return result

    @staticmethod
    def _ticket_number(title: str) -> int:
        match = re.search(r'DM[\s*|-]\d+', title.upper())
        ticket = None
        if match:
            res = re.findall(r"DM[\s|-]*(\d+)", match[0])
            if len(res) == 1:
                ticket = res[0]
        return ticket

    def get_merged_tickets(self, repos) -> SortedDict:
        pull_list = repos['pulls']
        tag_list = repos['tags']
        result = SortedDict()
        last_tag_date = None
        for pkg in tag_list:

            log.info("processing %s" % pkg)
            pulls = pull_list[pkg]
            tags = tag_list[pkg]
            for tag in tags:
                rtag = Tag(tag['name'])
                name = rtag.rel_name()
                if name not in result:
                    result[name] = dict()
                    result[name]['tickets'] = list()
                target = tag["target"]
                if 'tagger' in target:
                    date = target['tagger']['date']
                else:
                    date = target['authoredDate']
                tag_date = parse(date)
                if last_tag_date is None or tag_date > last_tag_date:
                    last_tag_date = tag_date
                result[name]['date'] = date
                current_pulls = deepcopy(pulls)
                for merged_at in current_pulls:
                    pull_date = parse(merged_at)
                    title = pulls[merged_at]
                    if pull_date <= tag_date:
                        ticket = self._ticket_number(title)
                        del pulls[merged_at]
                        result[name]['tickets'].append({
                            'product': pkg, 'title': title, 'date': merged_at, 'ticket': ticket
                        })
                    else:
                        break
            for merged_at in pulls:
                title = pulls[merged_at]
                date = datetime.datetime.now().isoformat()
                ticket = self._ticket_number(title)
                # use ~main for sorting to put it after any other tag
                if '~main' not in result:
                    result['~main'] = dict()
                    result['~main']['tickets'] = list()
                    result['~main']["date"] = date
                if parse(merged_at) > last_tag_date:
                    result['~main']['tickets'].append({
                        'product': pkg, 'title': title, 'date': merged_at, 'ticket': ticket
                    })
        return result

    @staticmethod
    def create_changelog(release: ReleaseType):
        log.info("Fetching EUPS data")
        eups = EupsData()
        eups_data = eups.get_releases(release)
        change_log = ChangeLog(eups_data)
        package_diff = change_log.get_package_diff()
        products = eups_data['products']
        log.info("Fetching JIRA ticket data")
        jira = JiraData()
        jira_data = jira.get_tickets()
        log.info("Fetching GitHub repo data")
        repos = change_log.get_package_repos(products, release)
        #repos = change_log.get_package_repos(SortedList(['afw', 'base']), release)
        log.info("Processing changelog data")
        repo_data = change_log.get_merged_tickets(repos)
        log.info("Writing RST files")
        outputdir = 'source/releases'
        if release == ReleaseType.WEEKLY:
            outputdir = 'source/weekly'
        writer = Writer(outputdir)
        writer.write_products(products)
        writer.write_releaes(jira_data, repo_data, package_diff)
