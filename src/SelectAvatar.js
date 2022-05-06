import React from 'react';
import {Form} from 'react-bootstrap';

class SelectAvatar extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            value: props.value,
        }
        this.handleSelect = this.handleSelect.bind(this);
    }
    get_name(id_hex) {
        for(var i in this.props.avatar_list) {
            if(this.props.avatar_list[i].id_hex === id_hex)
                return this.props.avatar_list[i].name;
        }
        return 'X';
    }
    handleSelect(e) {
        this.setState({
            value: e.target.value,
            name: this.get_name(e.target.value),
        });
        this.props.setProps(e.target.value);
    }
    render () {
        return (
            <Form.Control as="select" onChange={this.handleSelect} value={this.state.value}>
            {
                this.props.avatar_list.map((item) => {
                    var value = item.id_hex;
                    var option = item.id_hex + ':' + item.name;
                    return <option value={value} key={value}>{option}</option>
                })
            }
            </Form.Control>
        )
    }
}

export default SelectAvatar;