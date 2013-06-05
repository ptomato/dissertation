"""latex.py

Character translation utilities for LaTeX-formatted text.

Usage:
 - unicode(string,'latex')
 - ustring.decode('latex')
are both available just by letting "import latex" find this file.
 - unicode(string,'latex+latin1')
 - ustring.decode('latex+latin1')
where latin1 can be replaced by any other known encoding, also
become available by calling latex.register().

We also make public a dictionary latex_equivalents,
mapping ord(unicode char) to LaTeX code.

D. Eppstein, October 2003.
"""

from __future__ import generators
import codecs
import re
from sets import Set


def register():
    """Enable encodings of the form 'latex+x' where x describes another encoding.
    Unicode characters are translated to or from x when possible, otherwise
    expanded to latex.
    """
    codecs.register(_registry)


def getregentry():
    """Encodings module API."""
    return _registry('latex')


def _registry(encoding):
    if encoding == 'latex':
        encoding = None
    elif encoding.startswith('latex+'):
        encoding = encoding[6:]
    else:
        return None

    class Codec(codecs.Codec):
        def encode(self, input, errors='strict'):
            """Convert unicode string to latex."""
            output = []
            for c in input:
                if encoding:
                    try:
                        output.append(str(c).encode(encoding))
                        continue
                    except:
                        pass
                if unicode(c) in latex_equivalents:
                    output.append(latex_equivalents[unicode(c)])
                else:
                    output += ['{\\char', str(ord(c)), '}']
            return ''.join(output), len(input)

        def decode(self, input, errors='strict'):
            """Convert latex source string to unicode."""
            if encoding:
                input = unicode(input, encoding, errors)

            # Note: we may get buffer objects here.
            # It is not permussable to call join on buffer objects
            # but we can make them joinable by calling unicode.
            # This should always be safe since we are supposed
            # to be producing unicode output anyway.
            x = map(unicode, _unlatex(input))
            return u''.join(x), len(input)

    class StreamWriter(Codec, codecs.StreamWriter):
        pass

    class StreamReader(Codec, codecs.StreamReader):
        pass

    return (Codec().encode, Codec().decode, StreamReader, StreamWriter)


def _tokenize(tex):
    """Convert latex source into sequence of single-token substrings."""
    start = 0
    try:
        # skip quickly across boring stuff
        pos = _stoppers.finditer(tex).next().span()[0]
    except StopIteration:
        yield tex
        return

    while 1:
        if pos > start:
            yield tex[start:pos]
            if tex[start] == '\\' and not (tex[pos - 1].isdigit() and tex[start + 1].isalpha()):
                while pos < len(tex) and tex[pos].isspace():  # skip blanks after csname
                    pos += 1

        while pos < len(tex) and tex[pos] in _ignore:
            pos += 1    # flush control characters
        if pos >= len(tex):
            return
        start = pos
        if tex[pos:pos + 2] in {'$$': None, '/~': None}:    # protect ~ in urls
            pos += 2
        elif tex[pos].isdigit():
            while pos < len(tex) and tex[pos].isdigit():
                pos += 1
        elif tex[pos] == '-':
            while pos < len(tex) and tex[pos] == '-':
                pos += 1
        elif tex[pos] != '\\' or pos == len(tex) - 1:
            pos += 1
        elif not tex[pos + 1].isalpha():
            pos += 2
        else:
            pos += 1
            while pos < len(tex) and tex[pos].isalpha():
                pos += 1
            if tex[start:pos] == '\\char' or tex[start:pos] == '\\accent':
                while pos < len(tex) and tex[pos].isdigit():
                    pos += 1


