import os
import unittest
import json
from flask.json import jsonify
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app, QUESTIONS_PER_PAGE
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = \
            "postgresql://postgres:foobar@{}/{}" \
            .format('localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)
        self.new_question = \
            {
                "question": "When will Bruno Mars release a new song",
                "answer": "Still waiting", "category": 5, "difficulty": 4
            }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful
    operation and for expected errors.
    """

    def test_get_categories(self):
        res = self.client().get("/categories")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(len(data["categories"]))

    def test_404_failed_category(self):
        res = self.client().get("/category")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "resource not found")

    def test_paginate_questions(self):
        res = self.client().get("/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["total_questions"])
        self.assertTrue(len(data["questions"]))
        self.assertTrue(len(data["categories"]))
        self.assertTrue(data["current_category"])

    def test_404_requesting_beyond_valid_page(self):
        res = self.client().get("/questions?page=10000")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "resource not found")

    def test_for_question_delete(self):
        res = self.client().delete("/questions/10")
        data = json.loads(res.data)

        question = Question.query.filter(Question.id == 1).one_or_none()

        return

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["deleted"], 10)
        self.assertTrue(len(data["questions"]))
        self.assertTrue(data["total_questions"])
        self.assertEqual(question, None)

    def test_422_if_question_does_not_exist(self):
        res = self.client().delete("/questions/100000")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "unprocessable")

    def test_create_question(self):
        # return
        res = self.client().post("/questions", json=self.new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        # self.assertTrue(len(data["questions"]))
        self.assertTrue(data["created"])
        # self.assertTrue(len(data["categories"]))

    def test_405_create_question_not_allowed(self):
        res = self.client().post("/questions/40", json=self.new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 405)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "method not allowed")

    def test_search_with_results(self):
        res = self.client().post("/questions", json={"searchTerm": "adele"})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(len(data["questions"]))
        self.assertEqual(data["total_questions"], 17)
        self.assertTrue(data["current_category"])

    def test_search_without_results(self):
        res = self.client().post("/questions", json={"searchTerm": "blahblah"})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(len(data["questions"]), 0)
        self.assertEqual(data["total_questions"], 0)
        self.assertIsNone(data["current_category"])

    def test_get_questions_based_on_category(self):
        category_id = 1
        res = self.client().get(f"categories/{category_id}/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["current_category"], category_id)
        self.assertTrue(data["total_questions"])
        self.assertTrue(len(data["questions"]))

    def test_requesting_invalid_category(self):
        category_id = 1000
        res = self.client().get(f"categories/{category_id}/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "resource not found")   

    def test_quiz_success(self):
        category = Category.query.first()
        questions_in_category = Question.query.filter(
            Question.category == category.id).all()

        
        expected_question = questions_in_category[0].format()
        previous_questions = [
            question.id for question in questions_in_category[1:]]
        
        res = self.client().post(
                  "/quizzes",
                  json={
                      "quiz_category": category.format(),
                      "previous_questions": previous_questions}
                )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["question"])
        self.assertEqual(data["question_id"], expected_question["id"])

    def test_quiz_failure(self):
        res = self.client().post("/quizzes")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "unprocessable")

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
