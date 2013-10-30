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


CONTACT_INFO_SECTIONS = ('name', 'address', 'phone', 'email', 'fax')

def extract_contact_info(doctree):
    """
    Removes contact information from the provided `doctree`, and returns
    a dictionary with the relevant sections (See `CONTACT_INFO_SECTIONS`).
    """

    cidict = {}
    torem = []
    for node in doctree:
        if node.tagname == 'section':
            for n in node['names']:
                nl = n.lower()
                if nl in CONTACT_INFO_SECTIONS:
                    cidict[nl] = node
                    torem.append(node)
                    break

    for node in torem:
        doctree.remove(node)

    return cidict


def load_settings(content, comment=None):
    """
    Parses a settings file.

    The file itself should look like::

      [documentclass]
      article

      [documentoptions]
      12pt

      [latex_preamble]
      \usepackage{hyperref}
      \usepackage{color}



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
    commentre = re.compile(r'(.*?)((?<!\\){0})'.format(comment)) if comment else None
    esccomment = '\\' + comment if comment else None

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
        mtch = None if commentre is None else commentre.match(l)
        if mtch is not None:
            l = mtch.group(1)
            if l == '':
                # pure comment line
                continue
        if esccomment is not None:
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


def extract_texts(node):
    """
    gets the '#text' items from the provided node and returns them
    """
    cond = lambda n: n.tagname == '#text' and n.parent.tagname != 'title'
    return node.traverse(condition=cond, include_self=False)


DEFAULT_CITABLE_LEFT = ('[address]', )
DEFAULT_CITABLE_RIGHT = ('phone', 'fax', 'email')


def make_citable(cistrdict, writer_name, leftfields=DEFAULT_CITABLE_LEFT,
                 rightfields=DEFAULT_CITABLE_RIGHT):
    if writer_name == 'html':
        italicize = lambda s: '<i>' + s + '</i>'
        startrow = '<tr><td>'
        endrow = '</td></tr>'
        colsep = '</td><td>'
    elif writer_name == 'latex':
        italicize = lambda s: '\\textit{' + s + '}'
        startrow = ''
        endrow = r'\\'
        colsep = '&'
    else:
        raise ValueError("can't make citable for writer " + writer_name)

    rightlines = []
    leftlines = []
    for fields, lines in [(leftfields, leftlines), (rightfields, rightlines)]:
        for fi in fields:
            #[name] means don't include the name
            if fi.startswith('[') and fi.endswith(']'):
                fi = fi[1:-1]
                prefix = ''
            else:
                prefix = italicize(fi[0].upper() + fi[1:] + ':') + '~'

            tspl = cistrdict[fi].split('\n')
            tspl[0] = prefix + tspl[0]
            lines.extend(tspl)

    tablelines = []
    for i in range(max(len(leftlines), len(rightlines))):
        li = leftlines[i] if i < len(leftlines) else ''
        ri = rightlines[i] if i < len(rightlines) else ''
        tablelines.append(startrow + li + colsep + ri + endrow)

    return '\n'.join(tablelines)


#settings that apply here, instead of in docutils
SPECIAL_SETTINGS = {'latex': ['nobullets', 'preitemize', 'postsection', 'nofootnotespace'],
                    'html': ['onlydiv']}


def apply_doctree_special_settings(doctree, specialsettings):
    from docutils.nodes import raw as Raw

    if 'latex_postsection' in specialsettings:
        txt = specialsettings['latex_postsection']
        toinsert = []
        for node in doctree:
            if node.tagname == 'section':
                #insert at 1 to go after title
                for i, node2 in enumerate(node):
                    if node2.tagname == 'title':
                        #after title
                        node.insert(i + 1, Raw(text=txt, format='latex'))
                        break

    return doctree

def apply_str_special_settings(writtenstr, specialsettings):
    import re

    if 'latex_nobullets' in specialsettings:
        writtenstr = writtenstr.replace(r'\item ', r'\item[] ')

    if 'latex_preitemize' in specialsettings:
        hdr = specialsettings['latex_preitemize']
        writtenstr = writtenstr.replace(r'\begin{itemize}', hdr + '\n' + r'\begin{itemize}')

    if 'latex_nofootnotespace' in specialsettings:
        writtenstr = writtenstr.replace(' \\DUfootnotemark', '\\DUfootnotemark')

    if 'html_onlydiv' in specialsettings:
        lnstowrite = []
        divcnt = 0
        for l in writtenstr.split('\n'):
            if divcnt > 0:
                lnstowrite.append(l)
                divcnt += l.count('<div')
                divcnt -= l.count('</div')
            elif '<div class="document">' in l:
                divcnt += 1
        writtenstr = '\n'.join(lnstowrite)

    return writtenstr


def main(content, writer, fout=None, settingsfile=None):
    """
    Reads `content` as doctree, then write to the file `fout` using the
    `writer` given as an object or name.

    Loads settings from the default name if `settingsfile` is None, otherwise,
    the specified file.

    Returns the written content.
    """
    from os.path import exists
    from docutils.core import publish_from_doctree, publish_doctree
    from docutils.nodes import raw as Raw
    from docutils.writers import get_writer_class

    #first read the docstring
    if hasattr(content, 'children'):
        #assume this is a doctree
        doctree = content
    if hasattr(content, 'read'):
        s = f.read()
        doctree = publish_doctree(s)
    else:
        with open(content, 'r') as fo:
            s = fo.read()
            doctree = publish_doctree(s)

    #now figure out the writer and its settings
    if isinstance(writer, basestring):
        writer_name = writer
        if settingsfile is None:
            settingsfile = writer_name + '.cvsettings'
        stgs = load_settings(settingsfile) if exists(settingsfile) else None
        writer = get_writer_class(writer_name)()
    else:
        writer_name = writer.supported[0]
        if settingsfile is None:
            settingsfile = writer_name + '.cvsettings'
        stgs = load_settings(settingsfile) if exists(settingsfile) else None

    #now substitute the contact info if called for
    if 'contactinfotemplate' in stgs:
        citempl = stgs.pop('contactinfotemplate')
    elif 'contactinfotemplate\\' in stgs:
        citempl = stgs.pop('contactinfotemplate\\')
        #makes all "real" curly brackets into double-brackets, and \ed ones into singles
        citempl = citempl.replace('{', '{{').replace('}', '}}')
        citempl = citempl.replace('\\{', '').replace('\\}', '')
    else:
        citempl = None
    if citempl is not None:
        cistrdict = dict([(k, extract_texts(v)[-1]) for k, v in extract_contact_info(doctree).iteritems()])

        if '{citabledata}' in citempl:
            cistrdict['citabledata'] = make_citable(cistrdict, writer_name)
        cistr = citempl.format(**cistrdict)
        doctree.insert(0, Raw(text=cistr, format=writer_name))

    specialsettings = {}
    for si in SPECIAL_SETTINGS.get(writer_name, ''):
        if si in stgs:
            specialsettings[writer_name + '_' + si] = stgs.pop(si)

    #exclude any sections requested
    if 'excludesections' in stgs:
        secstoexclude = [secs.strip() for secs in stgs.pop('excludesections').split(',')]
        torem = []
        for node in doctree:
            if node.tagname == 'section' and str(node[0][0]) in secstoexclude:
                torem.append(node)
        for node in torem:
            doctree.remove(node)


    #now generate the actual output
    doctree = apply_doctree_special_settings(doctree, specialsettings)
    outstr = publish_from_doctree(doctree, writer=writer, settings_overrides=stgs)
    outstr = apply_str_special_settings(outstr, specialsettings)

    if fout:
        if hasattr(fout, 'write'):
            fout.write(outstr)
        else:
            with open(fout, 'w') as f:
                f.write(outstr)

    return outstr
