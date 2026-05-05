# Asset Allocation Manager - Streamlit App

이 디렉터리는 자산 배분 관리를 위한 Streamlit 웹 애플리케이션의 모듈화된 버전을 포함합니다.

## 파일 구조

```
streamlit/
├── __init__.py                    # 패키지 초기화 파일
├── main.py                        # 메인 앱 진입점
├── config_utils.py                # 설정 파일 로드/저장 유틸리티
├── asset_utils.py                 # 자산 비율 조회 유틸리티
├── rebalancing_utils.py           # 리밸런싱 실행 유틸리티
├── asset_allocation_page.py       # 자산 배분 설정 페이지
├── cost_average_page.py           # 원달러 평균 매수 설정 페이지
├── rebalancing_page.py            # 리밸런싱 실행 페이지
└── README.md                      # 이 파일
```

## 각 파일의 역할

### `main.py`
- 메인 앱의 진입점
- 탭 구조를 정의하고 각 페이지를 렌더링
- Streamlit 페이지 설정

### `config_utils.py`
- YAML 설정 파일 로드/저장 기능
- AssetAllocateAgent.yaml, CostAverageAgent.yaml 관리
- 에러 처리 및 사용자 피드백

### `asset_utils.py`
- 실제 계좌에서 현재 자산 비율 조회
- 샘플 데이터 제공 (API 연결 실패 시)
- 자산 비율 계산 로직

### `rebalancing_utils.py`
- 리밸런싱 실행 기능
- subprocess를 통한 외부 명령어 실행
- 실행 결과 처리 및 사용자 피드백

### `asset_allocation_page.py`
- 자산 배분 설정 UI
- 계좌별, 통화별 자산 비율 설정
- 자산 추가/삭제 기능
- 실시간 비율 검증

### `cost_average_page.py`
- 원달러 평균 매수 설정 UI
- 계좌별, 통화별 매수 금액/수량 설정
- 자산 추가/삭제 기능

### `rebalancing_page.py`
- 리밸런싱 실행 UI
- 경고 메시지 및 실행 정보 표시
- 실행 버튼 및 진행 상태 표시

## 사용법

### 새로운 모듈화된 버전 실행
```bash
streamlit run streamlit_app_new.py
```

### 기존 버전 실행 (비교용)
```bash
streamlit run streamlit_app.py
```

## 장점

1. **모듈화**: 각 기능이 독립적인 파일로 분리되어 유지보수가 용이
2. **가독성**: 코드가 기능별로 정리되어 이해하기 쉬움
3. **재사용성**: 각 모듈을 독립적으로 테스트하고 재사용 가능
4. **확장성**: 새로운 기능 추가 시 새로운 모듈만 추가하면 됨
5. **디버깅**: 문제 발생 시 해당 모듈만 집중해서 디버깅 가능

## 마이그레이션

기존 `streamlit_app.py`에서 새로운 구조로 마이그레이션하려면:

1. `streamlit_app_new.py`를 사용하여 앱 실행
2. 기존 기능이 모두 정상 작동하는지 확인
3. 문제없으면 `streamlit_app.py`를 백업하고 `streamlit_app_new.py`를 `streamlit_app.py`로 이름 변경

## 의존성

- streamlit
- pyyaml
- python-dotenv
- pandas (asset_utils.py에서 사용)
