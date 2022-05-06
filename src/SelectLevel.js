import React from 'react';
import {Form} from 'react-bootstrap';
import * as utils from './Utils';

class SelectLevel extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            value: Number(this.props.value),
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
                Array.from(new Array(100).keys()).map((n) => {
                    var value = n;
                    var option = '0x' + utils.hex(n) + ':LV ' + value;
                    return <option value={value} key={value}>{option}</option>
                })
            }
            </Form.Control>
        )
    }
}

export default SelectLevel;
