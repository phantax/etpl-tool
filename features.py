# Copyright (C) 2017
# Andreas Walz [andreas.walz@hs-offenburg.de]
# Offenburg University of Applied Sciences
# Institute of Reliable Embedded Systems and Communications Electronics (ivESK)
# [https://ivesk.hs-offenburg.de/]
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

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
            + [indent('vector<DataUnit*> stack;\nDataUnit* last = 0;\n')] \
            + indent('\n'.join(featureCode)).split('\n') \
            + ['}']

    # Prepend source file header
    featureCode.insert(0, '/*\n *  Do not change this file! It has been generated automatically by etpl-tool.\n */\n')
    featureCode.insert(1, '#include "DataUnit.h"\n#include <vector>\n')
    featureCode.insert(2, 'using std::vector;\n')

    return featureCode, featureList






