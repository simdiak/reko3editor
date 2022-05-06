import React from 'react';
import {Form} from 'react-bootstrap';
import * as utils from './Utils';

class SelectCustom extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            value: Number(this.props.value),
            option_list: this.props.option_list,
        }
        this.handleSelect = this.handleSelect.bind(this);
    }
    handleSelect(e) {
        this.setState({
            value: Number(e.target.value),
        });
        this.props.setProps(Number(e.target.value));
    }
    render () {
        return (
            <Form.Control as="select" onChange={this.handleSelect} value={this.state.value}>
            {
                this.props.option_list.map((item, i) => {
                    var value = i;
                    var option = item;
                    if(item.startsWith('0x'))
                        value = utils.dec(item.split(':')[0].replace('0x', ''));
                    else
                        option = '0x' + utils.hex(value) + ':' + item;
                    return <option value={value} key={i}>{option}</option>
                })
            }
            </Form.Control>
        )
    }
}
export default SelectCustom;