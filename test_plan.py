import json
from pathlib import Path
import sys
import tempfile
import unittest
import harness as h

class PlanTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.w = Path(self.t.name).resolve()
        self.r = self.w / 'records'; self.r.mkdir()
        (self.w / 'test_sample.py').write_text('import unittest\nclass T(unittest.TestCase):\n def test_one(self): self.assertEqual(1,1)\n')
        self.cmd = [sys.executable, '-m', 'unittest', 'discover', '-v']
        _, path = h.execute(self.cmd, self.w, self.r, 5, h.fingerprints(self.w, ['test_sample.py']))
        self.path = path
        self.spec = {'planned_checks': [{'id':'C1','required':True,'requirements':['R1'],
          'expected':'one test passes','command':self.cmd,'framework':'unittest','minimum_tests':1,
          'fingerprints':['test_sample.py'],'evidence':str(path.relative_to(self.r))}]}

    def result(self): return h.check_plan(self.spec, self.w, self.r)['status']

    def test_actual_unittest_success(self): self.assertEqual(self.result(), 'PASS')

    def test_missing_required_and_empty_plan(self):
        self.spec['planned_checks'][0]['evidence']=''
        self.assertEqual(self.result(),'NOT_RUN')
        self.assertEqual(h.check_plan({},self.w,self.r)['status'],'BLOCKED')

    def test_partial_count(self):
        self.spec['planned_checks'][0]['minimum_tests']=2
        self.assertEqual(self.result(),'FAIL')

    def test_duplicate_and_optional_only(self):
        self.spec['planned_checks'] *= 2
        self.assertEqual(self.result(),'BLOCKED')
        self.spec['planned_checks'] = [self.spec['planned_checks'][0]]
        self.spec['planned_checks'][0]['required']=False
        self.assertEqual(self.result(),'BLOCKED')

    def test_command_mismatch(self):
        self.spec['planned_checks'][0]['command']=['other']
        self.assertEqual(self.result(),'BLOCKED')

    def test_changed_input_and_output(self):
        (self.path.parent/'output.log').write_text('Ran 1 test in 0.0s\n\nOK\n')
        self.assertEqual(self.result(),'BLOCKED')

    def test_changed_fingerprint(self):
        (self.w/'test_sample.py').write_text('changed')
        self.assertEqual(self.result(),'BLOCKED')

    def test_actual_empty_unittest(self):
        (self.w/'test_sample.py').unlink()
        _, p = h.execute(self.cmd, self.w, self.r, 5)
        self.assertEqual(h.test_summary(p.parent/'output.log','unittest')['status'],'FAIL')

    def test_synthetic_pytest_summaries(self):
        p=self.w/'sample.log'
        for text, status in [('3 passed in 0.02s','PASS'), ('no tests ran in 0.01s','FAIL'),
                             ('1 passed, 2 deselected in 0.1s','HUMAN_CHECK'),
                             ('1 passed, 1 skipped in 0.1s','HUMAN_CHECK'),
                             ('garbage','HUMAN_CHECK')]:
            p.write_text(text)
            self.assertEqual(h.test_summary(p,'pytest')['status'],status)

    def test_skipped_and_unknown_framework(self):
        p=self.w/'sample.log';p.write_text('Ran 1 test in 0.1s\n\nOK (skipped=1)\n')
        self.assertEqual(h.test_summary(p,'unittest')['status'],'HUMAN_CHECK')
        self.assertEqual(h.test_summary(p,'other')['status'],'HUMAN_CHECK')

    def test_cli_plan(self):
        import subprocess
        p=self.w/'checks.json';p.write_text(json.dumps(self.spec))
        cmd=[sys.executable,str(h.ROOT/'harness.py'),'계획검사','--workspace',str(self.w),'--record-dir',str(self.r),'--input',str(p)]
        run=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout)['status'],'PASS')
