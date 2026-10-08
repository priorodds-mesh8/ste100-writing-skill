import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('run_evals', ROOT / 'evals/run_evals.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class EvalTests(unittest.TestCase):
    def test_case_validation(self):
        self.assertEqual(len(runner.validate()), 19)

    def record(self):
        return dict(case_id='uncertainty', variant='skill', output='The cable is loose.',
                    context=dict(host='Example host', host_version='test', model='test model', mode='plain', source_access='none'))

    def test_keywords_do_not_pass_meaning(self):
        result = runner.assess([self.record()], runner.validate())
        self.assertEqual(result[0]['status'], 'needs-human-review')

    def test_review_failure_is_retained(self):
        record = self.record()
        record['assessment'] = dict(reviewer='Example reviewer', notes='The output removes uncertainty.', checks=[False, False])
        self.assertEqual(runner.assess([record], runner.validate())[0]['status'], 'reviewer-fail')

    def test_incomplete_review_rejected(self):
        record = self.record()
        record['assessment'] = dict(reviewer='Example reviewer', notes='', checks=[True])
        with self.assertRaises(ValueError): runner.assess([record], runner.validate())


if __name__ == '__main__': unittest.main()