class _unlatex:
    """Convert tokenized tex into sequence of unicode strings.  Helper for decode()."""

    def __iter__(self):
        """Turn self into an iterator.  It already is one, nothing to do."""
        return self

    def __init__(self, tex):
        """Create a new token converter from a string."""
        self.tex = tuple(_tokenize(tex))  # turn tokens into indexable list
        self.pos = 0                    # index of first unprocessed token
        self.lastoutput = 'x'           # lastoutput must always be nonempty string

    def __getitem__(self, n):
        """Return token at offset n from current pos."""
        p = self.pos + n
        t = self.tex
        return p < len(t) and t[p] or None

    def next(self):
        """Find and return another piece of converted output."""
        if self.pos >= len(self.tex):
            raise StopIteration
        nextoutput = self.chunk()
        if self.lastoutput[0] == '\\' and self.lastoutput[-1].isalpha() and nextoutput[0].isalpha():
            nextoutput = ' ' + nextoutput   # add extra space to terminate csname
        self.lastoutput = nextoutput
        return nextoutput

    def chunk(self):
        """Grab another set of input tokens and convert them to an output string."""
        for delta, c in self.candidates(0):
            if c in _l2u:
                self.pos += delta
                return unichr(_l2u[c])
            elif len(c) == 2 and c[1] == 'i' and (c[0], '\\i') in _l2u:
                self.pos += delta       # correct failure to undot i
                return unichr(_l2u[(c[0], '\\i')])
            elif len(c) == 1 and c[0].startswith('\\char') and c[0][5:].isdigit():
                self.pos += delta
                return unichr(int(c[0][5:]))

        # nothing matches, just pass through token as-is
        self.pos += 1
        return self[-1]

    def candidates(self, offset):
        """Generate pairs delta,c where c is a token or tuple of tokens from tex
        (after deleting extraneous brackets starting at pos) and delta
        is the length of the tokens prior to bracket deletion.
        """
        t = self[offset]
        if t in _blacklist:
            return
        elif t == '{':
            for delta, c in self.candidates(offset + 1):
                if self[offset + delta + 1] == '}':
                    yield delta + 2, c
        elif t == '\\mbox':
            for delta, c in self.candidates(offset + 1):
                yield delta + 1, c
        elif t == '$' and self[offset + 2] == '$':
            yield 3, (t, self[offset + 1], t)
        else:
            q = self[offset + 1]
            if q == '{' and self[offset + 3] == '}':
                yield 4, (t, self[offset + 2])
            elif q:
                yield 2, (t, q)
            yield 1, t

