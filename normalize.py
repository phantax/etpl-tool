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







