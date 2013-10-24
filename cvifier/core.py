# cvifier: the CV transmogrifier
# Copyright (C) 2013 Erik Tollerud
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Module with the main functionality for `cvifier`
"""

from __future__ import division


def parse_content_file(content, comment='#'):
    """
    Parses a file with the text to go into the CV.

    The file itself should look like::

      [name]
      content here
      more content

      [something:1]
      stuff

      [something:2]
      morestuff *with rst*



    Parameters
    ----------
    content : str, file-like object, or list of strings
        The file (or list of lines) that should be parsed assuming the
        format described above.
    comment : str or None
        The character sequence to interpret as marking the start of a
        comment.  If a '\\' comes before, will be treated as a regular
        character.
    Returns
    -------
    contentdict : collections.OrderedDict
        A dictionary mapping section names to section content.
        Preserves the order the file provides them in.

    """
    import re
    from collections import defaultdict, OrderedDict

    markerrex = re.compile(r'\[(.*?)\](.*)')
    commentre = re.compile(r'(.*?)((?<!\\){0})'.format(comment))
    esccomment = '\\' + comment

    if isinstance(content, basestring):
        with open(content, 'r') as f:
            lines = f.read().split('\n')
    elif hasattr(content, 'read'):
        lines = content.read().split('\n')
    else:
        lines = []
        for l in content:
            lines.append(str(l))

    seccontent = defaultdict(list)
    orderedsections = []
    insection = None
    for l in lines:
        #
        mtch = commentre.match(l)
        if mtch is not None:
            l = mtch.group(1)
            if l == '':
                # pure comment line
                continue
        l.replace(esccomment, comment)

        mtch = markerrex.match(l)

        if mtch is None:
            if insection:
                seccontent[insection].append(l)
        elif mtch.group(2).strip() != '':
            raise ValueError('Content had a line that looks like a section header, but with extra content:"{0}"'.format(l))
        else:
            insection = mtch.group(1)
            orderedsections.append(insection)

    return OrderedDict([(k, '\n'.join(seccontent[k]).rstrip()) for k in orderedsections])

def write_content(content, writer):
    """
    Uses a docutils writer to generate content.  In yields *only* the content,
    not the CSS and such.

    Knows how to pull out content for 'html' and 'latex' writers.

    Parameters
    ----------
    content : str
        The content to write into a new form
    writer : str or Writer
        A a docutils writer to use for the output

    Returns
    -------
    docutilscontent : str
        The output of `docutils.core.publish_string`, possibly modified
        to strip out stuff like the css.
    """
    from docutils.core import publish_string
    if isinstance(writer, basestring):
        res = publish_string(content, writer_name=writer)
    else:
        res = publish_string(content, writer=writer)

    delimiters = None
    if writer == 'html':
        #strip out all but the stuff in the document div
        delimiters = ('<div class="document">', '</div>')
    elif writer == 'latex':
        delimiters = ('\\begin{document}', '\\end{document}')

    if delimiters:
        i = res.find(delimiters[0])
        if i == -1:
            raise ValueError('couldn\'t find start delimiter "{0}"'.format(delimiters[0]))
        j = res.find(delimiters[1], i)
        if j == -1:
            raise ValueError('couldn\'t find end delimiter "{0}"'.format(delimiters[1]))
        return res[(i + len(delimiters[0])):j]
    else:
        return res