latex_equivalents = {
    # Selected Basic Latin characters (0000-007F)
    u'\t':     ' ',
    u'\u000A': '\n',
    u'"':      '\\textquotedbl ',
    u'#':      '\\#',
    u'$':      '\\$',
    u'%':      '\\%',
    u'&':      '\\&',
    u'<':      '$<$',
    u'>':      '$>$',
    u'\\':     '\\textbackslash ',
    u'^':      '\\^{}',
    u'_':      '\\_',
    u'{':      '\\{',
    u'}':      '\\}',
    u'~':      '\\~{}',

    # Latin-1 Supplement (0080-00FF)
    # Skip: control characters (0080-009F)
    u'\N{No-break space}':                             '~',
    u'\N{Inverted exclamation mark}':                  '!`',
    u'\N{Cent sign}':                                  '\\not{c}',
    u'\N{Pound sign}':                                 '\\pounds ',
    u'\N{Currency sign}':                              '\\textcurrency ',  # textcomp
    u'\N{Yen sign}':                                   '\\textyen ',  # textcomp
    u'\N{Broken bar}':                                 '\\textbrokenbar ',  # textcomp
    u'\N{Section sign}':                               '\\S ',
    u'\N{Diaeresis}':                                  '\\"{}',
    u'\N{Copyright sign}':                             '\\copyright ',
    u'\N{Feminine ordinal indicator}':                 '\\textordfeminine ',
    u'\N{Left-pointing double angle quotation mark}':  '\\guillemotleft ',  # T1
    u'\N{Not sign}':                                   '\\neg ',
    u'\N{Soft hyphen}':                                '\\-',
    u'\N{Registered sign}':                            '\\textregistered ',
    u'\N{Macron}':                                     '\\={}',
    u'\N{Degree sign}':                                '\\textdegree ',
    u'\N{Plus-minus sign}':                            '$\\pm$',
    u'\N{Superscript two}':                            '$^2$',
    u'\N{Superscript three}':                          '$^3$',
    u'\N{Acute accent}':                               "\\'{}",
    u'\N{Micro sign}':                                 '\\textmu ',
    u'\N{Pilcrow sign}':                               '\\P',
    u'\N{Middle dot}':                                 '$\\cdot$',
    u'\N{Cedilla}':                                    '\\c{}',
    u'\N{Superscript one}':                            '$^1$',
    u'\N{Masculine ordinal indicator}':                '\\textordmasculine ',
    u'\N{Right-pointing double angle quotation mark}': '\\guillemotright ',  # T1
    u'\N{Vulgar fraction one quarter}':                '$\\frac{1}{4}$',
    u'\N{Vulgar fraction one half}':                   '$\\frac{1}{2}$',
    u'\N{Vulgar fraction three quarters}':             '$\\frac{3}{4}$',
    u'\N{Inverted question mark}':                     '?`',
    u'\N{Latin capital letter A with grave}':          '\\`A',
    u'\N{Latin capital letter A with acute}':          "\\'A",
    u'\N{Latin capital letter A with circumflex}':     '\\^A',
    u'\N{Latin capital letter A with tilde}':          '\\~A',
    u'\N{Latin capital letter A with diaeresis}':      '\\"A',
    u'\N{Latin capital letter A with ring above}':     '\\AA ',
    u'\N{Latin capital letter AE}':                    '\\AE ',
    u'\N{Latin capital letter C with cedilla}':        '\\c{C}',
    u'\N{Latin capital letter E with grave}':          '\\`E',
    u'\N{Latin capital letter E with acute}':          "\\'E",
    u'\N{Latin capital letter E with circumflex}':     '\\^E',
    u'\N{Latin capital letter E with diaeresis}':      '\\"E',
    u'\N{Latin capital letter I with grave}':          '\\`I',
    u'\N{Latin capital letter I with acute}':          "\\'I",
    u'\N{Latin capital letter I with circumflex}':     '\\^I',
    u'\N{Latin capital letter I with diaeresis}':      '\\"I',
    u'\N{Latin capital letter Eth}':                   '\\DH ',  # T1
    u'\N{Latin capital letter N with tilde}':          '\\~N',
    u'\N{Latin capital letter O with grave}':          '\\`O',
    u'\N{Latin capital letter O with acute}':          "\\'O",
    u'\N{Latin capital letter O with circumflex}':     '\\^O',
    u'\N{Latin capital letter O with tilde}':          '\\~O',
    u'\N{Latin capital letter O with diaeresis}':      '\\"O',
    u'\N{Multiplication sign}':                        '$\\times$',
    u'\N{Latin capital letter O with stroke}':         '\\O ',
    u'\N{Latin capital letter U with grave}':          '\\`U',
    u'\N{Latin capital letter U with acute}':          "\\'U",
    u'\N{Latin capital letter U with circumflex}':     '\\^U',
    u'\N{Latin capital letter U with diaeresis}':      '\\"U',
    u'\N{Latin capital letter Y with acute}':          "\\'Y",
    u'\N{Latin capital letter Thorn}':                 '\\TH ',  # T1
    u'\N{Latin small letter sharp S}':                 '\\ss',
    u'\N{Latin small letter A with grave}':            '\\`a',
    u'\N{Latin small letter A with acute}':            "\\'a",
    u'\N{Latin small letter A with circumflex}':       '\\^a',
    u'\N{Latin small letter A with tilde}':            '\\~a',
    u'\N{Latin small letter A with diaeresis}':        '\\"a',
    u'\N{Latin small letter A with ring above}':       '\\aa ',
    u'\N{Latin small letter AE}':                      '\\ae ',
    u'\N{Latin small letter C with cedilla}':          '\\c{c}',
    u'\N{Latin small letter E with grave}':            '\\`e',
    u'\N{Latin small letter E with acute}':            "\\'e",
    u'\N{Latin small letter E with circumflex}':       '\\^e',
    u'\N{Latin small letter E with diaeresis}':        '\\"e',
    u'\N{Latin small letter I with grave}':            '\\`\\i ',
    u'\N{Latin small letter I with acute}':            "\\'i",  # \i no wurk?
    u'\N{Latin small letter I with circumflex}':       '\\^\\i ',
    u'\N{Latin small letter I with diaeresis}':        '\\"\\i ',
    u'\N{Latin small letter Eth}':                     '\\dh ',  # T1
    u'\N{Latin small letter N with tilde}':            '\\~n',
    u'\N{Latin small letter O with grave}':            '\\`o',
    u'\N{Latin small letter O with acute}':            "\\'o",
    u'\N{Latin small letter O with circumflex}':       '\\^o',
    u'\N{Latin small letter O with tilde}':            '\\~o',
    u'\N{Latin small letter O with diaeresis}':        '\\"o',
    u'\N{Division sign}':                              '$\\div$',
    u'\N{Latin small letter O with stroke}':           '\\o ',
    u'\N{Latin small letter U with grave}':            '\\`u',
    u'\N{Latin small letter U with acute}':            "\\'u",
    u'\N{Latin small letter U with circumflex}':       '\\^u',
    u'\N{Latin small letter U with diaeresis}':        '\\"u',
    u'\N{Latin small letter Y with acute}':            "\\'y",
    u'\N{Latin small letter Thorn}':                   '\\th ',  # T1
    u'\N{Latin small letter Y with diaeresis}':        '\\"y',

    # Latin Extended A (0100-017F)
    u'\N{Latin capital letter A with macron}':          '\\=A',
    u'\N{Latin small letter A with macron}':            '\\=a',
    u'\N{Latin capital letter A with breve}':           '\\u{A}',
    u'\N{Latin small letter A with breve}':             '\\u{a}',
    u'\N{Latin capital letter A with ogonek}':          '\\c{A}',
    u'\N{Latin small letter A with ogonek}':            '\\c{a}',
    u'\N{Latin capital letter C with acute}':           "\\'C",
    u'\N{Latin small letter C with acute}':             "\\'c",
    u'\N{Latin capital letter C with circumflex}':      "\\^C",
    u'\N{Latin small letter C with circumflex}':        "\\^c",
    u'\N{Latin capital letter C with dot above}':       "\\.C",
    u'\N{Latin small letter C with dot above}':         "\\.c",
    u'\N{Latin capital letter C with caron}':           "\\v{C}",
    u'\N{Latin small letter C with caron}':             "\\v{c}",
    u'\N{Latin capital letter D with caron}':           "\\v{D}",
    u'\N{Latin small letter D with caron}':             "\\v{d}",
    u'\N{Latin capital letter D with stroke}':          '\\DJ ',  # T1
    u'\N{Latin small letter D with stroke}':            '\\dj ',  # T1
    u'\N{Latin capital letter E with macron}':          '\\=E',
    u'\N{Latin small letter E with macron}':            '\\=e',
    u'\N{Latin capital letter E with breve}':           '\\u{E}',
    u'\N{Latin small letter E with breve}':             '\\u{e}',
    u'\N{Latin capital letter E with dot above}':       '\\.E',
    u'\N{Latin small letter E with dot above}':         '\\.e',
    u'\N{Latin capital letter E with ogonek}':          '\\c{E}',
    u'\N{Latin small letter E with ogonek}':            '\\c{e}',
    u'\N{Latin capital letter E with caron}':           "\\v{E}",
    u'\N{Latin small letter E with caron}':             "\\v{e}",
    u'\N{Latin capital letter G with circumflex}':      '\\^G',
    u'\N{Latin small letter G with circumflex}':        '\\^g',
    u'\N{Latin capital letter G with breve}':           '\\u{G}',
    u'\N{Latin small letter G with breve}':             '\\u{g}',
    u'\N{Latin capital letter G with dot above}':       '\\.G',
    u'\N{Latin small letter G with dot above}':         '\\.g',
    u'\N{Latin capital letter G with cedilla}':         '\\c{G}',
    u'\N{Latin small letter G with cedilla}':           '\\c{g}',
    u'\N{Latin capital letter H with circumflex}':      '\\^H',
    u'\N{Latin small letter H with circumflex}':        '\\^h',
    u'\N{Latin capital letter I with tilde}':           '\\~I',
    u'\N{Latin small letter I with tilde}':             '\\~\\i ',
    u'\N{Latin capital letter I with macron}':          '\\=I',
    u'\N{Latin small letter I with macron}':            '\\=\\i ',
    u'\N{Latin capital letter I with breve}':           '\\u{I}',
    u'\N{Latin small letter I with breve}':             '\\u\\i ',
    u'\N{Latin capital letter I with ogonek}':          '\\c{I}',
    u'\N{Latin small letter I with ogonek}':            '\\c{i}',
    u'\N{Latin capital letter I with dot above}':       '\\.I',
    u'\N{Latin small letter dotless I}':                '\\i ',
    u'\N{Latin capital ligature IJ}':                   '{IJ}',
    u'\N{Latin small ligature IJ}':                     '{ij}',
    u'\N{Latin capital letter J with circumflex}':      '\\^J',
    u'\N{Latin small letter J with circumflex}':        '\\^\\j',
    u'\N{Latin capital letter K with cedilla}':         '\\c{K}',
    u'\N{Latin small letter K with cedilla}':           '\\c{k}',
    u'\N{Latin capital letter L with acute}':           "\\'L",
    u'\N{Latin small letter L with acute}':             "\\'l",
    u'\N{Latin capital letter L with cedilla}':         "\\c{L}",
    u'\N{Latin small letter L with cedilla}':           "\\c{l}",
    u'\N{Latin capital letter L with caron}':           "\\v{L}",
    u'\N{Latin small letter L with caron}':             "\\v{l}",
    u'\N{Latin capital letter L with middle dot}':      'L',  # FIXME!
    u'\N{Latin small letter L with middle dot}':        'l',  # FIXME!
    u'\N{Latin capital letter L with stroke}':          '\\L ',
    u'\N{Latin small letter L with stroke}':            '\\l ',
    u'\N{Latin capital letter N with acute}':           "\\'N",
    u'\N{Latin small letter N with acute}':             "\\'n",
    u'\N{Latin capital letter N with cedilla}':         "\\c{N}",
    u'\N{Latin small letter N with cedilla}':           "\\c{n}",
    u'\N{Latin capital letter N with caron}':           "\\v{N}",
    u'\N{Latin small letter N with caron}':             "\\v{n}",
    u'\N{Latin small letter N preceded by apostrophe}': "'n",  # ?
    u'\N{Latin capital letter Eng}':                    '\\NG ',  # T1
    u'\N{Latin small letter Eng}':                      '\\ng ',  # T1
    u'\N{Latin capital letter O with macron}':          '\\=O',
    u'\N{Latin small letter O with macron}':            '\\=o',
    u'\N{Latin capital letter O with breve}':           '\\u{O}',
    u'\N{Latin small letter O with breve}':             '\\u{o}',
    u'\N{Latin capital letter O with double acute}':    '\\H{O}',
    u'\N{Latin small letter O with double acute}':      '\\H{o}',
    u'\N{Latin capital ligature OE}':                   '\\OE ',
    u'\N{Latin small ligature OE}':                     '\\oe ',
    u'\N{Latin capital letter R with acute}':           "\\'R",
    u'\N{Latin small letter R with acute}':             "\\'r",
    u'\N{Latin capital letter R with cedilla}':         "\\c{R}",
    u'\N{Latin small letter R with cedilla}':           "\\c{r}",
    u'\N{Latin capital letter R with caron}':           "\\v{R}",
    u'\N{Latin small letter R with caron}':             "\\v{r}",
    u'\N{Latin capital letter S with acute}':           "\\'S",
    u'\N{Latin small letter S with acute}':             "\\'s",
    u'\N{Latin capital letter S with circumflex}':      "\\^S",
    u'\N{Latin small letter S with circumflex}':        "\\^s",
    u'\N{Latin capital letter S with cedilla}':         "\\c{S}",
    u'\N{Latin small letter S with cedilla}':           "\\c{s}",
    u'\N{Latin capital letter S with caron}':           "\\v{S}",
    u'\N{Latin small letter S with caron}':             "\\v{s}",
    u'\N{Latin capital letter T with cedilla}':         "\\c{T}",
    u'\N{Latin small letter T with cedilla}':           "\\c{t}",
    u'\N{Latin capital letter T with caron}':           "\\v{T}",
    u'\N{Latin small letter T with caron}':             "\\v{t}",
    u'\N{Latin capital letter T with stroke}':          'T',  # FIXME!
    u'\N{Latin small letter T with stroke}':            't',  # FIXME!
    u'\N{Latin capital letter U with tilde}':           "\\~U",
    u'\N{Latin small letter U with tilde}':             "\\~u",
    u'\N{Latin capital letter U with macron}':          "\\=U",
    u'\N{Latin small letter U with macron}':            "\\=u",
    u'\N{Latin capital letter U with breve}':           "\\u{U}",
    u'\N{Latin small letter U with breve}':             "\\u{u}",
    u'\N{Latin capital letter U with ring above}':      "\\r{U}",
    u'\N{Latin small letter U with ring above}':        "\\r{u}",
    u'\N{Latin capital letter U with double acute}':    "\\H{U}",
    u'\N{Latin small letter U with double acute}':      "\\H{u}",
    u'\N{Latin capital letter U with ogonek}':          "\\c{U}",
    u'\N{Latin small letter U with ogonek}':            "\\c{u}",
    u'\N{Latin capital letter W with circumflex}':      "\\^W",
    u'\N{Latin small letter W with circumflex}':        "\\^w",
    u'\N{Latin capital letter Y with circumflex}':      "\\^Y",
    u'\N{Latin small letter Y with circumflex}':        "\\^y",
    u'\N{Latin capital letter Y with diaeresis}':       '\\"Y',
    u'\N{Latin capital letter Z with acute}':           "\\'Z",
    u'\N{Latin small letter Z with acute}':             "\\'z",
    u'\N{Latin capital letter Z with dot above}':       "\\.Z",
    u'\N{Latin small letter Z with dot above}':         "\\.z",
    u'\N{Latin capital letter Z with caron}':           "\\v{Z}",
    u'\N{Latin small letter Z with caron}':             "\\v{z}",
    u'\N{Latin small letter long S}':                   's',  # FIXME!

    # Latin Extended-B (0180-024F)
    u'\N{Latin capital letter DZ with caron}':           "{D\\v{Z}}",  # 01C4
    u'\N{Latin capital letter D with small letter Z with caron}': "{D\\v{z}}",  # 01C5
    u'\N{Latin small letter DZ with caron}':             "{d\\v{z}}",  # 01C6
    u'\N{Latin capital letter LJ}':                      "{LJ}",  # 01C7
    u'\N{Latin capital letter L with small letter J}':   "{Lj}",  # 01C8
    u'\N{Latin small letter LJ}':                        "{lj}",  # 01C9
    u'\N{Latin capital letter NJ}':                      "{NJ}",  # 01CA
    u'\N{Latin capital letter N with small letter J}':   "{Nj}",  # 01CB
    u'\N{Latin small letter NJ}':                        "{nj}",  # 01CC
    u'\N{Latin capital letter A with caron}':            "\\v{A}",  # 01CD
    u'\N{Latin small letter A with caron}':              "\\v{a}",  # 01CE
    u'\N{Latin capital letter I with caron}':            "\\v{I}",  # 01CF
    u'\N{Latin small letter I with caron}':              "\\v\\i ",  # 01D0
    u'\N{Latin capital letter O with caron}':            "\\v{O}",  # 01D1
    u'\N{Latin small letter O with caron}':              "\\v{o}",  # 01D2
    u'\N{Latin capital letter U with caron}':            "\\v{U}",  # 01D3
    u'\N{Latin small letter U with caron}':              "\\v{u}",  # 01D4

    u'\N{Latin capital letter G with caron}':            "\\v{G}",  # 01E6
    u'\N{Latin small letter G with caron}':              "\\v{g}",  # 01E7
    u'\N{Latin capital letter K with caron}':            "\\v{K}",  # 01E8
    u'\N{Latin small letter K with caron}':              "\\v{k}",  # 01E9
    u'\N{Latin capital letter O with ogonek}':           "\\c{O}",  # 01EA
    u'\N{Latin small letter O with ogonek}':             "\\c{o}",  # 01EB

    u'\N{Latin small letter J with caron}':              "\\v\\j ",  # 01F0
    u'\N{Latin capital letter DZ}':                      "{DZ}",  # 01F1
    u'\N{Latin capital letter D with small letter Z}':   "{Dz}",  # 01F2
    u'\N{Latin small letter DZ}':                        "{dz}",  # 01F3
    u'\N{Latin capital letter G with acute}':            "\\'G",  # 01F4
    u'\N{Latin small letter G with acute}':              "\\'g",  # 01F5

    u'\N{Latin capital letter AE with acute}':           "\\'\\AE ",  # 01FC
    u'\N{Latin small letter AE with acute}':             "\\'\\ae ",  # 01FD
    u'\N{Latin capital letter O with stroke and acute}': "\\'\\O ",  # 01FE
    u'\N{Latin small letter O with stroke and acute}':   "\\'\\o ",  # 01FF

    # IPA Extensions (0250-02AF)

    # Spacing Modifier Letters (02B0-02FE)
    u'\N{Modifier letter circumflex accent}': '\\^{}',  # 02C6
    u'\N{Caron}':                             '\\v{}',  # 02C7

    u'\N{Breve}':                             '\\u{}',  # 02D8
    u'\N{Dot above}':                         '\\.{}',  # 02D9
    u'\N{Ring above}':                        '\\r{}',  # 02DA
    u'\N{Ogonek}':                            '\\c{}',  # 02DB
    u'\N{Small tilde}':                       '\\~{}',  # 02DC
    u'\N{Double acute accent}':               '\\H{}',  # 02DD

    # Greek and Coptic (0374-03FF)
    u'\N{Greek small letter Epsilon}': '$\\epsilon$',  # 03B5
    u'\N{Greek small letter Pi}':      '$\\pi$',  # 03C0
    # consider adding more Greek here

    # Cyrillic (0400-04FF)

    # tip from http://www.tex.ac.uk/cgi-bin/texfaq2html?label=bibtranscinit
    u'\N{Cyrillic capital letter Yu}': '{\\relax Yu}',  # 042E
    u'\N{Cyrillic capital letter Ya}': '{\\relax Ya}',  # 042F

    # Cyrillic Supplement (0500-0523)
    # Armenian (0531-0589)
    # Hebrew (05BE-05F4)
    # Arabic (0600-06FF)
    # Syriac (0700-074F)
    # Arabic Supplement (0750-076D)
    # Thaana (0780-07B1)
    # N'Ko (07C0-07FA)
    # Unified Canadian Aboriginal Syllabics (1401-1676)
    # Latin Extended Additional (1E00-1EFF)

    # General Punctuation (2000-206F)
    u'\N{Figure dash}':                 '--',  # 2012
    u'\N{En dash}':                     '--',  # 2013
    u'\N{Em dash}':                     '---',  # 2014

    u'\N{Left single quotation mark}':  "`",  # 2018
    u'\N{Right single quotation mark}': "'",  # 2019

    u'\N{Left double quotation mark}':  "``",  # 201C
    u'\N{Right double quotation mark}': "''",  # 201D

    u'\N{Dagger}':                      "\\dag ",  # 2020
    u'\N{Double dagger}':               "\\ddag ",  # 2021
    u'\N{Bullet}':                      "$\\bullet$",  # 2022

    u'\N{Horizontal ellipsis}':         "\\ldots ",  # 2026

    # Letterlike Symbols (2100-214F)
    u'\N{Trade mark sign}': "\\texttrademark ",  # 2122

    # Number Forms (2150-218F)
    # Arrows (2190-21FF)

    # Mathematical Operators (2200-22FF)
    u'\N{Partial differential}':     "$\\partial$",  # 2202

    u'\N{N-ary product}':            "$\\prod$",  # 220F

    u'\N{N-ary summation}':          "$\\sum$",  # 2211

    u'\N{Square root}':              "$\\surd$",  # 221A

    u'\N{Infinity}':                 "$\\infty$",  # 221E

    u'\N{Integral}':                 "$\\int$",  # 222B

    u'\N{Almost equal to}':          "$\\approx$",  # 2248

    u'\N{Not equal to}':             "$\\neq$",  # 2260

    u'\N{Less-than or equal to}':    "$\\leq$",  # 2264
    u'\N{Greater-than or equal to}': "$\\geq$",  # 2265

    # Block Elements (2580-259F)
    # Geometric Shapes (25A0-25FF)
    # Miscellaneous Symbols (2600-26C3)
    # Dingbats (2701-27BE)
    # Miscellaneous Mathematical Symbols A (27C0-27EF)
    # Supplemental Arrows A (27F0-27FF)
    # Braille Patterns (2800-28FF)
    # Latin Extended C (2C60-2C77)
    # CJK Unified Ideographs (4E00-9FFF)
    # Yi Syllables (A000-A48F)
    # Latin Extended D (A720-A721)

    # Alphabetic Presentation Forms (FB00-FB4F)
    u'\N{Latin small ligature FF}': '{ff}',
    u'\N{Latin small ligature FI}': '{fi}',
    u'\N{Latin small ligature FL}': '{fl}',

    # Specials (FFFC-FFFD)
}
for _i in range(0x0020):
    if chr(_i) not in latex_equivalents:
        latex_equivalents[chr(_i)] = ''
