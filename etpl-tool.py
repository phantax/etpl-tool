#!/usr/bin/python

# Copyright (C) 2017 Andreas Walz
# 
# Author: Andreas Walz [andreas.walz@hs-offenburg.de]
# 
# This file is part of etpl-tool.
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
# along with etpl-tool; if not, see <http://www.gnu.org/licenses/>
# or write to the Free Software Foundation, Inc., 51 Franklin Street,
# Fifth Floor, Boston, MA 02110-1301, USA.

#
# [parse] -> [check] -> [normalize] -> [sort] -> [check] -> [...]
#

import sys
from pyparsing import ParseBaseException
from core import *
from parse import *
from generate_cpp import *
import normalize


#
# _____________________________________________________________________________
#
def printError(msg):
    print TextFormatter.makeBoldRed('Error: {0}'.format(msg))
    quit()


#
# _____________________________________________________________________________
#
def printSyntaxError(error):    
    print(TextFormatter.makeBoldRed('Error in line {0}: {1}' \
            .format(error.lineno, error.msg)))
    print(error.line)
    print(' ' * (error.col - 1) + '^')
    quit()


#
# _____________________________________________________________________________
#
def indent(str, level=1):
    lines = [' '*(4 if s else 0)*level + s for s in str.split('\n')]
    return '\n'.join(lines)


#
# _____________________________________________________________________________
#
def main(argv):

    print('\n\033[1m*** etpl-tool: An parser/compiler for eTPL ***\033[0m\n')

    if len(argv) not in [1, 2]:
        print("Invalid number of arguments given. Exiting.\n")
        print("Usage: ./etpl-tool.py <input-file> [<output-file>]\n")
        quit()

    inputFile = argv[0]
    with open(inputFile, 'r') as f:
        text = ''.join([line for line in f])

    # ===== Parse input files =====
    try:
        typedefs = parse(text)
    except ParseBaseException as e:
        printSyntaxError(e)
    except EtplParseException as e:
        printSyntaxError(e.error)
    except TPLError as e:
        printError(str(e))

    #typedefs.addGlobalVar('lengthy')

    # ===== Print before normalization =====
    print '='*50 + '\nBefore normalization:\n' + '='*50 + '\n'
    print typedefs, '\n'*2

    # ===== Print generated source code =====
    print '='*50 + '\nGenerated source code:\n' + '='*50 + '\n'
    print typedefs.getTPLCode()
    print '\n'

    # ===== Normalize =====
    try:
        typedefs = typedefs.normalize()
    except TPLError as e:
        printError(str(e))

    # ===== Print after normalization =====
    print '='*50 + '\nAfter normalization:\n' + '='*50 + '\n'
    print typedefs, '\n'*2

    # ===== Resolve dependencies =====
    try:
        typedefs.sort()
        typedefs.generateTypeIDs()
    except TPLError as e:
        printError(str(e))

    # ===== Print after sorting =====
    print '='*50 + '\nAfter disentangling:\n' + '='*50 + '\n'
    print typedefs, '\n'*2

    # ===== CHECK =====
    try:
        typedefs.check()
    except TPLError as e:
        printError(str(e))


    # ===== Generate source code =====
    if len(argv) == 2:
        outputFile = argv[1]
        with open(outputFile, "w") as file:
            src = str(typedefs.generateCodeCpp())
            file.write(src)


#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);




