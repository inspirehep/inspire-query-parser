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

    # Collection
    "collection": "collection",

    # Experiment
    "experiment": "experiment",
    "exp": "experiment",

    # Journal
    "journal": "journal",
    "j": "journal",

    # Title
    "title": "title",
    "t": "title",

    # First-Author
    "first-author": "first-author",
    "firstauthor": "first-author",
    "fa": "first-author",

    # Exact-Author
    "exact-author": "exact-author",
    "exactauthor": "exact-author",
    "ea": "exact-author",
}
