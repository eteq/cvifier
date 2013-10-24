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


def read_to_doctree(f):
    """
    Generates a doctree from the file or filename`f`
    """
    from docutils.core import publish_doctree

    if hasattr(f, 'read'):
            s = f.read()
    else:
        with open(f, 'r') as fo:
            s = fo.read()

    return publish_doctree(s)

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


def load_settings(fn):
    """
    loads settings from filename `fn`, and return them as a dict
    """



def write_doctree(doctree, writer, fout=None, settingsfile=None):
    """
    Writes out the `doctree` to the file `fout` using the `writer` given
    as an object or name.

    Loads settings from the default name if `settingsfile` is None, otherwise,
    the specified file.

    Returns the written content.
    """
    from docutils.core import publish_from_doctree

    if isinstance(writer, basestring):
        stgs = load_settings(writer + '.cvsettings')
        res = publish_from_doctree(doctree, writer_name=writer, settings_overrides=stgs)
    else:
        stgs = load_settings(writer.supported[0] + '.cvsettings')
        res = publish_from_doctree(doctree, writer=writer, settings_overrides=stgs)



    if fout:
        if hasattr(fout, 'write'):
            fout.write(res)
        else:
            with open(fout, 'w') as f:
                f.write(res)

    return res
