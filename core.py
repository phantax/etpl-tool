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
# Class hierarchy:
#
#   TypeDef
#       BuiltInDef
#           IntDef
#               SIntDef
#               UIntDef
#           BitDef
#           ByteDef
#           OpaqueDef
#       ConstDef
#       InstanceDef
#       WrapperDef
#           VectorDef
#               StaticVectorDef
#               DynamicVectorDef
#           FragmentDef
#       EnumDef
#       StructDef
#           CaseDef
#               DefaultCaseDef
#       SelectDef
#
#

import math
from collections import Set
import itertools

# TODO: let a Select-Case construct support collective names/characteristics

# TODO: introduce a 'void' built-in type


def sumDicts(dict1, dict2):
    for key in dict2:
        dict1[key] = dict1.get(key, 0) + dict2.get(key)


class TextFormatter(object):

    useColor = True

    strColorEnd = '\033[0m'

    @staticmethod
    def makeBoldWhite(s):
        if TextFormatter.useColor:
            return '\033[1m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBoldRed(s):
        if TextFormatter.useColor:
            return '\033[1;31m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBoldGreen(s):
        if TextFormatter.useColor:
            return '\033[1;32m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBoldYellow(s):
        if TextFormatter.useColor:
            return '\033[1;33m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBoldBlue(s):
        if TextFormatter.useColor:
            return '\033[1;34m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBoldPurple(s):
        if TextFormatter.useColor:
            return '\033[1;35m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBoldCyan(s):
        if TextFormatter.useColor:
            return '\033[1;36m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeGreen(s):
        if TextFormatter.useColor:
            return '\033[32m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeRed(s):
        if TextFormatter.useColor:
            return '\033[31m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBlue(s):
        if TextFormatter.useColor:
            return '\033[34m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def indent(str, level=1):
        lines = [' '*(4 if s else 0)*level + s for s in str.split('\n')]
        return '\n'.join(lines)


def getUniqueName(names, proposal):
    name = proposal
    proposals = ('{0}_{1}'.format(proposal, i) for i in itertools.count(2))
    while name in names:
        name = proposals.next()
    return name


class TPLError(Exception):
    """
    Representation of a generic TPL error
    """

    def __init__(self, msg):
        Exception.__init__(self, msg)    


class TPLCheckError(Exception):
    """
    Representation of a TPL error during the checking phase
    """

    def __init__(self, msg):
        Exception.__init__(self, msg)    


class SizeDef(object):

    def __init__(self, size, bitScale=8):
        self.setSize(size)
        self.setBitScale(bitScale)

    def __str__(self):        
        if not self.getBitScale() in [1, 8]:
            raise Exception("Unknown bit scale")
        size = str(self.getSize()) if self.getSize() else ''
        unit = 'bits' if self.getBitScale() == 1 else ''
        delim = ' : ' if unit else ''
        return '{0}{1}{2}'.format(size, delim, unit)

    def setSize(self, size):
        self.size = size

    def getSize(self):
        return self.size

    def setBitScale(self, bitScale):
        self.bitScale = bitScale

    def getBitScale(self):
        return self.bitScale


class IntElement(object):

    def getRequiredSymbols(self):
        return set()


class IntLiteral(IntElement):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.getValue())

    def __int__(self):
        return self.getValue()

    def __add__(self, other):
        if not isinstance(other, IntLiteral):
            raise Exception('Invalid operation')
        return IntLiteral(self.getValue() + other.getValue())

    def __sub__(self, other):
        if not isinstance(other, IntLiteral):
            raise Exception('Invalid operation')
        return IntLiteral(self.getValue() - other.getValue())

    def __mul__(self, other):
        if not isinstance(other, IntLiteral):
            raise Exception('Invalid operation')
        return IntLiteral(self.getValue() * other.getValue())

    def __pow__(self, other):
        if not isinstance(other, IntLiteral):
            raise Exception('Invalid operation')
        return IntLiteral(self.getValue() ** other.getValue())

    def __lt__(self, other):
        return True if self.getValue() < int(other) else False

    def __gt__(self, other):
        return True if self.getValue() > int(other) else False

    def getValue(self):
        return self.value


class IntSymbol(IntElement):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return '${0}'.format(self.getName())

    def getName(self):
        return self.name

    def getRequiredSymbols(self):
        return set([self.getName()])


class TypeDefCollection(object):

    # TODO: Add iterator capability to this class

    def __init__(self, globalSymbols=None):
        self.clear()
        self.globalSymbols = globalSymbols if globalSymbols else set()
        # add built-in type definitions
        self.addDefs([UIntDef(i) for i in range(1, 65)])
        self.addDefs([SIntDef(i) for i in range(1, 65)])
        self.addDefs([BitDef(), ByteDef(), OpaqueDef()])

    def __str__(self):
        return self.getPrintString()

    def getPrintString(self, includeBuiltIn=False):
        return '\n\n'.join([str(t) for t in self.getTypeDefs(includeBuiltIn)])

    def __getitem__(self, index):
        if isinstance(index, int):
            return self.typedefs[index]
        elif isinstance(index, str):
            itemIter = (t for t in self.getTypeDefs() if t.getName() == index)
            try:
                return itemIter.next()
            except StopIteration:
                raise TPLError('Unknown type definition "{0}"'.format(index))
        else:
            raise TPLError('Unknown index type')

    def __len__(self):
        return len(self.getTypeDefs())

    def getName(self, default=None):
        return '_GLOBAL'

    def getChainedName(self, delim='_'):
        return self.getName()

    def clear(self):
        self.typedefs = []

    def addDef(self, typedef, autoUpdateName=False):
        if autoUpdateName:
            typedef.setName(typedef.getName())
        if typedef.getName() in self.getTypeNames():
            err = 'Element "{0}" already exists.'.format(typedef.getName())
            raise Exception(err)
        if not typedef.getName():
            raise Exception('Element has empty name')
        self.typedefs += [typedef]
        typedef.setParent(self)

    def addDefs(self, typedefs):
        for typedef in typedefs:
            self.addDef(typedef)

    def getTypeDefs(self, includeBuiltIn=True):
        if includeBuiltIn:
            return self.typedefs
        else:
            return [t for t in self.typedefs if not isinstance(t, BuiltInDef)]

    def getChildren(self):
        return self.getTypeDefs()

    def getTypeNames(self):
        return [t.getName() for t in self.getTypeDefs()]

    def addGlobalSymbol(self, name):
        self.globalSymbols.update(set([name]))

    def getGlobalSymbols(self):
        return self.globalSymbols

    def getKnownSymbols(self, ref=None):
        # we can safely ignore argument 'ref' here and just return all the
        # global symbols we known and all constant integer expressions
        symbols = {var: self for var in self.getGlobalSymbols()}
        symbols.update({const.getName(): self for const in self.getTypeDefs()
                if isinstance(const, ConstDef)})
        return symbols

    def getUndefinedSymbols(self):
        s = set()
        for t in self.getTypeDefs():
            s.update(t.getRequiredSymbols())
        s.difference_update(self.getGlobalSymbols())
        return s

    def dependsOnTypes(self):
        s = set()
        for t in self.getTypeDefs():
            s.update(t.dependsOnTypes())
        return s

    def generateTypeIDs(self):
        for i, t in enumerate(self.getTypeDefs()):
            t.setTypeID(100 + i)

    def check(self):
        # TODO: return a list of warnings with function check
        for t in self.getTypeDefs():
            t.check()

    def sort(self):

        def sufficient(typedef, typedefs):
            known = typedefs.getTypeNames()
            if typedef.getName() in known:
                return False
            if not typedef.dependsOnTypes().issubset(set(known)):
                return False
            return True

        # find unknown types referred to by type definitions
        unknown = self.dependsOnTypes()
        unknown.difference_update(self.getTypeNames())
        if len(unknown):
            raise TPLError('Unknown type "{0}"'.format(iter(unknown).next()))

        # sort type definitions such that no definition
        # appears before all the definitions it refers to
        pool = self.getTypeDefs()
        self.clear()
        while len(self) < len(pool):
            self.addDef((t for t in pool if sufficient(t, self)).next())

    def countReferences(self):
        refs = {}
        for t in self.getTypeDefs():
            sumDicts(refs, t.countReferences())
        return refs

    def getTPLCode(self):
        return '\n\n'.join([t.getTPLCode() for t in self.getTypeDefs(False)])    


