# 기록 규약 v1

records.json은 사실과 결정의 단일 기록, checks.json은 검사 계획·제출 규격입니다. 실제 기록은 하네스 밖에 둡니다. 원시 출력은 실행별 디렉터리의 output.log에 한 번 저장하고 경로만 참조합니다.

- requirements: id, kind(official/task/stakeholder/user/proposal/assumption), source(파일:쪽/절 또는 메시지), requirement, acceptance, revision, approval(승인 ID), implementation(작업 공간 기준 파일 배열), verification(수용 기준과 관측 대조), evidence(기록 경로 기준 result.json), status.
- questions: id, requirements, gap_source, question, impact_by_answer, state, actual_answer, answer_source. 미수신 답변은 빈 값.
- decisions: id, requirements, decision, reason, alternatives, limitations, source.
- approvals: id, gate(G1~G5), revision, scope, decision(approved/rejected/pending), source, time. 스크립트는 문자열·연결만 검사하며 실제 사용자 승인 여부는 Codex와 사용자가 대조.
- handoff: stage, current_state, pending, blockers, next_action, files, commands, approvals, evidence.
- checks.json: source, run_instructions, files([{path, format:file/json/csv, columns:CSV일 때, rows:선택}]), planned_checks([{id, requirements, command:인자 배열, expected, required:boolean, framework:pytest/unittest, minimum_tests:양수 정수, fingerprints:관련 상대 파일 배열, evidence}]).

PASS=지정 검사 실제 통과, FAIL=실행 결과 불충족, NOT_RUN=미실행, BLOCKED=필수 입력/권한/환경 부족, HUMAN_CHECK=사람 확인 대기.

추적검사는 모든 요구사항이 PASS인지 판정하지 않습니다. 형식 PASS여도 NOT_RUN 요구가 남을 수 있습니다. PASS 요구는 현재 revision 승인·구현·검증 설명·성공 실행·출력 파일·fingerprint가 필요합니다. 실행 시 --fingerprint에 관련 구현뿐 아니라 입력·테스트 파일도 지정하세요. 지정하지 않은 파일 변경은 자동 탐지하지 못합니다. 인과 관계와 업무 정확성은 수용 기준으로 별도 검증합니다.

최종 검증에서는 planned_checks의 필수 항목마다 실제 실행 범위·개수·증거를 대조합니다. 빈 검사/미실행/실패/사람 확인 대기를 포함해 전체 PASS로 집계하지 않습니다. 플랫폼 제출 완료는 사용자 확인 전 HUMAN_CHECK입니다.

증거에는 argv·cwd·시각·상태·실제 종료 코드·SHA256·출력 경로가 들어갑니다. 원본 출력은 로컬에 보존하며 자동 마스킹하지 않으므로 민감한 내용을 출력하는 명령을 실행하지 마세요. timeout이나 기록 실패는 BLOCKED. 실행기 CLI는 양수 child 종료 코드를 보존하고 시그널 종료는 128+시그널, 도구 오류는 2로 반환합니다. JSON의 exit_code는 원래 값을 보존합니다.

## 계획검사 입력 예시

아래는 설정 예시입니다. 실제 과제의 승인된 검사 범위와 개수를 넣고 실행 후 evidence를 연결합니다. 기존 양식에 예제 데이터를 자동 삽입하지 않습니다.

```json
{"id":"C1","requirements":["R1"],"expected":"승인된 3개 사례 통과","required":true,"command":["python","-m","unittest","discover","-s","tests","-v"],"framework":"unittest","minimum_tests":3,"fingerprints":["src/main.py","tests/test_main.py"],"evidence":"실제-실행-ID/result.json"}
```

argv는 실행 증거와 정확히 일치해야 합니다. --fingerprint에 관련 입력·구현·테스트를 지정해야 합니다. 기존 v1 증거에 출력 해시가 없으면 재실행합니다. optional 항목만 있는 계획과 빈 계획은 BLOCKED, 필수 증거 없음은 NOT_RUN, 개수 미달은 FAIL, skipped/deselected/해석 불가 출력은 HUMAN_CHECK입니다. 실패 상태는 성공으로 집계하지 않습니다. 필수 검사만 집계하며 선택 항목 제외를 표시합니다.

계획검사는 테스트 이름 전체를 비교하지 않습니다. 같은 개수의 다른 테스트 실행·누락된 계획 항목·기록 조작은 자동 증명할 수 없습니다. 단순한 사용자 프로그램은 성공 로그 형식을 흉내낼 수 있으므로 승인된 실제 테스트 명령과 범위를 사람이 확인합니다. 로그의 마지막 64KiB에서 요약을 해석하며 지원되지 않는 버전/언어/플러그인 형식은 HUMAN_CHECK로 둡니다.
