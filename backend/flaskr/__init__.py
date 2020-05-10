import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    cors = CORS(app, resources={"*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    @app.route('/categories', methods=['GET'])
    def retrieve_categories():
        categories = Category.query.order_by(Category.id).all()
        categories_formatted = {
            category.id: category.type for category in categories}

        if len(categories) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'categories': categories_formatted
        })

    @app.route('/questions', methods=['GET'])
    def retrieve_questions():

        questions = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, questions)

        categories = Category.query.order_by(Category.id).all()
        categories_formatted = {
            category.id: category.type for category in categories}

        if len(current_questions) == 0 or len(categories_formatted) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(Question.query.all()),
            'current_category': None,
            'categories': categories_formatted
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        question = Question.query.get(question_id)

        if question is None:
            abort(404)

        question.delete()

        return jsonify({
            'success': True,
            'deleted': question_id
        })

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()
        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)

        question = Question(question=new_question, answer=new_answer,
                            category=new_category, difficulty=new_difficulty)
        question.insert()
        return jsonify({
            'success': True,
            'created': question.id,
        })

    @app.route('/searchQuestions', methods=['POST'])
    def search_question():
        body = request.get_json()
        search_word = body.get('searchTerm', None)

        search_result = Question.query.filter(
            Question.question.ilike(f'%{search_word}%')).all()
        search_result_formatted = [question.format()
                                   for question in search_result]

        return jsonify({
            'success': True,
            'questions': search_result_formatted,
            'total_questions': len(search_result_formatted),
            'current_category': None
        })

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_by_category(category_id):

        questions = Question.query.filter(
            Question.category == category_id).all()
        questions_formatted = [question.format() for question in questions]

        if questions_formatted is None:
            abort(404)

        return jsonify({
            'success': True,
            'questions': questions_formatted,
            'total_questions': len(questions_formatted),
            'current_category': Category.query.get(category_id).type
        })

    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        body = request.get_json()
        previous_questions = body.get('previous_questions', [])
        category = body.get('quiz_category', None)
        category_id = category['id']
        new_questions = Question.query.filter(
            Question.id.notin_(previous_questions))

        if category_id == 0:
            questions_filterby_category = new_questions.all()
        else:
            questions_filterby_category = new_questions.filter(
                Question.category == category_id).all()
        if len(questions_filterby_category) > 0:
            question_random = random.choice(questions_filterby_category)
            question_formatted = question_random.format()
        else:
            question_formatted = False
        return jsonify({
            'success': True,
            'question': question_formatted
        })

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad request"
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'Not Found'
        }), 404

    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable entity"
        }), 422

    return app
