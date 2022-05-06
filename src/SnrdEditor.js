import React from 'react';
import {Container, Row, Col, Form} from 'react-bootstrap';
import ComboSection from './ComboSection';
import ComboScript from './ComboScript';

class SnrdEditor extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            snrd_list: [],
        }
        this.handleUpdateSnrd = this.handleUpdateSnrd.bind(this);
    }
    static getDerivedStateFromProps(props){
        return {
            snrd_list: props.snrd_list,
        }
    }
    handleUpdateSnrd(id, value){
        id = Number(id);
        this.setState({
            snrd_list: this.state.snrd_list.map((item, i) => i === id ? (item.paragraph_list = value,item) : item)
        }, () => {this.props.setProps(this.state.snrd_list)});
    }
    render () {
        return (
            <Container fluid="true">
            {
                this.state.snrd_list.map((snrd_item, id) => {
                    return <Container fluid="true" key={id}>
                        <Row>
                            <Col>第{id}子章</Col>
                        </Row>
                        <Row>
                            <Paragraphlist
                                trigger_list={this.props.trigger_list}
                                avatar_list={this.props.avatar_list}
                                action_list={this.props.action_list}
                                ai_list={this.props.ai_list}
                                juntuan_list={this.props.juntuan_list}
                                bingzhong_list={this.props.bingzhong_list}
                                daoju_list={this.props.daoju_list}
                                snrm_list={this.props.snrm_list}
                                paragraph_list={snrd_item.paragraph_list}
                                setProps={(v) => {this.handleUpdateSnrd(id, v)}}
                            />
                        </Row>
                    </Container>
                })
            }
            </Container>
        )
    }
}
class Paragraphlist extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            paragraph_list: [],
        };
        this.handleUpdateParagraph = this.handleUpdateParagraph.bind(this);
    }
    static getDerivedStateFromProps(props){
        return {
            paragraph_list: props.paragraph_list,
        }
    }
    handleUpdateParagraph(id, value){
        id = Number(id);
        this.setState({
            paragraph_list: this.state.paragraph_list.map((item, i) => i === id ? (item.section_list = value,item) : item)
        }, () => {this.props.setProps(this.state.paragraph_list)});
    }
    render () {
        return (
            <Col>
            {
                this.state.paragraph_list.map((paragraph_item, id) => {
                return <Container fluid="true" key={id}>
                    <Row>
                        <Col>第{id}段</Col>
                    </Row>
                    <Row>
                        <SectionList
                            trigger_list={this.props.trigger_list}
                            avatar_list={this.props.avatar_list}
                            action_list={this.props.action_list}
                            ai_list={this.props.ai_list}
                            juntuan_list={this.props.juntuan_list}
                            bingzhong_list={this.props.bingzhong_list}
                            daoju_list={this.props.daoju_list}
                            snrm_list={this.props.snrm_list}
                            section_list={paragraph_item.section_list}
                            setProps={(v) => {this.handleUpdateParagraph(id, v)}}
                        />
                    </Row>
                </Container>
                })
            }
            </Col>
        )
    }
}
class SectionList extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            // section_list: [],
            section_list: props.section_list,
        };
        this.handleUpdateSection = this.handleUpdateSection.bind(this);
        this.handleUpdateInstr = this.handleUpdateInstr.bind(this);
    }
    // static getDerivedStateFromProps(props){
    //     return {
    //         section_list: props.section_list,
    //     }
    // }
    handleUpdateInstr(id, value){
        id = Number(id);
        this.setState({
            section_list: this.state.section_list.map((item, i) => i === id ? (item.instr_index_code = value,item) : item)
        }, () => {this.props.setProps(this.state.section_list)});
    }
    handleUpdateSection(id, value){
        id = Number(id);
        this.setState({
            section_list: this.state.section_list.map((item, i) => i === id ? (item.script_list = value,item) : item)
        }, () => {this.props.setProps(this.state.section_list)});
    }
    render () {
        return (
            <Col>
            {
                this.state.section_list.map((section_item, id) => {
                    return <Container fluid="true" key={id}>
                        <Row>
                            <Col>第{id}节</Col>
                        </Row>
                        <Container fluid="true">
                            <Row>
                                <Col>
                                    <span>指令组</span>
                                   <ComboSection 
                                       trigger_list={this.props.trigger_list}
                                       avatar_list={this.props.avatar_list}
                                       instr_code={section_item.instr_index_code}
                                       setProps={(v) => {this.handleUpdateInstr(id, v)}}
                                    />
                                </Col>
                            </Row>
                        </Container>
                        <Container fluid="true">
                            <Row>
                                <Col>指令列表</Col>
                            </Row>
                            <Row>
                                <ScriptList
                                    trigger_list={this.props.trigger_list}
                                    avatar_list={this.props.avatar_list}
                                    action_list={this.props.action_list}
                                    ai_list={this.props.ai_list}
                                    juntuan_list={this.props.juntuan_list}
                                    bingzhong_list={this.props.bingzhong_list}
                                    daoju_list={this.props.daoju_list}
                                    snrm_list={this.props.snrm_list}
                                    script_list={section_item.script_list}
                                    setProps={(v) => {this.handleUpdateSection(id, v)}}
                                />
                            </Row>
                        </Container>
                    </Container>
                })
            }
            </Col>
        )
    }
}
class ScriptList extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            // script_list: [],
            script_list: props.script_list,
        };
        this.handleChangeScript = this.handleChangeScript.bind(this);
    }
    // static getDerivedStateFromProps(props){
    //     return {
    //         script_list: props.script_list,
    //     }
    // }
    handleChangeScript(e){
        var id = Number(e.target.id);
        var value = e.target.value;
        this.setState({
            script_list: this.state.script_list.map((item, i) => i === id ? value : item)
        }, () => {this.props.setProps(this.state.script_list)});
    }
    render () {
        return (
            <Col>
            {
                this.state.script_list.map((item, id) => {
                    var start_idx = item.split(' ').map((item) => {return RegExp('[0-9a-f]{2}').test(item)}).indexOf(false);
                    var script_item = item.split(' ').slice(0, start_idx).join(' ');
                    return <Container fluid="true" key={id}>
                        <Form inline>
                            <Form.Label>指令{id}</Form.Label>
                            <ComboScript
                                trigger_list={this.props.trigger_list}
                                avatar_list={this.props.avatar_list}
                                action_list={this.props.action_list}
                                ai_list={this.props.ai_list}
                                juntuan_list={this.props.juntuan_list}
                                bingzhong_list={this.props.bingzhong_list}
                                daoju_list={this.props.daoju_list}
                                snrm_list={this.props.snrm_list}
                                script_code={script_item}
                                setProps={(v) => {}}
                            />
                        </Form>
                    </Container>
                })
            }
            </Col>
        )
    }
}
export default SnrdEditor;