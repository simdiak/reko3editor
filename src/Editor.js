import React from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import {Container, Row, Col, Button, Tabs, Tab} from 'react-bootstrap';
import {Navbar, Nav, Form , FormControl} from 'react-bootstrap';
import * as settings from './Settings';
import SelectAvatar from './SelectAvatar';
import SelectLevel from './SelectLevel';
import SelectDaoju from './SelectDaoju';
import SelectBingzhong from './SelectBingzhong';
import SelectJuntuan from './SelectJuntuan';
import SelectAI from './SelectAI';
import SelectAction from './SelectAction';
import SelectPosition from './SelectPosition';
import SelectTrigger from './SelectTrigger';
import ComboSection from './ComboSection';
import ComboScript from './ComboScript';
import SnrdEditor from './SnrdEditor';
import SnrmEditor from './SnrmEditor';

class Reko3Editor extends React.Component {
    render () {
        return (
            <Container fluid="true">
            <TopNav />
            <ModTabs />
            </Container>
        )
    }
}
class TopNav extends React.Component {
    render () {
        return (
            <Navbar bg="primary" variant="dark">
                <Navbar.Brand href="#home">三国志英杰传编辑器</Navbar.Brand>
                    <Nav className="mr-auto">
                        <Nav.Link href="#home">Home</Nav.Link>
                        <Nav.Link href="#features">Features</Nav.Link>
                        <Nav.Link href="#pricing">Pricing</Nav.Link>
                    </Nav>
                    <Form inline>
                        <FormControl type="text" placeholder="Search" className="mr-sm-2" />
                        <Button variant="outline-light">Search</Button>
                    </Form>
            </Navbar>
        )
    }
}
class ModTabs extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            avatar_list: [],
            action_list: [],
            ai_list: [],
            daoju_list: [],
            bingzhong_list: [],
            juntuan_list: [],
            trigger_list: [],
            snrd_list: [],
            snrm_list: [],
        }
        fetch(settings.base_url + '/load_resource', {})
            .then((response) => {return response.json()})
            .then((json) => {
                this.setState({avatar_list: json.avatar_list});
                this.setState({action_list: json.action_list});
                this.setState({ai_list: json.ai_list});
                this.setState({daoju_list: json.daoju_list});
                this.setState({bingzhong_list: json.bingzhong_list});
                this.setState({juntuan_list: json.juntuan_list});
                this.setState({trigger_list: json.trigger_list});
            });
        fetch(settings.base_url + '/load_snrd/0', {}).then((response) => {return response.json()}).then((json) => {this.setState({snrd_list: json})});
        fetch(settings.base_url + '/load_snrm/0', {}).then((response) => {return response.json()}).then((json) => {this.setState({snrm_list: json})});
    }
    render_ () {
        if(this.state.snrm_list.length === 0)
        {
            return (
                <span>waiting</span>
            )
        }
        return (
                    <EditorTest
                        avatar_list={this.state.avatar_list}
                        action_list={this.state.action_list}
                        ai_list={this.state.ai_list}
                        daoju_list={this.state.daoju_list}
                        bingzhong_list={this.state.bingzhong_list}
                        juntuan_list={this.state.juntuan_list}
                        trigger_list={this.state.trigger_list}
                        snrm_list={this.state.snrm_list}
                    />
        )
    }
    render () {
        if(this.state.snrm_list.length === 0)
        {
            return (
                <span>waiting</span>
            )
        }
        return (
            <Tabs defaultActiveKey="snrd-editor" id="uncontrolled-tab-example">
                <Tab eventKey="snrd-editor" title="剧情编辑">
                    <SnrdEditor
                        trigger_list={this.state.trigger_list}
                        avatar_list={this.state.avatar_list}
                        action_list={this.state.action_list}
                        ai_list={this.state.ai_list}
                        juntuan_list={this.state.juntuan_list}
                        bingzhong_list={this.state.bingzhong_list}
                        daoju_list={this.state.daoju_list}
                        snrd_list={this.state.snrd_list}
                        snrm_list={this.state.snrm_list}
                        setProps={v => this.setState({snrd_list: v})}
                    />
                </Tab>
                <Tab eventKey="snrm-editor" title="文本编辑">
                    <SnrmEditor
                        snrm_list={this.state.snrm_list}
                        avatar_list={this.state.avatar_list}
                        setProps={v => this.setState({snrm_list: v})}
                    />
                </Tab>
                <Tab eventKey="test-field" title="组件测试">
                    <EditorTest
                        avatar_list={this.state.avatar_list}
                        action_list={this.state.action_list}
                        ai_list={this.state.ai_list}
                        daoju_list={this.state.daoju_list}
                        bingzhong_list={this.state.bingzhong_list}
                        juntuan_list={this.state.juntuan_list}
                        trigger_list={this.state.trigger_list}
                        snrm_list={this.state.snrm_list}
                    />
                </Tab>
            </Tabs>
        )
    }
}
class EditorTest extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            avatar: '0x000a',
            level: 30,
            daoju: 2,
            bingzhong: 10,
            juntuan: 3,
            trigger: 2,
            ai: 3,
            x: 4,
            y: 5,
            action: 1,
            instr_code: "01 01 0e 01 00 00 00 00 13 14",
            script_code: "08 6f 01",
            opp_script_code: "22 00 "+
                                        "05 00 03 09 00 00 01 00 02 00 00 06 05 "+
                                        "14 00 05 0a 01 5a 03 01 00 00 00 04 02 "+
                                        "15 00 04 09 00 00 01 00 00 00 00 00 02 "+
                                        "1b 00 06 09 00 00 01 00 00 00 00 00 02 "+
                                        "00 01 0b 08 00 00 01 00 00 00 00 00 01 "+
                                        "01 01 0b 0a 00 00 01 00 00 00 00 00 01 "+
                                        "02 01 0b 0c 00 00 01 00 00 00 00 00 01 "+
                                        "ff ff 0a 0b 00 00 01 00 00 00 00 0f 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00 ff ff 00 00 00 00 01 00 00 00 00 10 00",
            my_script_code: "03 00 "+
                                        "1e 00 00 01 05 00 00 01 00 00 "+
                                        "00 00 16 09 01 00 00 03 00 "+
                                        "01 00 14 0a 01 00 00 03 00 "+
                                        "02 00 14 09 01 00 00 03 00 "+
                                        "0c 00 10 07 01 01 00 03 00 "+
                                        "0f 00 10 06 01 01 01 03 00 "+
                                        "ff ff 00 00 00 00 00 03 00 ff ff 00 00 00 00 00 03 00 ff ff 00 00 00 00 00 03 00 ff ff 00 00 00 00 00 03 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00 ff ff 00 00 00 00 00 ff 00"
        }
        this.handleClickIt = this.handleClickIt.bind(this);
    }
    handleClickIt(){
        console.log(this.state);
    }
    render () {
        return (
        <Container fluid="true">
        <Row>
            <Col>
                <Form inline>
                    <SelectAvatar avatar_list={this.props.avatar_list} value={this.state.avatar} setProps={v => this.setState({avatar: v})}/>
                    <SelectLevel value={this.state.level}  setProps={v => this.setState({level: v})} />
                    <SelectDaoju daoju_list={this.props.daoju_list} value={this.state.daoju}  setProps={v => this.setState({daoju: v})} />
                    <SelectBingzhong bingzhong_list={this.props.bingzhong_list} value={this.state.bingzhong}  setProps={v => this.setState({bingzhong: v})} />
                    <SelectJuntuan juntuan_list={this.props.juntuan_list} value={this.state.juntuan}  setProps={v => this.setState({juntuan: v})} />
                    <SelectTrigger trigger_list={this.props.trigger_list} value={this.state.trigger}  setProps={v => this.setState({trigger: v})} />
                    <SelectAI ai_list={this.props.ai_list} value={this.state.ai}  setProps={v => this.setState({ai: v})} />
                    <SelectAction action_list={this.props.action_list} value={this.state.action}  setProps={v => this.setState({action: v})} />
                    <SelectPosition value_x={this.state.x}  value_y={this.state.y} setProps={pos => this.setState({x: pos.x, y:pos.y})} />
                    <Button variant="primary" onClick={this.handleClickIt}>aaa</Button>
                </Form>
            </Col>
        </Row>
        <Row>
            <Col>
                <ComboSection 
                    trigger_list={this.props.trigger_list}
                    avatar_list={this.props.avatar_list}
                    instr_code={this.state.instr_code}
                    setProps={(v) => this.setState({instr_code: v})}
                />
            </Col>
        </Row>
        <Row>
            <Col>
                <ComboScript
                    trigger_list={this.props.trigger_list}
                    avatar_list={this.props.avatar_list}
                    action_list={this.props.action_list}
                    ai_list={this.props.ai_list}
                    juntuan_list={this.props.juntuan_list}
                    bingzhong_list={this.props.bingzhong_list}
                    daoju_list={this.props.daoju_list}
                    snrm_list={this.props.snrm_list}
                    script_code={this.state.script_code}
                    setProps={(v) => {}}
                />
            </Col>
        </Row>
        </Container>
        )
    }
}
export default Reko3Editor;