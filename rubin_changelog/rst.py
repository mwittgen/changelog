import logging
from rstcloth import RstCloth
from sortedcontainers import SortedDict

log = logging.getLogger(__name__)


class Writer:
    def __init__(self, outputdir: str):
        self._outputdir = outputdir

    def write(self, jira: dict, tags: SortedDict, eups_diff):
        for tag in reversed(tags):
            name = tag
            if tag == "~main":
                name = "main"
            log.info("Writing", name)
            tickets = tags[tag]['tickets']
            ticket_dict = dict()
            doc = RstCloth(line_width=80)
            doc.h2(name)
            doc.newline()
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
                row.append([str(number), entry[0], ','.join(entry[1])])
            if len(row) > 0:
                doc.table(["Ticket", "Description", "Products"], data=row)
                doc.newline()
            doc.write(self._outputdir + '/' + name + '.rst')
