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

from collections import Set
from itertools import count
from core import *

# TODO: generate separate .cpp and .h files


#
# _____________________________________________________________________________
#
def indent(str, level=1):
    lines = [' '*(4 if s else 0)*level + s for s in str.split('\n')]
    return '\n'.join(lines)



class CodeObject(object):

    @staticmethod
    def indent(text, level=1):
        indented = [' '*(4 if s else 0)*level + s for s in text.split('\n')]
        return '\n'.join(indented)

    @staticmethod
    def objectify(code):
        if code is None:
            return None
        elif isinstance(code, CodeObject):
            return code
        elif isinstance(code, str):
            return SourceCode(code)
        elif isinstance(code, list):
            return CodeBlock([objectify(f) for f in code])
        else:
            raise Exception('Cannot objectify ' + str(code))

    def __init__(self):
        self.includes = set()
        self.resetComment()

    def requires(self, *objects):
        includes = set(self.includes)
        for obj in objects:
            if isinstance(obj, CodeObject):
                includes.update(obj.requires())
            elif isinstance(obj, list):
                pass
            elif obj is not None:
                raise Exception('Cannot extract what is required by ' + str(obj))
        return includes

    def addDependency(self, dep):
        self.includes.update([dep])

    def setComment(self, comment):
        self.comment = Comment(comment) if comment else None

    def resetComment(self):
        self.setComment(None)

    def getComment(self):
        return self.comment

    def getCommentStr(self):
        src = str(self.getComment()) + '\n' if self.getComment() else ''
        return src
    
    def getSpacing(self):
        return getattr(self, 'spacing', 0)

    def setSpacing(self, spacing):
        self.spacing = spacing    
        

class SourceCode(CodeObject):
    
    def __init__(self, code):
        CodeObject.__init__(self)
        self.code = str(code)

    def __str__(self):
        # add code of previous-level code object
        return self.getCommentStr() + self.code


class CodeBlock(CodeObject):
    
    def __init__(self, fragments=None):
        CodeObject.__init__(self)
        self.resetFragments()
        self.addFragments(fragments)
        self.setInnerSpacing('\n')

    def __str__(self):
        # add code of previous-level code object
        src = self.getCommentStr()
        return src + self.getInnerSpacing().join(
                [str(f) for f in self.fragments])

    def getInnerSpacing(self):
        return self.innerSpacing

    def setInnerSpacing(self, delim):
        self.innerSpacing = delim

    def requires(self):
        incs = CodeObject.requires(self)
        for c in self.fragments:
            incs.update(c.requires())
        return incs

    def resetFragments(self):
        self.fragments = []

    def addFragment(self, fragment):
        if not fragment is None:
            f = CodeObject.objectify(fragment)
            self.fragments += [f]
            return f
        else:
            return None

    def addFragments(self, fragments):
        if not fragments is None:
            for f in fragments:
                self.addFragment(f)        


class CodeFile(CodeBlock):

    def __init__(self):
        CodeBlock.__init__(self)
        self.setInnerSpacing('\n'*3)

    def __str__(self):
        # add code of previous-level code object
        src = self.getCommentStr()
        # add the license
        src += '/* LICENSE */\n\n'
        # add the list of includes
        requires = self.requires()
        src += '\n'.join([self.formInclude(s) for s in requires])
        if len(requires) > 0:
            src += '\n\n\n'
        # add the individual code fragments
        src += CodeBlock.__str__(self)
        return src

    def formInclude(self, inc):
        if inc[0] == '<' and inc[-1] == '>':
            return '#include {0}'.format(inc)
        else:
            return '#include "{0}"'.format(inc)


class Comment(CodeObject):

    def __init__(self, commentText):
        CodeObject.__init__(self)
        self.commentText = str(commentText)

    def __str__(self):
        # add code of previous-level code object
        return self.getCommentStr() + '/* {0} */'.format(self.commentText)


class VarType(CodeObject):

    @staticmethod
    def getUINT8():
        varType = VarType('uint8_t')
        varType.includes.update(['<inttypes.h>'])
        return varType

    def __init__(self, varType):
        CodeObject.__init__(self)
        self.varType = str(varType)

    def __str__(self):
        # add code of previous-level code object
        return self.getCommentStr() + self.varType


class VarDef(CodeObject):

    def __init__(self, varType, name=None, default=None):
        CodeObject.__init__(self)
        if isinstance(varType, VarType):
            self.varType = varType
        else:
            self.varType = VarType(varType)
        self.name = name
        self.default = default

    def __str__(self):
        # add code of previous-level code object
        src = self.getCommentStr()

        src += str(self.varType)
        if self.name:
            src += ' ' + self.name
        if self.default:
            src += ' = ' + str(self.default)
        return src

    def requires(self):
        incs = CodeObject.requires(self)
        incs.update(self.varType.requires())
        return incs


class VarDefLine(VarDef):

    def __init__(self, varType, name=None, default=None):
        VarDef.__init__(self, varType, name, default)

    def __str__(self):
        return VarDef.__str__(self) + ';'


