import unittest
from datetime import datetime, timedelta
import json

from src.database import (
    init_db,
    get_or_create_user,
    save_quiz_result,
    get_user_quiz_results,
    get_study_summary,
    get_topic_mastery,
    get_due_reviews,
    log_study_activity
)
from src.sm2 import calculate_sm2, score_to_quality, update_topic_after_quiz
from src.llm_client import format_gemma_prompt, extract_and_parse_json_quiz
from src.rag_engine import recursive_character_splitter, ResilientVectorStore

class TestEduGemma(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_database_and_user_creation(self):
        user = get_or_create_user("TestStudent_Auto")
        self.assertIsNotNone(user["id"])
        self.assertEqual(user["username"], "TestStudent_Auto")

    def test_quiz_results_and_analytics(self):
        user = get_or_create_user("QuizTester")
        save_quiz_result(
            user_id=user["id"],
            subject="Physics",
            chapter="Motion",
            total_questions=5,
            score=4.0
        )
        results = get_user_quiz_results(user["id"])
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["chapter"], "Motion")
        self.assertEqual(results[0]["score"], 4.0)

        summary = get_study_summary(user["id"])
        self.assertGreaterEqual(summary["total_questions"], 5)
        self.assertGreaterEqual(summary["avg_accuracy"], 70.0)

    def test_sm2_algorithm(self):
        # High score: quality 5
        rep, interval, ef, next_rev = calculate_sm2(quality=5, repetitions=0, interval_days=1, ease_factor=2.5)
        self.assertEqual(rep, 1)
        self.assertEqual(interval, 1)
        self.assertGreaterEqual(ef, 2.5)

        # Repetition 1 -> interval 6
        rep2, interval2, ef2, next_rev2 = calculate_sm2(quality=5, repetitions=1, interval_days=1, ease_factor=ef)
        self.assertEqual(rep2, 2)
        self.assertEqual(interval2, 6)

        # Low score: quality 1 (reset)
        rep_fail, interval_fail, ef_fail, _ = calculate_sm2(quality=1, repetitions=3, interval_days=15, ease_factor=2.5)
        self.assertEqual(rep_fail, 0)
        self.assertEqual(interval_fail, 1)
        self.assertLess(ef_fail, 2.5)

    def test_json_quiz_resilience(self):
        # Case 1: Markdown wrapped JSON
        sample_md = """Here is the quiz:
```json
[
  {
    "question": "What is speed?",
    "options": ["Scalar", "Vector", "Color", "Taste"],
    "correct_index": 0,
    "explanation": "Speed has magnitude only."
  }
]
```
Good luck!"""
        parsed = extract_and_parse_json_quiz(sample_md)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["question"], "What is speed?")
        self.assertEqual(parsed[0]["correct_index"], 0)

        # Case 2: Malformed text fallback
        sample_bad = "I cannot provide a quiz right now because of reasons."
        fallback_parsed = extract_and_parse_json_quiz(sample_bad, fallback_text="Kinematics chapter", count=2)
        self.assertGreaterEqual(len(fallback_parsed), 1)
        self.assertIn("question", fallback_parsed[0])

    def test_gemma_prompt_formatting(self):
        formatted = format_gemma_prompt("What is velocity?")
        self.assertTrue(formatted.startswith("<start_of_turn>user"))
        self.assertTrue("<start_of_turn>model" in formatted)

    def test_rag_text_splitter(self):
        long_text = "Photosynthesis is the process by which green plants make food. " * 30
        chunks = recursive_character_splitter(long_text, chunk_size=300, chunk_overlap=50)
        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertLessEqual(len(c), 500)

    def test_concept_graph_parser_and_mermaid(self):
        from src.llm_client import parse_concept_graph_json, convert_graph_to_mermaid, sanitize_mermaid_id
        
        sample_json = json.dumps({
            "root": {"id": "Kinematics", "label": "Kinematics in 1D", "desc": "Motion along a line"},
            "nodes": [
                {"id": "Vel", "label": "Velocity", "desc": "Rate of change of displacement"},
                {"id": "Acc", "label": "Acceleration", "desc": "Rate of change of velocity"}
            ],
            "edges": [
                {"source": "Kinematics", "target": "Vel", "label": "describes"},
                {"source": "Vel", "target": "Acc", "label": "differentiated to"}
            ]
        })
        graph = parse_concept_graph_json(sample_json)
        self.assertEqual(graph["root"]["id"], "Kinematics")
        self.assertEqual(len(graph["nodes"]), 2)
        
        mermaid = convert_graph_to_mermaid(graph)
        self.assertIn("graph TD", mermaid)
        self.assertIn("Kinematics in 1D", mermaid)
        self.assertIn("Velocity", mermaid)

        # Verify sanitizer
        self.assertEqual(sanitize_mermaid_id("Node (1) & Sub!"), "Node_1_Sub")

    def test_cs_ai_visual_explainer_prompt(self):
        from src.llm_client import explain_cs_ai_concept_visually
        # Test that prompt generation works with fallback/model query
        result = explain_cs_ai_concept_visually("Self-Attention Mechanism", topic_context="Transformers")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 20)

if __name__ == "__main__":
    unittest.main()

