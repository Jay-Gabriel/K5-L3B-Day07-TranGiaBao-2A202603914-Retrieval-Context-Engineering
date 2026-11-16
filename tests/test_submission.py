"""Regression tests for model decisions and reproducible evaluation."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'starter'))
from controller import GeminiController


class ControllerTests(unittest.TestCase):
    def controller(self, result):
        c = GeminiController(api_key='test-key', model='models/test')
        c._request = lambda payload: result
        return c

    def test_model_decides_initial_search(self):
        c = self.controller({'candidates': [{'content': {'parts': [
            {'functionCall': {'name': 'search', 'args': {'query': 'phân loại EF'}}}
        ]}}], 'usageMetadata': {'promptTokenCount': 12}})
        result = c.decide('EF giảm là gì?', [])
        self.assertEqual(result, {'action': 'search', 'query': 'phân loại EF'})
        self.assertEqual(c.calls[-1]['usage']['promptTokenCount'], 12)

    def test_malformed_model_output_is_error_not_abstention(self):
        c = self.controller({'candidates': [{'content': {'parts': [{'text': 'invalid output'}]}}]})
        with self.assertRaises(ValueError):
            c.decide('question', [{'context': 'text', 'context_ids': ['c1']}])

    def test_abstention_comes_from_model(self):
        c = self.controller({'candidates': [{'content': {'parts': [
            {'functionCall': {'name': 'answer', 'args': {'answer': 'Không đủ bằng chứng.', 'citations': []}}}
        ]}}]})
        self.assertEqual(c.decide('question', [{'context': 'text', 'context_ids': ['c1']}])['citations'], [])


class BenchmarkTests(unittest.TestCase):
    def test_dev_and_test_outputs_cannot_overwrite(self):
        import run_retrieval_benchmark as b
        self.assertNotEqual(b.output_dir(Path('/tmp/results'), 'dev', 'tfidf'),
                            b.output_dir(Path('/tmp/results'), 'test', 'tfidf'))

    def test_review_template_never_infers_grades_from_citations(self):
        from run_agent_benchmark import review_template
        trace = {'query_id': 'q', 'status': 'answered', 'citations': ['c1']}
        review = review_template({'id': 'q', 'answerable': True}, trace)
        self.assertIsNone(review['answer_grade'])
        self.assertEqual(review['citation_support'], [None])
        self.assertIsNone(review['context_grade'])

if __name__ == '__main__': unittest.main()

class CitationFormattingTests(unittest.TestCase):
    def test_valid_model_citation_is_formatted_without_inventing_source(self):
        c=GeminiController(api_key='test-key',model='test')
        c._request=lambda _: {'candidates':[{'content':{'parts':[{'functionCall':{'name':'answer','args':{'answer':'7 ngày','citations':['c1']}}}]}}]}
        self.assertEqual(c.decide('question',[{'context':'[c1] 7 ngày','context_ids':['c1']}])['answer'],'7 ngày [c1]')
    def test_unknown_citation_is_a_protocol_error(self):
        c=GeminiController(api_key='test-key',model='test')
        c._request=lambda _: {'candidates':[{'content':{'parts':[{'functionCall':{'name':'answer','args':{'answer':'7 ngày','citations':['invented']}}}]}}]}
        with self.assertRaises(ValueError):c.decide('question',[{'context':'text','context_ids':['c1']}])

class ProvenanceTests(unittest.TestCase):
    def test_unknown_vector_point_cannot_invent_lecture_source(self):
        from retrievers import QdrantDenseRetriever
        from types import SimpleNamespace
        retriever=object.__new__(QdrantDenseRetriever)
        retriever.chunk_by_id={};retriever.collection_name='test'
        retriever.embed_query=lambda _: [0.0]*384
        retriever.client=SimpleNamespace(query_points=lambda **_:SimpleNamespace(points=[SimpleNamespace(id='unknown',payload={'text':'unsupported content'},score=.9)]))
        with self.assertRaises(ValueError):retriever.search('question')

    def test_partial_or_stale_dev_run_cannot_authorize_test(self):
        from select_config import validate_dev_run
        from configs import write_json, CONFIGS
        from run_agent_benchmark import fingerprints,runtime_settings
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'baseline';root.mkdir()
            write_json(root/'run.json',{'fingerprints':fingerprints(),'runtime_settings':runtime_settings(),'model':runtime_settings()['model'],'config_name':'baseline','config':CONFIGS['baseline']})
            write_json(root/'traces.json',[]);write_json(root/'reviews.json',[]);write_json(root/'summary.json',{'review_note':'reviewed'})
            with self.assertRaises(ValueError):validate_dev_run(root)
