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

# TODO: make these functions operating on current collection (instead of
# creating a new one)


#
# _____________________________________________________________________________
#

def normalizeTypeDefs(self):
    normalized = TypeDefCollection(self.getGlobalSymbols())
    for t in self.getTypeDefs(False):
        normalized.addDef(t.normalize(normalized))
    return normalized

TypeDefCollection.normalize = normalizeTypeDefs


#
# _____________________________________________________________________________
#

def normalizeTypeDef(self, typedefs):
    return self

TypeDef.normalize = normalizeTypeDef


#
# _____________________________________________________________________________
#

def normalizeVectorDef(self, typedefs):

    # set default element name
    if not self.getElement().getName():
        self.getElement().setName('_E')

    # recursively normalize element
    self.setElement(self.getElement().normalize(typedefs))

    # flatten
    self.setElement(self.getElement().makeField(typedefs))

    # If the vector's element(s) is/are of opaque type ...
    if isinstance(self.getElement().followInstantiation()[0], OpaqueDef):
        if self.isItemBased:
            # ... then item based vectors don't make sense
            raise TPLError('Invalid use of opaque type in definition of "{0}"' \
                .format(self.getChainedName(' -> ')))
        else:
            # ... then turn this vector into an 'opaque' field            
            opaqueField = InstanceDef('opaque', self.getName())
            opaqueField.setSize(self.getSize())
            return opaqueField
    else:
        return self

VectorDef.normalize = normalizeVectorDef


#
# _____________________________________________________________________________
#

def normalizeStaticVectorDef(self, typedefs):

    vector = VectorDef.normalize(self, typedefs)

    # If this vector has been turned into an 'opaque'
    # field in the course of the canonicalization ...
    if isinstance(vector, InstanceDef):
        # ... then set the opaque field's length accordingly
        if self.getLength() is not None:
            vector.args['nbytes'] = self.getLength()

    return vector

StaticVectorDef.normalize = normalizeStaticVectorDef


#
# _____________________________________________________________________________
#

def normalizeDynamicVectorDef(self, typedefs):

    # create and configure integer field for vector length
    width = self.getNDigits(self.getLengthMaxValue(), 2)
    fieldN = InstanceDef('uint{0}'.format(width), '_N')
    if self.getLengthMinValue() != 0:
        fieldN.args['min'] = self.getLengthMin()
    if self.getLengthMaxValue() != 2**width - 1:
        fieldN.args['max'] = self.getLengthMax()

    vector = VectorDef.normalize(self, typedefs)

    # If this vector has been turned into an 'opaque'
    # field in the course of the canonicalization ...
    if isinstance(vector, InstanceDef):
        # ... then set the opaque field's length accordingly
        vector.args['nbytes'] = IntSymbol('_N')
    else:
        staticVector = StaticVectorDef(IntSymbol('_N'), \
                isItemBased=vector.isItemBased)
        staticVector.setName(vector.getName())
        staticVector.setElement(vector.getElement())
        staticVector.setFlags(vector.getFlags())
        vector = staticVector

    struct = StructDef([fieldN, vector])
    struct.setFlags(vector.getFlags())                        
    vector.resetFlags() 
    struct.setName(vector.getName())
    vector.setName('_V')

    return struct

DynamicVectorDef.normalize = normalizeDynamicVectorDef


#
# _____________________________________________________________________________
#

def keepInStructDef(member):
    if isinstance(member, FragmentDef):
        return True
    if isinstance(member, SelectDef):
        return True
    if isinstance(member, StaticVectorDef):
        return True
    return False

def normalizeStructDef(self, typedefs):
    # set default member names
    for i, t in enumerate(self.getMembers()):
        if not t.getName():
            t.setName('_M{0}'.format(i))
    # recursively normalize members
    for i in range(len(self.getMembers())):
        self.setMember(self[i].normalize(typedefs), i)
        if not keepInStructDef(self[i]):
            self.setMember(self[i].makeField(typedefs), i)
    return self

StructDef.normalize = normalizeStructDef


#
# _____________________________________________________________________________
#

def normalizeSelectDef(self, typedefs):
    # set default case names
    for i, c in enumerate(self.getCases()):
        if not c.getName():
            c.setName('_C{0}'.format(i))
    # recursively normalize cases
    for i in range(len(self.getCases())):
        self.setCase(self[i].normalize(typedefs), i)
    return self

SelectDef.normalize = normalizeSelectDef







