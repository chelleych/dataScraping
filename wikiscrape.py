"""
Scrape the from the online library Wikisource.

Given a wikisource author page link, These functions will return the author's
written works that are available on wikisource.

This script is not perfect, so there may be some irrelevant links, prose, etc.
in the output text.

This code was written because of the limmited flexibility of the Wikisource
e-book builder, which can only create a book after manually adding each desired
source text.

From Wikisource:
"This multilingual digital library, built by volunteers, is committed to
developing a free accessible collection of publications of every kind: novels,
poems, magazines, letters...
We distribute our books for free, starting from works not copyrighted or
published under a free license. You are free to use our e-books for any purpose
(including commercial exploitation), under the terms of the Creative Commons
Attribution-ShareAlike 3.0 Unported[2] license or, at your choice, those of the
GNU FDL[3]."

Warning: Not all works on wikisource are public domain, and some articles are
possible copyright violations. Use at your own risk.

http://wikisource.org
https://wikisource.org/wiki/Wikisource:Copyright_policy

"""

from lxml import html
import requests

def _make_tree(base_url):
    """
    Makes html tree from base_url link string.
    """
    page = requests.get(base_url)
    tree = html.fromstring(page.content)
    tree.make_links_absolute(base_url)
    return tree

def getAuthorWorksLinks(base_url, exclude_links=None):
    """
    From an author's Wikisource page, gets a list of links to their work

    Input:
    base_url
        String of the form 'https://en.wikisource.org/wiki/Author:'+author_name
        Link from wikisource that contains links to the author's works
    exclude_links
        List of strings that represent links
        Links to works on the page base_url that should be excluded
        (eg. works not by the author, works in irrelevant genres, etc.)
        Only links to Wikisource works need to be in this list. Author pages,
        edit links, etc. do not need to be in this list.

    Output:
    links
        List of string links to Wikisource pages of the author's written works
    """
    tree = _make_tree(base_url)
    # uses only the first link next to each bullet point
    linkElements = tree.xpath('/html/body/div[3]/div[3]/div[4]/div/ul/li/a[1]')
    links = [el.attrib['href'] for el in linkElements]
    # use only relevant links
    links = [el for el in links if r'/'.join(el.split(r'/')[:-1])=='https://en.wikisource.org/wiki']
    # exclude pages that are not author's work
    labels_excluded = ['Wikisource:', 'Author:', 'Special:' , 'File:', 'Help:']
    for label in labels_excluded:
        links = [el for el in links if label not in el.split(r'/')[-1]]

    # remove duplicates while retaining list order
    added = set()
    links = [el for el in links if not (el in added or added.add(el))]

    if exclude_links is not None:
        links = [el for el in links if el not in exclude_links]

    return links

def get_work(base_url):
    """
    Reads the wikisource page to get a string of the written work
    base_url
        String of the form 'https://en.wikisource.org/wiki/'+work_name
        Link from wikisource that contains an author's work
        The link may contain links to parts of the work, eg. chapters
    Outputs:
    sample_text
        A string of the author's work
    """
    tree = _make_tree(base_url)
    linkElements = tree.xpath('//*[@class="mw-parser-output"]//li/a')

    try:
        links = [el.attrib['href'] for el in linkElements]
        # use only relevant links
        links = [el for el in links if base_url in el]
        # including "full" will result in duplicates
        links = [el for el in links if not el.endswith(r'/full')]

        # remove duplicates while retaining list order
        added = set()
        links = [el for el in links if not (el in added or added.add(el))]
    except KeyError:
        links=[]

    if len(links) == 0:
        # there are no links to chapters or sections, so this page must contain
        # the desired work
        links = [base_url]

    # loop links and extract string from the author's work
    sample_text = ''
    for this_url in links:
        tree = _make_tree(this_url)
        # all pages should contain a link back to the author
        alllinks = []
        for el in tree.xpath('//a'):
            try:
                alllinks = alllinks + [el.attrib['href']]
            except KeyError:
                continue
        linksWithAuthor = [el for el in alllinks if base_url in el]
        if len(linksWithAuthor) == 0:
            # page does not contain a link to the author and is unlikely to be
            # by the author
            continue

        # extract text
        content = tree.xpath('.//div[@id="mw-content-text"]')
        txt = content[0].xpath('.//div[@class="mw-parser-output"]/div/p//text()'+
                            ' | .//div[@class="mw-parser-output"]/div/div/p//text()'+
                            ' | .//div[@class="mw-parser-output"]/p//text()')

        sample_text = sample_text + '\n'.join(txt)

    return sample_text

if __name__ == "__main__":
    # Get works by the author in the target link
    base_url = 'https://en.wikisource.org/wiki/Author:Howard_Phillips_Lovecraft'
    exclude_links = ['https://en.wikisource.org/wiki/H._P._Lovecraft:_A_Bibliography',
                    'https://en.wikisource.org/wiki/H._P._Lovecraft,_An_Evaluation']
    links = getAuthorWorksLinks(base_url, exclude_links)

    for i in range(len(links)):
        print(i,links[i])
        out = get_work(links[i])