class IfThenElse(CodeObject):

    def __init__(self, blIf, blThen=None, blElse=None):
        CodeObject.__init__(self)
        self.blIf = CodeObject.objectify(blIf)
        self.blThen = CodeObject.objectify(blThen)
        self.blElse = CodeObject.objectify(blElse)

    def __str__(self):
        # add code of previous-level code object
        comment = self.getCommentStr()
        if comment:
            comment = ' ' + comment

        form = 'if ({0}) {{{3}\n{2}{1}{2}}}'
        strIf = str(self.blIf) if self.blIf else ''
        strThen = indent(str(self.blThen)) + '\n' if self.blThen else ''
        space = '\n' * self.getSpacing()

        src = form.format(strIf, strThen, space, comment)

        if self.blElse:
            if isinstance(self.blElse, IfThenElse):
                src += ' else ' + str(self.blElse)
            else:
                form = ' else {{\n{1}{0}{1}}}'
                src += form.format(str(self.blElse), space)

        return src

    def addFragmentThenBranch(self, fragment):
        if not self.blThen:
            self.blThen = CodeBlock()
        self.blThen.addFragment(fragment)

    def addFragmentElseBranch(self, fragment):
        if not self.blElse:
            self.blElse = CodeBlock()
        self.blElse.addFragment(fragment)

    def setElseBranch(self, branch):
        self.blElse = branch

    def addElseIf(self, blElseIf):
        elseIf = IfThenElse(blElseIf)
        elseIf.setSpacing(self.getSpacing())
        self.setElseBranch(elseIf)
        return elseIf

    def addElse(self):
        blElse = CodeBlock()
        blElse.setSpacing(self.getSpacing())
        self.setElseBranch(blElse)
        return blElse

    def requires(self):
        incs = CodeObject.requires(self)
        incs.update(self.blIf.requires())
        if self.blThen:
            incs.update(self.blThen.requires())
        if self.blElse:
            incs.update(self.blElse.requires())
        return incs


class Function(CodeObject):

    def __init__(self, name, rettype=None, pars=None, const=False):
        CodeObject.__init__(self)
        self.name = name
        self.rettype = rettype
        self.pars = pars
        self.const = const
        self.body = CodeBlock()

    def __str__(self):
        # add code of previous-level code object
        src = self.getCommentStr()

        form = '{0} {1}({2}) {3}{{\n{4}}}'
        rettype = str(self.rettype) if self.rettype else 'void'
        name = str(self.name)
        pars = ', '.join([str(p) for p in self.pars]) if self.pars else ''
        body = '\n' + indent(str(self.body)) + '\n' if str(self.body) else ''
        const = 'const ' if self.const else ''
        return src + form.format(rettype, name, pars, const, body)

    def requires(self):
        return CodeObject.requires(self, self.pars, self.body, self.rettype)

    def getBody(self):
        return self.body


class Constructor(Function):

    def __init__(self, name, pars=None, initList=None):
        Function.__init__(self, name, None, pars, False)
        self.initList = initList if not initList is None else []

    def __str__(self):
        # add code of previous-level code object
        src = self.getCommentStr()

        form = '{0}({1}){2} {{\n\n{3}\n}}'
        name = str(self.name)
        pars = ', '.join([str(p) for p in self.pars]) if self.pars else ''
        initList = ' : ' + ', '.join(str(init)
                for init in self.initList) if len(self.initList) else ''
        body = indent(str(self.body)) if self.body else ''
        return src + form.format(name, pars, initList, body)

    def requires(self):
        return CodeObject.requires(self, self.pars, self.initList, self.body)

    def prependInitialization(self, init):
        self.initList.insert(0, CodeObject.objectify(init))


class Class(CodeObject):

    def __init__(self, name, inheritsFrom=None):
        CodeObject.__init__(self)
        self.name = name
        self.inheritsFrom = inheritsFrom if not inheritsFrom is None else []
        self.body = CodeBlock()
        self.body.setInnerSpacing('\n'*3)

    def __str__(self):
        # add code of previous-level code object
        src = self.getCommentStr()

        form = 'class {0}{1} {{\n\n{2}\n}};'
        name = str(self.name)
        inheritsFrom = ' : ' + ', '.join('{0} {1}'.format(a, b) 
                for a, b in self.inheritsFrom) if len(self.inheritsFrom) else ''
        body = indent(str(self.body)) if self.body else ''
        return src + form.format(name, inheritsFrom, body)

    def requires(self):
        return CodeObject.requires(self, self.inheritsFrom, self.body)

    def getBody(self):
        return self.body

    def addInheritance(self, inheritsFrom):
        self.inheritsFrom += [inheritsFrom]



#
# _____________________________________________________________________________
#

srcDataUnitHeader               = 'DataUnit.h'
strOpaqueFieldClass             = 'OpaqueField'
strOpaqueFieldHeader            = 'OpaqueField.h'
strEnumerationFieldClass        = 'EnumerationField'
strEnumerationFieldHeader       = 'EnumerationField.h'
strInternalNodeClass            = 'InternalNode'
strInternalNodeHeader           = 'InternalNode.h'
strStaticVectorDataUnitClass    = 'StaticVectorDataUnit'
strStaticVectorDataUnitHeader   = 'StaticVectorDataUnit.h'
strStreamVectorDataUnitClass    = 'StreamVectorDataUnit'
strStreamVectorDataUnitHeader   = 'StreamVectorDataUnit.h'


#
# _____________________________________________________________________________
#

#
#
#
def genCodeCpp_generateCodeCpp_TypeDefCollection(self):

    code = CodeFile()

    # some (hopefully) temporary hack
    code.addDependency(strOpaqueFieldHeader)

    for t in self.getTypeDefs():
        if isinstance(t, BuiltInDef):
            t.applyCppClassName()
        elif not isinstance(t, ConstDef):
#            print('Generating code for {0}...'.format(t.getName()))
            code.addFragment(t.generateCode())
#            try:
#                code.addFragment(t.generateCode())
#            except Exception as e:
#                raise Exception('While generating code for type "{0}": {1}' \
#                        .format(t.getName(), str(e)))

    return code

TypeDefCollection.generateCodeCpp = genCodeCpp_generateCodeCpp_TypeDefCollection


#
# _____________________________________________________________________________
#

#
# Generate a C++ object representing a data size definition
#
def genCodeCpp_generateCodeCpp_SizeDef(self):
    size = self.getSize()
    if not size:
        raise Exception("Invalid size")
    bitScale = self.getBitScale()
    if bitScale == 1:
        return 'BC(0, {0})'.format(size)
    elif bitScale == 8:
        return 'BC({0}, 0)'.format(size)
    else:
        raise Exception("Unknown bit scale")    

