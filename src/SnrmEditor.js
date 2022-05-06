import React from 'react';
import {Container, Row, Col, Form} from 'react-bootstrap';
import SelectAvatar from './SelectAvatar';

class SnrmEditor extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            snrm_list: [],
        }
        this.handleUpdateSnrm = this.handleUpdateSnrm.bind(this);
    }
    static getDerivedStateFromProps(props){
        return {
            snrm_list: props.snrm_list,
        }
    }
    handleUpdateSnrm(id, value){
        this.setState({
            snrm_list: this.state.snrm_list.map((item, i) => i === id ? (item.txt_list = value,item) : item)
        }, () => {this.props.setProps(this.state.snrm_list)});
    }
    render () {
        return (
            <Container fluid="true">
            {
                this.state.snrm_list.map((snrm_item, id) => {
                    return <Container fluid="true" key={id}>
                        <Row>
                            <Col>第{id}子章</Col>
                        </Row>
                        <Row>
                            <TxtList avatar_list={this.props.avatar_list} txt_list={snrm_item.txt_list} setProps={(v) => {this.handleUpdateSnrm(id, v)}}></TxtList>
                        </Row>
                    </Container>
                })
            }
            </Container>
        )
    }
}
class TxtList extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            txt_list: [],
        };
        this.handleUpdateTxt = this.handleUpdateTxt.bind(this);
    }
    static getDerivedStateFromProps(props){
        return {
            txt_list: props.txt_list,
        }
    }
    handleUpdateTxt(e){
        var id = Number(e.target.id);
        var value = e.target.value;
        this.setState({
            txt_list: this.state.txt_list.map((item, i) => i === id ? (item.txt = value,item) : item)
        }, () => {this.props.setProps(this.state.txt_list)});
    }
    setAvatar(id, avatar_id){
        if(avatar_id === '0xffff')
            avatar_id = '';
        this.setState({
            txt_list: this.state.txt_list.map((item, i) => i === id ? (item.name = avatar_id,item) : item)
        }, () => {this.props.setProps(this.state.txt_list)});
    }
    render () {
        return (
            <Col>
            {
                this.state.txt_list.map((txt_item, id) => {
                    var name = txt_item.name;
                    if(txt_item.name === '')
                        name = '0xffff';
                    return <Container fluid="true" key={id}>
                        <Form>
                            <Form.Group as={Row}>
                                <Form.Label column sm="1">{id}:{txt_item.addr}</Form.Label>
                                <Col sm="2">
                                    <SelectAvatar avatar_list={this.props.avatar_list} value={name} setProps={(v) => this.setAvatar(id, v)} />
                                </Col>
                                <Col sm="9">
                                    <Form.Control type="input" value={txt_item.txt} onChange={this.handleUpdateTxt} />
                                </Col>
                            </Form.Group>
                        </Form>
                    </Container>
                })
            }
            </Col>
        )
    }
}
export default SnrmEditor;