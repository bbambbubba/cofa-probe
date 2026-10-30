# 공개 전 체크리스트

현재 게시하지 않았습니다. 최소 기능 확인·개선 방향 확인·최종 검토 후 게시에 대한 별도 사용자 확인을 받습니다.

- [ ] README·지침·빈 templates·스크립트·합성 테스트·출처·라이선스만 공개 목록에 포함.
- [ ] 실제 문제·데이터·답변·실행 로그·개인 경로·접속 링크·인증정보·개인정보가 없는지 파일 내용을 검토.
- [ ] `git status --short --untracked-files=all`, `git ls-files`, `git ls-files --others --ignored --exclude-standard`로 추적/미추적/무시 파일 확인.
- [ ] `git log --all -p`로 삭제된 내용과 커밋 메시지까지 검토. .gitignore만 믿지 않음.
- [ ] 패턴 검색은 보조 수단이며 비밀값 부재를 보증하지 않음.
- [ ] 신규 MIT 저작권자 표기와 재사용 출처 확인.
- [ ] 자체 테스트 결과·Cofa 미검증·제한 사항 공개.
- [ ] 사용자가 검토된 파일과 게시 대상을 확인.

승인 후 사전 준비 환경에서만 수동 실행 예시(실제 URL로 교체):

```sh
git add QUICKSTART.md MODEL_GUIDE.md RELEASE_REVIEW.md README.md AGENTS.md PROMPTS.md harness.py schema.md templates tests OPTIONAL_TOOLS.md SOURCES.md VALIDATION.md PUBLISH.md LICENSE .gitignore
git diff --cached --check
git diff --cached
git commit -m "Add independently implemented Cofa step harness"
git branch -M main
git remote add origin https://github.com/OWNER/cofa-probe.git
git push -u origin main
```

기존 remote가 있으면 먼저 확인하며 덮어쓰지 않습니다. 이 push 절차는 대회 전 공개 도구 배포용입니다. 실제 대회 환경에서는 push·외부 전송을 수행하지 않습니다. 권한이 없으면 사용자 소유 GitHub 저장소에 사용자가 직접 게시합니다.
