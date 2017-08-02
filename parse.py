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

import sys
import math
from pyparsing import *
from core import *

# TODO: Allow setting configuration parameters, e.g. min-data-size = 8 bit
# TODO: Allow sourcing other TPL files from TPL file


class EtplParseException(Exception):

    def __init__(self, error):
        self.error = error


def failHard(s, l, expr, err):
    raise EtplParseException(err)


def getLineNumber(text, pos):
    return text.count('\n', 0, pos) + 1

# _____________________________________________________________________________

pypNonComment = ZeroOrMore(CharsNotIn('#'))
pypNonComment.setParseAction(lambda s, l, t: t if len(t) > 0 else [''])

pypComment = pythonStyleComment

pypLine = pypNonComment + Suppress(Optional(pypComment))

# _____

def Block(par, body, name=None):
    block = Suppress(Literal(par[0])) + body + Suppress(Literal(par[1]))
    if name:
        block.setName(name)
    return block

def CommaSeparatedList(expression):
    return expression + ZeroOrMore(Suppress(Literal(",")) - expression)


# _____

pypLineTerm = Suppress(Literal(";"))

pypKeywordExtern      = Keyword("extern")
pypKeywordOptional      = Keyword("optional")
pypKeywordDistinctive   = Keyword("distinctive")    # mark element in struct as the one defining an instance's distinctive type

pypKeywordExported      = Keyword("exported")       # export value of element

pypKeywordConst     = Keyword("const")

pypKeywordStruct    = Keyword("struct")

pypKeywordEnum      = Keyword("enum")

pypKeywordFlags     = Keyword("flags")

pypKeywordSelect    = Keyword("select")
pypKeywordCase      = Keyword("case")
pypKeywordDefault   = Keyword("default")

pypKeywordBits      = Keyword("bits")
pypKeywordBytes     = Keyword("bytes")

pypReserved = NotAny(
    pypKeywordExtern |
    pypKeywordOptional |
    pypKeywordConst | 
    pypKeywordStruct | 
    pypKeywordEnum | 
    pypKeywordFlags | 
    pypKeywordSelect |
    pypKeywordCase |
    pypKeywordDefault |
    pypKeywordBits |
    pypKeywordBytes)


# _____

# -----------------------------------------------------------------------------
# EBNF: Identifier = ...
# -----------------------------------------------------------------------------
pypIdentifier = pypReserved + Word(alphas, alphanums + "_")

pypIdentifierList = Group(delimitedList(pypIdentifier))

def get_pypIdentifier(name=None):
    if name:
        return pypReserved + Word(alphas, alphanums + "_").setName(name)
    else:
        return pypReserved + Word(alphas, alphanums + "_")


# _____________________________________________________________________________
#
# Integer expressions and ranges
# _____________________________________________________________________________

# -----------------------------------------------------------------------------
# EBNF: HexIntLiteral = ("0x" | "0X"), HexDigits;
# -----------------------------------------------------------------------------
pypHexIntLiteral = \
        CaselessLiteral("0x") \
        - Word(hexnums).setName('hex digits')

pypHexIntLiteral.setParseAction(lambda s, l, t: IntLiteral(int(t[1], 16)))


# -----------------------------------------------------------------------------
# EBNF: BinIntLiteral = ("0b" | "0B"), BinDigits;
# -----------------------------------------------------------------------------
pypBinIntLiteral = \
        CaselessLiteral("0b") \
        - Word('01').setName('binary digits')

pypBinIntLiteral.setParseAction(lambda s, l, t: IntLiteral(int(t[1], 2)))


# -----------------------------------------------------------------------------
# EBNF: DecIntLiteral = DecDigits;
# -----------------------------------------------------------------------------
pypDecIntLiteral = Word(nums)

pypDecIntLiteral.setParseAction(lambda s, l, t: IntLiteral(int(t[0])))