class TypeDef(object):

    flagExtern = 'extern'
    flagOptional = 'optional'
    flagDistinctive = 'distinctive'
    flagNames = [flagExtern, flagOptional, flagDistinctive]

    @staticmethod
    def getNDigits(number, base):
        return (i for i in itertools.count() if (base**i) > number).next()   

    @staticmethod
    def mergeTPLTriples(inner, outer):
        prefix = ((outer[0] + ' ') if outer[0] else '') + \
                (inner[0] if inner[0] else '')
        postfix = (inner[2] if inner[2] else '') + \
                (outer[2] if outer[2] else '')
        if outer[1]:
            name = outer[1]
        elif inner[1]:
            name = inner[1]
        else:
            name = None
        return (prefix, name, postfix)

    @staticmethod
    def concatFeatureStrings(str1, str2):
        list2 = str2.split('@') if str2 else []
        if len(list2) > 2:
            raise Exception(('Cannot concatenate feature strings "{0}" ' + \
                    'and "{1}"').format(str1, str2))
        path = '/'.join([str1] + list2[-1:])
        return '@'.join(list2[-2:-1] + ([path] if path else []))

    def __init__(self):
        self.setParent(None)
        self.setName(None)
        self.paramList = []
        self.resetFlags()
        self.resetSize()
        self.resetTypeID()

    def __str__(self):
        typeStr = '+' if self.isReal() else '-'
        if self.getFlagOptional():
            typeStr += '[{0}]'.format(TextFormatter.makeBoldYellow('optional'))
        if self.getFlagExtern():
            typeStr += '[{0}]'.format(TextFormatter.makeBoldYellow('extern'))
        if self.getFlagDistinctive():
            typeStr += '[{0}]'.format(TextFormatter.makeBoldYellow('distinctive'))
        typeStr += self.getTypeStr()
        sizeStr = ''
        if self.getSize():
            sizeStr = TextFormatter.makeBoldRed(self.getSizeStr())
        nameStr = self.getName('~')
        paramStr = self.getParamListStr()
        if paramStr:
            paramStr = TextFormatter.makeBoldYellow('<{0}>'.format(paramStr))
        string = '{0}{1}: {2}{3}'.format(typeStr, sizeStr, nameStr, paramStr)

        # add type ID
        #if self.getTypeID():
        #    string += ' ---> ' + TextFormatter.makeGreen('TypeID: {0}'.format(self.getTypeID()))

        # add variable dependencies
        #requiredVars = [TextFormatter.makeRed(str(var)) \
        #        for var in self.getRequiredSymbols()]
        #string += ' ---> required: [{0}]'.format(', '.join(requiredVars))

        # add known variables
        #varDefs = [TextFormatter.makeGreen('{0}@{1}') \
        #        .format(var, where.getChainedName('/')) \
        #        for var, where in self.getKnownSymbols().iteritems()]
        #string += ' ---> known: [{0}]'.format(', '.join(varDefs))

        # add chained name
        #string += '  >' + TextFormatter.makeGreen('/{0}'.format(self.getChainedName('/')))

        # add location of definition
        #if hasattr(self, 'tplLineNo'):
        #    string += '  ---> ' + TextFormatter.makeGreen('Defined here ":{0}"'.format(self.tplLineNo))

        content = self.getContentStr()
        if content:
            string += '\n' + TextFormatter.indent(content)
        return string

    def getSize(self):
        return self.size

    def setSize(self, size):
        self.size = size

    def getSizeStr(self):
        return '({0})'.format(str(self.getSize())) if self.getSize() else None

    def resetSize(self):
        self.setSize(None)

    def resetFlags(self):
        self.flags = {flag: False for flag in TypeDef.flagNames}

    def setFlags(self, flags):
        self.flags = flags

    def setFlag(self, flag, state=True):
        self.flags[flag] = state

    def setFlagExtern(self, state=True):
        self.setFlag(TypeDef.flagExtern, state)

    def setFlagOptional(self, state=True):
        self.setFlag(TypeDef.flagOptional, state)

    def setFlagDistinctive(self, state=True):
        self.setFlag(TypeDef.flagDistinctive, state)

    def getFlags(self):
        return self.flags

    def getFlag(self, flag):
        return self.getFlags()[flag]

    def getFlagExtern(self):
        return self.getFlag(TypeDef.flagExtern)

    def getFlagOptional(self):
        return self.getFlag(TypeDef.flagOptional)

    def getFlagDistinctive(self):
        return self.getFlag(TypeDef.flagDistinctive)

    def getFlagStr(self):
        flags = []
        if self.getFlagOptional():
            flags += ['optional']
        if self.getFlagExtern():
            flags += ['extern']
        if self.getFlagDistinctive():
            flags += ['distinctive']
        return ' '.join(flags)

    def getParent(self):
        return self.parent

    def setParent(self, parent):
        self.parent = parent

    def getTypeDefCollection(self):
        parent = self.getParent()
        if isinstance(parent, TypeDefCollection):
            return parent
        else:
            return parent.getTypeDefCollection()

    def getParamListStr(self):
        return ', '.join([str(p) for p in self.getParamList()])

    def getParamList(self):
        return self.paramList

    def addParameter(self, param):
        if not param in self.paramList:
            self.paramList += [param]
        else:
            TPLError('Parameter "{0}" already exists in definition of "{1}"' \
                    .format(param, self.getName()))

    def addParameters(self, params):
        self.paramList += params

    def getContentStr(self):
        return None

    def getName(self, default=None):
        return self.name if self.name else default

    def getPathFromRoot(self):
        parent = self.getParent()
        if isinstance(parent, TypeDef):
            return parent.getPathFromRoot() + [self]
        else:
            return [parent, self]

    def getChainedName(self, delim='_'):
        pathFromRoot = self.getPathFromRoot()
        # exclude Root (TypeDefCollection) here
        return delim.join([t.getName('~') for t in pathFromRoot[1:]])

    def setName(self, name):
        if not name:
            self.name = None
        else:
            if self.getParent():
                names = [t.name for t in self.getParent().getChildren()]
            else:
                names = []
            self.name = getUniqueName(names, name)
        return self.name

    def resetTypeID(self):
        self.typeID = None

    def setTypeID(self, typeID):
        self.typeID = typeID

    def getTypeID(self):
        return self.typeID

    def getChildren(self):
        return []

    def getKnownSymbols(self, ref=None):
        knownSymbols = {}
        if self.getParent():
            knownSymbols = self.getParent().getKnownSymbols(self)
        knownSymbols.update({var: self for var in self.getParamList()})
        return knownSymbols

    def getRequiredSymbols(self):
        s = set()
        size = self.getSize()
        if size and isinstance(size.getSize(), IntSymbol):
            s.update(set([size.getSize().getName()]))
        return s

    def dependsOnTypes(self):
        return set()

    def check(self):

        # run self check
        self.selfCheck()

        # run user-definded checks
        if hasattr(self, 'checks'):
            for check in self.checks:   
                check(self)

        # run children checks
        for child in self.getChildren():
            child.check()

        # run variable dependence check
        requiredSymbols = self.getRequiredSymbols()
        requiredSymbols.difference_update(set(self.getKnownSymbols().keys()))
        if requiredSymbols:
            first = (v for v in requiredSymbols).next()
            raise TPLCheckError(
                    'Unknown reference to "{0}" in definition of "{1}"' \
                    .format(first, self.getName()))

    def selfCheck(self):
        pass

    def makeField(self, typedefs):

        # find variable references that will be broken by making this TypeDef
        # an instantiation of a global TypeDef
        requiredVar = self.getRequiredSymbols()
        knownSymbols = self.getKnownSymbols()
        globalScope = self.getTypeDefCollection()
        brokenRefs = [var for var, where in knownSymbols.iteritems()
                if var in requiredVar and where is not globalScope]
        fieldArgs = {var: IntSymbol(var) for var in brokenRefs}

        name = self.getName()
        self.setName(self.getChainedName())
        typedefs.addDef(self)

        field = InstanceDef(self.getName(), name, fieldArgs)
        field.setFlags(self.getFlags())                        
        field.setSize(self.getSize())

        self.resetFlags()
        self.resetSize()
        self.addParameters(brokenRefs)

        return field

    def countReferences(self):
        refs = {}
        return refs

    def getTPLTriple(self):
        return (self.getFlagStr(), self.getName(), self.getSizeStr())

    def mergeWithBaseTPLTriple(self, triple):
        # need to use "class.function(instance)" rather than 
        # "instance.function()" to avoid infinite recursion
        return TypeDef.mergeTPLTriples(triple, TypeDef.getTPLTriple(self))

    def getTPLCode(self):
        # TODO: allow to return colored TPL code
        tplTriple = self.getTPLTriple()
        if tplTriple.count(None) == 3 or tplTriple[0] is None:
            raise TPLError('Failed to generate TPL')
        return '{0}{1}{2};'.format(tplTriple[0],
                (' ' + tplTriple[1]) if tplTriple[1] else '',
                tplTriple[2] if tplTriple[2] else '')

    def followInstantiation(self, args=None):
        return (self, args)

    def getRawBitWidth(self, args=None, selections=None):
        raise TPLError('Undefined raw bit width for abstract type')

    def getFeatures(self, dynlen=False):
        features = set()
        if dynlen or self.getSize() is not None:
            # feature indicating overflow
            features.add('.overflow@')
            # feature indicating underflow
            features.add('.underflow@')
        return features

    def getFullTypeNames(self):
        return ['{0}:{1}'.format(self.getName(), dynamicType) \
                for dynamicType in self.getDynamicTypeNames()]