SizeDef.generateCodeCpp = genCodeCpp_generateCodeCpp_SizeDef


#
# _____________________________________________________________________________
#

#
# Propose a name for the C++ class representing this type def
#
def genCodeCpp_getCppClassNameProposal_TypeDef(self):
    # generally, the class name consists of the type
    # (struct, enum, etc.) followed by the type defs name. 
    return 'T{0}_{1}'.format(self.getType(), self.getName())

TypeDef.getCppClassNameProposal = genCodeCpp_getCppClassNameProposal_TypeDef


#
# Set the name for the C++ class representing this type def
#
def genCodeCpp_setCppClassName_TypeDef(self, className):
    self.cppClassName = className

TypeDef.setCppClassName = genCodeCpp_setCppClassName_TypeDef


#
# Return the name of the C++ class representing this type
# def. Returns None if no class / class name exists
#
def genCodeCpp_getCppClassName_TypeDef(self):
    return getattr(self, 'cppClassName', None)

TypeDef.getCppClassName = genCodeCpp_getCppClassName_TypeDef


#
# Apply the name for the C++ class representing this type def
#
def genCodeCpp_applyCppClassNameProposal_TypeDef(self):
    proposal = self.getCppClassNameProposal()
    if proposal:
        self.setCppClassName(proposal)
    return self.getCppClassName()

TypeDef.applyCppClassNameProposal = genCodeCpp_applyCppClassNameProposal_TypeDef


#
# Resolve symbols
#
def genCodeCpp_resolveSymbols(args, symbols):
    if args is None:
        args = {}
    if symbols is None:
        symbols = {}
    resolved = {}
    symbolKeys = [key for key in args.iterkeys() \
            if isinstance(args[key], IntSymbol)]
    for key in args.iterkeys():
        if isinstance(args[key], IntSymbol):
            if args[key].getName() in symbols.iterkeys():
                resolved[key] = symbols[args[key].getName()]
            else:
                raise TPLError('Unknown symbol "{0}", Known: {1}'.format(args[key].getName(), ', '.join(symbols.iterkeys())))
        else:
            resolved[key] = args[key]
    return resolved


#
# Return the arguments/parameters for the C++ class instantiation as list
#
def genCodeCpp_getCppClassArgs_TypeDef(self, args=None, symbols=None):
    classArgs = getattr(self, 'cppClassArgs', [])
    classArgDefaults = getattr(self, 'cppClassArgDefaults', {}).copy()
    if args:
        classArgDefaults.update(args)

    # replace any symbol in the list of class arguments by its corresponding
    # C++ variable name
    classArgDefaults = genCodeCpp_resolveSymbols(classArgDefaults, symbols)

    return [s.format(**classArgDefaults) for s in classArgs]

TypeDef.getCppClassArgs = genCodeCpp_getCppClassArgs_TypeDef


#
# Return the arguments/parameters for the C++ class instantiation as string
#
def genCodeCpp_getCppClassArgsStr_TypeDef(self, args=None, symbols=None):
    return ', '.join(self.getCppClassArgs(args, symbols))

TypeDef.getCppClassArgsStr = genCodeCpp_getCppClassArgsStr_TypeDef


#
#
#
def genCodeCpp_getClassInstantiation_TypeDef(self, pointerName, args=None, symbols=None):
    className = self.getCppClassName()
    if className:
        classParams = self.getCppClassArgsStr(args, symbols)
        newInstance = 'new {0}({1})'.format(className, classParams)
        if pointerName:
            instanceCode = CodeObject.objectify('{0}* {1} = {2};'.format(
                    className, pointerName, newInstance))
        else:
            instanceCode = newInstance
    else:        
        instanceCode = self.getEmbeddedClassInstantiation(
                pointerName, args, symbols)
    return instanceCode

TypeDef.getClassInstantiation = genCodeCpp_getClassInstantiation_TypeDef


#
#
#
def genCodeCpp_prepareClass_TypeDef(self, inheritsFrom):

    cppClassName = self.applyCppClassNameProposal()

    myClass = Class(cppClassName)
    myClass.setComment('Definition of class "{0}" corresponding to {1} "{2}"' \
            .format(cppClassName, self.getType(), self.getName()))

    myClass.getBody().addFragment("public:")

    # generate type descriptor infrastructure
    typeDesc = Function('typeDescriptor',
            VarType('static inline const TypeDescriptor&'), None)
    typeDesc.addDependency(srcDataUnitHeader)
    typeDesc.setComment('Static function returning type descriptor of class "{0}"'.format(cppClassName))
    typeDesc.getBody().addFragment(
            ('static const TypeDescriptor desc({0}::typeDescriptor(),' \
                    + ' {1}, "{2}");').format(
                            inheritsFrom, self.getTypeID(), self.getName()))
    typeDesc.getBody().addFragment('return desc;')
    myClass.getBody().addFragment(typeDesc)

    getTypeDesc = Function('getTypeDescriptor',
            VarType('const TypeDescriptor&'), None, True)
    getTypeDesc.addDependency(srcDataUnitHeader)
    getTypeDesc.setComment('Function returning type descriptor of class "{0}"'.format(cppClassName))
    getTypeDesc.getBody().addFragment('return typeDescriptor();')
    myClass.getBody().addFragment(getTypeDesc)


    # set the list of class parameters 
    self.cppClassArgs = ['{{{0}}}'.format(p) for p in self.getParamList()]
    self.cppClassSymbols = {var: '_classparam_{0}'.format(var) \
            for var in self.getParamList()} 

    # generate class member fields corresponding to class parameters
    for p in self.getParamList():        
        f = VarDefLine('int', self.cppClassSymbols[p])  
        f.setComment('Class parameter "{0}"'.format(p))
        myClass.getBody().addFragment(f)

    # generate constructor
    params = [VarDef('int', p) for p in self.getParamList()]
    initList = ['{0}({1})'.format(self.cppClassSymbols[p], p) \
            for p in self.getParamList()]
    myConstructor = Constructor(cppClassName, params, initList)
    myConstructor.setComment('Default constructor of class "{0}"'.format(cppClassName))
    myConstructor.getBody().addFragment(
            'this->setName("{0}");'.format(self.getName()))

    size = self.getSize()
    if size:
        myConstructor.getBody().addFragment(
                'this->dissector().setSize({0});'.format(size.generateCodeCpp()))

    myClass.getBody().addFragment(myConstructor)

    #myClass.getBody().addFragment(getTypeNameFunc)

    # generate class cloning method
    newInst = Function('newInstance_',
            VarType(cppClassName + '*'), None, True)
    newInst.setComment('Function to create another instance of class "{0}"'.format(cppClassName))
    newInst.getBody().addFragment(self.getClassInstantiation('du', self.cppClassSymbols))
    newInst.getBody().addFragment('return du;')
    myClass.getBody().addFragment(newInst)

    # class environment
    myClassEnvironment = CodeBlock()
    myClassEnvironment.addFragment(Comment('=' * 73))    
    myClassEnvironment.addFragment('')
    myClassEnvironment.addFragment(myClass)    
    myClassEnvironment.addFragment('')
    #myClassEnvironment.addFragment(typeNameVarDef)

    # return class and constructor
    return myClassEnvironment, myClass, myConstructor

