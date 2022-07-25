import sys
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://postgres:admin@localhost:5432/todos"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class TodoList(db.Model):
    __tablename__ = "todolists"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    todos = db.relationship(
        "Todo", backref="list", lazy=True, cascade="all, delete-orphan"
    )


class Todo(db.Model):
    __tablename__ = "todos"
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey("todolists.id"), nullable=False)

    def __repr__(self):
        return f"<Todo id: {self.id} description: {self.description}>"


@app.route("/todo-list/create", methods=["POST"])
def create_todo_list():
    error = False
    response_body = {}
    try:
        name = request.get_json()["name"]
        new_todo_list = TodoList(name=name)
        db.session.add(new_todo_list)
        db.session.commit()
        response_body["id"] = new_todo_list.id
        response_body["name"] = new_todo_list.name
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return jsonify(response_body)


@app.route("/todo-list/<todo_list_id>/todo/create", methods=["POST"])
def create_todo(todo_list_id):
    error = False
    response_body = {}
    try:
        description = request.get_json()["description"]
        new_todo = Todo(description=description, completed=False, list_id=todo_list_id)
        db.session.add(new_todo)
        db.session.commit()
        response_body["id"] = new_todo.id
        response_body["description"] = new_todo.description
        response_body["completed"] = new_todo.completed
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return jsonify(response_body)


@app.route("/todo/<todo_id>/update", methods=["PATCH"])
def update_todo(todo_id):
    error = False
    try:
        completed = request.get_json()["completed"]
        todo = Todo.query.get(todo_id)
        todo.completed = completed
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return redirect(url_for("index"))


@app.route("/todo_list/<todo_list_id>/update", methods=["POST"])
def update_todo_list(todo_list_id):
    error = False
    try:
        todo_list = TodoList.query.get(todo_list_id)
        for todo in todo_list.todos:
            todo.completed = True
        db.session.add(todo_list)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        if error:
            abort(500)
        else:
            return redirect(url_for("index"))


@app.route("/todo-list/<todo_list_id>/delete", methods=["DELETE"])
def delete_todo_list(todo_list_id):
    error = False
    try:
        todo_list = TodoList.query.get(todo_list_id)
        for todo in todo_list.todos:
            db.session.delete(todo)

        db.session.delete(todo_list)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return redirect(url_for("index"))


@app.route("/todo/<todo_id>/delete", methods=["DELETE"])
def delete_todo(todo_id):
    error = False
    try:
        Todo.query.filter_by(id=todo_id).delete()
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return redirect(url_for("index"))


@app.route("/todo-list/<todo_list_id>")
def get_todo_list(todo_list_id):
    return render_template(
        "todo_list.html",
        todo_list=TodoList.query.get(todo_list_id),
        data=Todo.query.filter_by(list_id=todo_list_id).order_by(Todo.id.desc()).all(),
    )


@app.route("/", methods=["GET", "POST", "DELETE", "PATCH"])
def index():
    return render_template(
        "todo_lists.html", data=TodoList.query.order_by(TodoList.id.desc()).all()
    )


if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0", port=5000)
