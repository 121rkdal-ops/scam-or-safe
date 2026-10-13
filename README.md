# SCAM OR SAFE?

## 실행
`pip install -r requirements.txt`
`python -m streamlit run app.py`

## 구현
- 8문항, 정답 보기 길이 조정, 결과/영역별 학습 피드백
- SQLite 공개 댓글: 결과 페이지에서 닉네임·후기 입력, 최근 40개 공개
- 운영자 댓글 숨김: Streamlit secrets의 `ADMIN_PASSWORD` 설정 시 활성화

## 주의
- SQLite 로컬 파일은 Streamlit Community Cloud에서 영구 보존되지 않습니다. 앱 재시작/재배포 시 댓글이 사라질 수 있고 복수 인스턴스 간 공유도 보장되지 않습니다.
- 댓글은 개인정보를 입력하지 않도록 안내하며 단순 패턴 차단만 구현했습니다. 실제 공개 운영 전 스팸 방지·신고/삭제 정책·개인정보 안내·출처 URL 검증이 필요합니다.
- 사용자의 **퀴즈 응답은 서버에 수집하지 않습니다.** 세션 내 점수만 계산합니다.
- 문항은 교육용 가상 사례입니다. 출처 문서명과 URL은 배포 전 검증해야 합니다.