TypeDef.prepareClass = genCodeCpp_prepareClass_TypeDef


#
# _____________________________________________________________________________
#

#
#
#
def genCodeCpp_applyCppClassName_BitDef(self):
    self.setCppClassName('OpaqueField')
    self.cppClassArgs = ['BC(0, 1)']

BitDef.applyCppClassName = genCodeCpp_applyCppClassName_BitDef

#
#
#
def genCodeCpp_applyCppClassName_ByteDef(self):
    self.setCppClassName('OpaqueField')
    self.cppClassArgs = ['BC(1, 0)']

ByteDef.applyCppClassName = genCodeCpp_applyCppClassName_ByteDef

#
#
#
def genCodeCpp_applyCppClassName_OpaqueDef(self):
    self.setCppClassName('OpaqueField')
    self.cppClassArgs = ['BC({nbytes}, {nbits})']
    self.cppClassArgDefaults = {'nbytes': 0, 'nbits': 0}

OpaqueDef.applyCppClassName = genCodeCpp_applyCppClassName_OpaqueDef

#
#
#
def genCodeCpp_applyCppClassName_UIntDef(self):
    self.setCppClassName('IntegerField')
    self.cppClassArgs = ['BC(0, {0})'.format(self.getIntBitWidth()), 'false']

UIntDef.applyCppClassName = genCodeCpp_applyCppClassName_UIntDef

#
#
#
def genCodeCpp_applyCppClassName_SIntDef(self):
    self.setCppClassName('IntegerField')
    self.cppClassArgs = ['BC(0, {0})'.format(self.getIntBitWidth()), 'true']

SIntDef.applyCppClassName = genCodeCpp_applyCppClassName_SIntDef


#
# _____________________________________________________________________________
#

#
#
#
def genCodeCpp_getClassInstantiation_OpaqueDef(self, pointerName, args=None, symbols=None):
    if len(args):
        instArgs = args
    else:
        instArgs = {'nbytes': -1}
    opaqueInst = TypeDef.getClassInstantiation(self, pointerName, instArgs, symbols)
    if isinstance(instArgs.get('nbytes'), IntSymbol) \
            or isinstance(instArgs.get('nbits'), IntSymbol):
        opaqueInstBlock = CodeBlock()
        opaqueInstBlock.addFragment(opaqueInst)
        opaqueInstBlock.addFragment('{0}->propSet<int>("_dynlen", 1); // from genCodeCpp_getClassInstantiation_OpaqueDef' \
                .format(pointerName))
        return opaqueInstBlock
    return opaqueInst

OpaqueDef.getClassInstantiation = genCodeCpp_getClassInstantiation_OpaqueDef


#
# _____________________________________________________________________________
#

#
#
#
def genCodeCpp_getClassInstantiation_InstanceDef(self, pointerName, args=None, symbols=None):
    referredDef = self.getTypeDefCollection()[self.getTypeName()]

    instantiation = CodeBlock()
    instantiation.addFragment(referredDef.getClassInstantiation(
        pointerName, self.getArgs(args), symbols))

    # TODO: consider size
    size = self.getSize()
    if size:
        if pointerName:
            if isinstance(size.getSize(), IntSymbol):
                # resolve size symbol 
                cppSizeVar = genCodeCpp_resolveSymbols({'sizeVar': \
                    IntSymbol(size.getSize().getName())}, symbols)['sizeVar']
                instantiation.addFragment('{0}->propSet<int>("_dynlen", 1); // from genCodeCpp_getClassInstantiation_InstanceDef' \
                        .format(pointerName))
            instantiation.addFragment('{0}->dissector().setSize({1});' \
                    .format(pointerName, cppSizeVar))
        else:
            raise TPLError('Cannot set size in embedded instantiations')

    return instantiation

InstanceDef.getClassInstantiation = genCodeCpp_getClassInstantiation_InstanceDef


#
# _____________________________________________________________________________
#

