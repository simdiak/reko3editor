#ifndef LS11H
#define LS11H

#include <stddef.h>
#include <stdio.h>
#include <string.h>
//---------------------------------------------------------------------------
typedef unsigned char BYTE;

class TLS11
{
public:
    bool Decode(const BYTE *dict, const BYTE *in, size_t insize, BYTE *out, size_t outsize);
    bool Encode(BYTE *dict, BYTE *in, size_t insize, BYTE *out, size_t outsize);
    bool GetData(FILE *fp, char *buf, int offset, int size);

protected:
    size_t _inpos;
    int _bitpos;
    const BYTE *_in;

    unsigned int GetCode(void);
};

#endif