class BuiltInDef(TypeDef):
    """
    Representation of built-in types (e.g. integers, bits, bytes, etc.)
    """

    def __init__(self, name=None):
        TypeDef.__init__(self)
        self.setName(name)

    def isReal(self):
        return True

    def getType(self):
        return 'BuiltIn'

    def getTypeStr(self):
        return TextFormatter.makeBoldBlue('BUILTIN')

    def getTPLTriple(self):
        # TPL code generation for built-in types is pointless
        raise TPLError('Cannot generate TPL code of built-in types')


class IntDef(BuiltInDef):
    """
    Representation of integers
    """

    def __init__(self, width, signed):
        form = 'sint{0}' if signed else 'uint{0}'
        BuiltInDef.__init__(self, form.format(width))
        self.width = width
        self.addParameters(['min', 'max'])

    def isRecursive(self):
        return False

    def getIntBitWidth(self):
        return self.width

    def getRawBitWidth(self, args=None, selections=None):
        return self.getIntBitWidth()


class UIntDef(IntDef):
    """
    Representation of unsigned integers
    """

    def __init__(self, width):
        IntDef.__init__(self, width, False)


class SIntDef(IntDef):
    """
    Representation of signed integers
    """

    def __init__(self, width):
        IntDef.__init__(self, width, True)


class BitDef(BuiltInDef):
    """
    Representation of a single bit
    """

    def __init__(self):
        BuiltInDef.__init__(self, 'bit')

    def isRecursive(self):
        return False

    def getRawBitWidth(self, args=None, selections=None):
        return 1


class ByteDef(BuiltInDef):
    """
    Representation of a single byte
    """

    def __init__(self):
        BuiltInDef.__init__(self, 'byte')

    def isRecursive(self):
        return False

    def getRawBitWidth(self, args=None, selections=None):
        return 8


