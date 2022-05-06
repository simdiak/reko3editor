import React from 'react';
import {Form} from 'react-bootstrap';
import * as utils from './Utils';

class SelectNumber extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            value: Number(this.props.value),
            count: this.props.count,
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
                Array.from(new Array(this.state.count).keys()).map((n) => {
                    var value = n;
                    var option = '0x' + utils.hex(n) + ': ' + value;
                    return <option value={value} key={value}>{option}</option>
                })
            }
            </Form.Control>
        )
    }
}

export default SelectNumber;

