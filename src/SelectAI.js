import React from 'react';
import {Form} from 'react-bootstrap';
import * as utils from './Utils';

class SelectAI extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            value: props.value,
        }
        this.handleSelect = this.handleSelect.bind(this);
    }
    get_name(i) {
        return this.props.ai_list[i];
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
                this.props.ai_list.map((item, i) => {
                    var value = i;
                    var option = '0x' + utils.hex(i) + ':' + this.get_name(i);
                    return <option value={value} key={value}>{option}</option>
                })
            }
            </Form.Control>
        )
    }
}

export default SelectAI;