class OpaqueDef(BuiltInDef):
    """
    Representation of an opaque chuck of data
    """

    def __init__(self):
        BuiltInDef.__init__(self, 'opaque')
        self.addParameters(['nbits', 'nbytes'])

    def isRecursive(self):
        return False

    def getRawBitWidth(self, args=None, selections=None):
        if args is None:
            args = {}
        if 'nbytes' not in args and 'nbits' not in args:
            raise TPLError('In opaque type: Insufficient arguments ' + \
                    'to determine raw bit width')
        # TODO: Handle arguments that are not numeric but references
        return 8 * args.get('nbytes', 0) + args.get('nbits', 0)


# TODO: rename "ConstDef" -> "IntSymbolDef"
class ConstDef(TypeDef):
    """
    Representation of a constant integer
    """

    def __init__(self, name=None, value=None):
        TypeDef.__init__(self)
        self.setName(name)
        self.setValue(value)

    def getType(self):
        return 'Const'

    def getTypeStr(self):
        return TextFormatter.makeBoldBlue('CONST') + '(={0})' \
                .format(TextFormatter.makeBoldCyan(str(self.getValue())))

    def setValue(self, value):
        self.value = value

    def getValue(self):
        return self.value

    def getRequiredSymbols(self):
        return set()


class InstanceDef(TypeDef):
    """
    Representation of a type alias or instantiation
    """

    @staticmethod
    def mergeArgsDisjunct(args1, args2):
        merged = {}
        keys1 = set()
        if args1 is not None:
            merged.update(args1)
            keys1.update(set(args1))
        if args2 is not None:
            merged.update(args2)
            if len([k for k in keys1.intersection(set(args2)) \
                    if args1[k] != args2[k]]):
                print keys1.intersection(set(args2))
                raise TPLError('Conflicting arguments')      
        return merged

    def __init__(self, typename, name=None, args=None):
        TypeDef.__init__(self)
        self.args = args if args else {}
        self.setName(name)
        self.typename = typename

    def getType(self):
        if self.isAlias():
            return 'Alias'
        else:
            return 'Instance'

    def getTypeStr(self):
        if self.isAlias():
            form = TextFormatter.makeBoldBlue('ALIAS ') + '{0}{1}'
        else:
            form = TextFormatter.makeBoldBlue('INSTANCE ') + '{0}{1}'
        typeNameStr = TextFormatter.makeBoldWhite(self.getTypeName())
        argMapStr = self.getArgsStr()
        if argMapStr:
            argMapStr = TextFormatter.makeBoldYellow('<{0}>'.format(argMapStr))
        return form.format(typeNameStr, argMapStr)

    def isReal(self):
        return True

    def isAlias(self):
        return isinstance(self.getParent(), TypeDefCollection)

    def isRecursive(self):
        return self.followInstantiation()[0].isRecursive()

    def getTypeName(self):
        return self.typename

    def setArgs(self, args):
        self.args = InstanceDef.mergeArgsDisjunct(self.args, args)

    def getArgs(self, extArgs=None, includeBuiltIn=False):
        args = {}
        if hasattr(self, 'args'):
            args = InstanceDef.mergeArgsDisjunct(self.args, extArgs)
        elif extArgs:
            args = extArgs
        if includeBuiltIn:
            return args
        else:
            return dict(filter(lambda (k, v): not k.startswith('_'),
                    args.iteritems()))

    def hasArgs(self, extArgs=None, includeBuiltIn=False):
        return len(self.getArgs(extArgs, includeBuiltIn)) > 0

    def getArgsStr(self, extArgs=None, includeBuiltIn=False):
        myargs = ['{0}={1}'.format(k, v)
                for k, v in self.getArgs(extArgs, includeBuiltIn).iteritems()]
        return ', '.join(myargs)

    def getRequiredSymbols(self):
        s = TypeDef.getRequiredSymbols(self)
        s.update([arg.getName() for arg in self.getArgs().itervalues() \
                if isinstance(arg, IntSymbol)])
        return s

    def dependsOnTypes(self):
        s = TypeDef.dependsOnTypes(self)
        s.update(set([self.typename]))
        return s

    def countReferences(self):
        refs = {self.getTypeName(): 1}
        return refs

    def getTPLTriple(self):
        # TODO: Handle arguments which currently cannot be represented in TPL
        typeStr = self.getTypeName()
        if self.hasArgs(None, False):
            typeStr += '::<{0}>'.format(self.getArgsStr())
        return self.mergeWithBaseTPLTriple((typeStr, None, None))

    def makeField(self, typedefs):
        return self

    def selfCheck(self):    
        # make sure there are only integer-type arguments
        if [k.startswith('_') or isinstance(v, IntElement) for k, v in \
                self.getArgs().iteritems()].count(False):
            raise TPLCheckError('Non-integer type as argument of ' + \
                    'InstanceDef "{0}"'.format(self.getName()))

    def followInstantiation(self, args=None):
        return self.getTypeDefCollection()[self.getTypeName()] \
                .followInstantiation(self.getArgs(args))

    def getRawBitWidth(self, args=None, selections=None):
        typeDef, args = self.followInstantiation(args)
        bitWidth = typeDef.getRawBitWidth(args, selections)
        if isinstance(bitWidth, int):
            return bitWidth
        elif isinstance(bitWidth, str):
            # TODO: Also consider global constant integer definitions
            return selections[bitWidth]
        else:
            TPLError('Insufficient information to determine bit width')


class WrapperDef(TypeDef):

    def __init__(self):
        TypeDef.__init__(self)
        self.element = None

    def isReal(self):
        return True

    def isRecursive(self):
        return True

    def getElement(self):
        return self.element

    def setElement(self, element):
        self.element = element
        element.setParent(self)

    def embedElement(self, element):
        self.setElement(element)
        self.setName(element.name)
        self.setFlags(element.getFlags())
        element.setName(None)
        element.resetFlags()
        return self

    def getContentStr(self):
        return str(self.getElement())

    def getChildren(self):
        return [self.getElement()] if self.getElement() else []

    def getRequiredSymbols(self):
        s = TypeDef.getRequiredSymbols(self)
        s.update(self.getElement().getRequiredSymbols())
        return s

    def dependsOnTypes(self):
        s = TypeDef.dependsOnTypes(self)
        s.update(self.getElement().dependsOnTypes())
        return s

    def countReferences(self):
        return self.getElement().countReferences()


