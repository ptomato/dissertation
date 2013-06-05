#!/usr/bin/env python
"""
zotero2bibtex.py
Copyright 2009 Philip Chimento. All rights reserved.

The Zotero BibTeX exporter leaves much to be desired as to changing its
plain Unicode character-only formatting to LaTeX. Since I don't know Javascript
and don't want to use unstable versions of Zotero, this script converts Zotero
RDF/XML export to a BibTeX bibliography using my personal idiosyncratic
preferences.
"""

import sys
import re
import warnings
import argparse
import collections
import operator
import rdflib
import datetime
import unicodedata
import latex

# Namespaces used for relational data
bib = rdflib.Namespace('http://purl.org/net/biblio#')
dc = rdflib.Namespace('http://purl.org/dc/elements/1.1/')
dcterms = rdflib.Namespace('http://purl.org/dc/terms/')
foaf = rdflib.Namespace('http://xmlns.com/foaf/0.1/')
prism = rdflib.Namespace('http://prismstandard.org/namespaces/1.2/basic/')
rdf = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
zotero = rdflib.Namespace('http://www.zotero.org/namespaces/export#')
vcard = rdflib.Namespace('http://nwalsh.com/rdf/vCard#')

################################################################################

# Required fields for BibTeX item types
requiredfields = {
    'article': ('author', 'title', 'journal', 'year'),
    'book': ('author/editor', 'title', 'publisher', 'year'),
    'booklet': ('title'),
    'inbook': ('author/editor', 'title', 'chapter/pages', 'publisher', 'year'),
    'incollection': ('author', 'title', 'booktitle', 'publisher', 'year'),
    'inproceedings': ('author', 'title', 'booktitle', 'year'),
    'manual': ('title'),
    'mastersthesis': ('author', 'title', 'school', 'year'),
    'misc': (),
    'phdthesis': ('author', 'title', 'school', 'year'),
    'proceedings': ('title', 'year'),
    'techreport': ('author', 'title', 'institution', 'year'),
    'unpublished': ('author', 'title', 'note')
}

# Mapping of Zotero bibliography item types to BibTeX item types
typemapping = {
    'artwork':             'misc',
    'audioRecording':      'misc',
    'bill':                'misc',
    'blogPost':            'misc',
    'book':                'book',  # or manual
    'bookSection':         'incollection',  # or inbook
    'case':                'misc',
    'computerProgram':     'misc',
    'conferencePaper':     'inproceedings',
    'dictionaryEntry':     'misc',
    'document':            'misc',  # or booklet
    'eMail':               'unpublished',
    'encyclopediaArticle': 'misc',
    'film':                'misc',
    'forumPost':           'misc',
    'hearing':             'misc',
    'instantMessage':      'unpublished',
    'interview':           'misc',
    'journalArticle':      'article',
    'letter':              'unpublished',
    'magazineArticle':     'article',
    'manuscript':          'unpublished',
    'map':                 'misc',
    'newspaperArticle':    'article',
    'note':                'misc',
    'patent':              'misc',
    'podcast':             'misc',
    'presentation':        'unpublished',
    'radioBroadcast':      'misc',
    'report':              'techreport',  # or manual
    'statute':             'misc',
    'thesis':              'phdthesis',  # or mastersthesis or misc
    'tvBroadcast':         'misc',
    'videoRecording':      'misc',
    'webpage':             'misc'
}
# Bibtex types not corresponding to a Zotero type:
# booklet - A work that is printed and bound, but without a named publisher
#   or sponsoring institution.
# manual - Technical documentation


def biber_update_types():
    typemapping.update({
        'artwork':             'artwork',
        'audioRecording':      'audio',  # or music
        'bill':                'legislation',
        'blogPost':            'online',
        'case':                'jurisdiction',
        'computerProgram':     'software',
        'dictionaryEntry':     'inreference',
        'eMail':               'letter',
        'encyclopediaArticle': 'inreference',
        'film':                'movie',  # or video
        'forumPost':           'online',
        'hearing':             'jurisdiction',
        'letter':              'letter',
        'patent':              'patent',
        'podcast':             'audio',
        'report':              'report',
        'statute':             'legislation',
        'thesis':              'thesis',
        'videoRecording':      'video',
        'webpage':             'online',
    })

