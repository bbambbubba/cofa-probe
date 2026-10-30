import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import harness as h

class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cofa 한글 ')
        self.addCleanup(self.temp.cleanup)
        self.w = Path(self.temp.name).resolve()
        self.r = self.w / 'records'
        self.r.mkdir()
        (self.w / 'app.py').write_text('print(1)')

    def run_code(self, code, timeout=3):
        return h.execute([sys.executable, '-c', code], self.w, self.r, timeout,
                         h.fingerprints(self.w, ['app.py']))

    def test_success_failure_and_unique_logs(self):
        a, p = self.run_code('print("hello")')
        b, q = self.run_code('raise SystemExit(7)')
        self.assertEqual((a['status'], b['status'], b['exit_code']), ('PASS', 'FAIL', 7))
        self.assertNotEqual(p, q)
        self.assertIn('hello', (p.parent / 'output.log').read_text())

    def test_timeout(self):
        r, _ = self.run_code('import time; time.sleep(5)', .05)
        self.assertEqual((r['status'], r['reason']), ('BLOCKED', 'timeout'))
        self.assertIsNotNone(r['exit_code'])

    def test_missing_command_and_cwd(self):
        for cmd, cwd in [(['/no/such/command'], self.w), ([sys.executable], self.w / 'missing')]:
            r, _ = h.execute(cmd, cwd, self.r, 1)
            self.assertEqual(r['status'], 'BLOCKED')

    def test_no_shell_interpretation(self):
        r, p = h.execute([sys.executable, '-c', 'import sys; print(sys.argv[1])', '$(touch HACKED); hi'], self.w, self.r, 3)
        self.assertFalse((self.w / 'HACKED').exists())
        self.assertIn('$(touch', (p.parent / 'output.log').read_text())

    def test_large_output(self):
        r, p = self.run_code('print("a" * 1000000)')
        self.assertGreater((p.parent / 'output.log').stat().st_size, 1000000)

    def test_log_failure(self):
        with patch('harness.shutil.copyfileobj', side_effect=OSError('disk full')):
            r, _ = self.run_code('print(1)')
        self.assertEqual(r['status'], 'BLOCKED')

    def test_metadata_failure_prevents_execution(self):
        with patch('pathlib.Path.open', side_effect=PermissionError('denied')):
            with self.assertRaises(PermissionError):
                self.run_code('print(1)')

    def record(self):
        _, p = self.run_code('print(1)')
        return {'requirements': [{'id': 'R1', 'kind': 'task', 'source': 'brief:1',
                'requirement': 'one', 'acceptance': 'outputs 1', 'revision': 'v1',
                'status': 'PASS', 'approval': 'G1', 'implementation': ['app.py'],
                'evidence': str(p.relative_to(self.r)), 'verification': 'observed 1'}],
                'approvals': [{'id': 'G1', 'revision': 'v1', 'decision': 'approved', 'source': 'user:1'}]}

    def test_trace_current_then_stale(self):
        data = self.record()
        self.assertEqual(h.trace(data, self.w, self.r)['status'], 'PASS')
        (self.w / 'app.py').write_text('print(2)')
        self.assertEqual(h.trace(data, self.w, self.r)['status'], 'FAIL')

    def test_trace_missing_duplicate_bad_status_approval(self):
        for mutation in ('source', 'approval', 'evidence', 'status', 'duplicate'):
            d = self.record()
            if mutation == 'duplicate': d['requirements'] *= 2
            else: d['requirements'][0][mutation] = ''
            self.assertEqual(h.trace(d, self.w, self.r)['status'], 'FAIL')
        self.assertEqual(h.trace({}, self.w, self.r)['status'], 'FAIL')

    def test_failed_evidence(self):
        d = self.record()
        p = self.r / d['requirements'][0]['evidence']
        e = h.read(p); e['exit_code'] = 1; e['status'] = 'FAIL'
        p.write_text(json.dumps(e))
        self.assertEqual(h.trace(d, self.w, self.r)['status'], 'FAIL')

    def test_submission(self):
        (self.w / 'out.csv').write_text('id,value\na,1\n')
        spec = {'source': 'brief:2', 'run_instructions': 'read csv', 'files': [
            {'path': 'out.csv', 'format': 'csv', 'columns': ['id', 'value'], 'rows': 1}]}
        self.assertEqual(h.submission(spec, self.w)['status'], 'PASS')
        spec['files'][0]['rows'] = 2
        self.assertEqual(h.submission(spec, self.w)['status'], 'FAIL')
        self.assertEqual(h.submission({}, self.w)['status'], 'BLOCKED')

    def test_path_escape_empty_and_json(self):
        (self.w / 'empty').touch()
        (self.w / 'bad.json').write_text('{')
        (self.w / 'link').symlink_to('/etc/passwd')
        for name, fmt in [('empty', 'file'), ('../outside', 'file'), ('link', 'file'), ('bad.json', 'json')]:
            spec = {'source': 's', 'run_instructions': 'x', 'files': [{'path': name, 'format': fmt}]}
            self.assertEqual(h.submission(spec, self.w)['status'], 'FAIL')
        with self.assertRaises(ValueError): h.external_records(h.ROOT / 'records', self.w)

    def test_cli_exact_failure_code_and_invalid_input(self):
        cmd = [sys.executable, str(h.ROOT / 'harness.py'), '테스트', '--workspace', str(self.w), '--record-dir', str(self.r)]
        r = subprocess.run(cmd + ['--', sys.executable, '-c', 'raise SystemExit(7)'], capture_output=True)
        self.assertEqual(r.returncode, 7)
        r = subprocess.run(cmd, capture_output=True)
        self.assertEqual(r.returncode, 2)

if __name__ == '__main__':
    unittest.main()
