from flask import Flask, abort, jsonify
from flask_restful import Api, Resource, reqparse
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'

db = SQLAlchemy(app)


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    is_done = db.Column(db.Boolean, server_default='false')


with app.app_context():
    db.create_all()


class TaskSchema(Schema):
    class Meta:
        ordered = True
    id = fields.Integer()
    text = fields.String()
    is_done = fields.Boolean()


task_parser = reqparse.RequestParser(bundle_errors=True)
task_parser.add_argument(
    name='text',
    type=str,
    help='Task description is required!',
    required=True
)
task_parser.add_argument(
    name='is_done',
    type=bool,
    help='Required: indicate if this task is already done.',
    required=True
)


class TaskListResource(Resource):
    def get(self):
        schema = TaskSchema(many=True)
        return schema.dump(Task.query.all())

    def post(self):
        task = task_parser.parse_args()
        new = Task(text=task.get('text'), is_done=task.get('is_done'))
        db.session.add(new)
        db.session.commit()
        db.session.refresh(new)
        return TaskSchema().dump(new)


class TaskResource(Resource):
    def delete(self, task_id):
        effect = Task.query.filter(Task.id == task_id).delete()
        if effect:
            db.session.commit()
            return jsonify({"message": "The task has been deleted!"})
        else:
            return abort(404, 'The task does not exist!')

    def get(self, task_id):
        task = Task.query.filter(Task.id == task_id).first()
        if task:
            return TaskSchema().dump(task)
        else:
            return abort(404, 'The task does not exist!')

    def put(self, task_id):
        new = task_parser.parse_args()
        task = Task.query.filter(Task.id == task_id).first()
        if task:
            task.text = new.get('text')
            task.is_done = new.get('is_done')
            db.session.commit()
            return TaskSchema().dump(task)
        else:
            return abort(404, 'The task does not exist!')


api = Api(app)
api.add_resource(TaskListResource, '/tasks')
api.add_resource(TaskResource, '/tasks/<int:task_id>')

if __name__ == '__main__':
    app.run(debug=True)