# Biber types not corresponding to a Zotero type:
# mvbook - A multi-volume book
# bookinbook - Similar to inbook but intended for works originally published as
#   a standalone book. (e.g. reprinted in the collected works of an author.)
# suppbook - Supplemental material in a book
# collection - a single-volume collection with multiple, self-contained
#   contributions by distinct authors which have their own title
# mvcollection - A multivolume collection
# suppcollection - Supplemental material in a collection
# periodical - A complete issue of a periodical
# suppperiodical - Supplemental material in a periodical
# proceedings - A single-volume conference proceedings
# mvproceedings - A multivolume proceedings
# reference - A single-volume work of reference such as an encyclopedia
# mvreference - A multivolume reference

language_codes = {
    'en': 'english',
    'de': 'german',
    'fr': 'french'
}

################################################################################


# English ordinals
def ordinal(num):
    ordinals = ['zeroeth', 'first', 'second', 'third', 'fourth', 'fifth',
        'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth',
        'thirteenth', 'fourteenth', 'fifteenth', 'sixteenth', 'seventeenth',
        'eighteenth', 'nineteenth', 'twentieth']
    ordinalabbrev = {1: 'st', 2: 'nd', 3: 'rd'}

    if num <= 20:
        return ordinals[num]
    if num % 10 in range(1, 3) and num % 100 not in range(11, 13):
        return '%d%s' % (num, ordinalabbrev[num % 10])
    return '%dth' % num


def preserve_caps(title, detect_acronyms=False):
    """Preserve the capitalization of a title according to a certain heuristic.
    If there is an all-caps word, preserve the caps. If there is a CamelCapsed
    word, preserve the caps. If there is a capitalized word and it is not the
    first word, preserve the caps. If there is a number followed by a unit with
    caps in it, preserve the caps. This requires you not to have spurious caps
    in your Zotero library."""
    title = re.sub(r'\b([A-Z][A-Z0-9]+|[A-Z0-9]+[A-Z])\b', r'{\1}', title)
    title = re.sub(r'\b([A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+)\b', r'{\1}', title)
    title = re.sub(r'(?<=[^A-Z])\b([A-Z][a-z]+)\b', r'{\1}', title)
    title = re.sub(r'\b([0-9.]+\s+[a-z]*[A-Za-z/]+)\b', r'{\1}', title)
    if detect_acronyms:
        title = re.sub(r'(\{[A-Z0-9]+\})', r'{\\zoteroacronym\1}', title)
    return title

################################################################################


class Name:
    """Internal representation of an author's name"""
    def __init__(self, first, last):
        self.prefix = None
        self.suffix = None
        if first:
            if ', ' in first:
                first, self.suffix = first.split(', ', 1)
            self.givennames = first.split(" ")
        else:
            self.givennames = []
        surnames = []
        infixes = []
        for foo in last.split(' '):
            if surnames or not foo.islower():
                surnames.append(foo)
            else:
                infixes.append(foo)
        self.surname = ' '.join(surnames)
        self.infix = ' '.join(infixes)

    def __repr__(self):
        if self.givennames == []:
            first = 'None'
        else:
            first = ' '.join(self.givennames)
            if self.suffix:
                first += ', ' + self.suffix
        last = ''
        if self.infix:
            last += self.infix + ' '
        last += self.surname
        if first != 'None':
            first = '"' + first + '"'
        return 'Name({}, "{}")'.format(first, last)

    def full_name(self):
        if self.infix:
            retval = self.infix.encode('latex') + ' '
        else:
            retval = ''

        if ' ' in self.surname:
            retval += '{%s}' % self.surname.encode('latex')
        else:
            retval += self.surname.encode('latex')

        if not self.suffix and not self.prefix and not self.givennames:
            return retval
        if self.givennames == ['None']:
            if retval[0] == '{' and retval[-1] == '}':
                return retval
            return '{' + retval + '}'
        retval += ', '

        if self.suffix:
            retval += self.suffix.encode('latex') + ', '

        if self.prefix:
            retval += self.prefix.encode('latex') + ' '

        # Handle Cyrillic initials
        firstpart = (' '.join(self.givennames)).encode('latex')
        if 'Ya.' in firstpart:
            firstpart = firstpart.replace('Ya.', r'{\relax Ya}.')
        if 'Yu.' in firstpart:
            firstpart = firstpart.replace('Yu.', r'{\relax Yu}.')

        retval += firstpart
        return retval

