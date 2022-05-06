export function dec(i)
{
    // 十六进制转十进制
    return parseInt('0x' + i, 16);
}
export function hex(i, byte)
{
    // 整数转成十六进制字符串并补0
    var hex_i = Number(i).toString(16);
    if(hex_i.length % 2 === 1)
        hex_i = '0' + hex_i;
    if(byte)
    {
        while(hex_i.length < byte * 2)
            hex_i = '00' + hex_i;
    }
    return hex_i;
}
export function hex_code(hex_i, size, reverse)
{
    // 十六进制字符串改代码形式 '123' -> '01 23'
    // size为转换后应有的字节数
    // 如reverse=1，'123' -> '23 01'
    if(hex_i.length % 2 === 1)
        hex_i = '0' + hex_i;
    var _res = hex_i.replace(/[0-9a-z]{2}/g, '$& ');
    var _res_arr = _res.split(' ');
    _res_arr.pop();
    while(_res_arr.length < size)
        _res_arr.splice(0, 0, '00')
    if(reverse === 1)
        _res_arr.reverse()
    return _res_arr.join(' ')
}
export function code_hex(code, reverse)
{
    //十六进制代码转字符串
    //如reverse=0，'01 23' -> '123'
    //如reverse=1，'01 23' -> '2301'
    var _res_arr = code.split(' ');
    if(reverse === 1)
        _res_arr.reverse();
    var _res = _res_arr.join('');
    return _res === '00' ? _res : _res.replace(/^0+/g, '');
}