for _i in range(0x0020, 0x007f):
    if chr(_i) not in latex_equivalents:
        latex_equivalents[chr(_i)] = chr(_i)

# Characters that should be ignored and not output in tokenization
_ignore = Set([chr(i) for i in range(32) + [127]]) - Set('\t\n\r')

# Regexp of chars not in blacklist, for quick start of tokenize
_stoppers = re.compile('[\x00-\x1f!$\\-?\\{~\\\\`\']')

_blacklist = Set(' \n\r')
_blacklist.add(None)    # shortcut candidate generation at end of data

# Construction of inverse translation table
_l2u = {
    '\ ': ord(' ')   # unexpanding space makes no sense in non-TeX contexts
}

for _tex in latex_equivalents:
    if ord(_tex) <= 0x0020 or (ord(_tex) <= 0x007f and len(latex_equivalents[_tex]) <= 1):
        continue    # boring entry
    _toks = tuple(_tokenize(latex_equivalents[_tex]))
    if _toks[0] == '{' and _toks[-1] == '}':
        _toks = _toks[1:-1]
    if _toks[0].isalpha():
        continue    # don't turn ligatures into single chars
    if len(_toks) == 1 and (_toks[0] == "'" or _toks[0] == "`"):
        continue    # don't turn ascii quotes into curly quotes
    if _toks[0] == '\\mbox' and _toks[1] == '{' and _toks[-1] == '}':
        _toks = _toks[2:-1]
    if len(_toks) == 4 and _toks[1] == '{' and _toks[3] == '}':
        _toks = (_toks[0], _toks[2])
    if len(_toks) == 1:
        _toks = _toks[0]
    _l2u[_toks] = _tex

# Shortcut candidate generation for certain useless candidates:
# a character is in _blacklist if it can not be at the start
# of any translation in _l2u.  We use this to quickly skip through
# such characters before getting to more difficult-translate parts.
# _blacklist is defined several lines up from here because it must
# be defined in order to call _tokenize, however it is safe to
# delay filling it out until now.

for i in range(0x0020, 0x007f):
    _blacklist.add(chr(i))
_blacklist.remove('{')
_blacklist.remove('$')
for candidate in _l2u:
    if isinstance(candidate, tuple):
        if not candidate or not candidate[0]:
            continue
        firstchar = candidate[0][0]
    else:
        firstchar = candidate[0]
    _blacklist.discard(firstchar)
