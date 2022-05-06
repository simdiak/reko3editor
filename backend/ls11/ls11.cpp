#pragma hdrstop
#include "ls11.h"
//---------------------------------------------------------------------------
#pragma package(smart_init)

// https://tieba.baidu.com/p/2516199826?pn=1

bool TLS11::Decode(const BYTE *dict, const BYTE *in, size_t insize, BYTE *out, size_t outsize)
{
    size_t outpos = 0;
    unsigned int code, off, len;
    bool rs = true;

    _inpos = 0;
    _bitpos = 7;
    _in = in;
    while (_inpos < insize && outpos < outsize)
    {
        code = GetCode();

        if (code < 256)
        {
            out[outpos++] = dict[code];
        }
        else
        {
            off = code - 256;
            len = GetCode() + 3;
            for (unsigned int i = 0; i < len; i++)
            {
                out[outpos] = out[outpos - off];
                outpos++;
            }
        }
    }

    return rs;
}

bool TLS11::Encode(BYTE *dict, BYTE *in, size_t insize, BYTE *out, size_t outsize)
{
    return 0;
}

unsigned int TLS11::GetCode(void)
{
    unsigned int code, code2;
    int l;
    BYTE bit;

    code = 0;
    code2 = 0;
    l = 0;
    do
    {
        bit = (BYTE)((_in[_inpos] >> _bitpos) & 0x01);
        code = (code << 1) | bit;
        l++;
        _bitpos--;
        if (_bitpos < 0)
        {
            _bitpos = 7;
            _inpos++;
        }
    }while (bit);
    for (int i = 0; i < l; i++)
    {
        bit = (BYTE)((_in[_inpos] >> _bitpos) & 0x01);
        code2 = (code2 << 1) | bit;
        _bitpos--;
        if (_bitpos < 0)
        {
            _bitpos = 7;
            _inpos++;
        }
    }
    code += code2;

    return code;
}

bool TLS11::GetData(FILE *fp, char *buf, int offset, int size)
{
    fseek(fp, offset, SEEK_SET);
    fread(buf, size, 1, fp);
    return 0;
}

void out_data(char *buf, int size)
{
    for(int i=0;i<size;i++)
    {
        (i == 0 || i % 16) ? i : printf("\n");
        printf("%02hx ", buf[i] & 0x00ff);
    }
    printf("\n");
}

int read_int(char *buf)
{
    char res[4];
    res[0] = buf[3];
    res[1] = buf[2];
    res[2] = buf[1];
    res[3] = buf[0];
    int *res_int = (int*)res;
    return *res_int;
}

int main()
{
    const char *filename = "Snr4d.r3.orig";
    const char *new_filename = "Snr4d.r3.unzipped";
    FILE *fp = fopen(filename, "rb");
    FILE *fw = fopen(new_filename, "wb");
    TLS11 a;

    printf("== LS11 head ==\n");
    char header[0x10];
    a.GetData(fp, header, 0x00, 0x10);
    fwrite(header, 0x10, 1, fw);

    printf("== LS11 dict ==\n");
    int dict_start = 0x10;
    int size = 0x100;
    char ls11_dict[size];
    a.GetData(fp, ls11_dict, dict_start, size);
    out_data(ls11_dict, size);
    fwrite(ls11_dict, size, 1, fw);

    int sec_idx_start = 0x110;
    size = 0x4;
    char buf[size];
    int sec_n = 0;
    int cur_pos = sec_idx_start;
    int new_offset = 0;
    char section_data[1048576];
    int section_size = 0;
    while(1)
    {
        a.GetData(fp, buf, cur_pos, size);
        int zipped_size = read_int(buf);
        if(zipped_size != 0)
            printf("== section index ( %d ) ==\n", sec_n);
        else
            break;
        printf("zipped_size=%d\n", zipped_size);
        cur_pos += 4;

        a.GetData(fp, buf, cur_pos, size);
        int origin_size = read_int(buf);
        printf("origin_size=%d\n", origin_size);
        cur_pos += 4;

        fwrite(buf, size, 1, fw);
        fwrite(buf, size, 1, fw);

        a.GetData(fp, buf, cur_pos, size);
        int sec_offset = read_int(buf);
        printf("sec_offset=0x%x\n", sec_offset);
        if(sec_n == 0)
            new_offset = sec_offset;
        cur_pos += 4;

        char new_offset_buf[4];
        int *p = (int*)new_offset_buf;
        *p = read_int((char*)&new_offset);
        fwrite(new_offset_buf, size, 1, fw);

        new_offset += origin_size;
        printf("new_offset=0x%x\n", new_offset);

        sec_n++;

        //printf("== section data ==\n");
        char data[zipped_size];
        a.GetData(fp, data, sec_offset, zipped_size);
        //out_data(data, zipped_size);

        //printf("== section unzipped data ==\n");
        BYTE *unzipped_data[origin_size];
        if(zipped_size != origin_size)
            a.Decode((const BYTE*)ls11_dict, (const BYTE *)data, (size_t)zipped_size, (BYTE*)unzipped_data, (size_t)origin_size);
        else
            memcpy(unzipped_data, data, origin_size);
        //out_data((char*)unzipped_data, origin_size);
        printf("sec data size=%d\n", section_size);
        memcpy(&section_data[section_size], unzipped_data, origin_size);
        section_size += origin_size;
    }
    int zero = 0;
    fwrite(&zero, size, 1, fw);

    printf("sec count=%d\n", sec_n);
    printf("sec data size=%d\n", section_size);
    fwrite(section_data, section_size, 1, fw);

    fclose(fp);
    fclose(fw);
    return 0;
}