# -----------------------------------------------------------------------------
# EBNF: IntLiteral = HexIntLiteral | BinIntLiteral | DecIntLiteral;
# -----------------------------------------------------------------------------
pypIntLiteral = pypHexIntLiteral | pypBinIntLiteral | pypDecIntLiteral


# -----------------------------------------------------------------------------
# EBNF: IntSymbol = Identifier;
# -----------------------------------------------------------------------------
pypIntSymbol = pypIdentifier.copy()

pypIntSymbol.setParseAction(lambda s, l, t: IntSymbol(t[0]))


# -----------------------------------------------------------------------------
# EBNF: ;
# -----------------------------------------------------------------------------
pypOpExp    = Literal('^')
pypOpMult   = Literal('*')
pypOpPlus   = Literal('+')
pypOpMinus  = Literal('-')

pypIntExpr = operatorPrecedence(pypIntSymbol | pypIntLiteral, [
    (pypOpExp, 2, opAssoc.RIGHT,
        lambda s, l, t: reduce(lambda x, y: x ** y, t[0][0::2])),
    (pypOpMult, 2, opAssoc.LEFT,
        lambda s, l, t: reduce(lambda x, y: x * y, t[0][0::2])),
    (pypOpPlus, 2, opAssoc.LEFT,
        lambda s, l, t: reduce(lambda x, y: x + y, t[0][0::2])),
    (pypOpMinus, 2, opAssoc.LEFT,
        lambda s, l, t: reduce(lambda x, y: x - y, t[0][0::2]))])

pypConstIntExpr = operatorPrecedence(pypIntLiteral, [
    (pypOpExp, 2, opAssoc.RIGHT,
        lambda s, l, t: reduce(lambda x, y: x ** y, t[0][0::2])),
    (pypOpMult, 2, opAssoc.LEFT,
        lambda s, l, t: reduce(lambda x, y: x * y, t[0][0::2])),
    (pypOpPlus, 2, opAssoc.LEFT,
        lambda s, l, t: reduce(lambda x, y: x + y, t[0][0::2])),
    (pypOpMinus, 2, opAssoc.LEFT,
        lambda s, l, t: reduce(lambda x, y: x - y, t[0][0::2]))])

# _____

pypIntRange = pypIntExpr - Suppress(Literal("..")) - pypIntExpr

pypIntExprOrRange = pypIntExpr + Optional(Suppress(Literal("..")) - pypIntExpr)

pypConstIntExprOrRange = pypConstIntExpr + \
        Optional(Suppress(Literal("..")) - pypConstIntExpr)

# _____

#pypTypeDefs = Forward()


# _____________________________________________________________________________
#
# struct
# _____________________________________________________________________________

pypStructVarDefs = Forward()

pypStruct = Suppress(pypKeywordStruct) - Block('{}', pypStructVarDefs)
pypStruct.setParseAction(lambda s, l, t: StructDef(t))


# _____________________________________________________________________________
#
# Enum
# _____________________________________________________________________________

# -----------------------------------------------------------------------------
# EBNF: EnumItemCode = IntLiteralOrRange;
# -----------------------------------------------------------------------------
pypEnumItemCode = pypConstIntExprOrRange.copy()

pypEnumItemCode.setName('enumeration item code')


# -----------------------------------------------------------------------------
# EBNF: EnumItemIdentifier = Identifier;
# -----------------------------------------------------------------------------
pypEnumItemIdentifier = pypIdentifier.copy()

pypEnumItemIdentifier.setName('enumeration item name')


# -----------------------------------------------------------------------------
# EBNF: 
# -----------------------------------------------------------------------------
pypEnumItem = Optional(pypEnumItemIdentifier) + Block('()', pypEnumItemCode)

def parseEnumItem(s, l, t):
    if isinstance(t[0], str):
        return EnumItem(t[0], t[1], t[-1])
    else:
        # an anonymous enum item (without a name)
        return EnumItem(None, t[0], t[-1])

pypEnumItem.setParseAction(parseEnumItem)


