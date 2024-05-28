#!/home/iaross/miniconda3/bin/python

from easydict import easydict

import time
import json
import sys
import html
import requests
import urllib.parse
from typing import List

def jload(fn: str) -> dict:
    return easydict(json.load(open(fn)))

def plural_s(n: str) -> str:
    return "" if n == 1 else "s"


_html_template = u"""\
<!DOCTYPE html>
<html>
<head>
<title>{_title}</title>
<style>
  body {{ font-family: monospace }}
  .ar  {{ text-align: right }}
</style>
</head>
<body>
<h2>Article Count by Source</h2>

<p>Total Articles: {all.hits.total:,}</p>
<p>Last {since}: {day.hits.total:,}</p>

<p>
<table border=1>
<tr>
<th>Source</th>
<th>Last {since}</th>
<th>Total</th>
</tr>

{_source_table_rows}

</table>
</p>

<hr/>

<h2>Article Count by Pubname / Source</h2>
<p>Total Articles: {all.hits.total:,}</p>
<p>Last {since}: {day.hits.total:,}</p>

<p>
<table border=1>
<tr>
<th>Pubname</th>
<th>Source</th>
<th>Last {since}</th>
<th>Total</th>
</tr>

{_pubsrc_table_rows}

</table>
</p>

<h2>API Response checks</h2>
<p>
<table border=1>
<tr>
<th>URL</th>
<th>Name</th>
<th>Outcome</th>
</tr>
{_endpoints}
</table>
</p>

</body>
</html>
"""

def dcmap(xx) -> dict:
    return { x.key: x.doc_count for x in xx.buckets }


def bsort(xx, mapby):
    def key(b):
        return (-mapby.get(b.key, 0), -b.doc_count, b.key)
    return sorted(xx.buckets, key=key)


def mk_source_table_rows(sources, sources_24h) -> List[List]:
    map24h = dcmap(sources_24h.aggregations.sources)

    return [ [s.key, map24h.get(s.key, 0), s.doc_count]
             for s in bsort(sources.aggregations.sources, map24h) ]


def mk_pubsrc_table_rows(pubsrc, pubsrc_24h) -> List[List]:
    totals = { (p.key, s.key): s.doc_count
               for p in pubsrc.aggregations.pubnames.buckets
               for s in p.sources.buckets }

    return [ [p.key, s.key, s.doc_count, totals.get((p.key, s.key), 0)]
             for p in pubsrc_24h.aggregations.pubnames.buckets
             for s in p.sources.buckets ]


def mk_td(s: str) -> str:
    if isinstance(s, int):
        fmt = u"<td class='ar'>{:,}</td>"
    else:
        fmt = u"<td>{}</td>"
        s = html.escape(s)
    return fmt.format(s)


def mk_table_row(row: List) -> str:
    return u"<tr>\n%s\n</tr>" % u"\n".join( mk_td(cell) for cell in row )


def mk_table_rows(matrix: List[List]) -> str:
    return u"\n".join( mk_table_row(row) for row in matrix )


def mk_email(since: str, sources_out: str, sources_24h_out: str, pubsrc_out: str, pubsrc_24h_out: str):
    now = time.time()
    dstamp = time.strftime("%F", time.localtime(now))
    tstamp = time.strftime("%F %H:%M", time.localtime(now))
    desc = "Source and Pubname Summary"
    subject = "xDD New Document Summary for last %s as of %s" % (since, dstamp)

    s   = jload(sources_out)
    s24 = jload(sources_24h_out)
    p   = jload(pubsrc_out)
    p24 = jload(pubsrc_24h_out)

    e = easydict()

    e.all = s
    e.day = s24
    e.since = since
    e._source_table_rows = mk_table_rows(mk_source_table_rows(s, s24))
    e._pubsrc_table_rows = mk_table_rows(mk_pubsrc_table_rows(p, p24))
    e._title = subject

    e._endpoints = check_endpoints()

    html = _html_template.format(**e)

    print("Subject: %s" % subject)
    print()
    print(html)
#    print(check_endpoints())


#   s.hits.total
#   s.aggregations.sources.buckets[0].key
#   s.aggregations.sources.buckets[0].doc_count

#   p.hits.total
#   p.aggregations.pubnames.buckets[0].key
#   p.aggregations.pubnames.buckets[0].doc_count
#   p.aggregations.pubnames.buckets[0].sources.buckets[0].key
#   p.aggregations.pubnames.buckets[0].sources.buckets[0].doc_count


def check_endpoint(url: str, expected_n: int=None, json: bool=True) -> str:
    resp = requests.get(url)
    if resp.status_code != 200:
        return "Error! Non-200 status code returned."
    elif json and "error" in resp.json():
        return "Error! API returned a non-success."
    elif json and expected_n is not None and "success" in resp.json() and len(resp.json()['success']['data']) != expected_n:
        return f"Error! Unexpected number of results returned. Expected {expected_n} and got {len(resp.json()['success']['data'])}"
    return "Success"

def check_endpoints() -> str:
    """
    Check some xDD public-facing endpoints; ensure a 200 status code and, where appropriate, quickly check results.
    """
    endpoints = [
            ("Articles route - basic search", "https://xdd.wisc.edu/api/articles?term=test&max=10", 10, True),
            ("Articles route - scan and scroll", "https://xdd.wisc.edu/api/articles?term=test&full_results=true&per_page=500", 500, True),
            ("Journals route", "https://xdd.wisc.edu/api/journals?all", None, True),
            ("Dictionaries route", "https://xdd.wisc.edu/api/dictionaries?all", None, True),
            ("Basic metrics", "https://xdd.wisc.edu/api/metrics/basic", 4, True),
            ("Website", "https://xdd.wisc.edu", None, False),
            ("xdd-covid-19 - word2vec", "https://xdd.wisc.edu/sets/xdd-covid-19/word2vec/api/most_similar?word=test", 10, True),
            ("xdd-covid-19 - COSMOS", "https://xdd.wisc.edu/sets/xdd-covid-19/cosmos/api/", None, False),
            ("COSMOS - set visualizer", "https://xdd.wisc.edu/set_visualizer/", None, False),

            ]
    results = []
    for check, url, n_max, json in endpoints:
        results.append([check, url, check_endpoint(url, n_max, json)])
    return mk_table_rows(results)

#    table_results()

#    return ""


def main():
    mk_email(*sys.argv[1:])

if __name__ == '__main__':
    main()

