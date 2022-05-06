from flask import Flask, jsonify, request, make_response
import re
import json
import base64
import copy

reko3_dir = './reko3'

class Reko3Data:

    def __init__(self):
        self.debug = False
        self.bakdata = f'{reko3_dir}/Bakdata.r3'
        self.main_exe = f'{reko3_dir}/Main.exe'
        self.ls11_header = b''
        self.snrd_file = ''
        self.snrd_data = []
        self.snrm_file = ''
        self.snrm_data = []
        self.juntuan_map = {
            0x80: '劉備', 0x81: '曹操', 0x82: '孫權', 0x83: '公孫瓚',
            0x84: '袁紹', 0x85: '董卓', 0x86: '袁術', 0x87: '呂布',
            0x88: '陶謙', 0x89: '劉表', 0x8A: '劉璋', 0x8B: '張魯',
            0x8C: '馬騰', 0x8D: '孔融', 0x8E: '無屬',
        }
        self.juntuan_list = ['%s軍' % (jt) for jt in list(self.juntuan_map.values())]
        self.avatar_list = []
        self.bingzhong_list = []
        self.celve_list = []
        self.daoju_list = []
        self.trigger_descr = {
            0x00: '顺序执行',
            0x01: '分支执行',
            0x02: '进入城市建筑',
            0x03: '对话',
            0x04: '单挑',
            0x05: '进入城市',
            0x06: '战场移到点',
            0x07: '战斗胜利',
            0x08: '战斗失败',
            0x09: '指定回合',
            0x0A: '未知',
            0x0B: '战场移到区域',
            0x0C: '撤退',
        }
        self.trigger_list = list(self.trigger_descr.values())
        self.code_step = {
            0x00: {'plen': 2, 'descr': '显示带人物头像的系列对话'},
            0x01: {'plen': 5, 'descr': '指定人物在剧情场景的行动'},
            0x02: {'plen': 1, 'descr': '未知'},
            0x03: {'plen': 11 + 30 * 9, 'descr': '部署我军部队'},
            0x04: {'plen': 0, 'descr': '未知'},
            0x05: {'plen': 0, 'descr': '显示当前场景'},
            0x06: {'plen': 0, 'descr': '未知'},
            0x07: {'plen': 2, 'descr': '显示图片'},
            0x08: {'plen': 2, 'descr': '在屏幕中央显示多行信息'},
            0x09: {'plen': 2, 'descr': '指定战场/场景/大地图'},
            0x0A: {'plen': 5, 'descr': '部署非战斗模式中的人物'},
            0x0B: {'plen': 2, 'descr': '在画面中心显示信息'},
            0x0C: {'plen': 4, 'descr': '未知'},
            0x0D: {'plen': 2, 'descr': '在画面左下角框中显示信息'},
            0x0E: {'plen': 2, 'descr': '在画面中央显示信息'},
            0x0F: {'plen': 1, 'descr': '重新读入本章本节某段剧本指令'},
            0x10: {'plen': 4, 'descr': '武将单挑'},
            0x11: {'plen': 2, 'descr': '切换到地图/场景/战场'},
            0x12: {'plen': 0, 'descr': '本章结束'},
            0x13: {'plen': 0, 'descr': '段指令强制结束'},
            0x14: {'plen': 2, 'descr': '设置事件开关'},
            0x15: {'plen': 2, 'descr': '是否出战的对话框显示'},
            0x16: {'plen': 4, 'descr': '未知'},
            0x17: {'plen': 1, 'descr': '剧情模式开关'},
            0x18: {'plen': 2, 'descr': '人物消失、部队撤退'},
            0x19: {'plen': 0, 'descr': '未知'},
            0x1A: {'plen': 2, 'descr': '援军出现'},
            0x1B: {'plen': 1, 'descr': '获得道具'},
            0x1C: {'plen': 5, 'descr': '改变人物AI'},
            0x1D: {'plen': 4, 'descr': '未知'},
            0x1E: {'plen': 0, 'descr': '未知'},
            0x1F: {'plen': 0, 'descr': '未知'},
            0x20: {'plen': 99, 'descr': '子指令数目'},
            0x21: {'plen': 99, 'descr': '检查事件是否触发'},
            0x22: {'plen': 1 + 30 * 13, 'descr': '部署敌军'},
            0x23: {'plen': 0, 'descr': '选择我军出战部队'},
            0x24: {'plen': 3, 'descr': '修改武将阵营'},
            0x25: {'plen': 2, 'descr': '显示决定供选择'},
            0x26: {'plen': 3, 'descr': '改变战场地形'},
            0x27: {'plen': 3, 'descr': '放火或放水'},
            0x28: {'plen': 3, 'descr': '战场改变武将阵营'},
            0x29: {'plen': 0, 'descr': '游戏失败'},
            0x2A: {'plen': 1, 'descr': '显示游戏结局'},
            0x2B: {'plen': 3, 'descr': '给予黄金/残存部队获得经验'},
            0x2C: {'plen': 0, 'descr': '未知'},
            0x2D: {'plen': 2, 'descr': '兵力士气减半'},
            0x2E: {'plen': 5, 'descr': '切换所在城市'},
            0x2F: {'plen': 3, 'descr': '修改人物未知属性'},
            0x30: {'plen': 2, 'descr': '显示目标（剧情目标或战斗目标）'},
            0x31: {'plen': 0, 'descr': '与道具屋有关，废弃指令'},
            0x32: {'plen': 1, 'descr': '设置道具屋贩卖物品，废弃指令'},
            0x33: {'plen': 0, 'descr': '关闭单挑动画'},
            0x34: {'plen': 0, 'descr': '开启单挑动画'},
            0x35: {'plen': 3, 'descr': '单挑动画'},
            0x36: {'plen': 0, 'descr': '切换到战斗模式'},
            0x37: {'plen': 3, 'descr': '未知'},
            0x38: {'plen': 1, 'descr': '播放游戏音乐'},
            0x39: {'plen': 3, 'descr': '人物等级上升'},
            0x3A: {'plen': 3, 'descr': '改变人物兵种'},
            0x3B: {'plen': 2, 'descr': '重新定位场景位置'},
            0x3C: {'plen': 2, 'descr': '定位军团'},
            0x3D: {'plen': 1, 'descr': '一般存盘/战场存盘'},
            0xFF: {'plen': 0, 'descr': '本段指令结束'},
        }
        self.action_list = [v['descr'] for v in list(self.code_step.values())]
        self.build_list = {
            0x00: '宫殿', 0x01: '宫殿', 0x02: '议事厅', 0x03: '议事厅',
            0x04: '议事厅', 0x05: '议事厅', 0x06: '集会所', 0x07: '酒馆',
            0x08: '官邸', 0x09: '集会所', 0x0A: '？', 0x0B: '？',
            0x0C: '庭院', 0x0D: '官邸', 0x0E: '营帐', 0x0F: '营帐',
            0x10: '营帐', 0x11: '陈留', 0x12: '官邸', 0x13: '？',
            0x14: '茅庐', 0x15: '草庐', 0x16: '陶谦官邸',
        }
        self.ai_type_descr = {
            0x00: '原地警戒(攻击)',
            0x01: '主动出击',
            0x02: '原地待命',
            0x03: '主动攻击仇人',
            0x04: '移动到坐标(攻击)',
            0x05: '襄阳II关羽消灭曹仁',
            0x06: '移动到坐标(不攻击)',
            0x07: '这是什么AI？',
        }
        self.ai_list = list(self.ai_type_descr.values())

        self.read_base_data()

    def hex_int(self, i, byte_cnt=1):
        if byte_cnt == 1:
            fmt = '%02s'
        elif byte_cnt == 2:
            fmt = '%04s'
        return (fmt % (hex(i).replace('0x', ''))).replace(' ', '0')

    def hex_str(self, s):
        _str = ''
        for i in s:
            _str += self.hex_int(i) + ' '
        return _str

    def read2int(self, chars):
        _a = chars[1]
        _b = chars[0]
        return _a * 256 + _b

    def read4int(self, chars):
        _a = chars[0]
        _b = chars[1]
        _c = chars[2]
        _d = chars[3]
        return _a * 256 ** 3 + _b * 256 ** 2 + _c * 256 + _d

    def output(self, line):
        if self.debug:
            print(line)

    def read_base_data(self):
        self.avatar_list = []
        with open(self.bakdata, 'rb') as fp:
            self.output('人物基础数据')
            fp.seek(0x1100)
            for i in range(384):
                addr = hex(fp.tell())
                _name = fp.read(4)
                b = fp.read(2)
                if b[0] != 0:
                    _name += b
                name = _name.decode('big5').replace(' ', '')
                unknown = ''
                for x in fp.read(11):
                    unknown += self.hex_int(x) + ' '
                tongyu = ord(fp.read(1))
                wuli = ord(fp.read(1))
                zhili = ord(fp.read(1))
                fp.read(1)
                self.output('%s (%s) %s %d %d %d | %s' % (addr, self.hex_int(i), name, wuli, zhili, tongyu, unknown))
                _avatar = {
                    'id_hex': '0x' + self.hex_int(i, 2),
                    'name': name,
                    'wuli': wuli,
                    'zhili': zhili,
                    'tongyu': tongyu,
                }
                self.avatar_list.append(_avatar)
            _avatar = {
                'id_hex': '0x0400',
                'name': '任何人',
                'wuli': 0,
                'zhili': 0,
                'tongyu': 0,
            }
            self.avatar_list.append(_avatar)
            _avatar = {
                'id_hex': '0xffff',
                'name': '没有人',
                'wuli': 0,
                'zhili': 0,
                'tongyu': 0,
            }
            self.avatar_list.append(_avatar)

        self.bingzhong_list = []
        with open(self.main_exe, 'rb') as fp:
            self.output('兵种数据')
            fp.seek(0x37bf8)
            for i in range(19):
                addr = hex(fp.tell())
                _bing = b''
                while True:
                    c = fp.read(1)
                    if c != b'\x00':
                        _bing += c
                    else:
                        break
                bing = _bing.decode('big5')
                self.bingzhong_list.append(bing)
                self.output('%s %s' % (addr, bing))

        self.celve_list = []
        with open(self.main_exe, 'rb') as fp:
            self.output('策略数据')
            fp.seek(0x3a6ea)
            for i in range(36):
                addr = hex(fp.tell())
                _celve = b''
                while True:
                    c = fp.read(1)
                    if c != b'\x00':
                        _celve += c
                    else:
                        break
                celve = _celve.decode('big5')
                self.celve_list.append(celve)
                self.output('%s %s' % (addr, celve))

        self.daoju_list = []
        with open(self.bakdata, 'rb') as fp:
            self.output('道具数据')
            fp.seek(0x0d00)
            for i in range(63):
                addr = hex(fp.tell())
                _name = fp.read(10)
                try:
                    _i = _name.index(0)
                except:
                    _i = len(_name)
                name = _name[0:_i].decode('big5').replace(' ', '')
                self.daoju_list.append(name)
                unknown = ''
                for x in fp.read(3):
                    unknown += self.hex_int(x) + ' '
                _xiaoguo = fp.read(1)
                xiaoguo = self.hex_int(ord(_xiaoguo))
                _qiangdu = fp.read(1)
                qiangdu = self.hex_int(ord(_qiangdu))
                what_list = {
                    0: '加攻',
                    1: '转职',
                    2: '攻击',
                    3: '恢复',
                    4: '加速',
                    5: '加防',
                }
                _what = fp.read(1)
                what = what_list[ord(_what)]
                self.output('%s %s-%-5s 作用：%s 效果：%s 强度：%s | %s' % (addr, self.hex_int(i), name, what, xiaoguo, qiangdu, unknown))

        with open(self.bakdata, 'rb') as fp:
            self.output('初始化数据')
            fp.seek(0x3080)
            for i in range(384):
                addr = hex(fp.tell())
                name = self.get_avatar(i)['name']
                x = fp.read(1)
                juntuan = self.juntuan_map[ord(x)]
                fp.read(6)
                x = fp.read(1)
                bingzhong = self.bingzhong_list[ord(x)]
                level = ord(fp.read(1))
                exp = ord(fp.read(1))
                daoju = ''
                for x in fp.read(8):
                    if x != 0xFF:
                        daoju += '%s(%s) ' % (self.daoju_list[x], self.hex_int(x))
                self.output('%s %s %s軍 %s 等级%d 经验%d 道具：%s' % (addr, name, juntuan, bingzhong, level, exp, daoju))

    def read_msave(self, msave_file):
        with open(msave_file, 'rb') as fp:
            self.output('存档 %s 数据' % (msave_file))
            fp.seek(0x695)
            for i in range(384):
                addr = hex(fp.tell())
                name = self.get_avatar(i)['name']
                x = fp.read(1)
                juntuan = self.juntuan_map[ord(x)]
                fp.read(6)
                x = fp.read(1)
                bingzhong = self.bingzhong_list[ord(x)]
                level = ord(fp.read(1))
                exp = ord(fp.read(1))
                daoju = ''
                for x in fp.read(8):
                    if x != 0xFF:
                        daoju += '%s(%s) ' % (self.daoju_list[x], self.hex_int(x))
                self.output('%s %s %s軍 %s 等级%d 经验%d 道具：%s' % (addr, name, juntuan, bingzhong, level, exp, daoju))

    def set_snr(self, n):
        self.snrd_file = '../Snr%dd.r3' % (n)
        self.snrm_file = '../Snr%dm.r3' % (n)

    def read_snrd(self):
        self.snrd_data = []
        with open(self.snrd_file, 'rb') as fp:
            self.ls11_header = fp.read(0x110)
            cur_page = 0
            while True:
                size = self.read4int(fp.read(4))
                size2 = self.read4int(fp.read(4))
                offset = self.read4int(fp.read(4))
                if size == 0:
                    break
                item = {
                    'page': cur_page,
                    'offset': offset,
                    'offset_hex': '0x' + self.hex_int(offset),
                }
                self.snrd_data.append(item)
                cur_page += 1
            for i_page, page in enumerate(self.snrd_data):
                paragraph_list = []
                cur_paragraph = 0
                fp.seek(page['offset'])
                while True:
                    offset = self.read2int(fp.read(2))
                    if offset == 0xffff:
                        break
                    item = {
                        'paragraph': cur_paragraph,
                        'offset': offset,
                        'offset_hex': '0x' + self.hex_int(offset),
                    }
                    paragraph_list.append(item)
                    cur_paragraph += 1
                page['paragraph_list'] = paragraph_list
                for i_paragraph, paragraph in enumerate(paragraph_list):
                    section_list = []
                    i_section = 0
                    fp.seek(page['offset'] + paragraph['offset'])
                    while True:
                        # 多个组指令
                        _instr = fp.read(10)
                        sec_type = _instr[0]
                        sub_sec_num = _instr[1]
                        if sec_type == 0xff and sub_sec_num == 0xff:
                            break
                        offset = self.read2int(_instr[8:10])
                        offset_abs = page['offset'] + paragraph['offset'] + offset
                        item = {
                            'section': i_section,
                            'instr': self.hex_str(_instr),
                            'instr_type': sec_type,
                            'instr_type_descr': self.trigger_descr[sec_type],
                            'instr_bin': base64.b64encode(_instr).decode(),
                            'instr_descr': self.get_trigger_info(_instr),
                            'offset': offset,
                            'offset_hex': '0x' + self.hex_int(offset),
                            'offset_abs_start': offset_abs,
                            'offset_abs_start_hex': '0x' + self.hex_int(offset_abs),
                        }
                        section_list.append(item)
                        i_section += 1
                    for i, section in enumerate(section_list):
                        fp.seek(section['offset_abs_start'])
                        if i < len(section_list) - 1:
                            next_sec_offset = section_list[i+1]['offset_abs_start']
                        else:
                            try:
                                next_sec_offset = page['offset'] + paragraph_list[i_paragraph+1]['offset']
                            except:
                                try:
                                    next_sec_offset = self.snrd_data[i_page+1]['offset']
                                except:
                                    cur_pos = fp.tell()
                                    fp.seek(0, 2)
                                    next_sec_offset = fp.tell()
                                    fp.seek(cur_pos)
                        section['offset_abs_end'] = next_sec_offset
                        section['offset_abs_end_hex'] = '0x' + self.hex_int(next_sec_offset)
                        length = next_sec_offset - section['offset_abs_start']
                        _data = ''
                        # 读整段指令
                        _script_instr = fp.read(length)
                        section['script_instr'] = self.hex_str(_script_instr)
                        section['script_instr_bin'] = base64.b64encode(_script_instr).decode()
                        try:
                            section['script_instr_descr'] = self.resolv_script_instr(i_page, _script_instr)
                        except:
                            section['script_instr_descr'] = []
                            raise
                    paragraph['section_list'] = section_list
            #print(json.dumps(self.snrd_data, indent=2, ensure_ascii=False))
        self.snrd_data[0]['ls11_header'] = base64.b64encode(self.ls11_header)
        return self.snrd_data

    def get_avatar(self, avatar_id):
        if avatar_id == 0x400:
            return {
                'name': '任何人',
                'wuli': 0,
                'zhili': 0,
                'tongyu': 0,
            }
        return self.avatar_list[avatar_id]

    def get_trigger_info(self, instr):
        sec_type = instr[0]
        sec_type_descr = self.trigger_descr[sec_type]
        sub_sec_num = instr[1]
        offset = self.read2int(instr[8:10])
        addition = ''
        if sec_type == 0x02:
            build_id = instr[2]
            build_name = self.build_list[build_id]
            city_id = instr[4]
            addition = '进入城市[%x]的[%s]' % (city_id, build_name)
        elif sec_type == 0x03:
            avatar_id = self.read2int(instr[2:4])
            name = self.get_avatar(avatar_id)['name']
            addition = '对象:[%s]' % (name)
        elif sec_type == 0x04:
            avatar_id1 = self.read2int(instr[2:4])
            if avatar_id1 == 0x400:
                name1 = '任何人'
            else:
                name1 = self.get_avatar(avatar_id1)['name']
            avatar_id2 = self.read2int(instr[4:6])
            name2 = self.get_avatar(avatar_id2)['name']
            addition = '[%s]vs[%s]' % (name1, name2)
        elif sec_type == 0x05:
            city_id = instr[2]
            addition = '进入城市[%x]' % (city_id)
        elif sec_type == 0x06:
            avatar_id = self.read2int(instr[2:4])
            if avatar_id == 0x400:
                name = '任何人'
            else:
                name = self.get_avatar(avatar_id)['name']
            x = instr[4]
            y = instr[5]
            addition = '[%s]移动到(%d,%d)' % (name, x, y)
        elif sec_type == 0x09:
            round_cnt = instr[2]
            addition = '到达回合数[%d]' % (round_cnt)
        elif sec_type == 0x0B:
            avatar_id = self.read2int(instr[2:4])
            if avatar_id == 0x400:
                name = '任何人'
            else:
                name = self.get_avatar(avatar_id)['name']
            x1 = instr[4]
            y1 = instr[5]
            x2 = instr[6]
            y2 = instr[7]
            addition = '[%s]移动到左上(%d,%d)-右下(%d,%d)范围' % (name, x1, y1, x2, y2)
        elif sec_type == 0x0C:
            avatar_id = self.read2int(instr[2:4])
            name = self.get_avatar(avatar_id)['name']
            addition = '对象:[%s]' % (name)
        return '类型:%d-%s 子段号:0x%x 偏移:0x%x %s' % (sec_type, sec_type_descr, sub_sec_num, offset, addition)

    def read_snrm_txt(self, i_page, offset, has_title):
        for page in self.snrm_data:
            if page['page'] == i_page:
                for item in page['txt_list']:
                    if item['addr_relate'] == offset:
                        if has_title:
                            name = item['name']
                            return '[%s:%s]' % (name, item['txt_descr'])
                        else:
                            return '[%s]' % (item['txt_descr'])

    def get_detail(self, i_page, instr):
        _code = instr[0]
        if _code in [0x17]:
            status = instr[1]
            return '模式=%d' % (status)
        if _code in [0x09, 0x11]:
            map_id = instr[1]
            map_type = instr[2]
            map_list = {
                0x00: '汜水关', 0x01: '虎牢关', 0x02: '广川', 0x03: '信都',
                0x04: '巨鹿', 0x05: '清河', 0x06: '界桥', 0x07: '北海',
                0x08: '徐州', 0x09: '小沛', 0x0A: '泰山', 0x0B: '夏丘',
                0x0C: '彭城', 0x0D: '淮南', 0x0E: '下邳', 0x0F: '广陵',
                0x10: '兖州', 0x11: '古城', 0x12: '颖川', 0x13: '汝南',
                0x14: '江夏', 0x15: '南阳', 0x16: '博望坡', 0x17: '新野',
                0x18: '襄阳', 0x19: '长坂坡I', 0x1A: '长坂坡II', 0x1B: '江陵',
                0x1D: '贵阳', 0x1C: '公安', 0x1E: '武陵', 0x1F: '零陵',
                0x20: '长沙', 0x21: '雒', 0x22: '成都', 0x23: '瓦口关I',
                0x24: '瓦口关II', 0x25: '葭萌关I', 0x26: '葭萌关II', 0x27: '定军山',
                0x28: '天荡山', 0x29: '汉水', 0x2A: '阳平关', 0x2B: '西陵',
                0x2C: '夷陵', 0x2D: '麦', 0x2E: '南郡', 0x2F: '新野II',
                0x30: '宛I', 0x31: '宛II', 0x32: '许昌I', 0x33: '许昌II',
                0x34: '陈仓', 0x35: '长安', 0x36: '洛阳', 0x37: '邺I',
                0x38: '邺II', 0x39: '邺III',
            }
            if map_type == 0x30:
                name_type = '战场'
                name = map_list[map_id]
            elif map_type == 0x20:
                name_type = '城市'
                name = self.build_list[map_id]
            elif map_type == 0x10:
                name_type = '大地图'
                name = '大地图'
            else:
                name_type = 'map_id=%d map_type=%d' % (map_id, map_type)
                name = 'UNKNOWN'
            return '进入 %s-%s' % (name_type, name)
        if _code in [0x2E]:
            city_list = {
                'hebei': {
                    0x00: '平原',
                    0x01: '邺',
                    0x02: '白马',
                    0x05: '邺',
                    0x09: '北平',
                    0x0B: '徐州',
                    0x0C: '古城',
                    0x0E: '许昌',
                    0x11: '下邳',
                    0x12: '信都',
                },
                'jingzhou_bei': {
                    0x00: '南阳',
                    0x02: '江陵',
                    0x03: '襄阳',
                    0x04: '新野',
                    0x06: '隆中',
                    0x07: '江夏',
                    0x09: '江夏',
                },
                'jingzhou_nan': {
                    0x00: '襄阳',
                    0x02: '江陵',
                    0x06: '长沙',
                    0x07: '江夏',
                    0x0B: '耒阳',
                },
                'yizhou': {
                    0x02: '江陵',
                    0x03: '襄阳',
                    0x0A: '成都',
                },
            }
            city_id = self.read2int(instr[1:3])
            return '城市=%d' % (city_id)
        if _code in [0x24, 0x28]:
            avatar_id = self.read2int(instr[1:3])
            name = self.get_avatar(avatar_id)['name']
            target = instr[3] + 0x80
            juntuan = self.juntuan_map[target]
            return '[%s]阵营修改为[%s]' % (name, juntuan)
        if _code in [0x01, 0x0a]:
            avatar_id = self.read2int(instr[1:3])
            x = instr[3]
            y = instr[4]
            direction = instr[5]
            name = self.get_avatar(avatar_id)['name']
            return '[%s] (%d,%d) 朝向%d' % (name, x, y, direction)
        if _code in [0x10]:
            avatar_id1 = self.read2int(instr[1:3])
            name1 = self.get_avatar(avatar_id1)['name']
            avatar_id2 = self.read2int(instr[3:5])
            name2 = self.get_avatar(avatar_id2)['name']
            return '[%s]vs[%s]' % (name1, name2)
        if _code in [0x1c]:
            avatar_id = self.read2int(instr[1:3])
            name = self.get_avatar(avatar_id)['name']
            ai_type = instr[3]
            ai_descr = self.ai_type_descr[ai_type]
            if ai_type in [0x03, 0x05]:
                target = self.read2int(instr[4:6])
                target_name = self.get_avatar(target)['name']
                ai_descr += ' 目标[%s]' % (target_name)
            elif ai_type in [0x04, 0x06]:
                x = instr[4]
                y = instr[5]
                ai_descr += ' 目标(%d,%d)' % (x, y)
            return '改变[%s]的AI 类型[%d] 描述[%s]' % (name, ai_type, ai_descr)
        if _code in [0x27]:
            x = instr[1]
            y = instr[2]
            what = '放火' if instr[3] == 0x00 else '放水' if instr[3] == 0x01 else '取消'
            return '(%d,%d) %s' % (x, y, what)
        if _code in [0x1B]:
            daoju_id = instr[1]
            name = self.daoju_list[daoju_id]
            return '[%s]' % (name)
        if _code in [0x1A]:
            avatar_id = self.read2int(instr[1:3])
            name = self.get_avatar(avatar_id)['name']
            return '[%s]' % (name)
        if _code in [0x35]:
            avatar_id = self.read2int(instr[1:3])
            name = self.get_avatar(avatar_id)['name']
            ani_id = instr[3]
            return '[%s]单挑动画=%d' % (name, ani_id)
        if _code in [0x14]:
            event_id = instr[1]
            status = instr[2]
            return '设置事件 0x%s=%d' % (self.hex_int(event_id), status)
        if _code in [0x18]:
            avatar_id = self.read2int(instr[1:3])
            name = self.get_avatar(avatar_id)['name']
            return '[%s]' % (name)
        if _code in [0x2D]:
            target = '我军' if instr[1] == 0x00 else '敌军'
            effect = '士气' if instr[2] == 0x00 else '兵力'
            return '%s %s 减半' % (target, effect)
        if _code in [0x39]:
            avatar_id = self.read2int(instr[1:3])
            level = instr[3]
            name = self.get_avatar(avatar_id)['name']
            return '[%s]上升了[%d]级' % (name, level)
        if _code in [0x07]:
            pic_id = self.read2int(instr[1:3])
            return '图片=%d' % (pic_id)
        if _code in [0x38]:
            music_id = instr[1]
            return '音乐=%d' % (music_id)
        if _code in [0x2B]:
            vtype = '金' if instr[1] == 0x02 else '经验'
            value = self.read2int(instr[2:4])
            return '%s=%s' % (vtype, value)
        if _code in [0x00, 0x08, 0x0b, 0x0d, 0x0e, 0x25]:
            offset = self.read2int(instr[1:3])
            has_title = _code == 0x00
            return self.read_snrm_txt(i_page, offset, has_title)
        if _code in [0x03]:
            not_retreat = instr[1]
            round_cnt = instr[2]
            round_inherit = instr[3]
            opp_main = self.read2int(instr[6:8])
            if opp_main != 0xffff:
                opp_main_name = self.get_avatar(opp_main)['name']
            else:
                opp_main_name = '无'
            my_main = self.read2int(instr[10:12])
            my_main_name = self.get_avatar(my_main)['name']
            ret_txt = '不可撤退[%d] 回合数[%d] 继承回合数[%d] 敌军主将[%s] 我军主将[%s]' \
                    % (not_retreat, round_cnt, round_inherit, opp_main_name, my_main_name)
            info_list = []
            for i in range(0x1e):
                st = 12 + i * 9
                avatar_id = self.read2int(instr[st:st+2])
                if avatar_id == 0xffff:
                    name = '空'
                else:
                    try:
                        name = self.get_avatar(avatar_id)['name']
                    except:
                        continue
                x = instr[st+2]
                y = instr[st+3]
                appear = instr[st+5]
                appear_event = instr[st+6]
                if appear == 0:
                    appear_str = '直接出场'
                else:
                    appear_str = '事件%d出场' % (appear_event)
                direction = instr[st+7]
                fubing = instr[st+8]
                _info = '0x%s 0x%s %s (%d,%d) %s 朝向%d 伏兵%d' \
                        % (self.hex_int(i), self.hex_int(avatar_id), name,
                            x, y, appear_str, direction, fubing)
                info_list.append(_info)
            return ret_txt + '\n'.join(info_list)
        if _code in [0x22]:
            info_list = []
            for i in range(0x1e):
                st = 2 + i * 13
                avatar_id = self.read2int(instr[st:st+2])
                if avatar_id == 0xffff:
                    name = '空'
                else:
                    try:
                        name = self.get_avatar(avatar_id)['name']
                    except:
                        continue
                        name = '%d' % (avatar_id)
                x = instr[st+2]
                y = instr[st+3]
                appear = instr[st+4]
                appear_event = instr[st+5]
                if appear == 0:
                    appear_str = '直接出场'
                else:
                    appear_str = '事件%d出场' % (appear_event)
                direction = instr[st+6]
                fubing = instr[st+7]
                ai_type = instr[st+8]
                _a = instr[st+9]
                _b = instr[st+10]
                ai_target_id = _a + _b * 256
                _bingzhong = instr[st+11]
                try:
                    bingzhong = self.bingzhong_list[_bingzhong]
                except:
                    bingzhong = 'xx'
                level = instr[st+12]
                _info = '0x%s 0x%s %s %s 等级%d (%d,%d) %s 朝向%d 伏兵%d AI%d AI目标%d' \
                        % (self.hex_int(i), self.hex_int(avatar_id), name, bingzhong, level,
                            x, y, appear_str, direction, fubing, ai_type, ai_target_id)
                info_list.append(_info)
            return '\n'.join(info_list)
        return ''

    def resolv_script_instr(self, i_page, instr):
        _res = []
        step = 0 # 当前指令的参数长度
        params = ''
        i = 0
        while i < len(instr):
            _byte = instr[i]
            # 查找本指令参数长度
            if _byte == 0x20:
                step = instr[i+1] + 1
                if step > 0x80:
                    step -= 0x80
                descr = self.code_step[_byte]['descr']
            elif _byte == 0x32:
                step = instr[i+1] + 1
                descr = self.code_step[_byte]['descr']
            elif _byte == 0x21:
                # 21 | 02 | 00        | 01        | 63       | 1b 11 | 14 63 00  | ff
                #    | 跳2|已触0(无SA)|未触1(有SB)|SB:检查63 |1获马书|2设63为已触|
                ign_cnt = instr[i+1]
                tg1_cnt = instr[i+2]
                tg0_cnt = instr[i+3+tg1_cnt]
                step = 3 + tg1_cnt + tg0_cnt
                if tg1_cnt > 0:
                    s1 = i+3
                    e1 = s1 + tg1_cnt
                    tg1_events = self.hex_str(instr[s1:e1])
                else:
                    tg1_events = ''
                    s1 = 0
                    e1 = 0
                if tg0_cnt > 0:
                    s0 = i+4+tg1_cnt
                    e0 = s0 + tg0_cnt
                    tg0_events = self.hex_str(instr[s0:e0])
                else:
                    tg0_events = ''
                    s0 = 0
                    e0 = 0
                descr = '检查事件 未通过跳过[%d]条 已触发[%d]条(%s) 未触发[%d]条(%s)' \
                        % (ign_cnt, tg1_cnt, tg1_events, tg0_cnt, tg0_events)
            else:
                step = self.code_step[_byte]['plen']
                descr = self.code_step[_byte]['descr']
            # 截取到参数末尾
            _end = i + step + 1
            params = instr[i:_end]
            # 添加进_res
            _res.append(self.hex_str(params) + ' ' + descr + ' ' + self.get_detail(i_page, params))
            # i移动到下个指令
            i = _end
        return _res

    def read_snrm(self):
        self.snrm_data = []
        with open(self.snrm_file, 'rb') as fp:
            fp.seek(0)
            data_offset = self.read2int(fp.read(2))
            all_pages = int(data_offset / 2)
            fp.seek(0)
            offset_list = []
            for i in range(0, all_pages):
                offset = self.read2int(fp.read(2))
                offset_list.append(offset)
            fp.seek(0, 2)
            offset_list.append(fp.tell())
            for i in range(0, all_pages):
                item = {
                    'page': i,
                    'data_offset': data_offset,
                    'offset_start': offset_list[i],
                    'offset_start_hex': '0x%s' % (self.hex_int(offset_list[i])),
                    'offset_end': offset_list[i+1],
                    'offset_end_hex': '0x%s' % (self.hex_int(offset_list[i+1])),
                    'txt_list': [],
                }
                self.snrm_data.append(item)
            # 目录完成，开始各章文字提取
            for page in self.snrm_data:
                fp.seek(page['offset_start'])
                while True:
                    offset = fp.tell()
                    if offset >= page['offset_end']:
                        break
                    txt = b''
                    last_c = b'\x00'
                    while True:
                        c = fp.read(1)
                        if len(c) == 0:
                            break
                        if len(txt) > 2 and ord(c) == 0x00 \
                            or ord(c) == 0xff and ord(last_c) == 0xff:
                            if(ord(c) != 0x00):
                                txt += c
                            break
                        txt += c
                        last_c = c
                    descr = ''
                    name = ''
                    txt_type = ''
                    if txt[0] != 0xff:
                        avatar_id = self.read2int(txt[0:2])
                        if avatar_id < 0x180:
                            txt_type = '带头像对话'
                            name = '0x' + self.hex_int(avatar_id, 2) #+ ':' + self.get_avatar(avatar_id)['name']
                            txt_content = txt[2:]
                            descr = txt_content.decode('big5')
                        else:
                            txt_type = '一般文本'
                            name = ''
                            descr = txt.decode('big5')
                    item = {
                        'addr_relate': offset - page['offset_start'],
                        'addr_relate_hex': '0x%s' % (self.hex_int(offset - page['offset_start'], 2)),
                        'addr_abs': offset,
                        'addr_abs_hex': '0x%s' % (self.hex_int(offset)),
                        'name': name,
                        'txt_bin': base64.b64encode(txt).decode(),
                        'txt_type': txt_type,
                        'txt_code': self.hex_str(txt),
                        'txt_descr': descr,
                    }
                    page['txt_list'].append(item)
            #print(json.dumps(self.snrm_data, indent=2, ensure_ascii=False))
        return self.snrm_data

    def write_snrm(self, file_name, snrm_data=None):
        if not snrm_data:
            snrm_data = self.snrm_data
        with open(file_name, 'wb') as fp:
            data_offset = 2 * len(snrm_data)
            offset_list = [data_offset]
            for i in range(len(snrm_data)):
                fp.write(b'\x00\x00')
            for page in snrm_data:
                for item in page['txt_list']:
                    _data = base64.b64decode(item['txt_bin'])
                    if _data[0] != 0xff and _data[1] != 0xff:
                        _data += b'\x00'
                    fp.write(_data)
                offset_list.append(fp.tell())
            # 写入文件头章索引
            fp.seek(0)
            for i in range(len(snrm_data)):
                _a = offset_list[i] & 0x00ff
                _b = offset_list[i] >> 8 & 0x00ff
                _data = bytes([_a, _b])
                fp.write(_data)

    def write_snrd(self, file_name, snrd_data=None):
        if not snrd_data:
            snrd_data = self.snrd_data
            ls11_header = self.ls11_header
        else:
            ls11_header = base64.b64decode(snrd_data[0]['ls11_header'])
        with open(file_name, 'wb') as fp:
            # LS11头部
            fp.write(ls11_header)
            # page索引
            page_index_offset = fp.tell()
            for i in range(len(snrd_data)):
                fp.write(bytes([0] * 12))
            fp.write(bytes([0] * 4))
            page_offset_list = []
            # page内容
            for i_page, page in enumerate(snrd_data):
                page_offset_list.append(fp.tell())
                # paragraph索引
                paragraph_index_offset = fp.tell()
                for i in range(len(page['paragraph_list'])):
                    fp.write(bytes([0] * 2))
                fp.write(bytes([0xff] * 2))
                paragraph_offset_list = []
                for i_paragraph, paragraph in enumerate(page['paragraph_list']):
                    paragraph_offset_list.append(fp.tell() - paragraph_index_offset)
                    # section索引
                    section_index_offset = fp.tell()
                    for i, section in enumerate(paragraph['section_list']):
                        # 直接复制来占位,最后地址需要修改
                        fp.write(base64.b64decode(section['instr_bin']))
                    fp.write(bytes([0xff] * 10))
                    section_offset_list = []
                    for i, section in enumerate(paragraph['section_list']):
                        section_offset_list.append(fp.tell() - section_index_offset)
                        fp.write(base64.b64decode(section['script_instr_bin']))
                    end_offset = fp.tell() # 文件末尾
                    # 回头补充section偏移
                    saved_offset = fp.tell()
                    fp.seek(section_index_offset)
                    for i in range(len(paragraph['section_list'])):
                        fp.seek(8, 1)
                        _a = section_offset_list[i] & 0x00ff
                        _b = section_offset_list[i] >> 8 & 0x00ff
                        fp.write(bytes([_a, _b]))
                    fp.seek(saved_offset)
                # 回头补充paragraph偏移
                saved_offset = fp.tell()
                fp.seek(paragraph_index_offset)
                for i in range(len(page['paragraph_list'])):
                    _a = paragraph_offset_list[i] & 0x00ff
                    _b = paragraph_offset_list[i] >> 8 & 0x00ff
                    fp.write(bytes([_a, _b]))
                fp.seek(saved_offset)
            # 回头补充page偏移
            saved_offset = fp.tell()
            fp.seek(page_index_offset)
            for i in range(len(snrd_data)):
                if i < len(snrd_data) - 1:
                    length = page_offset_list[i+1] - page_offset_list[i]
                else:
                    length = end_offset - page_offset_list[i]
                _a = length & 0x00ff
                _b = length >> 8 & 0x00ff
                fp.seek(2, 1)
                fp.write(bytes([_b, _a]))
                fp.seek(2, 1)
                fp.write(bytes([_b, _a]))
                _a = page_offset_list[i] & 0x00ff
                _b = page_offset_list[i] >> 8 & 0x00ff
                fp.seek(2, 1)
                fp.write(bytes([_b, _a]))
            fp.seek(saved_offset)

    # f = open('BAKDATA.R3', 'rb+');f.seek(0x0d7e);f.write(b'\x80');f.close()

