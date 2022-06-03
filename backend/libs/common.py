def hex_int(i, byte_cnt=1):
    if byte_cnt == 1:
        fmt = '%02s'
    elif byte_cnt == 2:
        fmt = '%04s'
    return (fmt % (hex(i).replace('0x', ''))).replace(' ', '0')


def hex_str(s):
    _str = ''
    for i in s:
        _str += hex_int(i) + ' '
    return _str


def read2int(chars):
    _a = chars[1]
    _b = chars[0]
    return _a * 256 + _b


def read4int(chars):
    _a = chars[0]
    _b = chars[1]
    _c = chars[2]
    _d = chars[3]
    return _a * 256 ** 3 + _b * 256 ** 2 + _c * 256 + _d