class VectorDef(WrapperDef):
    """
    Representation of a vector
    """

    def __init__(self):
        WrapperDef.__init__(self)

    def getType(self):
        return 'Vector'

    def getTypeStr(self):
        return TextFormatter.makeBoldBlue('VECTOR') + \
                TextFormatter.makeBoldCyan(self.getVectorDef())

    def getTPLTriple(self):
        triple = TypeDef.mergeTPLTriples(self.getElement().getTPLTriple(), 
                (None, None, self.getVectorDef()))
        return self.mergeWithBaseTPLTriple(triple)

    def getFeatures(self, dynlen=False):
        features = TypeDef.getFeatures(self, dynlen)

        inst = self.getElement().followInstantiation()[0]
        if isinstance(inst, EnumDef):
            # <<< the vector's element is an EnumDef >>>
            features.update(['{0}%'.format(s) \
                    for s in inst.getFullTypeNames()])

        elif isinstance(inst, StructDef):
            # <<< the vector's element is a StructDef >>>
            dynamicTypes = inst.getDynamicTypeNames()

            for dynamicType in dynamicTypes:
                prefix = '{0}:{1}%'.format(inst.getName(), dynamicType)
                subFeatures = inst.getFeatures(False, dynamicType)
                features.add(prefix)
                if len(subFeatures) > 0:
                    features.update([TypeDef.concatFeatureStrings( \
                            prefix, feature) for feature in subFeatures])

        return features


class StaticVectorDef(VectorDef):
    """
    Representation of a static vector, i.e. a vector with an externly
    supplied length
    """

    def __init__(self, length=None, **args):
        VectorDef.__init__(self)
        self.isItemBased = args['isItemBased']
        self.setLength(length)

    def getLength(self):
        return self.length

    def setLength(self, length):
        if length is None or isinstance(length, IntElement):
            self.length = length
        else:
            raise Exception('Invalid length!')        

    def getRequiredSymbols(self):
        s = VectorDef.getRequiredSymbols(self)
        if self.getLength():
            s.update(self.getLength().getRequiredSymbols())
        return s

    def getVectorDef(self):
        try:
            unit = str(self.lengthUnit)
        except:
            unit = ''
        form = '[[{0}{1}]]' if self.isItemBased else '[{0}{1}]'
        return form.format(
            self.length if self.length is not None else '', unit)

    def getRawBitWidth(self, args=None, selections=None):
        if self.isItemBased:
            if self.length is None:
                raise TPLError('In vector "{0}": Cannot determine raw ' + \
                        'bit width of indefinite length vector')
            width = self.getElement().getRawBitWidth(args, selections)
            width = width * self.length
        else:
            if self.length is None:
                raise TPLError('In vector "{0}": Cannot determine raw ' + \
                        'bit width of indefinite length vector')
            width = self.length
            if hasattr(self, 'lengthUnit') and self.lengthUnit:
                width = width * self.lengthUnit.getBitScale()
            else:
                width = width * 8
        return width            


class DynamicVectorDef(VectorDef):
    """
    Representation of a dynamic vector, i.e. a self-contained vector with its
    own embedded length field
    """

    def __init__(self, lengthMin=None, lengthMax=None, **args):
        VectorDef.__init__(self)
        self.isItemBased = args['isItemBased']
        self.lengthMin = lengthMin
        self.lengthMax = lengthMax

    def getLengthMin(self):
        return self.lengthMin

    def getLengthMinValue(self):
        return self.getLengthMin().getValue()

    def getLengthMax(self):
        return self.lengthMax

    def getLengthMaxValue(self):
        return self.getLengthMax().getValue()

    def getVectorDef(self):
        try:
            unit = str(self.lengthUnit)
        except:
            unit = ''
        form = '<<{0}..{1}{2}>>' if self.isItemBased else '<{0}..{1}{2}>'
        lengthMin = self.lengthMin if self.lengthMin is not None else '?'
        lengthMax = self.lengthMax if self.lengthMax is not None else '?'
        return form.format(lengthMin, lengthMax, unit)

    def getRawBitWidth(self, args=None, selections=None):
        raise TPLError('In vector "{0}": Cannot determine raw ' + \
                'bit width of dynamic length vector')


class EnumItemAbstract(object):

    def __init__(self, name):
        self.name = name

    def getName(self, default=None):
        return self.name if not self.name is None else default

    def __str__(self):
        return self.getAsStr()

    def getAsStr(self, strWidth=None, *rest):
        if strWidth is None:
            strWidth = len(self.getName('<none>'))
        return '{0:{1}} := <abstract>'.format(self.getName('<none>'), strWidth)

    def getTPLCode(self):
        return self.getName()


class EnumItemFallback(EnumItemAbstract):

    def __init__(self, name):
        EnumItemAbstract.__init__(self, name)

    def __str__(self):
        return self.getAsStr()

    def getAsStr(self, strWidth=None, *rest):
        if strWidth is None:
            strWidth = len(self.getName('<none>'))
        return '{0:{1}} := <fallback>'.format(self.getName('<none>'), strWidth)

    def getTPLCode(self):
        return '{0}(*)'.format(self.getName())


class EnumItem(EnumItemAbstract):

    # TODO: allow enum items to cover multiple ranges

    def __init__(self, name, minCode=None, maxCode=None):
        EnumItemAbstract.__init__(self, name)
        self.minCode = minCode
        if maxCode is not None:
            if minCode is None:
                raise TPLError('Invalid codes for enumeration item')
            if maxCode < minCode:
                raise TPLError('Invalid range for enumeration item')
            self.maxCode = maxCode
        else:
            if name is None and minCode is None:
                raise TPLError('Invalid parameters for enumeration item')
            self.maxCode = minCode

    def __str__(self):
        strWidth = len(self.getName()) if self.getName() else 0
        hexWidth = EnumDef.getNDigits(self.getMaxCodeValue(), 16)
        decWidth = EnumDef.getNDigits(self.getMaxCodeValue(), 10)
        return self.getAsStr(strWidth, hexWidth, decWidth)        

    def getMinCode(self):
        return self.minCode

    def getMinCodeValue(self):
        return self.getMinCode().getValue()

    def getMaxCode(self):
        return self.maxCode

    def getMaxCodeValue(self):
        return self.getMaxCode().getValue()

    def isRange(self):
        if self.getMinCodeValue() != self.getMaxCodeValue():
            return True
        else:
            return False

    def getAsStr(self, strWidth, hexWidth, decWidth):
        form = TextFormatter.makeBoldPurple('0x{0:0{1}X}') \
                + ' (' + TextFormatter.makeBoldPurple('{0:{2}}') + ')'
        item = '{0:{1}} := '.format(
                self.getName() if self.getName() else '<none>', strWidth)
        item += form.format(self.getMinCodeValue(), hexWidth, decWidth)
        if self.isRange():
            item += ' .. '
            item += form.format(self.getMaxCodeValue(), hexWidth, decWidth)
        return item

    def getTPLCode(self):
        name = self.getName() if self.getName() else ''
        code = '{0}'.format(str(self.getMinCode()))
        if self.isRange():
            code += '..{0}'.format(self.getMaxCode())            
        return '{0}({1})'.format(name, code)