#
#
#
def genCodeCpp_generateCode_EnumDef(self):

    classEnvironment, enumClass, enumConstructor = \
            self.prepareClass('EnumerationField')
    enumClass.addInheritance(('public', strEnumerationFieldClass))
    enumClass.addDependency(strEnumerationFieldHeader)
    bitWidth = self.getEnumBitWidth()
    enumConstructor.prependInitialization(
            'EnumerationField(BC(0, {0}), staticList_)'.format(bitWidth))

    # add enumeration items

    enumClass.getBody().addFragment(
            VarDefLine('static EnumerationItemList', 'staticList_'))

    # enum item ids
    enumItemIds = CodeBlock()
    enumItemIdClassDefs = CodeBlock()

    # find length of the longest item name to allow for pretty formatting
    strWidth = max([len(item.getName()) for item in self.getItems() \
            if item.getName() is not None])

    makeList = CodeBlock()
    for item in self.getItems():
        if isinstance(item, EnumItem):
            # ignore anonymous items
            if item.getName() is None:
                continue
            if item.isRange():
                #makeList.addFragment(
                #    'id_{0:{3}} = staticList_.addItem("{0:{3}}", {1}, {2});' \
                #        .format(item.getName(), item.getMinCodeValue(),
                #            item.getMaxCodeValue(), strWidth))
                makeList.addFragment(
                    'staticList_.addItem("{0:{3}}", {1}, {2});' \
                        .format(item.getName(), item.getMinCodeValue(),
                            item.getMaxCodeValue(), strWidth))
            else:
                #makeList.addFragment(
                #    'id_{0:{2}} = staticList_.addItem("{0}"{3}, {1});'.format(
                #    item.getName(), item.getMinCodeValue(), strWidth,
                #    ' ' * (strWidth - len(item.getName()))))
                makeList.addFragment(
                    'staticList_.addItem("{0}"{3}, {1});'.format(
                    item.getName(), item.getMinCodeValue(), strWidth,
                    ' ' * (strWidth - len(item.getName()))))
            #enumItemIds.addFragment(VarDefLine(
            #    'int', '{0}::id_{1}'.format(enumClass.name, item.getName())))
            #enumItemIdClassDefs.addFragment(VarDefLine(
            #    'static int', 'id_{1}'.format(enumClass.name, item.getName())))
        elif isinstance(item, EnumItemFallback):
            if item.getName():
                idPrefix = 'id_{0} = '.format(item.getName())
                enumItemIds.addFragment(VarDefLine('int', 
                    '{0}::id_{1}'.format(enumClass.name, item.getName())))
                #enumItemIdClassDefs.addFragment(VarDefLine('static int', 
                #    'id_{0}'.format(item.getName())))
            else:
                idPrefix = ''
            #makeList.addFragment('{0}staticList_.addFallbackItem("{1}");' \
            #        .format(idPrefix, item.getName()))
            makeList.addFragment('staticList_.addFallbackItem("{1}");' \
                    .format(None, item.getName()))
        else:
            raise TPLError('Failed to generate code for enumeration item "{0}"' \
                .format(item.getName()))

    enumClass.getBody().addFragment(enumItemIdClassDefs)

    singleton = IfThenElse('staticList_.getNItems() == 0', makeList)

    enumConstructor.getBody().addFragment('')
    enumConstructor.getBody().addFragment(Comment(
        'Populate class-specific, static list of ' + \
        'enumeration items if not yet done'))
    enumConstructor.getBody().addFragment(singleton)

    classEnvironment.addFragment('')
    staticVarDef = VarDefLine('EnumerationItemList',
        '{0}::staticList_'.format(enumClass.name))
    staticVarDef.setComment('List of enumeration items for ' + \
        'enumeration class "{0}"'.format(enumClass.name))
    classEnvironment.addFragment(staticVarDef)
    
    #classEnvironment.addFragment('')
    #enumItemIds.setComment('Variables to hold IDs of enumeration items for ' + \
    #    'enumeration class "{0}"'.format(enumClass.name))
    #classEnvironment.addFragment(enumItemIds)

    return classEnvironment

EnumDef.generateCode = genCodeCpp_generateCode_EnumDef


#
# _____________________________________________________________________________
#

#
#
#
def genCodeCpp_generateCode_StructDef(self):

    classEnvironment, structClass, structConstructor = \
            self.prepareClass('InternalNode')
    structClass.addInheritance(('public', strInternalNodeClass))
    structClass.addDependency(strInternalNodeHeader)
    structConstructor.prependInitialization('InternalNode()')

    # add function to expand InternalNode
    structClass.getBody().addFragment(self.generateCodeExpand())

    # add function to encode InternalNode
    structClass.getBody().addFragment(self.generateCodeEncode())

    # add function to return distinctive name
    if len([m for m in self.getMembers() if m.getFlagDistinctive()]) > 0:
        structClass.getBody().addFragment(self.generateCodeDistinctive())

    # Empty structs are expanded from the very beginning
    if self.getNMembers() == 0:
        structConstructor.getBody().addFragment('this->setExpanded();')

    # TODO: add function to infer select cases
    # structClass.getBody().addFragment(self.generateCodeInferCases())

    return classEnvironment

StructDef.generateCode = genCodeCpp_generateCode_StructDef


#
#
#
def genCodeCpp_generateCodeMemberInstantiation_StructDef(self, iMember, pointerPrefix='', symbols=None):
    member = self[iMember]
    memberPointer = '{0}_M{1}'.format(pointerPrefix, iMember)
    code = CodeBlock()
    code.setComment('===== Struct member "{0}" ====='.format(member.getName()))
    code.addFragment(member.getClassInstantiation(memberPointer, None, symbols))
    code.addFragment('this->appendChildRenamed({0}, "{1}");'.format(
            memberPointer, member.getName()))
    return code    

StructDef.generateCodeMemberInstantiation = genCodeCpp_generateCodeMemberInstantiation_StructDef


