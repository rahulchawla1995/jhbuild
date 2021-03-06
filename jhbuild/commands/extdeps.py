# jhbuild - a build script for GNOME 2.x
# Copyright (C) 2012  Frederic Peters
#
#   extdeps.py: report details on GNOME external dependencies
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from optparse import make_option
import re
import socket
import sys
import time

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import jhbuild.moduleset
from jhbuild.commands import Command, register_command

HTML_AT_TOP = '''<html>
<head>
<title>%(title)s</title>
<style type="text/css">
body {
    font-family: sans-serif;
}
tbody th {
    background: #d3d7cf;
    text-align: left;
}
tbody td {
    text-align: center;
}

td { padding: 0 1em; }
td.rdeps { text-align: left; }

tr.zero { text-decoration: line-through; }
tr.far  { color: gray; }
tr.many { font-weight: bold; }

div#footer {
  margin-top: 2em;
  font-size: small;
}

</style>
</head>
<body>
<h1>%(title)s</h1>

'''


class cmd_extdeps(Command):
    doc = _('Report details on GNOME external dependencies')
    name = 'extdeps'

    def __init__(self):
        Command.__init__(self, [
            make_option('-o', '--output', metavar='FILE',
                    action='store', dest='output', default=None),
            make_option('--all-modules',
                        action='store_true', dest='list_all_modules', default=False),
            ])

    def run(self, config, options, args, help=None):
        if options.output:
            output = StringIO()
        else:
            output = sys.stdout

        config.partial_build = False
        self.module_set = jhbuild.moduleset.load(config)
        if options.list_all_modules:
            module_list = self.module_set.modules.values()
        else:
            module_list = self.module_set.get_module_list(args or config.modules, config.skip)

        if type(config.moduleset) is str:
            moduleset = [config.moduleset]
        else:
            moduleset = config.moduleset
        title = _('External deps for GNOME')
        for ms in moduleset:
            try:
                gnome_ver = re.findall('\d+\.\d+', ms)[0]
            except IndexError:
                continue
            title = _('External deps for GNOME %s') % gnome_ver
            break

        print >> output, HTML_AT_TOP % {'title': title}
        print >> output, '<table>'
        print >> output, '<tbody>'

        module_list.sort(lambda x,y: cmp(x.name.lower(), y.name.lower()))
        for mod in module_list:
            #if not mod.moduleset_name.startswith('gnome-suites-core-deps-base'):
            #    continue

            if not hasattr(mod.branch, 'version'):
                continue

            rdeps = self.compute_rdeps(mod)
            classes = []
            if len(rdeps) == 0:
                classes.append('zero')
            else:
                for rdep in rdeps:
                    rdep_mod = self.module_set.modules.get(rdep)
                    if not hasattr(rdep_mod.branch, 'version'):
                        break
                else:
                    # module who only has tarballs as dependency
                    classes.append('far')
                if len(rdeps) > 5:
                    classes.append('many')

            print >> output, '<tr class="%s">' % ' '.join(classes)
            print >> output, '<th>%s</th>' % mod.name
            version = mod.branch.version
            if mod.branch.patches:
                version = version + ' (%s)' % _('patched')
            print >> output, '<td class="version">%s</td>' % version
            print >> output, '<td class="url"><a href="%s">tarball</a></td>' % mod.branch.module
            if len(rdeps) > 5:
                rdeps = rdeps[:4] + [_('and %d others.')  % (len(rdeps)-4)]
            print >> output, '<td class="rdeps">%s</td>' % ', '.join(rdeps)
            print >> output, '</tr>'

        print >> output, '</tbody>'
        print >> output, '</table>'

        print >> output, '<div id="footer">'
        print >> output, 'Generated:', time.strftime('%Y-%m-%d %H:%M:%S %z')
        print >> output, 'on ', socket.getfqdn()
        print >> output, '</div>'

        print >> output, '</body>'
        print >> output, '</html>'

        if output != sys.stdout:
            file(options.output, 'w').write(output.getvalue())


    def compute_rdeps(self, module):
        rdeps = []
        for mod in self.module_set.modules.values():
            if mod.type == 'meta': continue
            if module.name in mod.dependencies:
                rdeps.append(mod.name)
        rdeps.sort(lambda x,y: cmp(x.lower(), y.lower()))
        return rdeps

register_command(cmd_extdeps)
