#!/usr/bin/env python3
"""Local, explicit-step evidence tools. Python 3.9+, standard library only."""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parent
STATES = {'PASS', 'FAIL', 'NOT_RUN', 'BLOCKED', 'HUMAN_CHECK'}


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def inside(path, root):
    return path == root or root in path.parents


def read(path):
    with Path(path).open(encoding='utf-8') as f:
        return json.load(f)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def safe_file(root, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError('상대 파일 경로가 필요합니다')
    p = (root / name).resolve()
    if not inside(p, root) or not p.is_file():
        raise ValueError('파일 누락 또는 작업 공간 이탈: ' + name)
    return p


def external_records(path, workspace):
    p = Path(path).resolve()
    if inside(p, ROOT) or not inside(p, workspace):
        raise ValueError('기록 경로는 과제 작업 공간 안, 하네스 저장소 밖이어야 합니다')
    p.mkdir(parents=True, exist_ok=True)
    return p


def emit(folder, report):
    target = folder / (str(uuid.uuid4()) + '.json')
    with target.open('x', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return target


def execute(argv, cwd, folder, timeout, fingerprints=None):
    if not argv or timeout <= 0:
        raise ValueError('명령과 양수 timeout이 필요합니다')
    run = folder / str(uuid.uuid4())
    run.mkdir()
    report = {'kind': 'execution', 'id': run.name, 'started': stamp(),
              'argv': argv, 'cwd': str(cwd), 'status': 'BLOCKED',
              'exit_code': None, 'output': 'output.log',
              'fingerprints': fingerprints or {}, 'scope': 'process-only',
              'note': '종료 0은 테스트 개수·요구사항 충족을 증명하지 않습니다'}
    # Reserve the metadata before starting a process; never overwrite evidence.
    meta = run / 'result.json'
    with meta.open('x', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False)
    try:
        # Temporary disk spool avoids unbounded memory and detects final log write errors.
        with tempfile.TemporaryFile() as spool:
            proc = subprocess.Popen(argv, cwd=cwd, stdout=spool, stderr=subprocess.STDOUT,
                                    shell=False, start_new_session=(os.name == 'posix'))
            try:
                code = proc.wait(timeout=timeout)
                report.update(exit_code=code, status='PASS' if code == 0 else 'FAIL')
            except subprocess.TimeoutExpired:
                if os.name == 'posix':
                    os.killpg(proc.pid, signal.SIGKILL)
                else:
                    proc.kill()
                code = proc.wait()
                report.update(exit_code=code, status='BLOCKED', reason='timeout')
            spool.seek(0)
            with (run / 'output.log').open('xb') as output:
                shutil.copyfileobj(spool, output)
    except OSError as exc:
        report.update(status='BLOCKED', reason=type(exc).__name__)
    if (run / 'output.log').is_file():
        report['output_sha256'] = digest(run / 'output.log')
    report['finished'] = stamp()
    # Atomic metadata replacement only inside this newly created run directory.
    temp = run / 'result.tmp'
    with temp.open('x', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    temp.replace(meta)
    return report, meta


def fingerprints(workspace, names):
    return {n: digest(safe_file(workspace, n)) for n in names}


def trace(data, workspace, record_dir):
    errors = []
    requirements = data.get('requirements', [])
    if not requirements:
        errors.append('요구사항이 비어 있습니다')
    approvals = {a.get('id'): a for a in data.get('approvals', [])}
    seen = set()
    for r in requirements:
        rid = r.get('id')
        for key in ('id', 'kind', 'source', 'requirement', 'acceptance', 'revision'):
            if not r.get(key):
                errors.append(f'{rid}: 필수 {key} 누락')
        if rid in seen:
            errors.append(f'{rid}: 중복 ID')
        seen.add(rid)
        if r.get('status') not in STATES:
            errors.append(f'{rid}: 상태 오류')
        if r.get('status') != 'PASS':
            continue
        a = approvals.get(r.get('approval'))
        if not a or not a.get('source') or a.get('revision') != r.get('revision') or a.get('decision') != 'approved':
            errors.append(f'{rid}: 현재 버전 사용자 승인 누락')
        if not r.get('implementation') or not r.get('evidence') or not r.get('verification'):
            errors.append(f'{rid}: 구현/검증 판단/증거 누락')
            continue
        try:
            ev = read(safe_file(record_dir, r['evidence']))
            if ev.get('status') != 'PASS' or ev.get('exit_code') != 0:
                errors.append(f'{rid}: 성공 실행 증거 아님')
            evidence_parent = safe_file(record_dir, r['evidence']).parent
            safe_file(evidence_parent, ev.get('output'))
            for name in r['implementation']:
                if ev.get('fingerprints', {}).get(name) != digest(safe_file(workspace, name)):
                    errors.append(f'{rid}: 구현 변경 또는 fingerprint 누락: {name}')
            for name, expected in ev.get('fingerprints', {}).items():
                if digest(safe_file(workspace, name)) != expected:
                    errors.append(f'{rid}: 입력/구현 변경: {name}')
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f'{rid}: 증거 오류 {exc}')
    return {'kind': 'trace', 'status': 'FAIL' if errors else 'PASS', 'errors': errors,
            'requirement_states': {r.get('id', '?'): r.get('status') for r in requirements},
            'note': '형식·연결 검사만 평가. 업무 정확성과 승인 진위는 사람이 확인합니다.'}


def submission(spec, workspace):
    errors = []
    files = spec.get('files', [])
    if not files or not spec.get('source') or not spec.get('run_instructions'):
        return {'kind': 'submission', 'status': 'BLOCKED', 'errors': ['출처·파일 규격·실행 방법 필요']}
    import csv
    for item in files:
        try:
            p = safe_file(workspace, item['path'])
            if p.stat().st_size == 0:
                raise ValueError('빈 파일')
            fmt = item.get('format', 'file')
            if fmt == 'json':
                read(p)
            elif fmt == 'csv':
                if not item.get('columns'):
                    raise ValueError('CSV 기대 열 필요')
                with p.open(encoding='utf-8-sig', newline='') as f:
                    rows = list(csv.reader(f))
                if not rows or rows[0] != item['columns'] or any(len(r) != len(rows[0]) for r in rows[1:]):
                    raise ValueError('CSV 열 불일치')
                if 'rows' in item and len(rows) - 1 != item['rows']:
                    raise ValueError('CSV 행 수 불일치')
            elif fmt != 'file':
                raise ValueError('지원하지 않는 형식; 별도 검사 필요')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"{item.get('path', '?')}: {exc}")
    return {'kind': 'submission', 'status': 'FAIL' if errors else 'PASS', 'errors': errors,
            'note': '파일 형식만 검사. 실행 방법의 실제 동작·저장 UI·최종 제출은 별도 확인.'}


def test_summary(path, framework):
    """Conservative terminal-summary parser; unknown output never passes."""
    tail = ''
    with path.open(encoding='utf-8', errors='replace') as f:
        for line in f:
            tail = (tail + line)[-65536:]
    tail = re.sub(r'\x1b\[[0-9;]*m', '', tail)
    if framework == 'unittest':
        matches = list(re.finditer(r'^Ran (\d+) tests? in .+$', tail, re.M))
        if not matches:
            return {'status': 'HUMAN_CHECK', 'reason': 'unittest summary not found'}
        m = matches[-1]
        count = int(m.group(1))
        end = tail[m.end():].strip()
        if count == 0:
            return {'status': 'FAIL', 'count': 0, 'reason': 'empty test suite'}
        if end != 'OK':
            return {'status': 'HUMAN_CHECK', 'count': count, 'reason': 'nonstandard, skipped or incomplete summary'}
        return {'status': 'PASS', 'count': count}
    if framework == 'pytest':
        lines = [x.strip('= ').strip() for x in tail.splitlines() if re.search(r' in \d+(?:\.\d+)?s', x)]
        if not lines:
            return {'status': 'HUMAN_CHECK', 'reason': 'pytest summary not found'}
        line = lines[-1]
        m = re.fullmatch(r'(\d+) passed in \d+(?:\.\d+)?s(?: \(.*\))?', line)
        if m and int(m.group(1)) > 0:
            return {'status': 'PASS', 'count': int(m.group(1))}
        if 'no tests ran' in line:
            return {'status': 'FAIL', 'count': 0, 'reason': 'empty test suite'}
        return {'status': 'HUMAN_CHECK', 'reason': 'failed/skipped/deselected/unknown summary'}
    return {'status': 'HUMAN_CHECK', 'reason': 'unsupported framework'}


def check_plan(spec, workspace, record_dir):
    checks = spec.get('planned_checks')
    if not isinstance(checks, list) or not checks:
        return {'kind': 'plan', 'status': 'BLOCKED', 'errors': ['검사 계획이 비어 있습니다'], 'results': []}
    results, ids = [], set()
    for c in checks:
        item = {'id': c.get('id'), 'status': 'BLOCKED'}
        try:
            if not c.get('id') or c['id'] in ids:
                raise ValueError('검사 ID 누락/중복')
            ids.add(c['id'])
            if type(c.get('required')) is not bool:
                raise ValueError('required는 명시적 boolean이어야 합니다')
            if not c.get('requirements') or not c.get('expected') or not c.get('command'):
                raise ValueError('요구 ID·기대 결과·명령 필요')
            if not c['required']:
                item.update(status='NOT_RUN', reason='optional: 전체 필수 검사 판정에서 제외')
            elif not c.get('evidence'):
                item.update(status='NOT_RUN', reason='증거 누락')
            else:
                ep = safe_file(record_dir, c['evidence'])
                ev = read(ep)
                if ev.get('kind') != 'execution' or ev.get('argv') != c['command'] or ev.get('cwd') != str(workspace):
                    raise ValueError('증거 종류/명령/작업 경로 불일치')
                output = safe_file(ep.parent, ev.get('output'))
                if ev.get('output_sha256') != digest(output):
                    raise ValueError('출력 해시 누락/변경: 새 실행 필요')
                names = c.get('fingerprints')
                if not isinstance(names, list) or not names:
                    raise ValueError('검사 관련 입력·구현·테스트 fingerprint 목록 필요')
                for name in names:
                    if ev.get('fingerprints', {}).get(name) != digest(safe_file(workspace, name)):
                        raise ValueError('fingerprint 누락/변경: ' + name)
                if ev.get('status') != 'PASS' or ev.get('exit_code') != 0:
                    item.update(status='FAIL' if ev.get('status') == 'FAIL' else 'BLOCKED', reason='실행 실패/차단')
                else:
                    item.update(test_summary(output, c.get('framework')))
                    minimum = c.get('minimum_tests')
                    if type(minimum) is not int or minimum < 1:
                        raise ValueError('minimum_tests는 승인된 양수 정수여야 합니다')
                    if item['status'] == 'PASS' and item['count'] < minimum:
                        item.update(status='FAIL', reason='승인된 최소 검사 개수 미달: 일부 실행 가능성')
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            item.update(status='BLOCKED', reason=str(exc))
        item['required'] = c.get('required', True)
        results.append(item)
    required = [r for r in results if r['required'] is not False or r['status'] == 'BLOCKED']
    states = [r['status'] for r in required]
    status = 'BLOCKED' if not required else next((x for x in ['FAIL', 'BLOCKED', 'NOT_RUN', 'HUMAN_CHECK'] if x in states), 'PASS')
    return {'kind': 'plan', 'status': status, 'results': results,
            'note': '승인된 계획의 필수 검사만 대조. 계획 자체의 완전성·동일 개수의 다른 테스트·업무 정확성은 별도 확인.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['진단', '테스트', '추적검사', '제출검사', '계획검사'])
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--record-dir', required=True)
    parser.add_argument('--timeout', type=float, default=30)
    parser.add_argument('--input', help='추적/제출 검사 JSON 파일')
    parser.add_argument('--fingerprint', action='append', default=[], help='작업 공간 기준 입력/구현 파일')
    # Commands are explicitly separated from harness options.
    raw = list(sys.argv[1:] if argv is None else argv)
    command = []
    if '--' in raw:
        cut = raw.index('--')
        command, raw = raw[cut + 1:], raw[:cut]
    args = parser.parse_args(raw)
    try:
        workspace = Path(args.workspace).resolve(strict=True)
        if not workspace.is_dir() or args.timeout <= 0:
            raise ValueError('작업 디렉터리/timeout 오류')
        folder = external_records(args.record_dir, workspace)
        if args.action == '테스트':
            report, target = execute(command, workspace, folder, args.timeout, fingerprints(workspace, args.fingerprint))
        elif args.action == '진단':
            results = []
            for cmd in ([sys.executable, '--version'], ['node', '--version'], ['git', '--version']):
                r, p = execute(cmd, workspace, folder, args.timeout)
                results.append({'tool': cmd[0], 'status': r['status'], 'evidence': str(p)})
            report = {'kind': 'environment', 'cwd': str(workspace), 'results': results,
                      'status': 'PASS' if all(r['status'] == 'PASS' for r in results) else 'BLOCKED'}
            target = emit(folder, report)
        else:
            if not args.input:
                raise ValueError('--input 필요')
            data = read(args.input)
            if args.action == '추적검사':
                report = trace(data, workspace, folder)
            elif args.action == '계획검사':
                report = check_plan(data, workspace, folder)
            else:
                report = submission(data, workspace)
            target = emit(folder, report)
        print(json.dumps({'report': str(target), **report}, ensure_ascii=False, indent=2))
        if args.action == '테스트' and report['status'] == 'FAIL':
            code = report['exit_code']
            return code if code > 0 else 128 - code
        return 0 if report['status'] == 'PASS' else 1 if report['status'] == 'FAIL' else 2
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        print(json.dumps({'status': 'BLOCKED', 'reason': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
