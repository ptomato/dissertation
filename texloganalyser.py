#!/usr/bin/env python

"""
texloganalyser -- displays selective infos from TeX log files

Various options may be used to select which information from the TeX log you
want to see/analyze (see next section). The default is to display only page
numbers (page numbers are **always** displayed).

*texloganalyser* is a program by Thomas van Oudenhove (`vanouden@enstimac.fr`).
Feel free to contact him for features requests or bugs.
"""

# License:
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
# USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

import os
import os.path
import re
import argparse

VERSION = '0.7'
COPYRIGHT = '2006-2010'
abstract = {'infos': 0, 'badboxes': 0, 'warnings': 0, 'errors': 0}


def scannedfile(logline, filetype):
    match = re.search(r'\("?(.*\.{})"?'.format(filetype), logline, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


parser = argparse.ArgumentParser(add_help=False,
    description='Displays selective infos of LaTeX logs')
parser.add_argument('--help', action='help')
parser.add_argument('--version', action='version',
    version=("This is texloganalyser, version {}\n"
        "Copyright {} Thomas van Oudenhove".format(VERSION, COPYRIGHT)))
parser.add_argument('-b', action='store_true', default=False, dest='badboxes',
    help='Displays bad box warnings')
parser.add_argument('-e', action='store_true', default=False, dest='errors',
    help='Displays errors')
parser.add_argument('-g', action='store_true', default=False, dest='images',
    help="Displays graphics (pdf, [e]ps, png, jpg) used")
parser.add_argument('-i', action='store_true', default=False, dest='infos',
    help='Displays informational messages')
parser.add_argument('-m', action='store_true', default=False, dest='end',
    help='Displays the memory summary at end of the log')
parser.add_argument('-p', action='store_true', default=False, dest='pages',
    help='Displays page numbers')
parser.add_argument('-s', action='store_true', default=False, dest='styles',
    help='Displays .sty and .cls files used')
parser.add_argument('-t', action='store_true', default=False, dest='texfiles',
    help='Displays .tex files used')
parser.add_argument('-w', action='store_true', default=False, dest='warnings',
    help='Displays all warnings')
parser.add_argument('logfile', type=argparse.FileType('r'), nargs='?',
    default='-',
    help='TeX log (default: read from standard input)')

args = parser.parse_args()

multiline_mode = False
multiline_signal = None
multiline_message = ''
errmsg_mode = False
errmsg_message = ''
texfilepath = None

for line in args.logfile:
    if errmsg_mode:
        match = re.match(r'l.(\d+) (.*)', line.strip())
        match2 = re.match(r'<\*> (.*)', line.strip())
        if match:
            errmsg_line = int(match.group(1))
            errmsg_context = match.group(2)
            errmsg_mode = False
            print '{}:{}: Error: {}\n\t{}'.format(os.path.basename(texfilepath),
                errmsg_line, errmsg_message, errmsg_context)
        elif match2:
            errmsg_file = match2.group(1)
            errmsg_mode = False
            print '{}:0: Error: {}'.format(errmsg_file, errmsg_message)
        else:
            continue

    if multiline_mode:
        if line.startswith(multiline_signal):
            multiline_message += ' ' + line[len(multiline_signal):].strip()
            continue
        else:
            multiline_mode = False
            match = re.search(r'on input line (\d+)', multiline_message)
            if match:
                errmsg_line = int(match.group(1))
                print '{}:{}: {}'.format(os.path.basename(texfilepath),
                    errmsg_line, multiline_message)
            else:
                print multiline_message

    # Page numbers
    if args.pages:
        matches = re.findall(r'\[[0-9]+\]', line)
        for match in matches:
            print match

    if args.end and 'Here is how much' in line:
        print '\n' + line

    # look for boxes warnings
    if args.badboxes and ('Overfull' in line or 'Underfull' in line):
        abstract['badboxes'] += 1
        match = re.search(r'at lines (\d+)--(\d+)', line)
        if match:
            print '{}:{}: {}'.format(os.path.basename(texfilepath),
                match.group(1), line.strip())
        else:
            print line,

    # TeX files used
    package = scannedfile(line, "tex")
    if package:
        try:
            texfilepath = os.path.relpath(package)  # save for later
        except ValueError:  # different drive
            texfilepath = package
        if args.texfiles:
            print '(' + texfilepath + ')'

    # sty and cls files used
    if args.styles:
        package = scannedfile(line, "sty")
        if not package:
            package = scannedfile(line, "cls")
        if package:
            print '{{{}}}'.format(os.path.basename(package))

    # images (pdf, ps, jpg, png)
    if args.images:
        for t in ('pdf', 'eps', 'ps', 'png', 'jpg'):
            package = scannedfile(line, t)
            if package:
                try:
                    print '(' + os.path.relpath(package) + ')'
                except ValueError:
                    print '(' + package + ')'

    # infos
    match = re.match(r'(LaTeX|Package) (\w+) Info', line)
    if match:
        abstract['infos'] += 1
        if args.infos:
            multiline_mode = True
            multiline_signal = '({})'.format(match.group(2))
            multiline_message = line.strip()

    # display all warnings
    if line.startswith('LaTeX Warning'):
        abstract['warnings'] += 1
        if args.warnings:
            multiline_mode = True
            multiline_signal = '    '
            multiline_message = line.strip()  # remove newline
    else:
        match = re.match(r'(LaTeX|Package) (\w+) Warning', line)
        if match:
            abstract['warnings'] += 1
            if args.warnings:
                multiline_mode = True
                multiline_signal = '({})'.format(match.group(2))
                multiline_message = line.strip()

    # display errors
    match = re.match(r'! (.*)\.', line)
    if match:
        abstract['errors'] += 1
        if args.errors:
            errmsg_mode = True
            errmsg_message = match.group(1)

args.logfile.close()
print abstract['infos'], 'infos,',
print abstract['badboxes'], 'bad boxes,',
print abstract['warnings'], "warnings,",
print abstract['errors'], 'errors.'