#
#
#
def genCodeCpp_generateCodeExpand_StructDef(self):

    # name of C++ variable to indicate that expansion is complete
    doneVarName = 'complete'

    # signature of the "expand_" function
    expandPars  = [VarDef('size_t', 'len')]
    expandPars += [VarDef('size_t', 'decoded')]
    expandPars += [VarDef('bool', 'dry')]
    expandPars += [VarDef('bool', 'ahead')]
    expand = Function('expand_', VarType('bool'), expandPars)

    expandBody = expand.getBody()

    # add definition of C++ variable indicating whether expansion is complete 
    doneVar = CodeBlock()
    doneVar.addFragment('bool {0} = false;'.format(doneVarName))
    doneVar.setComment('will be set to true once expansion is complete')
    expandBody.addFragment(doneVar)

    guard = IfThenElse('len == 0')
    guard.setSpacing(1)
    currentGuard = guard

    loadedVars = {}
    decodedVar = -1

    for i, m in enumerate(self.getMembers()):

        # determine which local variables the current member depends on
        requiredVars = m.getRequiredSymbols()
        knownVarDefs = m.getKnownSymbols()
        classParams = self.getParamList()
        requiredLocalVars = sorted([self.getMemberIndex(var) \
                for var in requiredVars \
                if knownVarDefs.get(var, None) is self and var not in classParams])
        maxRequiredLocalVar = max([-1] + requiredLocalVars)

        # TODO: support optional members

# ============================================================================================================
#
#        } else if (len == 5 && decoded >= 3 && headIndex == 5) {
#
#            if (!dry) {
#                /* ===== Struct member "compression_method" ===== */
#                TEnum_CompressionMethod* _M5 = new TEnum_CompressionMethod();
#                this->appendChildRenamed(_M5, "compression_method");
#            } else {
#                complete = true;
#            }
#
#        } else if (len == 6 && decoded >= 3 && headIndex == 6) {
#
#            if (!dry) {
#                /* ===== Struct member "extensions" ===== */
#                TStruct_ServerHello_extensions* _M6 = new TStruct_ServerHello_extensions();
#                this->appendChildRenamed(_M6, "extensions");
#                complete = true;
#            } else {
#                complete = true;
#            }
#
#        }
#
# ============================================================================================================

        if maxRequiredLocalVar > decodedVar:
            decodedVar = maxRequiredLocalVar
            currentGuard = currentGuard.addElseIf(
                    'len == {0} && decoded >= {1}' \
                            .format(i, maxRequiredLocalVar + 1))

        instanceFragment = CodeBlock()

        symbols = self.cppClassSymbols.copy()
        for localVar in requiredLocalVars:
            refVarName = self.getMembers()[localVar].getName()
            instanceFragment.addFragment(
                    'int _value_{0} = (*this)[{1}]->propGet<int>(".value");' \
                            .format(refVarName, localVar))
            symbols[refVarName] = '_value_{0}'.format(refVarName)

        memberPointer = '_M{0}'.format(i)
        instanceFragment.addFragment(m.getClassInstantiation(memberPointer, None, symbols))

        currentGuard.addFragmentThenBranch(instanceFragment)

        #continue

        # SelectDef adds member instances by itself
        if not isinstance(m, SelectDef):
            instanceFragment.setComment(
                    '===== Struct member "{0}" ====='.format(m.getName()))
            currentGuard.addFragmentThenBranch(
                    'this->appendChildRenamed({0}, "{1}");'.format(
                            memberPointer, m.getName()))

    currentGuard.addFragmentThenBranch('{0} = true;'.format(doneVarName))

    expandBody.addFragment(guard)
    expandBody.addFragment('return {0};'.format(doneVarName))

    return expand

StructDef.generateCodeExpand = genCodeCpp_generateCodeExpand_StructDef


#
#
#
def genCodeCpp_invertSymbolUsage(typeDef, symbolName, access, valueVarName):

    if isinstance(typeDef, StaticVectorDef) \
            and symbolName == typeDef.getLength().getName():    
        if typeDef.isItemBased:
            # Symbol usage in TPL: "Type name[[symbol]]"
            inverted = IfThenElse('{0} != 0'.format(access))
            inverted.addFragmentThenBranch(
                    '{0} = {1}->getNChildren();'.format(valueVarName, access))
        else:
            # Symbol usage in TPL: "Type name[symbol]"
            inverted = IfThenElse('{0} != 0'.format(access))
            inverted.addFragmentThenBranch(
                    '{0} = {1}->getLength().byteAligned();' \
                            .format(valueVarName, access))
            
    elif isinstance(typeDef, InstanceDef) \
            and isinstance(typeDef.followInstantiation()[0], OpaqueDef) \
            and symbolName == typeDef.getArgs()['nbytes'].getName():
        # Symbol usage in TPL: "opaque name[symbol]"
        inverted = IfThenElse('{0} != 0'.format(access))
        inverted.addFragmentThenBranch(
                '{0} = {1}->getLength().byteAligned();' \
                        .format(valueVarName, access))
    
    elif isinstance(typeDef, SelectDef):
        if symbolName == typeDef.getTestSymbolName():
            # Symbol usage in TPL: "select (symbol) { ... }"
            inverted = None
        else:
            inverted = CodeBlock()
            # TODO: make this branch-dependent
            # inverted.addFragment(VarDefLine('int', 'branch', 'inferCaseBranch_{0}_()'.format(typeDef.getName())))
            for i, c in enumerate(typeDef.getCases()):
                # TODO: make this branch-dependent
                # 'branch == {0}'.format(i)
                # TODO: make this more efficient (don't use operator[] twice)
                caseBranchGuard = IfThenElse('true')
                caseBranchGuard.addFragmentThenBranch(
                        genCodeCpp_invertSymbolUsage(c[0], symbolName, access, valueVarName))
                inverted.addFragment(caseBranchGuard)
    
    elif typeDef.getSize() is not None \
            and symbolName == typeDef.getSize().getSize().getName():
        # Symbol usage in TPL: "Type name(symbol)" 
        inverted = IfThenElse('{0} != 0'.format(access))
        inverted.addFragmentThenBranch(
                '{0} = {1}->getLength().byteAligned();' \
                        .format(valueVarName, access))
    
    else:
        inverted = None
        
    return inverted
    