# -----------------------------------------------------------------------------
# EBNF: FallbackEnumItem = [ EnumItemIdentifier ] "(" "*" ")"
# -----------------------------------------------------------------------------
pypFallbackEnumItem = Optional(pypEnumItemIdentifier) \
                    + Suppress(Block('()', Literal('*')))

def parseFallbackEnumItem(s, l, t):
    if len(t) > 0:
        return EnumItemFallback(t[0])
    else:
        # an anonymous enum item (without a name)
        return EnumItemFallback(None)

pypFallbackEnumItem.setParseAction(parseFallbackEnumItem)


# -----------------------------------------------------------------------------
# EBNF: 
# -----------------------------------------------------------------------------
pypGenericEnumItem = pypFallbackEnumItem | pypEnumItem

pypGenericEnumItem.setName('enumeration item')

pypGenericEnumItem.setFailAction(failHard)


# -----------------------------------------------------------------------------
# EBNF: 
# -----------------------------------------------------------------------------
pypEnumBody = CommaSeparatedList(pypGenericEnumItem)


# -----------------------------------------------------------------------------
# EBNF: 
# -----------------------------------------------------------------------------
pypEnum = Suppress(pypKeywordEnum) - Block('{}', pypEnumBody)

pypEnum.setParseAction(lambda s, l, t: EnumDef(t))


# _____________________________________________________________________________
#
# Data Size Unit Definitions
# _____________________________________________________________________________

pypKeywordBits.setParseAction(lambda s, l, t: SizeDef(None, 1))
pypKeywordBytes.setParseAction(lambda s, l, t: SizeDef(None, 8))

pypSizeUnit = pypKeywordBits | pypKeywordBytes

pypSizeUnitDef = Literal(":") - pypSizeUnit
pypSizeUnitDef.setParseAction(lambda s, l, t: t[1])


# _____________________________________________________________________________
#
# Vectors
# _____________________________________________________________________________

pypVectorLength = pypIntExpr

pypVector1  = Literal("[").setParseAction(lambda s, l, t:
                StaticVectorDef(isItemBased=False)) \
            - Optional(pypVectorLength - Optional(pypSizeUnitDef)) \
            - Suppress(Literal("]"))

pypVector2  = Literal("[[").setParseAction(lambda s, l, t:
                StaticVectorDef(isItemBased=True)) \
            - Optional(pypVectorLength) \
            - Suppress(Literal("]]"))

pypVector = pypVector2 | pypVector1

def parseVector(s, l, t):
    if len(t) >= 2:
        t[0].length = t[1]
    # add unit of length if one has been specified
    if len(t) >= 3:
        t[0].lengthUnit = t[2]
    return t[0]

pypVector.setParseAction(parseVector)

# _____

pypSelfContVector1  = Literal("<").setParseAction(lambda s, l, t:
                        DynamicVectorDef(isItemBased=False)) \
                    - pypIntExprOrRange \
                    - Optional(pypSizeUnitDef) \
                    - Suppress(Literal(">"))

pypSelfContVector2  = Literal("<<").setParseAction(lambda s, l, t:
                        DynamicVectorDef(isItemBased=True)) \
                    - pypIntExprOrRange \
                    - Suppress(Literal(">>"))

pypSelfContVector = pypSelfContVector2 | pypSelfContVector1

def parseSelfContVector(s, l, t):
    indexLen = sum([1 if isinstance(i, IntElement) else 0 for i in t])
    if indexLen == 1:
        t[0].lengthMin = IntLiteral(0)
        t[0].lengthMax = t[1]
    elif indexLen == 2:
        t[0].lengthMin = t[1]
        t[0].lengthMax = t[2]
    else:
        raise Exception('Invalid index range for vector')
    # add unit of length if one has been specified
    if isinstance(t[-1], SizeDef):
        t[0].lengthUnit = t[-1]
    return t[0]

pypSelfContVector.setParseAction(parseSelfContVector)

# _____

pypVectorDef = pypVector | pypSelfContVector