class EnumDef(TypeDef):
    """
    Representation of an enumeration
    """

    def __init__(self, items=None):
        TypeDef.__init__(self)
        self.resetItems()
        self.addItems(items)

    def __getitem__(self, index):
        if isinstance(index, int):
            # Find an item by its index
            if index < 0 or index >= len(self.getItems()):
                # The item index requested is out of range: either less than
                # zero or beyond the existing items
                raise TPLError('In enum "{0}": Item index ({1}) out of range' \
                        .format(self.getName(), index))                
            # Return the item by its index
            return self.getItems()[index]
        elif isinstance(index, str):
            # Find an item by its name
            itemIter = (i for i in self.getItems() if i.getName() == index)
            try:
                return itemIter.next()
            except StopIteration:
                raise TPLError('In enum "{0}": Unknown item "{1}"' \
                        .format(self.getName(), index))
        else:
            raise TPLError('In enum "{0}": Invalid item index type' \
                    .format(self.getName()))

    def isReal(self):
        return True

    def isRecursive(self):
        return False

    def getType(self):
        return 'Enum'

    def getTypeStr(self):
        return TextFormatter.makeBoldBlue('ENUM') + '({0})' \
                .format(TextFormatter.makeBoldCyan(str(self.getEnumBitWidth())))

    def getContentStr(self):
        # Get the string length of the longest item name, where "<none>"
        # (6 characters) will be used for items without a name
        strWidth = max([(len(item.getName()) if item.getName() else 6)
                for item in self.getItems()])
        hexWidth = EnumDef.getNDigits(self.getMaxCodeValue(), 16)
        decWidth = EnumDef.getNDigits(self.getMaxCodeValue(), 10)
        return '\n'.join([item.getAsStr(
                strWidth, hexWidth, decWidth) for item in self.getItems()])

    def resetItems(self):
        self.items = []

    def addItem(self, item):
        self.items += [item]

    def addItems(self, items):
        if items:
            for i in items:
                self.addItem(i)

    def getItems(self):
        return self.items

    def getItemNames(self):
        return [item.getName() for item in self.getItems() \
                if item.getName() is not None]

    def getMaxCodeValue(self):
        return max([item.getMaxCodeValue() \
            for item in self.items if isinstance(item, EnumItem)])

    def getEnumBitWidth(self):
        return self.getNDigits(self.getMaxCodeValue(), 2)

    def selfCheck(self):
        if len([item for item in self.getItems() \
                if isinstance(item, EnumItemFallback)]) > 1:
            raise TPLCheckError('Multiple fallback items in enumeration "{0}"' \
                    .format(self.getName()))

    def getTPLTriple(self):
        return (pre, self.getName(), self.getSizeStr())

    def getTPLTriple(self):
        body = ',\n'.join([item.getTPLCode() for item in self.getItems()])
        if body:
            body = '\n' + body + '\n'
        pre = 'enum {{{0}}}'.format(TextFormatter.indent(body))
        return self.mergeWithBaseTPLTriple((pre, None, None))

    def getRawBitWidth(self, args=None, selections=None):
        return self.getEnumBitWidth()

    def getFeatures(self, dynlen=False):
        features = TypeDef.getFeatures(self, dynlen)
        features.update(self.getFullTypeNames())
        return features

    def getDynamicTypeNames(self):
        return self.getItemNames()


