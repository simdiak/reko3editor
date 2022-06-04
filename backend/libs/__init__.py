import base64
from . import data_maps
from . import common


class Reko3Data:

    def __init__(self, reko3_dir, snr):
        self.debug = False
        self.reko3_dir = reko3_dir
        self.bakdata = f'{self.reko3_dir}/Bakdata.r3'
        self.main_exe = f'{self.reko3_dir}/Main.exe'
        self.snrd_file = f'{self.reko3_dir}/Snr%dd.r3' % (snr)
        self.snrm_file = f'{self.reko3_dir}/Snr%dm.r3' % (snr)
        self.ls11_header = b''
        self.snrd_data = []
        self.snrm_data = []

        self.juntuan_map = data_maps.juntuan_map
        self.juntuan_list = ['%s軍' % (jt)
                             for jt in list(self.juntuan_map.values())]
        self.avatar_list = []
        self.bingzhong_list = []
        self.celve_list = []
        self.daoju_list = []
        self.trigger_descr = data_maps.trigger_descr
        self.trigger_list = list(self.trigger_descr.values())
        self.code_step = data_maps.code_step
        self.action_list = [v['descr'] for v in list(self.code_step.values())]
        self.build_list = data_maps.build_list
        self.ai_type_descr = data_maps.ai_type_descr
        self.ai_list = list(self.ai_type_descr.values())

        self.avatar_list = self.init_data_avatar()
        self.bingzhong_list = self.init_data_bingzhong()
        self.celve_list = self.init_data_celve()
        self.daoju_list = self.init_data_daoju()
        self.avatar_first = self.init_data_avatar_first()

    def output(self, line):
        if self.debug:
            print(line)

    def init_data_avatar(self):
        _avatar_list = []
        with open(self.bakdata, 'rb') as fp:
            self.output('========人物基础数据========')
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
                    unknown += common.hex_int(x) + ' '
                tongyu = ord(fp.read(1))
                wuli = ord(fp.read(1))
                zhili = ord(fp.read(1))
                fp.read(1)
                self.output('%s (%s) %s %d %d %d | %s' % (
                    addr, common.hex_int(i), name, wuli, zhili, tongyu, unknown))
                _avatar = {
                    'id_hex': '0x' + common.hex_int(i, 2),
                    'addr': addr,
                    'name': name,
                    'wuli': wuli,
                    'zhili': zhili,
                    'tongyu': tongyu,
                }
                _avatar_list.append(_avatar)
            _avatar = {
                'id_hex': '0x0400',
                'name': '任何人',
                'wuli': 0,
                'zhili': 0,
                'tongyu': 0,
            }
            _avatar_list.append(_avatar)
            _avatar = {
                'id_hex': '0xffff',
                'name': '没有人',
                'wuli': 0,
                'zhili': 0,
                'tongyu': 0,
            }
            _avatar_list.append(_avatar)
        return _avatar_list

    def init_data_bingzhong(self):
        _bingzhong_list = []
        with open(self.main_exe, 'rb') as fp:
            self.output('========兵种数据========')
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
                _bingzhong_list.append(bing)
                self.output('%s %s' % (addr, bing))
        return _bingzhong_list

    def init_data_celve(self):
        _celve_list = []
        with open(self.main_exe, 'rb') as fp:
            self.output('========策略数据========')
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
                _celve_list.append(celve)
                self.output('%s %s' % (addr, celve))
        return _celve_list

    def init_data_daoju(self):
        _daoju_list = []
        with open(self.bakdata, 'rb') as fp:
            self.output('========道具数据========')
            fp.seek(0x0d00)
            for i in range(63):
                addr = hex(fp.tell())
                _name = fp.read(10)
                try:
                    _i = _name.index(0)
                except:
                    _i = len(_name)
                name = _name[0:_i].decode('big5').replace(' ', '')
                unknown = ''
                for x in fp.read(3):
                    unknown += common.hex_int(x) + ' '
                _xiaoguo = fp.read(1)
                xiaoguo = common.hex_int(ord(_xiaoguo))
                _qiangdu = fp.read(1)
                qiangdu = common.hex_int(ord(_qiangdu))
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
                _daoju_list.append({
                    'name': name,
                    'effect_id': ord(_what),
                    'effect': what,
                    'xiaoguo': ord(_xiaoguo),
                    'qiangdu': ord(_qiangdu),
                })
                self.output('%s %s-%-5s 作用：%s 效果：%s 强度：%s | %s' % (addr,
                            common.hex_int(i), name, what, xiaoguo, qiangdu, unknown))
        return _daoju_list

    def init_data_avatar_first(self):
        _avatar_first = []
        with open(self.bakdata, 'rb') as fp:
            self.output('========人物初始属性========')
            fp.seek(0x3080)
            for i in range(384):
                addr = hex(fp.tell())
                name = self.get_avatar(i)['name']
                x = fp.read(1)
                juntuan_id = ord(x)
                juntuan = self.juntuan_map[juntuan_id]
                fp.read(6)
                x = fp.read(1)
                bingzhong_id = ord(x)
                bingzhong = self.bingzhong_list[bingzhong_id]
                level = ord(fp.read(1))
                exp = ord(fp.read(1))
                daoju_str = ''
                daoju_list = []
                for x in fp.read(8):
                    if x != 0xFF:
                        daoju_str += '%s(%s) ' % (
                            self.daoju_list[x], common.hex_int(x))
                        daoju_list.append({
                            'id': x,
                            'name': self.daoju_list[x],
                        })
                _avatar = {
                    'id_hex': '0x' + common.hex_int(i, 2),
                    'addr': addr,
                    'name': name,
                    'juntuan_id': juntuan_id,
                    'juntuan': juntuan,
                    'bingzhong_id': bingzhong_id,
                    'bingzhong': bingzhong,
                    'level': level,
                    'exp': exp,
                    'daoju_list': daoju_list,
                }
                _avatar_first.append(_avatar)
                self.output('%s %s %s軍 %s 等级%d 经验%d 道具：%s' %
                            (addr, name, juntuan, bingzhong, level, exp, daoju_str))
        return _avatar_first

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
                        daoju += '%s(%s) ' % (
                            self.daoju_list[x], common.hex_int(x))
                self.output('%s %s %s軍 %s 等级%d 经验%d 道具：%s' %
                            (addr, name, juntuan, bingzhong, level, exp, daoju))

    def read_snrd(self):
        self.snrd_data = []
        with open(self.snrd_file, 'rb') as fp:
            self.ls11_header = fp.read(0x110)
            cur_page = 0
            while True:
                size = common.read4int(fp.read(4))
                size2 = common.read4int(fp.read(4))
                offset = common.read4int(fp.read(4))
                if size == 0:
                    break
                item = {
                    'page': cur_page,
                    'offset': offset,
                    'offset_hex': '0x' + common.hex_int(offset),
                }
                self.snrd_data.append(item)
                cur_page += 1
            for i_page, page in enumerate(self.snrd_data):
                paragraph_list = []
                cur_paragraph = 0
                fp.seek(page['offset'])
                while True:
                    offset = common.read2int(fp.read(2))
                    if offset == 0xffff:
                        break
                    item = {
                        'paragraph': cur_paragraph,
                        'offset': offset,
                        'offset_hex': '0x' + common.hex_int(offset),
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
                        offset = common.read2int(_instr[8:10])
                        offset_abs = page['offset'] + \
                            paragraph['offset'] + offset
                        item = {
                            'section': i_section,
                            'instr': common.hex_str(_instr),
                            'instr_type': sec_type,
                            'instr_type_descr': self.trigger_descr[sec_type],
                            'instr_bin': base64.b64encode(_instr).decode(),
                            'instr_descr': self.get_trigger_info(_instr),
                            'offset': offset,
                            'offset_hex': '0x' + common.hex_int(offset),
                            'offset_abs_start': offset_abs,
                            'offset_abs_start_hex': '0x' + common.hex_int(offset_abs),
                        }
                        section_list.append(item)
                        i_section += 1
                    for i, section in enumerate(section_list):
                        fp.seek(section['offset_abs_start'])
                        if i < len(section_list) - 1:
                            next_sec_offset = section_list[i +
                                                           1]['offset_abs_start']
                        else:
                            try:
                                next_sec_offset = page['offset'] + \
                                    paragraph_list[i_paragraph+1]['offset']
                            except:
                                try:
                                    next_sec_offset = self.snrd_data[i_page+1]['offset']
                                except:
                                    cur_pos = fp.tell()
                                    fp.seek(0, 2)
                                    next_sec_offset = fp.tell()
                                    fp.seek(cur_pos)
                        section['offset_abs_end'] = next_sec_offset
                        section['offset_abs_end_hex'] = '0x' + \
                            common.hex_int(next_sec_offset)
                        length = next_sec_offset - section['offset_abs_start']
                        _data = ''
                        # 读整段指令
                        _script_instr = fp.read(length)
                        section['script_instr'] = common.hex_str(_script_instr)
                        section['script_instr_bin'] = base64.b64encode(
                            _script_instr).decode()
                        try:
                            section['script_instr_descr'] = self.resolv_script_instr(
                                i_page, _script_instr)
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
        offset = common.read2int(instr[8:10])
        addition = ''
        if sec_type == 0x02:
            build_id = instr[2]
            build_name = self.build_list[build_id]
            city_id = instr[4]
            addition = '进入城市[%x]的[%s]' % (city_id, build_name)
        elif sec_type == 0x03:
            avatar_id = common.read2int(instr[2:4])
            name = self.get_avatar(avatar_id)['name']
            addition = '对象:[%s]' % (name)
        elif sec_type == 0x04:
            avatar_id1 = common.read2int(instr[2:4])
            if avatar_id1 == 0x400:
                name1 = '任何人'
            else:
                name1 = self.get_avatar(avatar_id1)['name']
            avatar_id2 = common.read2int(instr[4:6])
            name2 = self.get_avatar(avatar_id2)['name']
            addition = '[%s]vs[%s]' % (name1, name2)
        elif sec_type == 0x05:
            city_id = instr[2]
            addition = '进入城市[%x]' % (city_id)
        elif sec_type == 0x06:
            avatar_id = common.read2int(instr[2:4])
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
            avatar_id = common.read2int(instr[2:4])
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
            avatar_id = common.read2int(instr[2:4])
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
            city_id = common.read2int(instr[1:3])
            return '城市=%d' % (city_id)
        if _code in [0x24, 0x28]:
            avatar_id = common.read2int(instr[1:3])
            name = self.get_avatar(avatar_id)['name']
            target = instr[3] + 0x80
            juntuan = self.juntuan_map[target]
            return '[%s]阵营修改为[%s]' % (name, juntuan)
        if _code in [0x01, 0x0a]:
            avatar_id = common.read2int(instr[1:3])
            x = instr[3]
            y = instr[4]
            direction = instr[5]
            name = self.get_avatar(avatar_id)['name']
            return '[%s] (%d,%d) 朝向%d' % (name, x, y, direction)
        if _code in [0x10]:
            avatar_id1 = common.read2int(instr[1:3])
            name1 = self.get_avatar(avatar_id1)['name']
            avatar_id2 = common.read2int(instr[3:5])
            name2 = self.get_avatar(avatar_id2)['name']
            return '[%s]vs[%s]' % (name1, name2)
        if _code in [0x1c]:
            avatar_id = common.read2int(instr[1:3])
            name = self.get_avatar(avatar_id)['name']
            ai_type = instr[3]
            ai_descr = self.ai_type_descr[ai_type]
            if ai_type in [0x03, 0x05]:
                target = common.read2int(instr[4:6])
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
            avatar_id = common.read2int(instr[1:3])
            name = self.get_avatar(avatar_id)['name']
            return '[%s]' % (name)
        if _code in [0x35]:
            avatar_id = common.read2int(instr[1:3])
            name = self.get_avatar(avatar_id)['name']
            ani_id = instr[3]
            return '[%s]单挑动画=%d' % (name, ani_id)
        if _code in [0x14]:
            event_id = instr[1]
            status = instr[2]
            return '设置事件 0x%s=%d' % (common.hex_int(event_id), status)
        if _code in [0x18]:
            avatar_id = common.read2int(instr[1:3])
            name = self.get_avatar(avatar_id)['name']
            return '[%s]' % (name)
        if _code in [0x2D]:
            target = '我军' if instr[1] == 0x00 else '敌军'
            effect = '士气' if instr[2] == 0x00 else '兵力'
            return '%s %s 减半' % (target, effect)
        if _code in [0x39]:
            avatar_id = common.read2int(instr[1:3])
            level = instr[3]
            name = self.get_avatar(avatar_id)['name']
            return '[%s]上升了[%d]级' % (name, level)
        if _code in [0x07]:
            pic_id = common.read2int(instr[1:3])
            return '图片=%d' % (pic_id)
        if _code in [0x38]:
            music_id = instr[1]
            return '音乐=%d' % (music_id)
        if _code in [0x2B]:
            vtype = '金' if instr[1] == 0x02 else '经验'
            value = common.read2int(instr[2:4])
            return '%s=%s' % (vtype, value)
        if _code in [0x00, 0x08, 0x0b, 0x0d, 0x0e, 0x25]:
            offset = common.read2int(instr[1:3])
            has_title = _code == 0x00
            return self.read_snrm_txt(i_page, offset, has_title)
        if _code in [0x03]:
            not_retreat = instr[1]
            round_cnt = instr[2]
            round_inherit = instr[3]
            opp_main = common.read2int(instr[6:8])
            if opp_main != 0xffff:
                opp_main_name = self.get_avatar(opp_main)['name']
            else:
                opp_main_name = '无'
            my_main = common.read2int(instr[10:12])
            my_main_name = self.get_avatar(my_main)['name']
            ret_txt = '不可撤退[%d] 回合数[%d] 继承回合数[%d] 敌军主将[%s] 我军主将[%s]' \
                % (not_retreat, round_cnt, round_inherit, opp_main_name, my_main_name)
            info_list = []
            for i in range(0x1e):
                st = 12 + i * 9
                avatar_id = common.read2int(instr[st:st+2])
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
                        % (common.hex_int(i), common.hex_int(avatar_id), name,
                            x, y, appear_str, direction, fubing)
                info_list.append(_info)
            return ret_txt + '\n'.join(info_list)
        if _code in [0x22]:
            info_list = []
            for i in range(0x1e):
                st = 2 + i * 13
                avatar_id = common.read2int(instr[st:st+2])
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
                        % (common.hex_int(i), common.hex_int(avatar_id), name, bingzhong, level,
                            x, y, appear_str, direction, fubing, ai_type, ai_target_id)
                info_list.append(_info)
            return '\n'.join(info_list)
        return ''

    def resolv_script_instr(self, i_page, instr):
        _res = []
        step = 0  # 当前指令的参数长度
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
                    tg1_events = common.hex_str(instr[s1:e1])
                else:
                    tg1_events = ''
                    s1 = 0
                    e1 = 0
                if tg0_cnt > 0:
                    s0 = i+4+tg1_cnt
                    e0 = s0 + tg0_cnt
                    tg0_events = common.hex_str(instr[s0:e0])
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
            _res.append(common.hex_str(params) + ' ' + descr +
                        ' ' + self.get_detail(i_page, params))
            # i移动到下个指令
            i = _end
        return _res

    def read_snrm(self):
        self.snrm_data = []
        with open(self.snrm_file, 'rb') as fp:
            fp.seek(0)
            data_offset = common.read2int(fp.read(2))
            all_pages = int(data_offset / 2)
            fp.seek(0)
            offset_list = []
            for i in range(0, all_pages):
                offset = common.read2int(fp.read(2))
                offset_list.append(offset)
            fp.seek(0, 2)
            offset_list.append(fp.tell())
            for i in range(0, all_pages):
                item = {
                    'page': i,
                    'data_offset': data_offset,
                    'offset_start': offset_list[i],
                    'offset_start_hex': '0x%s' % (common.hex_int(offset_list[i])),
                    'offset_end': offset_list[i+1],
                    'offset_end_hex': '0x%s' % (common.hex_int(offset_list[i+1])),
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
                        avatar_id = common.read2int(txt[0:2])
                        if avatar_id < 0x180:
                            txt_type = '带头像对话'
                            # + ':' + self.get_avatar(avatar_id)['name']
                            name = '0x' + common.hex_int(avatar_id, 2)
                            txt_content = txt[2:]
                            descr = txt_content.decode('big5')
                        else:
                            txt_type = '一般文本'
                            name = ''
                            descr = txt.decode('big5')
                    item = {
                        'addr_relate': offset - page['offset_start'],
                        'addr_relate_hex': '0x%s' % (common.hex_int(offset - page['offset_start'], 2)),
                        'addr_abs': offset,
                        'addr_abs_hex': '0x%s' % (common.hex_int(offset)),
                        'name': name,
                        'txt_bin': base64.b64encode(txt).decode(),
                        'txt_type': txt_type,
                        'txt_code': common.hex_str(txt),
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
                    paragraph_offset_list.append(
                        fp.tell() - paragraph_index_offset)
                    # section索引
                    section_index_offset = fp.tell()
                    for i, section in enumerate(paragraph['section_list']):
                        # 直接复制来占位,最后地址需要修改
                        fp.write(base64.b64decode(section['instr_bin']))
                    fp.write(bytes([0xff] * 10))
                    section_offset_list = []
                    for i, section in enumerate(paragraph['section_list']):
                        section_offset_list.append(
                            fp.tell() - section_index_offset)
                        fp.write(base64.b64decode(section['script_instr_bin']))
                    end_offset = fp.tell()  # 文件末尾
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
