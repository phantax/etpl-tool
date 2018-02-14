#!/usr/bin/python

# THE-MAN-TOOLS: A suite of useful tools for cryptography and embedded 
# system security.
# Copyright (C) 2015 Andreas Walz
# 
# Author: Andreas Walz
# 
# This file is part of THE-MAN-TOOLS.
# 
# THE-MAN-TOOLS are free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of
# the License, or (at your option) any later version.
# 
# THE-MAN-TOOLS are distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with THE-MAN-TOOLS; if not, see <http://www.gnu.org/licenses/>
# or write to the Free Software Foundation, Inc., 51 Franklin Street,
# Fifth Floor, Boston, MA 02110-1301, USA.

#
# [parse] -> [check] -> [canonicalize] -> [disentangle] -> [check] -> [...]
#

import sys


#
# _____________________________________________________________________________
#
def indent(str, level=1):
    lines = [' '*(4 if s else 0)*level + s for s in str.split('\n')]
    return '\n'.join(lines)


#
# _____________________________________________________________________________
#
def makeFeatures(features):

    sortedFeatureTuples = sorted([tuple(f.split('@')[::-1]) for f in features])
    featuresSorted = ['@'.join(list(s)) for s in sortedFeatureTuples]

    featureCode = []
    featureList = []

    depth = 0
    prefix = []
    for fi, f in enumerate(featuresSorted):

        if '@' in f:
            # >>> Property-basef feature >>>
            fPath, fProp = tuple(f.split('@'))
            featureList += ['{0}@{1}'.format(fProp, fPath)]
        else:
            # >>> Feature based on presence of GMT node >>>
            fPath, fProp = f, None
            featureList += [fPath]

        fPathSplit = fPath.split('/')
        while prefix and (len(prefix[-1]) > len(fPathSplit) or [a == b for a, b in
                zip(fPathSplit, prefix[-1])].count(False) > 0):
            prefix.pop()

        levelChange = False
        if len(prefix) != depth:
            levelChange = True

        while len(prefix) > depth:
            featureCode += ['stack.push_back(base);', 'base = last;']
            depth += 1
        while len(prefix) < depth:
            depth -= 1
            featureCode += ['base = stack.back();', 'stack.pop_back();']

        if levelChange:
            featureCode += ['\n/* <<< base path now is: "{0}" >>> */\n' \
                    .format('/'.join(prefix[-1] if prefix else []))]

        path = '/'.join(fPathSplit[len(prefix[-1]) if prefix else 0:])           


        featureCode += ['/* this is feature #{1}: "{0}" */'.format('@'.join(f.split('@')[::-1]), fi)]

        if fProp:
            atPath = '@{0}'.format(path) if path else ''
            featureCode += ['features.push_back((base != 0) && base->propGetDefault<bool>("{0}{1}", false));\n' \
                    .format(fProp, atPath)]
        else:
            featureCode += ['features.push_back((base != 0) && ((last = base->getByPath("{0}")) != 0));\n' \
                    .format(path)]
            prefix.append(fPathSplit)

    featureCode = ['void evaluateFeatures(DataUnit* base, vector<bool>& features) {\n'] \
            + [indent('vector<DataUnit*> stack;\nDataUnit* last;\n')] \
            + indent('\n'.join(featureCode)).split('\n') \
            + ['}']

    return featureCode, featureList