class StructDef(TypeDef):
    """
    Representation of a structure, i.e. an ordered composition of types
    """

    def __init__(self, members=None):
        TypeDef.__init__(self)
        self.resetMembers()
        self.addMembers(members)

    def isReal(self):
        return True

    def isRecursive(self):
        return True

    def __getitem__(self, index):
        if isinstance(index, int):
            # Find a member by its index
            if index < 0 or index >= len(self.getMembers()):
                # The member index requested is out of range: either less than
                # zero or beyond the existing members
                raise TPLError(
                        'In struct "{0}": Member index ({1}) out of range' \
                                .format(self.getName(), index))                
            # Return the member by its index
            return self.getMembers()[index]
        elif isinstance(index, str):
            # Find a member by its name: define an iterator that should only
            # find one member, namely the one with the name given by <index>
            memIter = (m for m in self.getMembers() if m.getName() == index)
            try:
                # If a member with the name <index> exists the iterator will
                # return that single element, or raise an exception otherwise
                return memIter.next()
            except StopIteration:
                raise TPLError('In struct "{0}": Unknown member "{1}"' \
                        .format(self.getName(), index))
            # This should not happen as the statement in the try block above is
            # expected to either return from this function or raise a
            # StopIteration exception
            raise TPLError('In struct "{0}": Unknown error' \
                    .format(self.getName()))
        else:
            # The member index type is invalid as it seems to be neither an
            # integer nor a string, therefore raise an exception
            raise TPLError('In struct "{0}": Invalid member index type' \
                    .format(self.getName()))

    def getType(self):
        return 'Struct'

    def getTypeStr(self):
        return TextFormatter.makeBoldBlue('STRUCT')

    def getContentStr(self):
        return '\n'.join([str(m) for m in self.getMembers()])

    def resetMembers(self):
        """ Remove all members from this struct """
        self.members = []

    def addMember(self, member):
        """ Add a new member to this struct """
        # Make sure a member with the same name does not exist (except for
        # anonymous members whose name is <None>)
        if member.getName() not in self.getMemberNames(True):
            # Add the new member to the list of members and update its parent
            # relation accordingly
            self.members += [member]
            member.setParent(self)
        else:
            # There is already another member with the same name in this
            # struct, therefore raise an exception
            raise TPLError(
                    'In struct "{0}": Member with name "{1}" already exists' \
                            .format(self.getName(), member.getName()))

    def addMembers(self, members):
        if members:
            for m in members:
                self.addMember(m)

    def setMember(self, member, index):
        self.members[index] = member
        member.setParent(self)

    def getMembers(self):
        return self.members

    def getMemberNameCounts(self, includeEmbedded=False, disambiguate=False, \
            mergeEmbedded=False):
        counts = {}
        for m in self.getMembers():
            if isinstance(m, SelectDef) and includeEmbedded:
                if mergeEmbedded:
                    sumDicts(counts, { k: 1 for k in m.getMemberNameCounts( \
                            True, disambiguate).keys() })
                else:
                    sumDicts(counts, m.getMemberNameCounts(True, disambiguate))
            elif disambiguate:
                sumDicts(counts, { self.disambiguateMemberName(m): 1 })
            else:
                sumDicts(counts, { m.getName(): 1 })
        return counts

    def getMemberNames(self, includeEmbedded=False, disambiguate=False):
        return self.getMemberNameCounts(includeEmbedded, disambiguate).keys()

    def getMemberIndex(self, name):
        return (i for i, m in enumerate(self.getMembers()) \
                if m.getName() == name).next()

    def getNMembers(self):
        return len(self.getMembers())

    def getDistinctiveMembers(self):
        """ Return the (correctly ordered) list of member that 
        are distinctive, i.e. which make up the struct's dynamic type """
        return [m for m in self.getMembers() if m.getFlagDistinctive()]
       
    def getChildren(self):
        return self.getMembers()

    def getKnownSymbols(self, ref=None):
        symbols = TypeDef.getKnownSymbols(self, self)
        if ref in self.getMembers():
            localMembers = self.getMembers()[0:self.getMembers().index(ref)]
            symbols.update({m.getName(): self for m in localMembers})
        return symbols

    def getRequiredSymbols(self):
        """ Return a set of variable names that this struct depends on """
        s = TypeDef.getRequiredSymbols(self)
        for m in self.getMembers():
            s.update(m.getRequiredSymbols())
            localVars = [var for var, where in m.getKnownSymbols().iteritems() \
                    if where is self]
            s.difference_update(set(localVars))
        return s

    def dependsOnTypes(self):
        s = TypeDef.dependsOnTypes(self)
        for m in self.getMembers():
            s.update(m.dependsOnTypes())
        return s

    def selfCheck(self):

        # Find non-optional members following optional ones
        opts = [1 if m.getFlagOptional() else 0 for m in self.getMembers()]
        mask = [1 if sum(opts[0:i+1]) else 0 for i in range(len(opts))]
        if opts != mask:
            first = (self[i] for i in range(len(opts)) \
                    if opts[i] != mask[i]).next()
            raise TPLCheckError(('Non-optional member "{0}" following ' + \
                    'optional member(s) in struct "{1}"') \
                    .format(first.getName(), self.getChainedName("/")))

        # Find distinctive members that are not an enum
        distinctives = [m for m in self.getMembers() if m.getFlagDistinctive()]
        nonEnumDistinctives = [m for m in self.getMembers() \
                        if m.getFlagDistinctive() and \
                                not isinstance(m.followInstantiation()[0], EnumDef)]
        if len(nonEnumDistinctives) > 0:
            raise TPLCheckError(('Distinctive non-enum member "{0}" ' + \
                    ' in struct "{1}"').format(nonEnumDistinctives[0].getName(),
                    self.getChainedName("/")))        

        # Find duplicate name members
        counts = self.getMemberNameCounts(True, False, True)
        if len(counts) > 0 and max(counts.values()) > 1:
            duplicates = (name for name in counts if counts[name] > 1)
            raise TPLCheckError(('Members with duplicate name "{0}" in ' + \
                    'struct "{1}"').format(duplicates.next(), self.getName()))

        # Find nested ambiguous members
        counts = self.getMemberNameCounts(True, True, False)
        if len(counts) > 0 and max(counts.values()) > 1:
            duplicates = (name for name in counts if counts[name] > 1)
            raise TPLCheckError(('Ambiguous members "{0}" in ' + \
                    'struct "{1}"').format(duplicates.next(), self.getName()))

    def countReferences(self):
        refs = {}
        for m in self.getMembers():
            sumDicts(refs, m.countReferences())
        return refs

    def getTPLTriple(self):
        body = '\n'.join([m.getTPLCode() for m in self.getMembers()])
        if body:
            body = '\n' + body + '\n'
        pre = 'struct {{{0}}}'.format(TextFormatter.indent(body))
        return self.mergeWithBaseTPLTriple((pre, None, None))

    def getRawBitWidth(self, args=None, selections=None):
        return sum([m.getRawBitWidth(args, selections) \
                for m in self.getMembers()])

    def disambiguateMemberName(self, member):
        if member in self.getMembers():
            # nothing to do in a plain StructDef
            return member.getName()
        else:
            raise Exception('Cannot disambiguate non-members')

    def getFeatures(self, dynlen=False, dynamicType=None):

        # Dissect dynamic type
        symbolChoices = {}
        if dynamicType:
            distinctives = self.getDistinctiveMembers()
            choices = dynamicType.split('+')

            # make sure the dynamic type has the correct dimensionality
            if len(distinctives) != len(choices):
                raise Exception(('Wrong dimensionality of dynamic type "{0}"' + \
                        ' for struct "{1}"').format(dynamicType, self.getName()))                        

            # make sure the components of the dynamic type are known
            for member, choice in zip(distinctives, choices):
                inst = member.followInstantiation()[0]
                if choice not in inst.getItemNames():
                    raise Exception(('Invalid dynamic type "{0}" for struct' + \
                            ' "{1}"').format(dynamicType, self.getName()))                        
                symbolChoices[member.getName()] = choice

        features = TypeDef.getFeatures(self, dynlen)

        for c in self.getMembers():
            # skip members pre-determined by dynamic
            # type, i.e. most probably EnumDefs
            if c.getName() in symbolChoices:
                continue
            if c.isReal():

                # check whether this is a dynamic length member
                hasSize = True if c.getSize() else False

                inst = c.followInstantiation()[0]
                name = self.disambiguateMemberName(c)
                features.add(name)
                # TODO: consider dynlen for the following two getFeatures(...)
                if inst.isRecursive():
                    features.update([TypeDef.concatFeatureStrings(name, f) \
                            for f in inst.getFeatures(hasSize)])
                else:
                    # Most probably an EnumDef
                    # TODO
                    features.update(['{0}%{1}'.format(feature, c.getName()) \
                            for feature in inst.getFeatures(hasSize)])
            elif isinstance(c, SelectDef):
                features.update(c.getFeatures(False, symbolChoices))
        return features

    def getDynamicTypeNames(self):

        # Find distinctive member
        distinctives = self.getDistinctiveMembers()
        if len(distinctives) == 0:
            return []

        # dynamic types are constructed from the cartesian
        # product of distinctive EnumDef members
        distinctiveNames = itertools.product( \
                *[d.followInstantiation()[0].getItemNames() for d in distinctives])
        return ['+'.join(name) for name in distinctiveNames]


