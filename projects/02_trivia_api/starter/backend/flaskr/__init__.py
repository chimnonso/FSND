import json
import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 8


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    def paginate(request, selection):
        page = request.args.get("page", 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE

        questions = [question.format() for question in selection]
        current_questions = questions[start:end]
        return current_questions

    def list_of_categories(current_questions):
        category_list = []

        for question in current_questions:
            if question not in category_list:
                category_list.append(question['id'])

        return category_list

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @cross_origin()
    @app.route("/")
    def hello():
        return "Hello Word"

    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type, Authorization, true')
        response.headers.add(
            'Access-Control-Allow-Methods',
            'GET, POST, PATCH, DELETE, OPTION')

        return response

    @app.route("/categories")
    def get_categories():
        categories = Category.query.all()
        if len(categories) == 0:
            abort(404)
        formatted_categories = {
            category.id: category.type for category in categories
            }

        return jsonify({
            "success": True,
            "categories": formatted_categories
        })

    @app.route("/questions")
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate(request, selection)

        if len(current_questions) == 0:
            abort(404)

        categories = Category.query.all()
        formatted_categories = {
            category.id: category.type for category in categories
            }

        category_list = list_of_categories(current_questions)

        return jsonify({
            "success": True,
            "questions": current_questions,
            "total_questions": len(selection),
            "categories": formatted_categories,
            "current_category": category_list
        })

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def remove_question(question_id):

        try:
            question = Question.query. \
                filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate(request, selection)

            return jsonify({
                "success": True,
                "deleted": question_id,
                "questions": current_questions,
                "total_questions": len(selection)
            })

        except:
            abort(422)

    @app.route("/questions", methods=["POST"])
    def create_question():
        body = request.get_json()

        question = body.get("question", None)
        answer = body.get("answer", None)
        difficulty = body.get("difficulty", None)
        category = body.get("category", None)
        search_term = body.get("searchTerm", None)

        if search_term:
            search_questions = Question.query. \
                filter(Question.question.ilike(f"%{search_term}%")).all()
            questions = paginate(request, search_questions)
            
            if len(questions) > 0:
                category_list = list_of_categories(questions)
            else:
                category_list = None

            return jsonify({
                "success": True,
                "questions": questions,
                "total_questions": len(search_questions),
                "current_category": category_list
            })

        else:

            if (question is None or answer is None or
                    difficulty is None or category is None):
                abort(422)

            categories = Category.query.all()
            formatted_categories = {
                category.id: category.type for category in categories
                }

            try:
                new_question = Question(
                    question=question,
                    answer=answer,
                    difficulty=difficulty,
                    category=category)
                new_question.insert()

                selection = Question.query.order_by(Question.id).all()
                current_questions = paginate(request, selection)

                return jsonify({
                    "success": True,
                    # "questions": current_questions,
                    "created": new_question.id,
                    # "total_questions": len(selection),
                    # "categories": categories,
                })
            except:
                abort(405)

    @app.route("/categories/<int:category_id>/questions")
    def get_questions_of_category(category_id):
        try:
            selection = Question.query. \
                filter(Question.category == category_id).all()

            if len(selection) == 0:
                abort(404)
            questions = paginate(request, selection)

            return jsonify({
                "success": True,
                "current_category": category_id,
                "total_questions": len(selection),
                "questions": questions,
            })
        except:
            abort(404)

    @app.route("/quizzes", methods=["POST"])
    def play_quiz():
        body = request.get_json()
        print(body)

        try:
            if body is None or 'quiz_category' not in body.keys():
                abort(422)

            previous_question = body.get("previous_questions")
            quiz_category = body.get("quiz_category")["id"]
            print(quiz_category)
            if quiz_category == 0:
                query = Question.query \
                    .filter(
                            Question.id.notin_((previous_question))
                        ).all()
            else:
                query = Question.query \
                    .filter(
                        Question.category == quiz_category,
                        Question.id.notin_((previous_question))).all()

            if len(query) > 0:
                question = random.choice(query).format()
            else:
                question = None

            return jsonify({
                "success": True,
                "question": question,
                "question_id": question["id"]
            })
        except:
            abort(422)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(405)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "method not allowed"
        }), 405

    return app