app = Flask(__name__)
rd = Reko3Data()

def make_resp(resp):
    r = make_response(resp)
    r.headers['Access-Control-Allow-Origin'] = '*'
    return r

@app.route('/')
def root():
    return open('reko3ed.html').read()

@app.route('/load_snrm/<int:n>')
def load_snrm(n):
    rd.set_snr(n)
    snrm_data_short = copy.deepcopy(rd.read_snrm())
    for item in snrm_data_short:
        del item['data_offset']
        del item['offset_end']
        del item['offset_start']
        del item['offset_end_hex']
        del item['offset_start_hex']
        del item['page']
        for txt in item['txt_list']:
            txt['txt'] = txt['txt_descr']
            txt['addr'] = txt['addr_relate_hex']
            txt['code'] = txt['txt_code']
            del txt['addr_abs']
            del txt['addr_abs_hex']
            del txt['addr_relate']
            del txt['addr_relate_hex']
            del txt['txt_bin']
            del txt['txt_code']
            del txt['txt_type']
            del txt['txt_descr']
    return make_resp(jsonify(snrm_data_short))

@app.route('/load_snrd/<int:n>')
def load_snrd(n):
    rd.set_snr(n)
    rd.read_snrm()
    snrd_data_short = copy.deepcopy(rd.read_snrd())
    snrd_data_short[0]["ls11_header"] = snrd_data_short[0]["ls11_header"].decode()
    for page in snrd_data_short:
        cur_page = page['page']
        page['addr'] = page['offset_hex']
        del page['offset']
        del page['offset_hex']
        del page['page']
        for paragraph in page['paragraph_list']:
            paragraph['addr'] = paragraph['offset_hex']
            del paragraph['offset']
            del paragraph['offset_hex']
            del paragraph['paragraph']
            for section in paragraph['section_list']:
                section['instr_offset'] = section['offset_hex']
                section['instr_index_code'] = section['instr']
                section['instr_type'] = section['instr_type_descr']
                section['script_code'] = section['script_instr']
                section['script_list'] = section['script_instr_descr']
                section['page'] = cur_page
                del section['instr']
                del section['instr_bin']
                del section['instr_descr']
                del section['instr_type']
                del section['instr_type_descr']
                del section['offset']
                del section['offset_abs_end']
                del section['offset_abs_end_hex']
                del section['offset_abs_start']
                del section['offset_abs_start_hex']
                del section['offset_hex']
                del section['script_instr']
                del section['script_instr_bin']
                del section['script_instr_descr']
                del section['section']
    return make_resp(jsonify(snrd_data_short))

