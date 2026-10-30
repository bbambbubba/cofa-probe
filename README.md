# Cofa Probe Harness

미공개 과제용 단계별 지침과 로컬 증거 도구. 과제 언어·분야·정답을 정하지 않습니다. Python 3.9 이상과 표준 라이브러리만 사용합니다. 실제 Cofa 호환성은 미검증입니다.

처음 사용하면 [간단 사용법](QUICKSTART.md), 모델을 선택하려면 [모델·추론 수준 안내](MODEL_GUIDE.md)를 먼저 읽으세요.

## 시작
1. 실제 과제의 README·AGENTS.md·제출 경로를 먼저 읽습니다. 기존 파일을 덮어쓰지 않습니다.
2. Codex에 “이 하네스의 AGENTS.md와 PROMPTS.md를 읽고 시작·환경 진단을 수행해줘”라고 요청합니다. 하위 clone의 지침은 상위 과제에 자동 적용된다고 가정하지 않습니다.
3. 기록은 하네스 저장소 **밖**, 제공 과제 작업 공간 **안**에 둡니다. templates는 빈 양식이며 기존 기록이 없을 때만 복사합니다.
4. PROMPTS.md에서 한 단계씩 선택합니다. 다섯 승인 지점에서 사용자 확인을 기다립니다.

## 실제 터미널 명령
아래 /path는 실제 경로로 바꿉니다. --workspace는 과제 작업 공간이며 현재 셸 위치와 무관합니다.

```sh
python /path/cofa-probe/harness.py --help
python /path/cofa-probe/harness.py 진단 --workspace /path/task --record-dir /path/task/records
python /path/cofa-probe/harness.py 테스트 --workspace /path/task --record-dir /path/task/records --timeout 60 --fingerprint src/main.py -- python -m unittest discover -s tests -v
python /path/cofa-probe/harness.py 추적검사 --workspace /path/task --record-dir /path/task/records --input /path/task/records/records.json
python /path/cofa-probe/harness.py 제출검사 --workspace /path/task --record-dir /path/task/records --input /path/task/records/checks.json
```

테스트 명령은 `--` 뒤 인자를 셸 재해석 없이 실행합니다. 파이프·리다이렉션은 처리하지 않습니다. 인자에 비밀값을 넣지 마세요. 명령·출력은 로컬 증거에 저장되며 자동 외부 전송은 없습니다. 실행 대상 프로그램 자체가 외부 통신하거나 비밀값을 출력하는지는 실행 전 별도로 검토합니다.

실행기 PASS는 프로세스 종료 0만 의미합니다. 필수 검사 누락·빈 테스트·최소 개수 미달은 아래 계획검사로 별도 확인합니다.

```sh
python /path/cofa-probe/harness.py 계획검사 --workspace /path/task --record-dir /path/task/records --input /path/task/records/checks.json
```

계획검사는 필수 항목의 실제 argv/cwd·출력 SHA256·관련 파일 fingerprint·프레임워크 요약·최소 테스트 수를 대조합니다. 승인된 계획이 빠짐없이 작성됐는지와 업무 정확성까지 증명하지는 않습니다. pytest/unittest의 인식 가능한 성공 요약만 자동 통과하며 skipped/deselected·알 수 없는 형식은 HUMAN_CHECK입니다.

상세 기록은 schema.md, 선택 도구는 OPTIONAL_TOOLS.md, 검증 범위는 VALIDATION.md, 공개 전 절차는 PUBLISH.md를 읽습니다.

## 하네스 자체 테스트
저장소 루트에서 `python -m unittest discover -s tests -v`를 실행합니다. 자체 테스트 통과는 대회 과제 성공이나 제출 완료의 증거가 아닙니다.
