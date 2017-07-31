# etpl-tool: A Parser for an Enhanced Version of the TLS Presentation Language (eTPL) and a C++ Code Generator 

The *tplman* tool is an attempt to provide a comprehensive and powerful software instrument to parse network protocol and network message definitions written in an enhanced version of the TLS presentation language (referred to as *eTPL* in the following). TPL has been introduced with [RFC2246](https://tools.ietf.org/html/rfc2246) for the very particular goal of documenting TLS and its protocol message encoding. However, it appears to be of interest beyond its original intention and with some adaptions is used in other places as well (see e.g. the specification of [security header and certificate formats](http://www.etsi.org/deliver/etsi_ts/103000_103099/103097/01.01.01_60/ts_103097v010101p.pdf) by ETSI).

*tplman* consists of several loosely coupled Python modules for parsing TPL definitions, checking, analyzing, optimizing a TPL-defined data model, and generating code for decoding and encoding actual data described by TPL. For the sake of improving the usability of TPL extending the feature set of TPL 

## Language syntax and constructs

### Type definitions

Type definitions in TPL follow a simple scheme based on the type of the definition followed by the name of the definition:

    // TYPE NAME;
    uint8 Length;

This defines a new type "Length" which is equivalent to the built-in type "unit8". Obviously, such a definition is not very helpful but there is a number of possible extensions that make type definitions very powerful.



### Type parametrization

Types may be parametrized by setting key-value paris

    // Set the integer's maximum
    uint8::<max=25> Length;

    // Set the integer's minimum and maximum
    uint8::<min=1, max=25> Length;


### Built-in types

### Constant integers (const)

    const myInt = 16;

### Enumerations (enum)

    enum {
        no(0), yes(1), (255)
    } MyBool;

### Structures (struct)

    struct {
        MyBool bool;
    } MyStruct;


Within the definition of a composite type (struct, see below), elements may be anonymous, e.g. the name may be omitted:

    struct {
        TYPE;
    } MyStruct;

### Select/case switches

### Imposing field length

### Vectors

    // Vector of uint16 with length of 8 octets
    uint16 MyIntVector1[8];

    // Vector of uint16 with 8 elements
    uint16 MyIntVector2[[8]];

    // Vector of uint16 with between 0 and 8 octets (actual length preceeding)
    uint16 MyIntVector3<0..8>;
    uint16 MyIntVector4<8>;

    // Vector of uint16 with between 0 and 8 elements (actual length preceeding)
    uint16 MyIntVector5<<0..8>>;
    uint16 MyIntVector6<<8>>;

    // Infinite vector of uint16
    uint16 MyIntVector7[];


### Comments


## Contact

Andreas Walz
andreas.walz@hs-offenburg.de
Institute of Reliable Embedded Systems and Communication Electronics
Offenburg University of Applied Sciences
ivesk.hs-offenburg.de