@app.route('/write_snr', methods=['POST'])
def write_snr():
    # write snrd
    snrd_data = request.json['snrd']
    for page in snrd_data:
        for paragraph in page['paragraph_list']:
            for section in paragraph['section_list']:
                _code = b''
                code_list = re.match('^([0-9a-f]+\s?)+', section['instr_index_code']).group().strip()
                for c in code_list.split(' '):
                    _code += bytes([eval('0x'+c)])
                section['instr_bin'] = base64.b64encode(_code)
                del section['instr_index_code']
                _code = b''
                for subcode in section['script_list']:
                    code_list = re.match('^([0-9a-f]+\s?)+', subcode).group().strip()
                    for c in code_list.split(' '):
                        _code += bytes([eval('0x'+c)])
                section['script_instr_bin'] = base64.b64encode(_code)
                del section['script_code']
    filename = 'new_snrd.data'
    rd.write_snrd(filename, snrd_data)
    # write snrm
    snrm_data = request.json['snrm']
    for page in snrm_data:
        for item in page['txt_list']:
            _code = b''
            code_list = re.match('^([0-9a-f]+\s?)+', item['code']).group().strip()
            for c in code_list.split(' '):
                _code += bytes([eval('0x'+c)])
            item['txt_bin'] = base64.b64encode(_code)
    filename = 'new_snrm.data'
    rd.write_snrm(filename, snrm_data)
    data = {
        'snrm': snrm_data,
        'snrd': snrd_data,
    }
    return make_resp(jsonify(data))