#
#
#
def genCodeCpp_generateCodeEncode_StructDef(self):

    encode = Function('updateMember_', VarType('bool'), [VarDef('size_t', 'index')])

    encode.getBody().addFragment(VarDefLine('bool', 'ok', 'true'))

    guard = None

    # Check each member in the struct ...
    for i, m in enumerate(self.getMembers()):

        # ... and find subsequent members that depend on them
        listDepend = [dep for dep in self.getMembers()[i:] \
                if m.getName() in dep.getRequiredSymbols()]

        if not len(listDepend):
            # We ignore the member if there is no dependence on it
            continue

        test = 'index == {0}'.format(i)
        if not guard:
            guard = IfThenElse(test)
            currentGuard = guard
        else:
            currentGuard = currentGuard.addElseIf(test)

        if True in [isinstance(dep, SelectDef) for dep in listDepend]:
            currentGuard.addFragmentThenBranch(Comment('{0}: {1} <--- {2}' \
                    .format(i, m.getName(), ', '.join(['f-of-cases-in({0})' \
                            .format(dep.getName()) for dep in listDepend]))))
        else:
            currentGuard.addFragmentThenBranch(Comment('{0}: {1} <--- {2}' \
                    .format(i, m.getName(), ', '.join(['f({0})' \
                            .format(dep.getName()) for dep in listDepend]))))

        # The list of values that the current member should be updated with
        values = []

        # Now infer the type of dependence
        for depMem in listDepend:

            # We will need the member's index in order to refer to it
            depMemIndex = self.getMembers().index(depMem)

            memberAccess = '(*this)[{0}]'.format(depMemIndex)
            valueVarName = '_value_{0}'.format(len(values))

            value = genCodeCpp_invertSymbolUsage(depMem, m.getName(), memberAccess, valueVarName)
            
            if value is not None:
                currentGuard.addFragmentThenBranch(VarDefLine('int',
                        valueVarName, '0'))
                currentGuard.addFragmentThenBranch(value)
                values += [valueVarName]

        if len(values) > 1:
            listSetValueTests = ['{0} == {1}'.format(values[iVal], values[iVal + 1]) for iVal in range(len(values) - 1)]
            setValueTest = ' && '.join(listSetValueTests)
            valueGuard = IfThenElse(setValueTest)
            valueGuard.addFragmentElseBranch('ok = false;')
            currentGuard.addFragmentThenBranch(valueGuard)
        elif len(values) == 1:
            valueGuard = currentGuard        
        else:
            valueGuard = None

        if valueGuard:
            valueGuard.addFragmentThenBranch(
                    '(*this)[{0}]->propSet<int>(".value", {1});'.format(i, values[0]))



    encode.getBody().addFragment(guard)
    encode.getBody().addFragment('return ok;')
    return encode


StructDef.generateCodeEncode = genCodeCpp_generateCodeEncode_StructDef
    

#
#
#
def genCodeCpp_generateCodeDistinctive_StructDef(self):

    code = Function('getDynamicTypeName_', VarType('std::string'), None, True)

    # get a list of all distinctive members making up the dynamic type
    dynamicTypeMembers = [m.getName() \
            for m in self.getMembers() if m.getFlagDistinctive()]

    if len(dynamicTypeMembers) == 1:
        # one single distinctive member
        code.getBody().addFragment(VarDefLine('DataUnit*', 'du', '(*this)[{0}]' \
                .format(self.getMemberIndex(dynamicTypeMembers[0]))))
        code.getBody().addFragment('return (du != 0) ? du->propGetDefault' + \
                '<std::string>(".name", "") : "";')
    else:
        # multiple distinctive members
        code.getBody().addFragment(VarDefLine('std::string', 'dynamicType'))    
        code.getBody().addFragment(VarDefLine('DataUnit*', 'du'))
        for i, mem in enumerate(dynamicTypeMembers):
            if i > 0:
                code.getBody().addFragment('dynamicType += "+";')
            code.getBody().addFragment('du = (*this)[{0}];'.format(
                    self.getMemberIndex(mem)))

            guard = IfThenElse('du != 0')
            guard.addFragmentThenBranch('dynamicType += du->propGetDefault<std::string>(".name", "");')
            code.getBody().addFragment(guard)

        code.getBody().addFragment('return dynamicType;')

    return code


StructDef.generateCodeDistinctive = genCodeCpp_generateCodeDistinctive_StructDef


#
#
#
def genCodeCpp_generateCodeInferCases_StructDef(self):

    listInferFuncs = CodeBlock()

    listSelects = [(i, m) for i, m in enumerate(self.getMembers()) if isinstance(m, SelectDef)]
    for iSelect, select in listSelects:
    
        inferFunc = Function('inferCaseBranch_{0}_'.format(select.getName()), VarType('int'))
        inferFunc.getBody().addFragment(VarDefLine('int', 'offset', '{0}'.format(iSelect)))
        inferFunc.getBody().addFragment(VarDefLine('int', 'branch', '-1'))

        listListTypes = []

        for iCase, case in enumerate(select.getCases()):

            listTypes = []
            for m in case.getMembers():
                if isinstance(m, InstanceDef):
                    listTypes += [m.followInstantiation()[0].getCppClassName()]
                else:
                    listTypes += ['unkown']
            # TODO: this test should not depend on string comparison
            listListTypes += [';'.join(listTypes)]

            inferFunc.getBody().addFragment(Comment(
                    '{0}: {1}'.format(case.getName(), str(listTypes))))

            testFormString = '(*this)[offset + {0}]->isOfType({1}::typeDescriptor())'
            test = ' && '.join([testFormString.format(iType, className) \
                    for iType, className in enumerate(listTypes)])
            guard = IfThenElse(test)
            guard.addFragmentThenBranch('branch = {0};'.format(iCase))

            inferFunc.getBody().addFragment(guard)


        if len(set(listListTypes)) != len(listListTypes):
            raise TPLError(
                    'Indistinguishable case branches in definition of "{0}"' \
                    .format(self.getChainedName('/')))

        inferFunc.getBody().addFragment('return branch;')

        listInferFuncs.addFragment(inferFunc)


    return listInferFuncs

