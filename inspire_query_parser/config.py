"""
A collection of INSPIRE related keywords.

This dictionary has a twofold use.
Primarily, the parser uses its keys to generate INSPIRE related keywords (i.e. qualifiers) and secondly, the mapping it
provides is used by a visitor at a later phase to actually translate from the shortened variants to the canonical ones.
"""
INSPIRE_PARSER_KEYWORDS = {
    # Author
    "author": "author",
    "au": "author",
    "a": "author",

    # Author-Count
    "author-count": "author-count",
    "authorcount": "author-count",
    "ac": "author-count",

    # Collection
    "collection": "collection",

    # Exact-Author
    "exact-author": "exact-author",
    "exactauthor": "exact-author",
    "ea": "exact-author",

    # Experiment
    "experiment": "experiment",
    "exp": "experiment",

    # First-Author
    "first-author": "first-author",
    "firstauthor": "first-author",
    "fa": "first-author",

    # Fulltext
    "fulltext": "fulltext",
    "ft": "fulltext",

    # Journal
    "journal": "journal",
    "j": "journal",

    # Reference
    "reference": "reference",
    "citation": "reference",
    'jour-vol-page': 'reference',  # ??
    'jvp': 'reference',  # ??

    # Title
    "title": "title",
    "t": "title",
}
