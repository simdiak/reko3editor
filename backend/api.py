from flask import Flask, jsonify, request, make_response
import re
import base64
import copy
from libs import Reko3Data

app = Flask(__name__)
reko3_dir = "./reko3"


def make_resp(resp):
    r = make_response(resp)
    r.headers['Access-Control-Allow-Origin'] = '*'
    return r


@app.route('/')
def root():
    return open('reko3ed.html').read()


@app.route('/load_snrm/<int:n>')
def load_snrm(n):
    rd = Reko3Data(reko3_dir, n)
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
    rd = Reko3Data(reko3_dir, n)
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


@app.route('/write_snr/<int:n>', methods=['POST'])
def write_snr(n):
    # write snrd
    rd = Reko3Data(reko3_dir, n)
    snrd_data = request.json['snrd']
    for page in snrd_data:
        for paragraph in page['paragraph_list']:
            for section in paragraph['section_list']:
                _code = b''
                code_list = re.match(
                    '^([0-9a-f]+\s?)+', section['instr_index_code']).group().strip()
                for c in code_list.split(' '):
                    _code += bytes([eval('0x'+c)])
                section['instr_bin'] = base64.b64encode(_code)
                del section['instr_index_code']
                _code = b''
                for subcode in section['script_list']:
                    code_list = re.match(
                        '^([0-9a-f]+\s?)+', subcode).group().strip()
                    for c in code_list.split(' '):
                        _code += bytes([eval('0x'+c)])
                section['script_instr_bin'] = base64.b64encode(_code)
                del section['script_code']
    filename = f'{reko3_dir}/Snr{n}d.r3'
    rd.write_snrd(filename, snrd_data)
    # write snrm
    snrm_data = request.json['snrm']
    for page in snrm_data:
        for item in page['txt_list']:
            _code = b''
            code_list = re.match('^([0-9a-f]+\s?)+',
                                 item['code']).group().strip()
            for c in code_list.split(' '):
                _code += bytes([eval('0x'+c)])
            item['txt_bin'] = base64.b64encode(_code)
    filename = f'{reko3_dir}/Snr{n}m.r3'
    rd.write_snrm(filename, snrm_data)
    data = {
        'OK': 1
    }
    return make_resp(jsonify(data))


@app.route('/trans/<data>')
def trans(data):
    txt = eval('b\'\\u'+'\\u'.join(re.findall('(....)',
               data.replace('%u', '')))+'\'').decode('unicode_escape')
    c_str = ''
    try:
        txt.encode('big5')
    except Exception as e:
        err_ch = '%%u%s' % (re.findall(
            '.*character.*u([0-9a-f]+).*position.*', str(e))[0])
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
    rd = Reko3Data(reko3_dir, 0)
    return make_resp(jsonify(rd.avatar_list))


@app.route('/load_avatar_first')
def load_avatar_first():
    rd = Reko3Data(reko3_dir, 0)
    return make_resp(jsonify(rd.avatar_first))


@app.route('/load_instr_index_code')
def load_instr_index_code():
    rd = Reko3Data(reko3_dir, 0)
    return make_resp(jsonify(rd.trigger_descr))


@app.route('/load_trigger')
def load_trigger():
    rd = Reko3Data(reko3_dir, 0)
    return make_resp(jsonify(rd.trigger_list))


@app.route('/load_script_code')
def load_script_code():
    rd = Reko3Data(reko3_dir, 0)
    return make_resp(jsonify(rd.code_step))


@app.route('/load_action')
def load_action():
    rd = Reko3Data(reko3_dir, 0)
    return make_resp(jsonify(rd.action_list))


@app.route('/load_bingzhong')
def load_bingzhong():
    rd = Reko3Data(reko3_dir, 0)
    return make_resp(jsonify(rd.bingzhong_list))


@app.route('/load_daoju')
def load_daoju():
    rd = Reko3Data(reko3_dir, 0)
    return make_resp(jsonify(rd.daoju_list))


@app.route('/load_ai')
def load_ai():
    rd = Reko3Data(reko3_dir, 0)
    return make_resp(jsonify(rd.ai_list))


@app.route('/load_juntuan')
def load_juntuan():
    rd = Reko3Data(reko3_dir, 0)
    return make_resp(jsonify(rd.juntuan_list))


@app.route('/load_resource')
def load_resource():
    rd = Reko3Data(reko3_dir, 0)
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
    app.run(host='0.0.0.0', port=8888, debug=True)