class CaseDef(StructDef):

    def __init__(self, cond=None, members=None):
        StructDef.__init__(self, members)
        self.cond = cond

    def isReal(self):
        return False

    def getTypeStr(self):
        condStr = ', '.join(TextFormatter.makeBoldCyan(s) for s in self.cond)
        return TextFormatter.makeBoldGreen('CASE') + ' {0}'.format(condStr)

    def getContentStr(self):
        return '\n'.join([str(m) for m in self.getMembers()])

    def getSelectDef(self):
        parent = self.getParent()
        if isinstance(parent, SelectDef):
            return parent
        else:
            raise TPLError('CaseDef is not embedded in SelectDef')

    def getRootSelectDef(self):
        selectDef = self.getSelectDef()
        if isinstance(selectDef.getParent(), CaseDef):
            return selectDef.getParent().getRootSelectDef()
        else:
            return selectDef

    def getCondStr(self):
        return ', '.join([s for s in self.cond])

    def getTPLTriple(self):
        body = '\n'.join([m.getTPLCode() for m in self.getMembers()])
        pre = 'case {0}:\n{1}'.format(self.getCondStr(), TextFormatter.indent(body))
        return self.mergeWithBaseTPLTriple((pre, None, None))

    def getTPLCode(self):
        return self.getTPLTriple()[0]

    def disambiguateMemberName(self, member):
        if member in self.getMembers():
            selectDef = self.getRootSelectDef()
            if selectDef.getMemberNameCounts(True)[member.getName()] > 1:
                return '{0}%{1}'.format( \
                        member.followInstantiation()[0].getName(), \
                        member.getName())
            else:
                return member.getName()
        else:
            raise Exception('Cannot disambiguate non-members')


class DefaultCaseDef(CaseDef):

    def __init__(self, members=None):
        CaseDef.__init__(self, None, members)

    def getTypeStr(self):
        return TextFormatter.makeBoldGreen('DEFAULT')

    def getTPLTriple(self):
        body = '\n'.join([m.getTPLCode() for m in self.getMembers()])
        pre = 'default:\n{0}'.format(TextFormatter.indent(body))
        return self.mergeWithBaseTPLTriple((pre, None, None))

    def getTPLCode(self):
        return self.getTPLTriple()[0]


class SelectDef(TypeDef):

    def __init__(self, testSymbol=None, cases=None):
        TypeDef.__init__(self)
        self.testSymbol = testSymbol
        self.resetCases()
        self.addCases(cases)

    def isReal(self):
        return False

    def isRecursive(self):
        return True

    def getDefaultCase(self):
        defaultCases = [c for c in self.getCases() \
                if isinstance(c, DefaultCaseDef)]
        # there shouldn't be more than one default case
        return defaultCases[0] if defaultCases else None

    def __getitem__(self, index):
        if isinstance(index, int):
            return self.getCases()[index]
        elif isinstance(index, str):
            matchingCases = [c for c in self.getCases() \
                    if not isinstance(c, DefaultCaseDef) \
                            and index in list(c.cond)]
            if matchingCases:
                return matchingCases[0]
            else:
                return self.getDefaultCase()            
        else:
            raise Exception('SelectDef: Unknown index type')

    def getTypeStr(self):
        return '{0}({1})'.format(TextFormatter.makeBoldGreen('SELECT'),
            TextFormatter.makeBoldCyan(self.getTestVarName()))

    def getContentStr(self):
        return '\n'.join([str(c) for c in self.getCases()])

    def getTestVarName(self):
        return self.testSymbol

    def resetCases(self):
        self.cases = []

    def addCase(self, case):
        self.cases += [case]
        case.setParent(self)

    def addCases(self, cases):
        if cases:
            for c in cases:
                self.addCase(c)

    def setCase(self, case, index):
        self.cases[index] = case
        case.setParent(self)

    def getCases(self):
        return self.cases

    def getChildren(self):
        return self.getCases()

    def getMemberNameCounts(self, includeEmbedded=False, disambiguate=False):
        if includeEmbedded:
            counts = {}
            for c in self.getCases():
                sumDicts(counts, c.getMemberNameCounts(True, disambiguate))
            return counts
        else:
            # that one actually doesn't make sense
            return {}

    def getMemberNames(self, includeEmbedded=False, disambiguate=False):
        return self.getMemberNameCounts(includeEmbedded, disambiguate).keys()

    def selfCheck(self):

        # Make sure SelectDef lives inside a StructDef
        if not isinstance(self.getParent(), StructDef):
            raise TPLCheckError(
                    'SelectDef "{0}" only possible inside a StructDef' \
                    .format(self.getChainedName('/')))            

        # Make sure there is exactly one valid default branch
        listDefaults = [1 if isinstance(c, DefaultCaseDef) else 0 \
                for c in self.getCases()]
        if sum(listDefaults) == 0:
            raise TPLCheckError(
                    'Missing default case branch in definition of "{0}"' \
                    .format(self.getChainedName('/')))
        elif sum(listDefaults) > 1:
            raise TPLCheckError(
                    'More than one default case branch in definition of "{0}"' \
                    .format(self.getChainedName('/')))
        elif listDefaults[-1] != 1:
            raise TPLCheckError(
                    'Default case not at end of case list in definition of "{0}"' \
                    .format(self.getChainedName('/')))            

        # Make sure each case has the same number of members
        # TODO: get rid of this restriction
        listNMembers = [c.getNMembers() for c in self.getCases()]
        if min(listNMembers) != max(listNMembers):
            raise TPLCheckError(
                    'Unbalanced number of case members in definition of "{0}"' \
                    .format(self.getChainedName('/')))

    def getRequiredSymbols(self):
        s = TypeDef.getRequiredSymbols(self)
        s.update(set([self.getTestVarName()]))
        for c in self.getCases():
            s.update(c.getRequiredSymbols())
        return s

    def dependsOnTypes(self):
        s = TypeDef.dependsOnTypes(self)
        for c in self.getCases():
            s.update(c.dependsOnTypes())
        return s

    def getTPLTriple(self):
        body = '\n'.join([c.getTPLCode() for c in self.getCases()])
        if body:
            body = '\n' + body + '\n'
        pre = 'select ({0}) {{{1}}}'.format(self.getTestVarName(),
                TextFormatter.indent(body))
        return self.mergeWithBaseTPLTriple((pre, None, None))

    def getFeatures(self, dynlen=False, symbolChoices=None):
        features = TypeDef.getFeatures(self, dynlen)       
        if self.getTestVarName() in symbolChoices:
            # we only need to consider one specific case branch
            matchingCase = self[symbolChoices[self.getTestVarName()]]
            features.update(matchingCase.getFeatures())
        else:
            # we need to consider all possible case branches
            for case in self.getCases():
                features.update(case.getFeatures())
        return features


class FragmentDef(WrapperDef):

    def __init__(self):
        WrapperDef.__init__(self)

    def getTypeStr(self):
        return TextFormatter.makeBoldGreen('FRAGMENT')

    def getTPLTriple(self):
        triple = TypeDef.mergeTPLTriples(self.getElement().getTPLTriple(), 
                (None, None, '*'))
        return self.mergeWithBaseTPLTriple(triple)