# _____________________________________________________________________________
#
# Select/Case
# _____________________________________________________________________________

pypCase = pypKeywordCase \
        - pypIdentifierList \
        - Suppress(Literal(":")) \
        - pypStructVarDefs
pypCase.setParseAction(lambda s, l, t: CaseDef(t[1], t[2:]))


pypDefaultCase  = pypKeywordDefault \
                - Suppress(Literal(":")) \
                - pypStructVarDefs
pypDefaultCase.setParseAction(lambda s, l, t: DefaultCaseDef(t[1:]))

pypCases = ZeroOrMore(pypCase) + Optional(pypDefaultCase)

pypSelectTest = pypIdentifier

pypSelect = pypKeywordSelect - Block('()', pypSelectTest) - Block('{}', pypCases)
pypSelect.setParseAction(lambda s, l, t: SelectDef(t[1], t[2:]))


# _____________________________________________________________________________
#
# Size
# _____________________________________________________________________________

pypSize = pypIntExpr | pypIdentifier

pypSizeDef  = Suppress(Literal('(')) \
            - pypSize \
            - Optional(pypSizeUnitDef) \
            - Suppress(Literal(')'))

def parseSizeDef(s, l, t):
    if len(t) == 2:
        size = t[1]
        size.setSize(t[0])
    else:
        size = SizeDef(t[0])
    return size

pypSizeDef.setParseAction(parseSizeDef)


# _____________________________________________________________________________
#
# Type Parametrization
# _____________________________________________________________________________

# -----------------------------------------------------------------------------
# EBNF: 
# -----------------------------------------------------------------------------
pypTypeParameterName = get_pypIdentifier('parameter name')


# -----------------------------------------------------------------------------
# EBNF: 
# -----------------------------------------------------------------------------
pypTypeParameterValue = pypIntExpr | Word(alphas, alphanums + "_")

pypTypeParameterValue.setName('parameter value')


# -----------------------------------------------------------------------------
# EBNF: TypeParameterChoice = TypeParameterName, "=", TypeParameterValue;
# -----------------------------------------------------------------------------
pypTypeParameterChoice = \
        pypTypeParameterName \
        - Suppress(Literal('=')) \
        - pypTypeParameterValue

pypTypeParameterChoice.setParseAction(lambda s, l, t: {t[0]: t[1]})


# -----------------------------------------------------------------------------
# EBNF: TypeParameterChoiceList =
#               "<", TypeParameterChoice, { (",", TypeParameterChoice) }, ">";
# -----------------------------------------------------------------------------
pypTypeParameterChoiceList = \
        Suppress(Literal('<')) \
        - pypTypeParameterChoice \
        + ZeroOrMore(Suppress(Literal(",")) - pypTypeParameterChoice) \
        - Suppress(Literal('>'))

pypTypeParameterChoiceList.setParseAction(lambda s, l, t: reduce( \
        lambda x, y: InstanceDef.mergeArgsDisjunct(x, y), t))

pypTypeParameterChoiceList.setFailAction(failHard)


# -----------------------------------------------------------------------------
# EBNF: TypeParametrization = "::", TypeParameterChoiceList;
# -----------------------------------------------------------------------------
pypTypeParametrization = Suppress(Literal('::')) - pypTypeParameterChoiceList

pypTypeParametrization.setParseAction(lambda s, l, t: \
        reduce(lambda x, y: InstanceDef.mergeArgsDisjunct(x, y), t));

# _____________________________________________________________________________
#
# Constdefs
# _____________________________________________________________________________

pypLiteralConstAssign = Literal('=')

pypConstDef = Suppress(pypKeywordConst) \
            - pypIdentifier \
            - Suppress(pypLiteralConstAssign) \
            - pypIntExpr \
            - pypLineTerm \

pypConstDef.setParseAction(lambda s, l, t: ConstDef(t[0], t[1]))


# _____________________________________________________________________________
#
# Typedefs
# _____________________________________________________________________________