################################################################################


class BibItem:
    """Internal representation of a bibliography item"""
    def __init__(self):
        # BibTeX item type
        self.zoterotype = None
        self.itemtype = None
        self.bibtexkey = None

        # BibTeX defined fields
        self.address = None       # Publisher's address (city)
        self.annote = None        # Annotation for annotated bibliography styles
        self.author = []          # list of Name()
        self.booktitle = None     # if only part of it is being cited
        self.chapter = None       # number
        self.crossref = None      # Key of cross-referenced entry
        self.edition = None       # Long form ("first")
        self.editor = []          # list of Name()
        self.eprint = None
        # Specification of electronic publication, often a preprint or technical
        # report
        self.howpublished = None  # if publishing method nonstandard
        self.institution = None   # not necessarily the publisher
        # Biber: is an alias for .school but is a list
        self.journal = None
        self.key = None
        # hidden field used for specifying or overriding the alphabetical order
        # of entries, when the author and editor fields are missing. Not
        # citation key.
        self.month = None         # Biber: use number
        self.note = None
        self.number = None        # journal issue or series number
        self.organization = None  # conference sponsor
        self.pages = None
        self.publisher = None
        self.school = None
        self.series = None        # Hardy Boys,Lecture Notes in Computer Science
        self.title = None
        self.bibtextype = None
        # 'type' field: type of tech report, e.g. Research Note
        self.volume = None
        self.year = None

        # Biber extended fields
        self.abstract = None
        self.addendum = None  # text to be printed at the end of the entry
        self.afterword = []  # author(s) of an afterword to the work
        self.annotator = []  # author(s) of annotations to the work
        self.authortype = None  # not used in standard styles
        self.bookauthor = []  # author(s) of the .booktitle
        self.bookpagination = None  # pagination scheme of .booktitle
        self.booksubtitle = None  # subtitle of .booktitle
        self.booktitleaddon = None  # annex to .booktitle, print in other font
        self.commentator = []  # author(s) of a commentary to the work
        self.date = None  # replacement for .month, .year?
        self.doi = None
        self.editora = []  # other editorial roles
        self.editorb = []
        self.editorc = []
        self.editortype = None  # .editor's role - editor, compiler, reviser, &c
        self.editoratype = None
        self.editorbtype = None
        self.editorctype = None
        self.eid = None  # electronic identifier of an @article
        self.entrysubtype = None  # not used in standard styles
        self.eprintclass = None
        self.eprinttype = None
        self.eventdate = None  # date of conference, symposium, etc.
        self.eventtitle = None  # title of conference, symposium, etc.
        self.file = None  # link to local PDF
        self.foreword = []  # author(s) of a foreword to the work
        self.holder = []  # holder(s) of a patent if different from .author
        self.hyphenation = None  # hyphenation language for the work
        self.indextitle = None  # title to use for indexing instead of .title
        self.introduction = []  # author(s) of an introduction to the work
        self.isan = None  # International Standard Audiovisual Number
        self.isbn = None  # Book
        self.ismn = None  # Music
        self.isrn = None  # Report
        self.issn = None  # Serial
        self.issue = None  # journal issue labeled as 'Spring', e.g.
        self.issuesubtitle = None
        self.issuetitle = None  # title of specific journal issue
        self.iswc = None  # International Standard Work Code
        self.journalsubtitle = None  # subtitle of journal, newspaper, etc.
        self.label = None  # fallback field if data is missing
        self.language = []  # language(s) of the work
        self.library = None  # library name and call number
        self.mainsubtitle = None
        self.maintitle = None  # main title of a multivolume book
        self.maintitleaddon = None
        self.nameaddon = None  # e.g. alias, pen name, real name
        self.origdate = None  # pub date of original edition if reprint, transl.
        self.origlanguage = None  # if translated
        self.origlocation = []  # if reprinted
        self.origpublisher = []  # if reprinted
        self.origtitle = []  # if translated
        self.pagetotal = None  # total number of pages
        self.pagination = None  # page, column, line, verse, section, paragraph
        self.part = None  # number of a partial volume
        self.pubstate = None  # e.g. 'in press'
        self.reprinttitle = None
        self.shortauthor = []  # e.g. {NASA} and Doe, John
        self.shorteditor = []
        self.shorthand = None  # ??
        self.shorthandintro = None  # Henceforth cited as ...
        self.shortjournal = None  # journal abbreviation
        self.shortseries = None
        self.shorttitle = None
        self.sorttitle = None
        self.subtitle = None  # subtitle of the work
        self.titleaddon = None  # annex to title, to be printed in other font
        self.translator = []  # translator(s) of the work
        self.url = None
        self.urldate = None  # access date of .url
        self.venue = None  # location of conference or symposium
        self.version = None  # software or manual version
        self.volumes = None  # total number of volumes

        # Biber meta-fields
        self.keywords = []

        # Fields that are meaningless to BibTeX but contain Zotero information
        self.timestamp = None

    def field(self, fieldname):
        return '\t{0} = {{{1}}},\n'.format(fieldname, getattr(self, fieldname).encode('latex'))

    def field_preserve_caps(self, fieldname, detect_acronyms=False):
        return '\t{0} = {{{1}}},\n'.format(fieldname, preserve_caps(getattr(self, fieldname).encode('latex'), detect_acronyms))

    def bibtex_string(self, use_abbrevs=False, use_biber=False, detect_acronyms=False):
        months = ['', 'jan', 'feb', 'mar', 'apr', 'may', 'jun',
            'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        retval = '@%s {%s,\n' % (self.itemtype, self.bibtexkey)

        # Common fields that should be at the top to increase readability
        if self.title:
            retval += self.field_preserve_caps('title', detect_acronyms)
        if self.author:
            retval += '\tauthor = {%s},\n' % \
                ' and '.join(map(Name.full_name, self.author))

        # Date
        if self.year:
            retval += '\tyear = %d,\n' % self.year
        if self.month and self.month != 0:
            if use_biber:
                retval += '\tmonth = {{{0}}},\n'.format(self.month)
            else:
                retval += '\tmonth = %s,\n' % months[self.month]

        # Journal
        if self.journal:
            fieldname = 'journaltitle' if use_biber else 'journal'
            if use_abbrevs and self.shortjournal:
                abbrev = self.shortjournal.encode('latex').replace('. ', '.\ ')
                retval += '\t{1} = {{{0}}},\n'.format(abbrev, fieldname)
            else:
                retval += '\t{0} = {{{1}}},\n'.format(fieldname, self.journal.encode('latex'))

        if self.volume:
            retval += self.field('volume')
        if self.number:
            retval += self.field('number')
        if self.pages:
            retval += self.field('pages')

        # Not-so-common fields, alphabetically in the middle
        if self.address:
            fieldname = 'location' if use_biber else 'address'
            retval += '\t{0} = {{{1}}},\n'.format(fieldname, self.address.encode('latex'))
        if self.annote:
            fieldname = 'annotation' if use_biber else 'annote'
            retval += '\t{0} = {{{1}}},\n'.format(fieldname, self.annote.encode('latex'))
        if self.booktitle:
            retval += self.field_preserve_caps('booktitle', detect_acronyms)
        if self.chapter:
            retval += self.field('chapter')
        if self.edition:
            if use_biber:
                retval += '\tedition = {{{0}}},\n'.format(self.edition)
            else:
                retval += '\tedition = {%s},\n' % ordinal(self.edition)
        if self.editor:
            retval += '\teditor = {%s},\n' % \
                ' and '.join(map(Name.full_name, self.editor)).encode('latex')
        if self.howpublished:
            retval += self.field('howpublished')
        if self.institution:
            retval += self.field('institution')
        if self.key:
            retval += '\tkey = {%s},\n' % self.key
        if self.organization:
            retval += self.field('organization')
        if self.publisher:
            retval += self.field('publisher')
        if self.school:
            fieldname = 'institution' if use_biber else 'school'
            retval += '\t{0} = {{{1}}},\n'.format(fieldname, self.school.encode('latex'))
        if self.series:
            retval += self.field('series')
        if self.bibtextype:
            retval += '\ttype = {%s},\n' % self.bibtextype if use_biber else self.bibtextype.encode('latex')

        # Biber fields; print them in any case, since BibTeX allows arbitrary ones
        if self.doi:
            retval += '\tdoi = {%s},\n' % self.doi
        if self.eventtitle:
            retval += self.field_preserve_caps('eventtitle', detect_acronyms)
        if self.eventdate:
            retval += self.field('eventdate')
        if self.hyphenation:
            retval += self.field('hyphenation')
        if self.language:
            retval += self.field('language')
        if self.library:
            retval += self.field('library')
        if self.shortjournal and not use_abbrevs:
            retval += self.field('shortjournal')
        if self.shorttitle:
            retval += self.field('shorttitle')
        if self.sorttitle:
            retval += self.field('sorttitle')
        if self.url:
            retval += '\turl = {%s},\n' % self.url
        if self.urldate:
            retval += '\turldate = {%s},\n' % self.urldate

        # Keywords, notes, etc. go at the end
        if self.note:
            retval += self.field('note')
        if self.abstract:
            retval += self.field('abstract')
        if self.keywords:
            retval += '\tkeywords = {%s},\n' % ', '.join(self.keywords)
        if self.timestamp:
            retval += '\ttimestamp = {%s},\n' % self.timestamp

        retval = retval.rstrip(',\n')  # remove last comma
        retval += '\n}\n'
        return retval

################################################################################


def generate_keys(bibitems):
    """ Generate a unique key for each bibliography item, and return it in a
    dictionary """
    delchars = ''.join(c for c in map(chr, range(256)) if not c.isalnum())
    for bibitem in bibitems:
        # If there was already a key overridden, then use that
        if bibitem.bibtexkey:
            continue

        # Decompose accented letters into ASCII letters plus combining marks,
        # then ignore combining marks and other non-ASCII characters
        # then take the last word of the author's last name
        # also delete non-alphanumeric characters
        try:
            authors = [unicodedata.normalize('NFKD', a.surname).encode('ASCII',
                'ignore').split()[-1]
                for a in bibitem.author]
        except IndexError:
            pass
        except TypeError:
            print '"' + a.surname + '"'
            print unicodedata.normalize('NFKD', a.surname)
            raise
        if len(authors) == 0:
            try:
                authors = [
                    unicodedata.normalize('NFKD', a.surname).encode('ASCII',
                    'ignore').split()[-1]
                    for a in bibitem.editor]
            except IndexError:
                authors = []
        authors = [a.translate(None, delchars) for a in authors]

        # Determine how to build the key depending on the item type
        if bibitem.itemtype == 'book':
            bibitem.bibtexkey = authors[0] + (authors[1] if len(authors) > 1 else '')
        elif bibitem.itemtype == 'mastersthesis':
            bibitem.bibtexkey = authors[0] + 'MastersThesis'
        elif bibitem.itemtype == 'phdthesis':
            bibitem.bibtexkey = authors[0] + 'PhDThesis'
        elif bibitem.itemtype == 'thesis':
            if bibitem.bibtextype == 'phdthesis':
                bibitem.bibtexkey = authors[0] + 'PhDThesis'
            elif bibitem.bibtextype == 'mathesis':
                bibitem.bibtexkey = authors[0] + 'MastersThesis'
            elif bibitem.bibtextype == 'candthesis':
                bibitem.bibtexkey = authors[0] + 'BachelorsThesis'
            else:
                bibitem.bibtexkey = authors[0] + 'Thesis'
        else:
            try:
                key_firstpart = authors[0]
            except IndexError:
                key_firstpart = bibitem.title.split(None, 1)[0]
            if bibitem.year:
                bibitem.bibtexkey = key_firstpart + unicode(bibitem.year)
            else:
                bibitem.bibtexkey = key_firstpart + 'Undated'

    # Make sure all the keys are unique
    keycount = collections.Counter([b.bibtexkey for b in bibitems])
    for bibitem in bibitems:
        if keycount[bibitem.bibtexkey] != 1:
            badkey = bibitem.bibtexkey
            nonuniques = [b for b in bibitems if b.bibtexkey == badkey]
            nonuniques.sort(key=operator.attrgetter('month', 'title'))
            for ix, b in enumerate(nonuniques):
                b.bibtexkey += chr(ord('a') + ix)
                keycount[b.bibtexkey] += 1
            keycount[badkey] = 0


################################################################################
# Shorthand


def value(graph, node, predicate):
    return graph.value(subject=node, predicate=predicate, any=False, default=None)


def value_if_type(graph, node, iftype):
    if value(graph, node, rdf['type']) == iftype:
        return value(graph, node, rdf['value'])
    return None


def name_from_rdf_person(g, item):
    givenname = value(g, item, foaf['givenname'])
    surname = value(g, item, foaf['surname'])
    return Name(
        unicode(givenname) if givenname else u'',
        unicode(surname) if surname else u'')

################################################################################


def process_item(g, item, use_biber=False, write_abstract=False):
    bibitem = BibItem()

    # item type
    bibitem.zoterotype = value(g, item, zotero['itemType'])
    try:
        bibitem.itemtype = typemapping[bibitem.zoterotype]
    except KeyError:
        print 'Unknown Zotero item type', bibitem.zoterotype
        print item
        bibitem.itemtype = 'misc'

    # Do item type cookery here

    # Figure out the difference between PhD and Master's thesis
    if use_biber:
        if bibitem.itemtype == 'thesis':
            thesis_type = value(g, item, zotero['type'])
            if thesis_type:
                if 'phd' in thesis_type.lower():
                    bibitem.bibtextype = 'phdthesis'
                elif 'master' in thesis_type.lower():
                    bibitem.bibtextype = 'mathesis'
                elif 'bachelor' in thesis_type.lower():
                    bibitem.bibtextype = 'candthesis'
    else:
        if bibitem.itemtype == 'phdthesis':
            thesis_type = value(g, item, zotero['type'])
            if thesis_type:
                if 'master' in thesis_type.lower():
                    bibitem.itemtype = 'mastersthesis'
                elif 'bachelor' in thesis_type.lower():
                    bibitem.itemtype = 'misc'

    # title is the only required field for any item type
    try:
        bibitem.title = value(g, item, dc['title'])
    except rdflib.exceptions.UniquenessError:
        # Encyclopedia articles and proceedings have 2 titles, for example
        titles = list(g.objects(subject=item, predicate=dc['title']))
        if bibitem.itemtype == 'inproceedings':
            # Guess which title is the proceedings title
            booktitle = None
            for t in titles:
                if t.lower().startswith('proceedings'):
                    booktitle = t
                    titles.remove(booktitle)
                    break
            bibitem.booktitle = booktitle
            bibitem.title = titles[0]
        else:
            bibitem.title = '{} --- {}'.format(titles[1], titles[0])
            # Encyclopedia format

    # list of authors
    if (item, bib['authors'], None) in g:
        authorlist = g.seq(value(g, item, bib['authors']))
        bibitem.author = [name_from_rdf_person(g, a) for a in authorlist]
    if (item, bib['editors'], None) in g:
        editorlist = g.seq(value(g, item, bib['editors']))
        bibitem.editor = [name_from_rdf_person(g, a) for a in editorlist]
    if bibitem.zoterotype == 'patent' and (item, zotero['inventors'], None) in g:
        inventorlist = g.seq(value(g, item, zotero['inventors']))
        bibitem.author = [name_from_rdf_person(g, a) for a in inventorlist]
    if bibitem.zoterotype == 'computerProgram' and (item, zotero['programmers'], None) in g:
        programmerlist = g.seq(value(g, item, zotero['programmers']))
        bibitem.author = [name_from_rdf_person(g, a) for a in programmerlist]

    # date
    datestring = value(g, item, dc['date'])
    if datestring is None:
        bibitem.year = None
    else:
        dateformats = [
            '%Y',  # least specific ones first
            '%B %Y',
            '%b %Y',
            '%b. %Y',
            '%m/%Y',
            '%m/%d/%Y',
            '%B 00, %Y',
            '%B %d, %Y',
            '%b %d %Y',
            '%b %d, %Y',
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d-%m-%Y',
            '%d %B %Y',
            '%d %b %Y',
        ]
        for format in dateformats:
            try:
                formatted = datetime.datetime.strptime(datestring, format)
                bibitem.year = formatted.year
                if format != '%Y':  # avoid default month of January
                    bibitem.month = formatted.month
                break
            except ValueError:
                pass
        if not bibitem.year:
            warnings.warn('Unknown date format: "{}"'.format(datestring))
    if bibitem.itemtype == 'inproceedings' and datestring is not None:
        bibitem.eventdate = '{0.year}-{0.month}-{0.day}'.format(formatted)

    # keywords
    for keyword in g.objects(item, dc['subject']):
        if type(keyword) is rdflib.Literal:
            bibitem.keywords.append(keyword)
        else:
            kwstring = value_if_type(g, keyword, zotero['AutomaticTag'])
            if kwstring is not None:
                bibitem.keywords.append(kwstring)

    # journal
    for parent in g.objects(item, dcterms['isPartOf']):
        if value(g, parent, rdf['type']) == bib['Journal']:
            bibitem.journal = value(g, parent, dc['title'])
            bibitem.volume = value(g, parent, prism['volume'])
            bibitem.number = value(g, parent, prism['number'])
            for identifier in g.objects(parent, dc['identifier']):
                if identifier.startswith('DOI '):
                    bibitem.doi = identifier[4:]
                elif identifier.startswith('ISSN '):
                    bibitem.issn = identifier[5:]
            bibitem.shortjournal = value(g, parent, dcterms['alternative'])

        # inbook
        elif value(g, parent, rdf['type']) == bib['Book']:
            bibitem.booktitle = value(g, parent, dc['title'])
            bibitem.volume = value(g, parent, prism['volume'])

            for grandparent in g.objects(parent, dcterms['isPartOf']):
                if value(g, grandparent, rdf['type']) == bib['Series']:
                    bibitem.series = value(g, grandparent, dc['title'])

        # magazine article
        elif value(g, parent, rdf['type']) == bib['Periodical']:
            bibitem.journal = value(g, parent, dc['title'])

    # pages
    bibitem.pages = value(g, item, bib['pages'])
    # if the pages are not APS-style numbering, replace - with figure dash
    if bibitem.pages and not bibitem.pages[1:6].isdigit():
        bibitem.pages.replace('-', '\N{Figure dash}')

    # conference info
    conference = value(g, item, bib['presentedAt'])
    if conference:
        bibitem.eventtitle = value(g, conference, dc['title'])

    # note
    for reference in g.objects(item, dcterms['isReferencedBy']):
        bibitem.note = value_if_type(g, reference, bib['Memo'])

    # timestamp
    datestring = value(g, item, dcterms['dateSubmitted'])
    if datestring:
        try:
            ts = datetime.datetime.strptime(datestring, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            ts = datetime.datetime.strptime(datestring, '%Y-%m-%d')
        bibitem.timestamp = '%04d.%02d.%02d' % (ts.year, ts.month, ts.day)
        if bibitem.zoterotype == 'webpage':
            bibitem.urldate = '%04d-%02d-%02d' % (ts.year, ts.month, ts.day)

    # url
    for ids in g.objects(item, dc['identifier']):
        bibitem.url = value_if_type(g, ids, dcterms['URI'])

    # publisher
    publisher = value(g, item, dc['publisher'])
    if publisher:
        bibitem.publisher = value(g, publisher, foaf['name'])
        address = value(g, publisher, vcard['adr'])
        bibitem.address = value(g, address, vcard['locality'])

    # Patent info
    if bibitem.zoterotype == 'patent':
        bibitem.number = value(g, item, prism['number'])
        bibitem.bibtextype = value(g, item, zotero['country'])
        bibitem.publisher = value(g, item, zotero['issuingAuthority'])

    # Language
    langcode = value(g, item, zotero['language'])
    if langcode:
        if langcode in language_codes:
            bibitem.language = bibitem.hyphenation = language_codes[langcode]
        elif langcode in language_codes.values():
            bibitem.language = bibitem.hyphenation = langcode

    # various info
    bibitem.library = value(g, item, zotero['libraryCatalog'])
    bibitem.shorttitle = value(g, item, zotero['shortTitle'])
    if write_abstract:
        bibitem.abstract = value(g, item, dcterms['abstract'])

    # Override any fields if specified in the "Extra" field with a format of
    # fieldname = {fieldvalue}
    extra = value(g, item, dc['description'])
    if extra:
        extra_lines = extra.split('\n')
        for line in extra_lines:
            match = re.match(r'^([a-z]+) = \{(.*)\}$', line)
            if match:
                setattr(bibitem, match.group(1), match.group(2))

    return bibitem

################################################################################


def main(argv=None):
    parser = argparse.ArgumentParser(description='Converts Zotero RDF to BibTeX.')
    parser.add_argument('infile',
        type=argparse.FileType('r'),
        nargs='?',
        default=sys.stdin,
        help='Input Zotero RDF file (default: read from standard input)')
    parser.add_argument('outfile',
        type=argparse.FileType('w'),
        nargs='?',
        default=sys.stdout,
        help='Output BibTeX file (default: write to standard output)')
    parser.add_argument('--biber',
        action='store_true',
        help="Use Biber's extensions to BibTeX format")
    parser.add_argument('--abbreviations',
        action='store_true',
        help='Put the journal abbreviation in the "journal" field instead of in the "abbrev" field')
    parser.add_argument('--acronyms',
        action='store_true',
        help='Try to detect acronyms in titles and surround them with \\zoteroacronym')
    parser.add_argument('--version',
        action='version',
        version='Zotero2BibTeX version 0')
    args = parser.parse_args()

    latex.register()

    if args.biber:
        biber_update_types()

    g = rdflib.ConjunctiveGraph()
    g.load(args.infile)

    # Iterate over all the items in the bibliography
    bibitems = [process_item(g, s, use_biber=args.biber)
        for s, o in g.subject_objects(zotero['itemType'])
        if g.value(subject=s, predicate=zotero['itemType']) != 'attachment']

    # Generate unique keys for each item according to my personal style
    generate_keys(bibitems)

    for bibitem in bibitems:
        args.outfile.write(bibitem.bibtex_string(
            use_biber=args.biber,
            use_abbrevs=args.abbreviations,
            detect_acronyms=args.acronyms))

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
