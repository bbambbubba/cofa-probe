# 공개 배포 전 파일 검토

검토일: 2026-10-30. 결론: 아래 명시적 18개 파일은 공개 후보로 준비됨. GitHub 게시·저작권자 최종 확인은 HUMAN_CHECK이며 아직 게시하지 않았습니다.

## 확인 결과

- 문서·코드·합성 테스트·빈 양식·라이선스 범위를 확인했습니다. 공식 PDF 원문, 참고 저장소 사본, 실제 과제·답변·데이터, 제작 대화와 원시 실행 로그는 배포 목록에 없습니다.
- 개인 홈 경로, 키 형태, 개인키 헤더, 이메일, 인증 포함 URL 패턴 검색에서 일치 0건입니다. 내용 검토와 패턴 검색은 모든 민감정보 부재를 보증하지 않습니다.
- 두 JSON 양식은 빈 상태입니다. 문서 내부 상대 링크가 존재합니다.
- harness.py와 테스트 2개의 SHA256이 개선-v2의 24개 테스트 통과 버전과 일치합니다. 이번 변경은 안내 문서만으로 코드 테스트를 반복하지 않았습니다.
- Git 추적 파일·커밋 이력은 아직 없습니다. 삭제된 커밋 내용도 없습니다. 공개 대상 18개 파일을 명시적으로 스테이징했습니다. 커밋과 게시 전 상태입니다.
- 무시 파일은 Python 캐시 3개이며 공개 ZIP에서 제외합니다. .git 전체, 캐시, 하네스 밖 검증 원시 로그도 포함하지 않습니다. 원본 파일을 임의 삭제하지 않았습니다.
- 코드 재사용 없이 독립 구현했습니다. MIT 문서가 있으며 현재 저작권 표기는 Cofa Probe Harness contributors입니다. 게시할 소유자가 최종 확인해야 합니다.
- 모델 안내는 대회 가이드의 버전과 공식 API 문서를 구분합니다. 표의 작업 배정은 시작 설정 제안이며 실측 우열이 아닙니다. Cofa 모델·추론 메뉴·MCP·제출 UI는 미검증입니다.

## 검토 중 반영한 수정

QUICKSTART.md와 MODEL_GUIDE.md를 추가하고 README 진입 링크와 PUBLISH 명시적 add 목록을 갱신했습니다. 최신 Terra 6.1 특성을 대회 표기의 Terra 5.6에 적용하지 않았습니다. 게시용 ZIP에는 공개 목록만 포함합니다.

## 공개 파일 목록

- `.gitignore`
- `AGENTS.md`
- `LICENSE`
- `OPTIONAL_TOOLS.md`
- `PROMPTS.md`
- `PUBLISH.md`
- `README.md`
- `SOURCES.md`
- `VALIDATION.md`
- `harness.py`
- `schema.md`
- `templates/checks.json`
- `templates/records.json`
- `tests/test_harness.py`
- `tests/test_plan.py`
- `QUICKSTART.md`
- `MODEL_GUIDE.md`
- `RELEASE_REVIEW.md`

## 남은 사용자 확인

게시할 GitHub 소유자/저장소, MIT 저작권자 표기, 공개할 파일 목록을 확인한 뒤 게시를 승인해야 합니다. 원 요청 §9의 게시 전 확인 단계입니다. 이 검토는 대회 사용 허가나 실제 제출 완료를 대신하지 않습니다.
