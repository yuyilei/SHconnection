from flask import jsonify, request, g
from . import api
from ..models import Teacher, Parent, TEvaluation, PEvaluation, TScore, PScore, Child, Theclass
from .. import db
from .decorators import parent_login_required, login_required, teacher_login_required



@api.route('/evaluation/teacher/',methods=['POST'])
@teacher_login_required
def teacher_send_evaluation():
    """
    老师发送评价
    :return:
    """
    tid = request.args.get('tid')
    cid = request.args.get('childid')

    json_data = request.get_json()
    comment = json_data['comment']
    score = json_data['score']

    te = TEvaluation()
    te.content = comment
    te.teacher_id = tid
    te.child_id = cid
    db.session.add(te)
    db.session.commit()

    for each in score:
        ts = TScore()
        ts.name = each['name']
        ts.score = each['score']
        ts.evaluation_id = te.id
        db.session.add(ts)

    db.session.commit()

    return jsonify({ 'msg' : '评价成功' }), 200

@api.route('/evaluation/teacher/all/',methods=['GET'])
@login_required
def get_teacher_evaluation():
    """
    获取老师对某一孩子的评价
    :return:
    """
    tid = request.args.get('tid')
    cid = request.args.get('childid')

    te = TEvaluation.query.filter_by(teacher_id=tid,child_id=cid).all()

    return jsonify({
        'eval' : [ t.to_json() for t in te ]
    }),200



@api.route('/evaluation/parent/',methods=['POST'])
@parent_login_required
def parent_send_evaluation():
    """
    家长发送评价
    :return:
    """
    p = g.current_user
    pid = request.args.get('pid')
    json_data = request.get_json()
    comment = json_data['comment']
    score = json_data['score']

    if p.id != int(pid):
        return jsonify({ 'msg' : '验证错误！'}), 401

    pe = PEvaluation()
    pe.content = comment
    pe.child_id = p.child_id
    pe.parent_id = p.id
    db.session.add(pe)
    db.session.commit()

    for each in score:
        ps = PScore()
        ps.name = each['name']
        ps.score = each['score']
        ps.evaluation_id = pe.id
        db.session.add(ps)

    db.session.commit()

    return jsonify({ 'msg' : '评价成功'})


@api.route('/evaluation/parent/all/',methods=['GET'])
@login_required
def get_parent_evaluation():
    """
    获取家长对某一孩子的评价
    :return:
    """
    pid = request.args.get('pid')
    cid = g.current_parent.child_id

    pe = PEvaluation.query.filter_by(parent_id=pid,child_id=cid).all()

    return jsonify({
        'eval' : [ p.to_json() for p in pe ]
    }),200


@api.route('/evaluation/parent/view/',methods=['GET'])
@parent_login_required
def get_parent_view():
    """
    查看评价时，家长看到的list
    :return:
    """
    p = g.current_user
    class_id = p.child.class_id
    theclass = Theclass.query.filter_by(id=class_id).first()

    teachers = [ t.eval_info() for t in theclass.teachers ]
    return jsonify({
        'teachers' : teachers,
    }), 200


@api.route('/evaluation/teacher/view/',methods=['GET'])
@parent_login_required
def get_teacher_view():
    """
    查看评价时，老师看到的list
    :return:
    """

    cid = request.args.get('cid')
    theclass = Theclass.query.filter_by(id=cid).first()
    teachers = [ t.eval_info() for t in theclass.teachers ]
    parents = []
    for child in theclass.childs:
        parents += [p.eval_info() for p in child.parents]

    return jsonify({
        'teachers' : teachers,
        'parents' : parents,
    }), 200



@api.route('/evaluation/teacher/teacher/',methods=['GET'])
@teacher_login_required
def get_teacher_teacher():
    """
    老师端点击一个老师看到的是这个老师对班级所有孩子的评价
    :return:
    """
    cid = request.get_json().get('cid')
    tid = request.get_json().get('tid')
    teacher = Teacher.query.filter_by(id=tid).first()
    tname = teacher.name

    theclass =  Theclass.query.filter_by(id=cid).first()
    evals = []
    for child in theclass.childs:
        for eval in child.tevaluations:
            if eval.teacher_id == tid:
                evals.append(eval.eval_info())

    return jsonify({
        'evals' : evals,
        'teacher' : tname,
    }), 200


@api.route('/evaluation/teacher/parent/',methods=['GET'])
@teacher_login_required
def get_teacher_parent():
    """
    老师端点击一个家长看到的是全部老师对这个家长的孩子的评论
    :return:
    """
    pid = request.get_json().get('pid')
    p = Parent.query.filter_by(id=pid).first()
    child = p.child

    evals = [ e.eval_info() for e in child.pevaluations ]
    return jsonify({
        'evals' : evals,
        'child' : child.name,
    }), 200


@api.route('/evaluation/parent/teacher/',methods=['GET'])
@parent_login_required
def get_parent_teacher():
    """
    家长端点击一个老师看到的是这个老师对这个家长的孩子的评论
    :return:
    """
    p = g.current_user
    child = p.child
    tid = request.get_json().get('tid')
    evals = [ e.eval_info_brief() for e in child.tevaluations if e.teacher_id == tid ]
    tname = Teacher.query.filter_by(id=tid).first().name

    return jsonify({
        'evals' : evals,
        'teacher' : tname,
    }), 200


@api.route('/evaluation/parent/parent/',methods=['GET'])
@parent_login_required
def get_parent_parent():
    """
    家长端点击我看到的是这个家长对自己的孩子的评论
    :return:
    """
    p = g.current_user
    child = p.child
    evals = [ e.eval_info_brief() for e in child.pevaluations ]

    return jsonify({
        'evals' : evals,
        'child' : child.name,
    }), 200