StructDef.generateCodeInferCases = genCodeCpp_generateCodeInferCases_StructDef



#
# _____________________________________________________________________________
#

#
#
#
def genCodeCpp_generateCode_StaticVectorDef(self):

    classEnvironment, vectorClass, vectorConstructor = \
            self.prepareClass('StaticVectorDataUnit'
                    if self.length is not None and self.isItemBased
                    else 'StreamVectorDataUnit')

    if self.length is not None and self.isItemBased:        
        vectorClass.addInheritance(('public', strStaticVectorDataUnitClass))
        vectorClass.addDependency(strStaticVectorDataUnitHeader)
        vectorConstructor.prependInitialization(
                'StaticVectorDataUnit({0})'.format(self.length))
    else:
        vectorClass.addInheritance(('public', strStreamVectorDataUnitClass))
        vectorClass.addDependency(strStreamVectorDataUnitHeader)
        if self.length is not None:
            vectorConstructor.prependInitialization(
                    'StreamVectorDataUnit(BC({0}, 0))'.format(self.length))
        else:
            vectorConstructor.prependInitialization('StreamVectorDataUnit()')

    # set the vector element template
    templatePointer = '_T'
    templateFragment = CodeBlock()
    templateFragment.setComment('set the vector element template')
    templateFragment.addFragment(
            self.getElement().getClassInstantiation(templatePointer))
    templateFragment.addFragment(
            'this->setElementTemplate({0});'.format(templatePointer))
    vectorConstructor.getBody().addFragment(templateFragment)

    return classEnvironment

StaticVectorDef.generateCode = genCodeCpp_generateCode_StaticVectorDef


#
#
#
def genCodeCpp_getEmbeddedClassInstantiation_StaticVectorDef(self, pointerName, args=None, symbols=None):
    if not pointerName:
        raise TPLError('Cannot instantiate vector inline')

    dynlen = True
    code = CodeBlock()
    if self.length is not None:
        if not isinstance(self.getLength(), IntSymbol):
            dynlen = False
        length = genCodeCpp_resolveSymbols({'length': self.getLength()}, symbols)['length']
        if self.isItemBased:
            code.addDependency(strStaticVectorDataUnitHeader)        
            instance = 'new StaticVectorDataUnit({0})'.format(length)
        else:
            code.addDependency(strStreamVectorDataUnitHeader)
            instance = 'new StreamVectorDataUnit(BC({0}, 0))'.format(length)
    else:
        code.addDependency(strStreamVectorDataUnitHeader)
        instance = 'new StreamVectorDataUnit()'
    
    code.addFragment('VectorDataUnit* {0} = {1};'.format(pointerName, instance))
    code.addFragment(self.getElement().getClassInstantiation(pointerName + '_V'))
    code.addFragment('{0}->setElementTemplate({1});'.format(pointerName, pointerName + '_V'))
    if dynlen:
        code.addFragment('{0}->propSet<int>("_dynlen", 1); // from genCodeCpp_getEmbeddedClassInstantiation_StaticVectorDef'.format(pointerName))
        #code.addFragment('{0}->propSet<std::string>(".binding.length", "{1}");' \
        #        .format(pointerName, self.getLength()))
    return code

StaticVectorDef.getEmbeddedClassInstantiation = genCodeCpp_getEmbeddedClassInstantiation_StaticVectorDef


#
# _____________________________________________________________________________
#

#
#
#
def genCodeCpp_getEmbeddedClassInstantiation_SelectDef(self, pointerName, args=None, symbols=None):

    if args is None:
        args = {}

    parentStruct = self.getParent()
    if not isinstance(parentStruct, StructDef):
        raise TPLError('Select not embedded inside struct')

    testVarName = self.getTestSymbolName()
    testVarDef = parentStruct[testVarName].followInstantiation()[0]
    if not isinstance(testVarDef, EnumDef):
        raise TPLError('Test variable is not an enumeration')

    cppTestVar = genCodeCpp_resolveSymbols({'testVar': IntSymbol(testVarName)}, symbols)['testVar']

    guard = None
    for case in self.getCases():

        if not isinstance(case, DefaultCaseDef):
            test = []
            for cond in case.cond:
                branchItem = testVarDef[cond]
                if branchItem.isRange():
                    test += ['{0} >= {1} && {0} <= {2}'.format(cppTestVar,
                            branchItem.getMinCode(), branchItem.getMaxCode())]
                else:        
                    test += ['{0} == {1}'.format(cppTestVar,
                            branchItem.getMinCode())]
            if len(test) > 1:
                test = ' || '.join(['({0})'.format(t) for t in test])
            else:
                test = ' || '.join(test)

            if not guard:
                guard = IfThenElse(test)
                currentGuard = guard
            else:
                currentGuard = currentGuard.addElseIf(test)

            for i, caseMember in enumerate(case.getMembers()):
                memberPointer = '_CM{0}'.format(i)
                currentGuard.addFragmentThenBranch(case.generateCodeMemberInstantiation(i, '_C', symbols))

        else:
            currentGuard = currentGuard.addElse()

            for i, caseMember in enumerate(case.getMembers()):
                memberPointer = '_CM{0}'.format(i)
                currentGuard.addFragment(case.generateCodeMemberInstantiation(i, '_C', symbols))

    return guard

SelectDef.getEmbeddedClassInstantiation = genCodeCpp_getEmbeddedClassInstantiation_SelectDef