pypAliasTypeName = pypIdentifier.copy()
pypAliasTypeName.setParseAction(lambda s, l, t: InstanceDef(t[0]))

pypAlias = pypAliasTypeName + Optional(pypTypeParametrization)

def parseParametrizedTypeName(s, l, t):
    if len(t) > 1:
        t[0].setArgs(t[1])
    return t[0]
    
pypAlias.setParseAction(parseParametrizedTypeName);

pypType = pypStruct ^ pypEnum ^ pypAlias

# Don't allow two size definitions follow each other
pypVectorOrSizeDef = pypVectorDef | (pypSizeDef + ~FollowedBy(pypSizeDef))

pypTypeExtensions   = ZeroOrMore(pypVectorOrSizeDef)


pypTypeDef  = pypType \
            - pypIdentifier \
            - pypTypeExtensions \
            - pypLineTerm

def parseTypeDef(s, l, t):

    # the type
    var = t[0]

    # definition name
    var.name = t[1]

    # vectors, wrappers, etc.
    for e in t[2:]:
        if isinstance(e, WrapperDef):
            var = e.embedElement(var)
        elif isinstance(e, SizeDef):
            var.setSize(e)
    var.tplLineNo = getLineNumber(s, l)
    return var

pypTypeDef.setParseAction(parseTypeDef)


pypFile = ZeroOrMore(pypConstDef | pypTypeDef) + stringEnd


# _____________________________________________________________________________
#
# Struct Vardefs
# _____________________________________________________________________________

# TODO: Allow extern definitions to give a link, e.g. "extern(../myx) uint8 x;"

pypStructVarQualifier = \
        pypKeywordExtern | \
        pypKeywordOptional | \
        pypKeywordDistinctive


pypInstanceTypeName = pypIdentifier.copy()
pypInstanceTypeName.setParseAction(lambda s, l, t: InstanceDef(t[0]))

pypInstance = pypInstanceTypeName + Optional(pypTypeParametrization)


pypStructVarType = pypStruct | pypEnum | pypSelect | pypInstance

pypStructVarTypeExtensions = ZeroOrMore(pypVectorOrSizeDef)

pypStructVarDef = Optional(pypStructVarQualifier) \
                + pypStructVarType \
                - Optional(pypIdentifier) \
                - pypStructVarTypeExtensions \
                - pypLineTerm

def parseStructVarDef(s, l, t):
    i = (i for i, x in enumerate(t) if isinstance(x, TypeDef)).next()
    var = t[i]
    # assign member modifiers
    if pypKeywordExtern in t[:i]:
        var.setFlagExtern() 
    if pypKeywordOptional in t[:i]:
        var.setFlagOptional()
    if pypKeywordDistinctive in t[:i]:
        var.setFlagDistinctive()
    # assign name if one has been given
    if len(t) > i + 1 and isinstance(t[i + 1], str):
        var.name = t[i + 1]
    # apply vector, size, and fragment definitions
    for e in t[i + 1:]:
        if isinstance(e, WrapperDef):
            var = e.embedElement(var)
        elif isinstance(e, SizeDef):
            var.setSize(e)
    var.tplLineNo = getLineNumber(s, l)
    return var

pypStructVarDef.setParseAction(parseStructVarDef)

pypStructVarDefs << ZeroOrMore(pypStructVarDef)


#
# _____________________________________________________________________________
#
def printError(text, lineno, col, msg):
    lines = text.split('\n')
    print('Error in line {0}: {1}'.format(lineno, msg))
    print(lines[lineno - 1])
    print('{0}^'.format(' ' * (col - 1)))


#
# _____________________________________________________________________________
#
def removeComments(text):
    return '\n'.join(reduce(lambda x, y: x + y,
        [pypLine.parseString(line).asList() for line in text.split('\n')]))


#
# _____________________________________________________________________________
#
def parse(text):

    typedefs = TypeDefCollection()
    typedefs.addDefs(pypFile.parseString(removeComments(text)).asList())
    return typedefs    


