# IPU AI 방화벽 Docs Linking Plan

## 목적

이 문서는 현재 쌓인 `business`, `development`, 상위 `docs` 문서를 어떻게 연결하고 노출할지 정리한다.  
목표는 문서가 많아져도 처음 보는 사람이 어디서부터 봐야 하는지 쉽게 알 수 있게 만드는 것이다.

## 현재 상태

현재 문서 구조는 다음처럼 나뉘어 있다.

- `docs/00-master-roadmap.md`
- `docs/development/*`
- `docs/business/*`

이 구조 자체는 나쁘지 않지만, 상위 진입점이 명확하지 않으면 문서를 찾기 어려워질 수 있다.

## 기본 원칙

- 루트 README는 가장 짧은 진입점이어야 한다.
- `docs/`는 전체 문서 구조를 안내하는 허브가 되어야 한다.
- `docs/business/`와 `docs/development/`는 각자의 인덱스를 가져야 한다.
- 처음 보는 사람, 개발자, 고객 대응 담당자가 각각 다른 경로로 들어갈 수 있어야 한다.

## 권장 문서 진입 구조

### 1. 루트 README

루트 README에는 아래만 간단히 연결하는 것이 좋다.

- 제품 한 줄 소개
- 현재 상태
- 빠른 시작
- 주요 문서 링크
  - master roadmap
  - business index
  - development index

즉 루트 README는 상세 문서가 아니라 `입구`여야 한다.

### 2. docs 허브 문서

`docs/README.md` 또는 유사한 상위 문서를 두고 아래를 안내하는 것이 좋다.

- 문서 구조 개요
- business 문서로 가는 링크
- development 문서로 가는 링크
- 추천 읽기 순서

### 3. business 인덱스

이미 [30-business-doc-index.md](./30-business-doc-index.md)가 있다.  
이 문서를 business 진입 문서로 계속 유지하면 된다.

### 4. development 인덱스

development 쪽도 business와 비슷하게 인덱스 문서가 있으면 좋다.

예:

- `docs/development/00-development-doc-index.md`

여기에는:

- 제품 개요
- 시스템 아키텍처
- MVP 범위
- 백로그
- 향후 기술 문서

를 연결하면 된다.

## 권장 링크 구조

### 루트 README에서 링크할 문서

- `docs/00-master-roadmap.md`
- `docs/business/30-business-doc-index.md`
- `docs/development/00-development-doc-index.md` 또는 기존 핵심 문서

### docs 허브에서 링크할 문서

- business 핵심 요약 문서
- development 핵심 구조 문서
- 현재 상태를 설명하는 master roadmap

### business 인덱스에서 링크할 문서

- 이미 분류 체계가 갖춰져 있으므로 유지

### development 인덱스에서 링크할 문서

- `01-product-overview`
- `02-system-architecture`
- `03-mvp-scope`
- `04-backlog`
- 이후 API/엔진/테스트 관련 문서가 생기면 추가

## 사용자별 추천 진입점

### 1. 처음 보는 사람

- 루트 README
- `28-executive-summary-ko`
- `12-one-page-summary`

### 2. 개발 담당자

- `docs/00-master-roadmap.md`
- development 인덱스
- 아키텍처 문서
- 백로그

### 3. 영업/사업 담당자

- business 인덱스
- 세일즈 메시지
- PoC 문서
- FAQ

### 4. 투자자/운영사

- executive summary
- investor one-pager
- investor Q&A

## 지금 필요한 최소 조치

가장 먼저 필요한 것은 아래 두 가지다.

1. `docs/README.md` 추가
2. `docs/development/00-development-doc-index.md` 추가

이 두 문서가 생기면 구조가 훨씬 안정된다.

## 나중에 할 수 있는 보강

- 루트 README에 문서 링크 정리
- 각 폴더별 README 정리
- 실제 고객 사례가 생긴 뒤 case study 섹션 추가
- development 문서가 늘어나면 API/엔진/테스트 별 하위 인덱스 추가

## 피해야 할 것

- 루트 README에 모든 링크를 다 넣는 것
- business와 development 문서를 한 파일에 섞는 것
- 인덱스 없이 문서를 계속 추가하는 것

## 결론

현재 문서 체계는 이미 충분히 좋다.  
다만 이제는 문서를 더 만드는 것만큼, `어떻게 들어오고 어떻게 찾아보게 할 것인가`를 정리해야 한다.  
루트 README는 입구, `docs/README.md`는 허브, `business/development` 인덱스는 분야별 안내 역할을 하도록 정리하는 것이 가장 자연스럽다.
