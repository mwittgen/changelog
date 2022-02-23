import logging
from pprint import pprint

from rstcloth import RstCloth
from sortedcontainers import SortedDict, SortedList
from .tag import *

log = logging.getLogger(__name__)


class Writer:
    def __init__(self, outputdir: str):
        self._outputdir = outputdir

    def write_products(self, products: SortedList, ncols: int = 5) -> None:
        products_len = len(products)
        cols = list()
        for i in range(products_len // ncols +
                       (products_len % ncols) // ncols):
            rows = list()
            for j in range(ncols):
                index = i * ncols + j
                if index < products_len:
                    rows.append(products[index])
                else:
                    rows.append('')
            cols.append(rows)
        doc = RstCloth(line_width=80)
        doc.h2('Products')
        doc.newline()
        doc.table(['Products', '', '', '', ''], data=cols)
        doc.write(self._outputdir + '/products.rst')

    def write_releaes(self, jira: dict, tags: SortedDict, eups_diff: SortedDict) -> None:
        index = SortedList()
        weekly_flag = False
        for tag in reversed(tags):
            date = tags[tag]['date']
            doc = RstCloth(line_width=80)
            rtag = Tag(tag)
            name = rtag.rel_name()
            weekly_flag = rtag.is_weekly()
            if rtag in eups_diff or name == 'main':
                index.add(rtag)
            pkg_table = list()
            doc.h2(name)
            doc.newline()
            doc.content("Released at %s" % date)
            doc.newline()
            if rtag in eups_diff:
                removed_pkg = eups_diff[rtag]["removed"]
                added_pkg = eups_diff[rtag]["added"]
                removed_len = len(removed_pkg)
                added_len = len(added_pkg)
                max_len = max(removed_len, added_len)
                for i in range(max_len):
                    entry1 = ''
                    entry2 = ''
                    if i < added_len:
                        entry1 = added_pkg[i]
                    if i < removed_len:
                        entry2 = removed_pkg[i]
                    pkg_table.append([entry1, entry2])
                if len(pkg_table) > 0:
                    doc.table(["Added Product(s)", "Removed Products(s)"], data=pkg_table)
                else:
                    doc.content("No products added in this tag")
                doc.newline()
            log.info("Writing %s" % name)
            tickets = tags[tag]['tickets']
            ticket_dict = SortedDict()
            row = list()
            for ticket in tickets:
                number = ticket['ticket']
                key = 'DM-' + str(number)
                if key not in jira:
                    continue
                msg = jira[key]
                product = ticket['product']
                if number not in ticket_dict:
                    ticket_dict[number] = (msg, [product])
                else:
                    ticket_dict[number][1].append(product)
            for number in ticket_dict:
                entry = ticket_dict[number]
                link = f"`DM-{number} <https://jira.lsstcorp.org/browse/DM-{number}>`_"
                row.append([link, entry[0], ', '.join(entry[1])])
            if len(row) > 0:
                doc.table(["Ticket(s) Merged", "Description", "Product(s)"], data=row)
                doc.newline()
            else:
                doc.content("No changes in this tag")
            doc.write(self._outputdir + '/' + name + '.rst')
        title = 'Releases'
        if weekly_flag:
            title = "Weekly Releases"
        doc = RstCloth()
        doc.h2(title)
        doc.newline()
        doc.directive('toctree')
        doc.field("caption", title, 3)
        doc.field("maxdepth", '2', 3)
        doc.field('hidden', '', 3)
        doc.newline()
        doc.content('products', 3)
        for i in reversed(index):
            doc.content(i.rel_name(), 3)
        doc.newline()
        doc.content('- :doc:`products`')
        for i in reversed(index):
            rel = i.rel_name()
            doc.content(f'- :doc:`{rel}`')
        doc.write(self._outputdir + '/' + '/index.rst')
