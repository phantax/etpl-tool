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
import features


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
def usage():
    print('Usage: ./etpl-tool.py [OPTIONS] <input-file>')
    print('Options:')
    print(' -p<filename>    Write message parsing code (C++) to file <filename>')
    print(' -b<basetype>    Select base type for further processing')
    print(' -F<filename>    Write feature extraction code (C++) to file <filename>')
    print(' -f<filename>    Write list of features to file <filename>')


#
# _____________________________________________________________________________
#
def main(argv):

    # Parsing command line arguments
    args = {
        'p': None,  # Output filename for message parsing code (C++)
        'b': None,  # Base type for further processing
        'F': None,  # Output filename for feature extraction code (C++)
        'f': None,  # Output filename for feature list
    }
    argFileIndex = 0
    for i, arg in enumerate(argv):
        if not arg.startswith('-'):
            argFileIndex = i
            break
        if len(arg) < 2:
            # >>> Invalid argument >>>
            continue   
        elif len(arg) < 3:
            # >>> Single flag >>>
            args[arg[1]] = True
        elif arg[1] in '':
            # >>> Integer argument >>>
            args[arg[1]] = int(arg[2:])
        else:
            # >>> Other (e.g., string) argument >>>
            args[arg[1]] = arg[2:]
    if (argFileIndex + 1) != len(argv):
        print('Wrong number of input files given (expect exactly one).')
        usage()
        return
    inputFilename = argv[argFileIndex]
    parsingCodeFilename = args['p']
    baseTypeName = args['b']
    featureCodeFilename = args['F']
    featureListFilename = args['f']

    print('\n\033[1m*** etpl-tool: A parser/compiler for eTPL ***\033[0m\n')

    # ===== Read input files =====
    with open(inputFilename, 'r') as f:
        text = ''.join([line for line in f])

    # ===== Parse input file =====
    try:
        typedefs = parse(text)
    except ParseBaseException as e:
        printSyntaxError(e)
    except EtplParseException as e:
        printSyntaxError(e.error)
    except TPLError as e:
        printError(str(e))

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


    # ===== Generate parsing source code =====
    if parsingCodeFilename:
        with open(parsingCodeFilename, "w") as file:
            src = str(typedefs.generateCodeCpp())
            file.write(src)

    # ===== Generate feature list and extraction source code =====
    if featureCodeFilename or featureListFilename:

        if not baseTypeName:
            print('Missing base type for features.')
            usage()
            return

        featureCode, featureList = features.makeFeatures(
                typedefs[baseTypeName].getFeatures(True))

        if featureCodeFilename:
            with open(featureCodeFilename, "w") as file:
                file.write('\n'.join(featureCode))

        if featureListFilename:
            with open(featureListFilename, "w") as file:
                file.write('\n'.join(featureList))


#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);




