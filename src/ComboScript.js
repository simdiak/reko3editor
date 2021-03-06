import React from 'react';
import {Container, Form, Row, InputGroup, Button} from 'react-bootstrap';
import SelectAction from './SelectAction';
import SelectAvatar from './SelectAvatar';
import SelectDaoju from './SelectDaoju';
import SelectLevel from './SelectLevel';
import SelectBingzhong from './SelectBingzhong';
import SelectJuntuan from './SelectJuntuan';
import SelectAI from './SelectAI';
import SelectPosition from './SelectPosition';
import SelectNumber from './SelectNumber';
import SelectCustom from './SelectCustom';
import * as utils from './Utils';

class ComboScript extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            script_arr: props.script_code.split(' '),
        }
        this.handleUpdateCombo = this.handleUpdateCombo.bind(this);
    }
    fill_length(arr, length){
        while(arr.length < length)
            arr.push('00');
        while(arr.length > length)
            arr.pop();
    }
    handleUpdateCombo(idx, value, length) {
        if(typeof(value) == 'number')
            value = utils.hex(value);
        else
            value = value.replace('0x', '');
        if(value.length === 2)
        {
            this.setState({
                script_arr: this.state.script_arr.map((item, i) => i === idx ? value : item)
            }, () => {
                var script_arr = this.state.script_arr;
                if(length > 0)
                    script_arr = script_arr.slice(0, length);
                this.props.setProps(script_arr.join(' '));
            });
        }
        else if(value.length === 4)
        {
            var v1 = value.substr(0, 2);
            var v2 = value.substr(2, 2);
            this.setState({
                script_arr: this.state.script_arr.map((item, i) => i === idx ? v2 : (i === idx + 1 ? v1 : item))
            }, () => {
                var script_arr = this.state.script_arr;
                if(length > 0)
                    script_arr = script_arr.slice(0, length);
                this.props.setProps(script_arr.join(' '));
            });
        }
    }
    render () {
        var script_arr = this.state.script_arr;
        var script_action = utils.dec(script_arr[0]);
        var subitems = [];
        if([0x00, 0x08, 0x0b, 0x0d, 0x0e, 0x25].indexOf(script_action) !== -1)
        {
            // 00 ????????????????????????????????????
            // 08 ?????????????????????????????????
            // 0b ???????????????????????????
            // 0d ????????????????????????????????????
            // 0e ???????????????????????????
            // 25 ?????????????????????
            var length = 3;
            this.fill_length(script_arr, length);
            var offset = '0x' + script_arr[2] + script_arr[1];
            var txt_list = this.props.snrm_list[0].txt_list;
            subitems = [
                <span key={1}>??????</span>,
                <SelectTxt avatar_list={this.props.avatar_list} txt_list={txt_list} key={2} value={offset} setProps={(v) => {this.handleUpdateCombo(1, v, length)}} />,
            ];
        }
        else if([0x01, 0x0a].indexOf(script_action) !== -1)
        {
            // 01 ????????????????????????????????????
            // 0a ?????????????????????????????????
            // eslint-disable-next-line
            var length = 6;
            this.fill_length(script_arr, length);
            var name = '0x' + script_arr[2] + script_arr[1];
            var x = utils.dec(script_arr[3]);
            var y = utils.dec(script_arr[4]);
            var dir = utils.dec(script_arr[5]);
            subitems = [
                <span key={1}>??????</span>,
                <SelectAvatar avatar_list={this.props.avatar_list} key={2} value={name} setProps={(v) => {this.handleUpdateCombo(1, v, length)}} />,
                <span key={3}>??????</span>,
                <SelectPosition value_x={x}  value_y={y} key={4} setProps={(v) => {this.handleUpdateCombo(3, utils.hex(v.y) + utils.hex(v.x), length)}} />,
                <span key={5}>??????</span>,
                <SelectNumber count={4} value={dir} key={6} setProps={(v) => {this.handleUpdateCombo(5, v, length)}} />,
            ];
        }
        else if(script_action === 0x03)
        {
            // 03 ??????????????????
            // eslint-disable-next-line
            var length = 2 + 10 + 30 * 9;
            this.fill_length(script_arr, length);
            subitems = [
                <DeployMyArmy
                    avatar_list={this.props.avatar_list}
                    bingzhong_list={this.props.bingzhong_list}
                    deploy_list={script_arr}
                    key={1}
                    setMyArmy={(v) => {this.handleUpdateCombo(2, v.join(' '), 2 + 10 + 30 * 9)}}
                />
            ];
        }
        else if([0x05, 0x12, 0x13, 0x23, 0x29, 0x31, 0x33, 0x34, 0x36, 0xff].indexOf(script_action) !== -1)
        {
            // 05 ??????????????????
            // 12 ????????????
            // 13 ?????????????????????
            // 23 ????????????????????????
            // 29 ????????????
            // 31 ?????????????????????????????????
            // 33 ??????????????????
            // 34 ??????????????????
            // 36 ?????????????????????
            // ff ??????????????????
            // eslint-disable-next-line
            var length = 1;
            this.fill_length(script_arr, length);
        }
        else if(script_action === 0x07)
        {
            // 07 ????????????
            // eslint-disable-next-line
            var length = 3;
            this.fill_length(script_arr, length);
            var pic_id = utils.dec(script_arr[2] + script_arr[1]);
            subitems = [
                <span key={1}>??????</span>,
                <SelectNumber count={288} value={pic_id} key={2} setProps={(v) => {this.handleUpdateCombo(1, utils.hex(v, 2), length)}} />,
            ];
        }
        else if(script_action === 0x09)
        {
            // 09 ????????????/??????/?????????
        }
        else if(script_action === 0x0f)
        {
            // 0f ??????????????????????????????????????????
        }
        else if(script_action === 0x10)
        {
            // 10 ????????????
            // eslint-disable-next-line
            var length = 5;
            this.fill_length(script_arr, length);
            var name1 = '0x' + script_arr[2] + script_arr[1];
            var name2 = '0x' + script_arr[4] + script_arr[3];
            subitems = [
                <span key={1}>??????</span>,
                <SelectAvatar avatar_list={this.props.avatar_list} key={2} value={name1} setProps={(v) => {this.handleUpdateCombo(1, v, length)}} />,
                <span key={3}>??????</span>,
                <SelectAvatar avatar_list={this.props.avatar_list} key={4} value={name2} setProps={(v) => {this.handleUpdateCombo(3, v, length)}} />,
            ];
        }
        else if(script_action === 0x11)
        {
            // 11 ???????????????/??????/??????
        }
        else if(script_action === 0x14)
        {
            // 14 ??????????????????
            // eslint-disable-next-line
            var length = 3;
            this.fill_length(script_arr, length);
            var event_id = utils.dec(script_arr[1]);
            var switch_id = utils.dec(script_arr[2]);
            subitems = [
                <span key={1}>??????</span>,
                <SelectNumber count={256} value={event_id} key={2} setProps={(v) => {this.handleUpdateCombo(1, v, length)}} />,
                <span key={3}>??????</span>,
                <SelectNumber count={2} value={switch_id} key={4} setProps={(v) => {this.handleUpdateCombo(2, v, length)}} />,
            ];
        }
        else if(script_action === 0x15)
        {
            // 15 ??????????????????????????????
        }
        else if(script_action === 0x17)
        {
            // 17 ??????????????????
        }
        else if([0x18, 0x1a].indexOf(script_action) !== -1)
        {
            // 18 ???????????????????????????
            // 1a ????????????
            // eslint-disable-next-line
            var length = 3;
            this.fill_length(script_arr, length);
            // eslint-disable-next-line
            var name = '0x' + script_arr[2] + script_arr[1];
            subitems = [
                <span key={1}>??????</span>,
                <SelectAvatar avatar_list={this.props.avatar_list} key={2} value={name} setProps={(v) => {this.handleUpdateCombo(1, v, length)}} />,
            ];
        }
        else if(script_action === 0x1b)
        {
            // 1b ????????????
            // eslint-disable-next-line
            var length = 2;
            this.fill_length(script_arr, length);
            // eslint-disable-next-line
            var daoju = script_arr[1];
            subitems = [
                <span key={1}>??????</span>,
                <SelectDaoju daoju_list={this.props.daoju_list} key={2} value={daoju} setProps={(v) => {this.handleUpdateCombo(1, v, length)}} />,
            ];
        }
        else if(script_action === 0x1c)
        {
            // 1c ????????????AI
            // eslint-disable-next-line
            var length = 6;
            this.fill_length(script_arr, length);
            // eslint-disable-next-line
            var name = '0x' + script_arr[2] + script_arr[1];
            var ai = utils.dec(script_arr[3]);
            var ai_target = [];
            if([3, 5].indexOf(ai) !== -1)
            {
                var name_tg = '0x' + script_arr[5] + script_arr[4];
                ai_target = [
                    <span key={5}>??????</span>,
                    <SelectAvatar avatar_list={this.props.avatar_list} key={6} value={name_tg} setProps={(v) => {this.handleUpdateCombo(4, v, length)}} />,
                ];
            }
            else if([4, 6].indexOf(ai) !== -1)
            {
                // eslint-disable-next-line
                var x = utils.dec(script_arr[4]);
                // eslint-disable-next-line
                var y = utils.dec(script_arr[5]);
                ai_target = [
                    <span key={7}>??????</span>,
                    <SelectPosition value_x={x}  value_y={y} key={8} setProps={(v) => {this.handleUpdateCombo(4, utils.hex(v.y) + utils.hex(v.x), length)}} />,
                ];
            }
            subitems = [
                <span key={1}>??????</span>,
                <SelectAvatar avatar_list={this.props.avatar_list} key={2} value={name} setProps={(v) => {this.handleUpdateCombo(1, v, length)}} />,
                <span key={3}>AI</span>,
                <SelectAI ai_list={this.props.ai_list} key={4} value={ai} setProps={(v) => {this.handleUpdateCombo(3, v, length)}} />,
            ].concat(ai_target);
        }
        else if(script_action === 0x20)
        {
            // 20 ???????????????
        }
        else if(script_action === 0x21)
        {
            // 21 ????????????????????????
            subitems = [
                <EventsCheck check_list={script_arr} key={1} />
            ];
        }
        else if(script_action === 0x22)
        {
            // 22 ????????????
            // eslint-disable-next-line
            var length = 2 + 30 * 13;
            this.fill_length(script_arr, length);
            subitems = [
                <DeployOppArmy
                    avatar_list={this.props.avatar_list}
                    ai_list={this.props.ai_list}
                    bingzhong_list={this.props.bingzhong_list}
                    deploy_list={script_arr}
                    key={1}
                    setOppArmy={(v) => {this.handleUpdateCombo(2, v.join(' '), 2 + 30 * 13)}}
                />
            ];
        }
        else if([0x24, 0x28].indexOf(script_action) !== -1)
        {
            // 24 ??????????????????
            // 28 ????????????????????????
            // eslint-disable-next-line
            var length = 4;
            this.fill_length(script_arr, length);
            // eslint-disable-next-line
            var name = '0x' + script_arr[2] + script_arr[1];
            var juntuan = utils.dec(script_arr[3]);
            subitems = [
                <span key={1}>??????</span>,
                <SelectAvatar avatar_list={this.props.avatar_list} key={2} value={name} setProps={(v) => {this.handleUpdateCombo(1, v, length)}} />,
                <span key={3}>??????</span>,
                <SelectJuntuan juntuan_list={this.props.juntuan_list} value={juntuan} key={4} setProps={(v) => {this.handleUpdateCombo(3, v, length)}} />,
            ];
        }
        else if(script_action === 0x26)
        {
            // 26 ??????????????????
            // eslint-disable-next-line
            var length = 4;
            this.fill_length(script_arr, length);
            // eslint-disable-next-line
            var x = utils.dec(script_arr[1]);
            // eslint-disable-next-line
            var y = utils.dec(script_arr[2]);
            var ground = utils.dec(script_arr[3]);
            var option_list = [
                '??????',
                '??????',
                '??????',
            ];
            subitems = [
                <span key={1}>??????</span>,
                <SelectPosition value_x={x}  value_y={y} key={2} setProps={(v) => {this.handleUpdateCombo(1, utils.hex(v.y) + utils.hex(v.x), length)}} />,
                <span key={3}>??????</span>,
                <SelectCustom option_list={option_list} value={ground} key={4} setProps={(v) => {this.handleUpdateCombo(3, v, length)}} />,
            ];
        }
        else if(script_action === 0x27)
        {
            // 27 ???????????????
            // eslint-disable-next-line
            var length = 4;
            this.fill_length(script_arr, length);
            // eslint-disable-next-line
            var x = utils.dec(script_arr[1]);
            // eslint-disable-next-line
            var y = utils.dec(script_arr[2]);
            var what = utils.dec(script_arr[3]);
            // eslint-disable-next-line
            var option_list = [
                '??????',
                '??????',
                '??????',
            ];
            subitems = [
                <span key={1}>??????</span>,
                <SelectPosition value_x={x}  value_y={y} key={2} setProps={(v) => {this.handleUpdateCombo(1, utils.hex(v.y) + utils.hex(v.x), length)}} />,
                <span key={3}>??????</span>,
                <SelectCustom option_list={option_list} value={what} key={4} setProps={(v) => {this.handleUpdateCombo(3, v, length)}} />,
            ];
        }
        else if(script_action === 0x2a)
        {
            // 2a ??????????????????
            // eslint-disable-next-line
            var length = 2;
            this.fill_length(script_arr, length);
            // eslint-disable-next-line
            var what = utils.dec(script_arr[1]);
            // eslint-disable-next-line
            var option_list = [
                '????????????',
                '?????????????????????',
                '??????????????????',
                '??????????????????',
            ];
            subitems = [
                <span key={1}>??????</span>,
                <SelectCustom option_list={option_list} value={what} key={2} setProps={(v) => {this.handleUpdateCombo(1, v, length)}} />,
            ];
        }
        else if(script_action === 0x2b)
        {
            // 2b ????????????/????????????????????????
            // eslint-disable-next-line
            var length = 4;
            this.fill_length(script_arr, length);
            // eslint-disable-next-line
            var type = utils.dec(script_arr[1]);
            var count = '0x' + script_arr[3] + script_arr[2];
            // eslint-disable-next-line
            var option1_list = [
                '0x02:???',
                '0x04:????????????????????????',
            ];
            var option2_list = [
                '0x0032:50',
                '0x0064:100',
                '0x00c8:200',
                '0x01f4:500',
                '0x03e8:1000',
                '0x07d0:2000',
            ];
            subitems = [
                <span key={1}>??????</span>,
                <SelectCustom option_list={option1_list} value={type} key={2} setProps={(v) => {this.handleUpdateCombo(1, v, length)}} />,
                <span key={3}>??????</span>,
                <SelectCustom option_list={option2_list} value={count} key={4} setProps={(v) => {this.handleUpdateCombo(2, utils.hex(v, 2), length)}} />,
            ];
        }
        else if(script_action === 0x2d)
        {
            // 2d ??????????????????
            // eslint-disable-next-line
            var length = 3;
            this.fill_length(script_arr, length);
            // eslint-disable-next-line
            var target = utils.dec(script_arr[1]);
            // eslint-disable-next-line
            var what = utils.dec(script_arr[2]);
            // eslint-disable-next-line
            var option1_list = [
                '??????',
                '??????',
            ];
            // eslint-disable-next-line
            var option2_list = [
                '????????????',
                '????????????',
            ];
            subitems = [
                <span key={1}>??????</span>,
                <SelectCustom option_list={option1_list} value={target} key={2} setProps={(v) => {this.handleUpdateCombo(1, v, length)}} />,
                <span key={3}>??????</span>,
                <SelectCustom option_list={option2_list} value={what} key={4} setProps={(v) => {this.handleUpdateCombo(2, v, length)}} />,
            ];
        }
        else if(script_action === 0x2e)
        {
            // 2e ??????????????????
        }
        else if(script_action === 0x2f)
        {
            // 2f ????????????????????????
            // eslint-disable-next-line
            var length = 4;
            this.fill_length(script_arr, length);
            // eslint-disable-next-line
            var name = '0x' + script_arr[2] + script_arr[1];
            var attr = utils.dec(script_arr[3]);
            subitems = [
                <span key={1}>??????</span>,
                <SelectAvatar avatar_list={this.props.avatar_list} key={2} value={name} setProps={(v) => {this.handleUpdateCombo(1, v, length)}} />,
                <span key={3}>??????</span>,
                <SelectNumber count={256} value={attr} key={4} setProps={(v) => {this.handleUpdateCombo(3, v, length)}} />,
            ];
        }
        else if(script_action === 0x30)
        {
            // 30 ?????????????????????????????????????????????
        }
        else if(script_action === 0x32)
        {
            // 32 ??????????????????????????????????????????
        }
        else if(script_action === 0x35)
        {
            // 35 ????????????
            // eslint-disable-next-line
            var length = 4;
            this.fill_length(script_arr, length);
            // eslint-disable-next-line
            var name = '0x' + script_arr[2] + script_arr[1];
            var ani = utils.dec(script_arr[3]);
            subitems = [
                <span key={1}>??????</span>,
                <SelectAvatar avatar_list={this.props.avatar_list} key={2} value={name} setProps={(v) => {this.handleUpdateCombo(1, v, length)}} />,
                <span key={3}>??????</span>,
                <SelectNumber count={16} value={ani} key={4} setProps={(v) => {this.handleUpdateCombo(3, v, length)}} />,
            ];
        }
        else if(script_action === 0x38)
        {
            // 38 ??????????????????
            // eslint-disable-next-line
            var length = 2;
            this.fill_length(script_arr, length);
            var music_id = utils.dec(script_arr[1]);
            subitems = [
                <span key={1}>??????</span>,
                <SelectNumber count={16} value={music_id} key={2} setProps={(v) => {this.handleUpdateCombo(1, v, length)}} />,
            ];
        }
        else if(script_action === 0x39)
        {
            // 39 ??????????????????
            // eslint-disable-next-line
            var length = 4;
            this.fill_length(script_arr, length);
            // eslint-disable-next-line
            var name = '0x' + script_arr[2] + script_arr[1];
            var level = utils.dec(script_arr[3]);
            subitems = [
                <span key={1}>??????</span>,
                <SelectAvatar avatar_list={this.props.avatar_list} key={2} value={name} setProps={(v) => {this.handleUpdateCombo(1, v, length)}} />,
                <span key={3}>????????????</span>,
                <SelectNumber count={256} value={level} key={4} setProps={(v) => {this.handleUpdateCombo(3, v, length)}} />,
            ];
        }
        else if(script_action === 0x3a)
        {
            // 3a ??????????????????
            // eslint-disable-next-line
            var length = 4;
            this.fill_length(script_arr, length);
            // eslint-disable-next-line
            var name = '0x' + script_arr[2] + script_arr[1];
            var bingzhong = utils.dec(script_arr[3]);
            subitems = [
                <span key={1}>??????</span>,
                <SelectAvatar avatar_list={this.props.avatar_list} key={2} value={name} setProps={(v) => {this.handleUpdateCombo(1, v, length)}} />,
                <span key={3}>??????</span>,
                <SelectBingzhong bingzhong_list={this.props.bingzhong_list} value={bingzhong} key={4} setProps={(v) => {this.handleUpdateCombo(3, v, length)}} />,
            ];
        }
        else if(script_action === 0x3b)
        {
            // 3b ????????????????????????
        }
        else if(script_action === 0x3c)
        {
            // 3c ????????????
        }
        else if(script_action === 0x3d)
        {
            // 3d ????????????/????????????
        }
        return (
            <Form.Group>
                <SelectAction  action_list={this.props.action_list} value={script_action} setProps={(v) => {this.handleUpdateCombo(0, v, 0)}} />
                {subitems.map((item) => {return item})}
            </Form.Group>
        )
    }
}
class SelectTxt extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            value: props.value,
        }
        this.handleSelect = this.handleSelect.bind(this);
    }
    handleSelect(e){
        var value = e.target.value;
        this.setState({
            value: value
        }, () => {this.props.setProps(value)})
    }
    get_name(id_hex) {
        for(var i in this.props.avatar_list) {
            if(this.props.avatar_list[i].id_hex === id_hex)
                return this.props.avatar_list[i].name;
        }
        return 'X';
    }
    render () {
        return (
            <Form.Control as="select" onChange={this.handleSelect} value={this.state.value}>
            {
                this.props.txt_list.map((item, i) => {
                    var value = item.addr;
                    var txt = '';
                    if(item.name === '')
                        txt = item.txt;
                    else
                        txt = '(' + item.addr + ')[' + this.get_name(item.name) + ']' + item.txt;
                    var option = txt.substring(0, 30) + '(???' + txt.length + '???)';
                    return <option value={value} key={i}>{option}</option>
                })
            }
            </Form.Control>
        )
    }
}
class EventsCheck extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            check_list: props.check_list,
        }
        this.handleSelect = this.handleSelect.bind(this);
    }
    handleAdd(type){
        var id = 0;
        var check_list = this.state.check_list;
        var passed_cnt = utils.dec(check_list[2]);
        if(type === 100)
        {
            id = 3 + passed_cnt;
            var old_cnt = utils.dec(check_list[2]);
            check_list[2] = utils.hex(old_cnt+1);
            check_list.splice(id, 0, '00');
        }
        else if(type === 200)
        {
            var nopass_cnt = utils.dec(check_list[3 + passed_cnt]);
            id = 4 + passed_cnt + nopass_cnt;
            // eslint-disable-next-line
            var old_cnt = utils.dec(check_list[3+passed_cnt]);
            check_list[3+passed_cnt] = utils.hex(old_cnt+1);
            check_list.splice(id, 0, '00');
        }
        this.setState({
            check_list: check_list,
        }, () => console.log(this.state.check_list))
    }
    handleDel(type){
        var id = 0;
        var check_list = this.state.check_list;
        var passed_cnt = utils.dec(check_list[2]);
        if(type >= 100 && type < 200)
        {
            id = 3 + type - 100;
            var old_cnt = utils.dec(check_list[2]);
            check_list[2] = utils.hex(old_cnt-1);
            check_list.splice(id, 1);
        }
        else if(type >= 200 && type < 300)
        {
            id = 4 + passed_cnt + type - 200;
            // eslint-disable-next-line
            var old_cnt = utils.dec(check_list[3+passed_cnt]);
            check_list[3+passed_cnt] = utils.hex(old_cnt-1);
            check_list.splice(id, 1);
        }
        this.setState({
            check_list: check_list,
        }, () => console.log(this.state.check_list))
    }
    handleSelect(type, value){
        var id = 0;
        if(type === 0)
            id = 1;
        else if(type >= 100 && type < 200)
            id = 3 + type - 100;
        else if(type >= 200 && type < 300)
        {
            var passed_cnt = utils.dec(this.state.check_list[2]);
            id = 4 + passed_cnt + type - 200;
        }
        this.setState({
            check_list: this.state.check_list.map((item, i) => i === id ? utils.hex(value) : item)
        }, () => console.log(this.state.check_list))
        // }, () => {this.props.setProps(value)})
    }
    render () {
        var check_list = this.state.check_list;
        var jump_cnt = utils.dec(check_list[1]);
        var passed_cnt = utils.dec(check_list[2]);
        var nopass_cnt = utils.dec(check_list[3+passed_cnt]);
        return (
            <Form.Group>
                <span key={1}>????????????????????????</span>
                <SelectNumber count={256} value={jump_cnt} key={2} setProps={(v) => {this.handleSelect(0, v)}} />
                <span key={3}>???????????????</span>
                {
                    Array.from(new Array(passed_cnt).keys()).map((i) => {
                        return <InputGroup key={100+i}>
                                <SelectNumber count={256} value={utils.dec(check_list[3+i])} setProps={(v) => {this.handleSelect(100+i, v)}} />
                                <InputGroup.Append>
                                    <Button variant="danger" onClick={() => {this.handleDel(100+i)}}>-</Button>
                                </InputGroup.Append>
                            </InputGroup>
                    })
                }
                <Button variant="primary" onClick={() => {this.handleAdd(100)}}>+</Button>
                <span key={4}>???????????????</span>
                {
                    Array.from(new Array(nopass_cnt).keys()).map((i) => {
                        return <InputGroup key={200+i}>
                                <SelectNumber count={256} value={utils.dec(check_list[4+passed_cnt+i])} setProps={(v) => {this.handleSelect(200+i, v)}} />
                                <InputGroup.Append>
                                    <Button variant="danger" onClick={() => {this.handleDel(200+i)}}>-</Button>
                                </InputGroup.Append>
                            </InputGroup>
                    })
                }
                <Button variant="primary" onClick={() => {this.handleAdd(200)}}>+</Button>
            </Form.Group>
        )
    }
}
class DeployOppArmy extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            deploy_list: props.deploy_list,
        }
        this.handleUpdateArmy = this.handleUpdateArmy.bind(this);
    }
    handleUpdateArmy(num, idx, value) {
        var deploy_list = this.state.deploy_list;
        var offset = 2 + num * 13 + idx;
        if(typeof(value) == 'number')
            value = utils.hex(value);
        else
            value = value.replace('0x', '');
        if(value.length === 2)
        {
            deploy_list[offset] = value;
            this.setState({
                deploy_list: deploy_list,
            }, () => {
                this.props.setOppArmy(this.state.deploy_list);
            });
        }
        else if(value.length === 4)
        {
            var v1 = value.substr(0, 2);
            var v2 = value.substr(2, 2);
            deploy_list[offset] = v2;
            deploy_list[offset+1] = v1;
            this.setState({
                deploy_list: deploy_list,
            }, () => {
                this.props.setOppArmy(this.state.deploy_list);
            });
        }
    }
    render () {
        var deploy_list = this.state.deploy_list;
        var appear_list = [
            '??????',
            '??????',
        ];
        return (
            <Container fluid="true">
                {
                    Array.from(new Array(30).keys()).map((i) => {
                        var start = 2 + 13 * i;
                        var name = '0x' + deploy_list[start+1] + deploy_list[start];
                        var x = utils.dec(deploy_list[start+2]);
                        var y = utils.dec(deploy_list[start+3]);
                        var appear = utils.dec(deploy_list[start+4]);
                        var event = utils.dec(deploy_list[start+5]);
                        var dir = utils.dec(deploy_list[start+6]);
                        var fubing = utils.dec(deploy_list[start+7]);
                        var ai = utils.dec(deploy_list[start+8]);
                        var bingzhong = utils.dec(deploy_list[start+11]);
                        var level = utils.dec(deploy_list[start+12]);
                        var ai_target = '';
                        if([3, 5].indexOf(ai) !== -1)
                        {
                            var name_tg = '0x' + deploy_list[10] + deploy_list[9];
                            ai_target = <span>
                                    <span>??????</span>
                                    <SelectAvatar avatar_list={this.props.avatar_list} value={name_tg} setProps={(v) => {this.handleUpdateArmy(i, 9, v)}} />
                                </span>
                        }
                        else if([4, 6].indexOf(ai) !== -1)
                        {
                            // eslint-disable-next-line
                            var x = utils.dec(deploy_list[9]);
                            // eslint-disable-next-line
                            var y = utils.dec(deploy_list[10]);
                            ai_target = <span>
                                    <span>??????</span>
                                    <SelectPosition value_x={x}  value_y={y} setProps={(v) => {this.handleUpdateArmy(i, 9, v)}} />
                                </span>
                        }
                        return <Form.Group as={Row} key={i}>
                                    <span>??????{i+1}</span>
                                    <SelectAvatar avatar_list={this.props.avatar_list} value={name} setProps={(v) => {this.handleUpdateArmy(i, 0, v)}} />
                                    <span>??????</span>
                                    <SelectPosition value_x={x}  value_y={y} setProps={(v) => {this.handleUpdateArmy(i, 2, utils.hex(v.y) + utils.hex(v.x))}} />
                                    <span>??????</span>
                                    <SelectCustom option_list={appear_list} value={appear} setProps={(v) => {this.handleUpdateArmy(i, 4, v)}} />
                                    <span>??????</span>
                                    <SelectNumber count={256} value={event} setProps={(v) => {this.handleUpdateArmy(i, 5, v)}} />
                                    <span>??????</span>
                                    <SelectNumber count={4} value={dir} setProps={(v) => {this.handleUpdateArmy(i, 6, v)}} />
                                    <span>??????</span>
                                    <SelectNumber count={2} value={fubing} setProps={(v) => {this.handleUpdateArmy(i, 7, v)}} />
                                    <span>AI</span>
                                    <SelectAI ai_list={this.props.ai_list} value={ai} setProps={(v) => {this.handleUpdateArmy(i, 8, v)}} />
                                    {ai_target}
                                    <span>??????</span>
                                    <SelectBingzhong bingzhong_list={this.props.bingzhong_list} value={bingzhong} setProps={(v) => {this.handleUpdateArmy(i, 11, v)}} />
                                    <span>??????</span>
                                    <SelectLevel value={level} setProps={(v) => {this.handleUpdateArmy(i, 12, v)}} />
                                </Form.Group>
                    })
                }
            </Container>
        )
    }
}
class DeployMyArmy extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            deploy_list: props.deploy_list,
        }
        this.handleUpdateArmy = this.handleUpdateArmy.bind(this);
    }
    handleUpdateSetting(offset, value) {
        var deploy_list = this.state.deploy_list;
        if(typeof(value) == 'number')
            value = utils.hex(value);
        else
            value = value.replace('0x', '');
        if(value.length === 2)
        {
            deploy_list[offset] = value;
            this.setState({
                deploy_list: deploy_list,
            }, () => {
                this.props.setMyArmy(this.state.deploy_list);
            });
        }
        else if(value.length === 4)
        {
            var v1 = value.substr(0, 2);
            var v2 = value.substr(2, 2);
            deploy_list[offset] = v2;
            deploy_list[offset+1] = v1;
            this.setState({
                deploy_list: deploy_list,
            }, () => {
                this.props.setMyArmy(this.state.deploy_list);
            });
        }
    }
    handleUpdateArmy(num, idx, value) {
        var deploy_list = this.state.deploy_list;
        var offset = 2 + 10 + num * 9 + idx;
        if(typeof(value) == 'number')
            value = utils.hex(value);
        else
            value = value.replace('0x', '');
        if(value.length === 2)
        {
            deploy_list[offset] = value;
            this.setState({
                deploy_list: deploy_list,
            }, () => {
                this.props.setMyArmy(this.state.deploy_list);
            });
        }
        else if(value.length === 4)
        {
            var v1 = value.substr(0, 2);
            var v2 = value.substr(2, 2);
            deploy_list[offset] = v2;
            deploy_list[offset+1] = v1;
            this.setState({
                deploy_list: deploy_list,
            }, () => {
                this.props.setMyArmy(this.state.deploy_list);
            });
        }
    }
    render () {
        var deploy_list = this.state.deploy_list;
        var appear_list = [
            '??????',
            '??????',
        ];
        var no_retreat = utils.dec(deploy_list[1]);
        var round_cnt = utils.dec(deploy_list[2]);
        var inherit_round = utils.dec(deploy_list[3]);
        var opp_master = '0x' + deploy_list[7] + deploy_list[6];
        var my_master = '0x' + deploy_list[11] + deploy_list[10];
        return (
            <Container fluid="true">
                <Form.Group as={Row}>
                    <span>????????????</span>
                    <SelectNumber count={2} value={no_retreat} setProps={(v) => {this.handleUpdateSetting(1, v)}} />
                    <span>?????????</span>
                    <SelectNumber count={100} value={round_cnt} setProps={(v) => {this.handleUpdateSetting(2, v)}} />
                    <span>???????????????</span>
                    <SelectNumber count={2} value={inherit_round} setProps={(v) => {this.handleUpdateSetting(3, v)}} />
                    <span>????????????</span>
                    <SelectAvatar avatar_list={this.props.avatar_list} value={opp_master} setProps={(v) => {this.handleUpdateSetting(6, v)}} />
                    <span>????????????</span>
                    <SelectAvatar avatar_list={this.props.avatar_list} value={my_master} setProps={(v) => {this.handleUpdateSetting(10, v)}} />
                </Form.Group>
                {
                    Array.from(new Array(15).keys()).map((i) => {
                        var start = 12 + 9 * i;
                        var name = '0x' + deploy_list[start+1] + deploy_list[start];
                        var x = utils.dec(deploy_list[start+2]);
                        var y = utils.dec(deploy_list[start+3]);
                        var appear = utils.dec(deploy_list[start+5]);
                        var event = utils.dec(deploy_list[start+6]);
                        var dir = utils.dec(deploy_list[start+7]);
                        var fubing = utils.dec(deploy_list[start+8]);
                        return <Form.Group as={Row} key={i}>
                                    <span>??????{i+1}</span>
                                    <SelectAvatar avatar_list={this.props.avatar_list} value={name} setProps={(v) => {this.handleUpdateArmy(i, 0, v)}} />
                                    <span>??????</span>
                                    <SelectPosition value_x={x}  value_y={y} setProps={(v) => {this.handleUpdateArmy(i, 2, utils.hex(v.y) + utils.hex(v.x))}} />
                                    <span>??????</span>
                                    <SelectCustom option_list={appear_list} value={appear} setProps={(v) => {this.handleUpdateArmy(i, 5, v)}} />
                                    <span>??????</span>
                                    <SelectNumber count={256} value={event} setProps={(v) => {this.handleUpdateArmy(i, 6, v)}} />
                                    <span>??????</span>
                                    <SelectNumber count={4} value={dir} setProps={(v) => {this.handleUpdateArmy(i, 7, v)}} />
                                    <span>??????</span>
                                    <SelectNumber count={2} value={fubing} setProps={(v) => {this.handleUpdateArmy(i, 8, v)}} />
                                </Form.Group>
                    })
                }
            </Container>
        )
    }
}
export default ComboScript;