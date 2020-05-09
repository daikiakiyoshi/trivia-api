import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start =  (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    '''
    cors = CORS(app, resources={"*": {"origins": "*"}})

    '''
    @TODO: Use the after_request decorator to set Access-Control-Allow
    '''
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    '''
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    '''
    @app.route('/categories', methods=['GET'])
    def retrieve_categories():
        categories = Category.query.order_by(Category.id).all()
        categories_formatted = {category.id:category.type for category in categories}

        if len(categories) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'categories': categories_formatted
        })

    '''
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    '''
    @app.route('/questions', methods=['GET'])
    def retrieve_questions():
        try:
            questions = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, questions)

            categories = Category.query.order_by(Category.id).all()
            categories_formatted = {category.id:category.type for category in categories}

            if len(current_questions) == 0 or len(categories_formatted) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(Question.query.all()),
                'current_category': None,
                'categories': categories_formatted
            })

        except:
          abort(422)

    '''
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    '''

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()

            return jsonify({
                'success': True,
                'deleted': question_id
            })

        except:
          abort(422)

    '''
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    '''

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()
        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)

        try:
            question = Question(question=new_question, answer=new_answer,
                                category=new_category, difficulty=new_difficulty)
            question.insert()
            return jsonify({
                'success': True,
                'created': question.id,
            })

        except:
            abort(422)

    '''
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    '''
    @app.route('/searchQuestions', methods=['POST'])
    def search_question():
        body = request.get_json()
        search_word = body.get('searchTerm', None)
        try:
            search_result = Question.query.filter(Question.question.ilike(f'%{search_word}%')).all()
            search_result_formatted = [question.format() for question in search_result]

            if len(search_result_formatted) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'questions': search_result_formatted,
                'total_questions': len(search_result_formatted),
                'current_category': None
            })

        except:
            abort(422)

    '''
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    '''
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_by_category(category_id):
        try:
            questions = Question.query.filter(Question.category == category_id).all()
            questions_formatted = [question.format() for question in questions]

            if questions_formatted is None:
                abort(404)

            return jsonify({
                'success': True,
                'questions': questions_formatted,
                'total_questions': len(questions_formatted),
                'current_category': Category.query.get(category_id).type
            })
        except:
          abort(422)

    '''
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    '''
    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        body = request.get_json()
        previous_questions = body.get('previous_questions', [])
        category = body.get('quiz_category', None)
        category_id = category['id']
        try:
            new_questions = Question.query.filter(Question.id.notin_(previous_questions))
            if category_id == 0:
                questions_filterby_category = new_questions.all()
            else:
                questions_filterby_category = new_questions.filter(Question.category == category_id).all()
            if len(questions_filterby_category) > 0:
                question_random = random.choice(questions_filterby_category)
                question_formatted = question_random.format()
            else:
                question_formatted = False
            return jsonify({
                'success': True,
                'question': question_formatted
            })
        except:
            abort(422)

    '''
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    '''
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error" : 400,
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
            "error" : 422,
            "message": "Unprocessable entity"
        }), 422

    return app
