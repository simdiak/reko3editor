import React from 'react';
import {Form} from 'react-bootstrap';
import SelectAvatar from './SelectAvatar';
import SelectPosition from './SelectPosition';
import SelectNumber from './SelectNumber';
import SelectTrigger from './SelectTrigger';
import * as utils from './Utils';

class ComboSection extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            instr_arr: props.instr_code.split(' '),
        }
        this.handleUpdateCombo = this.handleUpdateCombo.bind(this);
    }
    handleUpdateCombo(idx, value) {
        if(typeof(value) == 'number')
            value = utils.hex(value);
        else
            value = value.replace('0x', '');
        if(value.length === 2)
        {
            this.setState({
                instr_arr: this.state.instr_arr.map((item, i) => i === idx ? value : item)
            }, () => {this.props.setProps(this.state.instr_arr.join(' '))});
        }
        else if(value.length === 4)
        {
            var v1 = value.substr(0, 2);
            var v2 = value.substr(2, 2);
            this.setState({
                instr_arr: this.state.instr_arr.map((item, i) => i === idx ? v2 : (i === idx + 1 ? v1 : item))
            }, () => {this.props.setProps(this.state.instr_arr.join(' '))});
        }
    }
    render () {
        var instr_arr = this.state.instr_arr;
        var instr_action = utils.dec(instr_arr[0]);
        var section_id = utils.dec(instr_arr[1]);
        var subitems = [
            // 段号
            <span key={0}>段号</span>,
            <SelectNumber count={256} value={section_id} key={1} setProps={(v) => {this.handleUpdateCombo(1, v)}} />,
        ]
        if([0x00, 0x01].indexOf(instr_action) !== -1)
        {
            // 00 顺序执行
            // 01 分支执行
        }
        else if(instr_action === 0x02)
        {
            // 02 进入城市建筑
        }
        else if(instr_action === 0x03)
        {
            // 03 对话
            var name = '0x' + instr_arr[3] + instr_arr[2];
            subitems = subitems.concat([
                <span key={2}>目标</span>,
                <SelectAvatar avatar_list={this.props.avatar_list} key={3} value={name} setProps={(v) => {this.handleUpdateCombo(2, v)}} />,
            ])
        }
        else if(instr_action === 0x04)
        {
            // 04 单挑
            var name1 = '0x' + instr_arr[3] + instr_arr[2];
            var name2 = '0x' + instr_arr[5] + instr_arr[4];
            subitems = subitems.concat([
                <span key={2}>胜方</span>,
                <SelectAvatar avatar_list={this.props.avatar_list} key={3} value={name1} setProps={(v) => {this.handleUpdateCombo(2, v)}} />,
                <span key={4}>负方</span>,
                <SelectAvatar avatar_list={this.props.avatar_list} key={5} value={name2} setProps={(v) => {this.handleUpdateCombo(4, v)}} />,
            ])
        }
        else if(instr_action === 0x05)
        {
            // 05 进入城市
        }
        else if(instr_action === 0x06)
        {
            // 06 战场移到点
            // eslint-disable-next-line
            var name = '0x' + instr_arr[3] + instr_arr[2];
            var x = utils.dec(instr_arr[4]);
            var y = utils.dec(instr_arr[5]);
            subitems = subitems.concat([
                <span key={2}>人物</span>,
                <SelectAvatar avatar_list={this.props.avatar_list} key={3} value={name} setProps={(v) => {this.handleUpdateCombo(2, v)}} />,
                <span key={4}>坐标</span>,
                <SelectPosition value_x={x}  value_y={y} key={5} setProps={(v) => {this.handleUpdateCombo(4, utils.hex(v.y) + utils.hex(v.x))}} />,
            ])
        }
        else if(instr_action === 0x07)
        {
            // 07 战斗胜利
        }
        else if(instr_action === 0x08)
        {
            // 08 战斗失败
        }
        else if(instr_action === 0x09)
        {
            // 09 指定回合
            var round = utils.dec(instr_arr[2]);
            subitems = subitems.concat([
                <span key={2}>回合</span>,
                <SelectNumber count={100} value={round} key={3} setProps={(v) => {this.handleUpdateCombo(2, v)}} />,
            ])
        }
        else if(instr_action === 0x0a)
        {
            // 0a 未知
        }
        else if(instr_action === 0x0b)
        {
            // 0b 战场移到区域
            // eslint-disable-next-line
            var name = '0x' + instr_arr[3] + instr_arr[2];
            var x0 = utils.dec(instr_arr[4]);
            var y0 = utils.dec(instr_arr[5]);
            var x1 = utils.dec(instr_arr[6]);
            var y1 = utils.dec(instr_arr[7]);
            subitems = subitems.concat([
                <span key={2}>人物</span>,
                <SelectAvatar avatar_list={this.props.avatar_list} key={3} value={name} setProps={(v) => {this.handleUpdateCombo(2, v)}} />,
                <span key={4}>左上坐标</span>,
                <SelectPosition value_x={x0}  value_y={y0} key={5} setProps={(v) => {this.handleUpdateCombo(4, utils.hex(v.y) + utils.hex(v.x))}} />,
                <span key={6}>右下坐标</span>,
                <SelectPosition value_x={x1}  value_y={y1} key={7} setProps={(v) => {this.handleUpdateCombo(6, utils.hex(v.y) + utils.hex(v.x))}} />,
            ])
        }
        else if(instr_action === 0x0c)
        {
            // 0c 撤退
        }
        return (
            <Form inline>
                <SelectTrigger  trigger_list={this.props.trigger_list} value={instr_action} setProps={(v) => {this.handleUpdateCombo(0, v)}} />
                {subitems.map((item) => {return item})}
            </Form>
        )
    }
}
export default ComboSection;