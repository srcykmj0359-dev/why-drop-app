# 왜빠짐

국장 개인투자자를 위한 AI 하락 원인 분석 앱 MVP입니다.

## 주요 기능

- 종목명/종목코드 검색
- 주가/등락률/원달러 환율 표시
- 네이버 뉴스 기반 하락 원인 분석
- OpenDART 공시 조회
- AI 요약 및 하락 원인 점수판
- 심층 분석 리포트
- 관심종목 저장
- 최근 조회 종목
- 코스피·코스닥 급락 TOP
- 공시 위험 TOP
- 캐시/호출량 관리
- 오류 처리 및 로그 저장

## 로컬 실행

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

## 환경변수

로컬에서는 `.env` 파일을 생성하고 아래 값을 넣습니다.

```env
OPENAI_API_KEY=...
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...
DART_API_KEY=...
```

배포 시에는 Streamlit Cloud 또는 배포 플랫폼의 Secrets/Environment Variables에 등록합니다.

## 주의

`.env`, `cache_data`, `api_usage.json`, `error_log.txt`, `watchlist.json`, `recent_queries.json`은 GitHub에 올리지 않습니다.
