import logging

from rstcloth import RstCloth
from sortedcontainers import SortedDict, SortedList

log = logging.getLogger(__name__)


class Writer:
    def __init__(self, outputdir: str):
        self._outputdir = outputdir

    def write(self, jira: dict, tags: SortedDict, eups_diff: SortedDict, products: SortedList) -> None:
        n_col = 5
        products_len = len(products)
        cols = list()
        for i in range(products_len // n_col +
                       (products_len % n_col) // n_col):
            rows = list()
            for j in range(n_col):
                index = i * n_col + j
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

        for tag in reversed(tags):
            doc = RstCloth(line_width=80)
            name = tag
            name = name.replace('.', '_')
            if tag == "~main":
                name = "main"
            pkg_table = list()
            doc.h2(name)
            doc.newline()
            if name in eups_diff:
                removed_pkg = eups_diff[name]["removed"]
                added_pkg = eups_diff[name]["added"]
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
                doc.table(["Ticket", "Description", "Product(s)"], data=row)
                doc.newline()
            doc.write(self._outputdir + '/' + name + '.rst')
