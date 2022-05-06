import React from 'react';
import {Form} from 'react-bootstrap';
import * as utils from './Utils';

class SelectPosition extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            x: Number(this.props.value_x),
            y: Number(this.props.value_y),
        }
        this.handleSelectX = this.handleSelectX.bind(this);
        this.handleSelectY = this.handleSelectY.bind(this);
    }
    handleSelectX(e) {
        var x = Number(e.target.value);
        this.setState({x: x});
        this.props.setProps({x: x, y: this.state.y});
    }
    handleSelectY(e) {
        var y = Number(e.target.value);
        this.setState({y: y});
        this.props.setProps({x: this.state.x, y: y});
    }
    render () {
        return (
            <Form.Group inline="true">
                <Form.Control as="select" onChange={this.handleSelectX} value={this.state.x}>
                {
                    Array.from(new Array(100).keys()).map((n) => {
                        var value = n;
                        var option = '0x' + utils.hex(n) + ':X=' + value;
                        return <option value={value} key={value}>{option}</option>
                    })
                }
                </Form.Control>
                <Form.Control as="select" onChange={this.handleSelectY} value={this.state.y}>
                {
                    Array.from(new Array(100).keys()).map((n) => {
                        var value = n;
                        var option = '0x' + utils.hex(n) + ':Y=' + value;
                        return <option value={value} key={value}>{option}</option>
                    })
                }
                </Form.Control>
            </Form.Group>
        )
    }
}

export default SelectPosition;