@app.route('/trans/<data>')
def trans(data):
    txt = eval('b\'\\u'+'\\u'.join(re.findall('(....)', data.replace('%u', '')))+'\'').decode('unicode_escape')
    c_str = ''
    try:
        txt.encode('big5')
    except Exception as e:
        err_ch = '%%u%s' % (re.findall('.*character.*u([0-9a-f]+).*position.*', str(e))[0])
        ret_data = {
            'err_ch': err_ch,
        }
        return ret_data
    for c in txt.encode('big5'):
        c_str += '%x ' % (c)
    ret_data = {
        'txt': data,
        'code': c_str,
    }
    return make_resp(jsonify(ret_data))

@app.route('/load_avatar')
def load_avatar():
    return make_resp(jsonify(rd.avatar_list))

@app.route('/load_instr_index_code')
def load_instr_index_code():
    return make_resp(jsonify(rd.trigger_descr))

@app.route('/load_trigger')
def load_trigger():
    return make_resp(jsonify(rd.trigger_list))

@app.route('/load_script_code')
def load_script_code():
    return make_resp(jsonify(rd.code_step))

@app.route('/load_action')
def load_action():
    return make_resp(jsonify(rd.action_list))

@app.route('/load_bingzhong')
def load_bingzhong():
    return make_resp(jsonify(rd.bingzhong_list))

@app.route('/load_daoju')
def load_daoju():
    return make_resp(jsonify(rd.daoju_list))

@app.route('/load_ai')
def load_ai():
    return make_resp(jsonify(rd.ai_list))

@app.route('/load_juntuan')
def load_juntuan():
    return make_resp(jsonify(rd.juntuan_list))

@app.route('/load_resource')
def load_resource():
    data = {
        'avatar_list': rd.avatar_list,
        'action_list': rd.action_list,
        'bingzhong_list': rd.bingzhong_list,
        'daoju_list': rd.daoju_list,
        'ai_list': rd.ai_list,
        'juntuan_list': rd.juntuan_list,
        'trigger_list': rd.trigger_list,
    }
    return make_resp(jsonify(data))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8888, debug=True)
#    rd.set_snr(0)
#    rd.read_snrm()
#    rd.read_snrd()
#    rd.write_snrm('new_snrm.data')
#    rd.write_snrd('new_snrd.data')
#    rd.read_msave('../MSAVE0.R3S')
