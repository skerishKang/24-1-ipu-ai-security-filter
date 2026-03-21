# 13. HWP Conversion Candidates

## 목적

이 문서는 바이너리 `.hwp` 파일을 `manual-preview` 입력 경로에 연결하기 위한 현실적인 변환 후보를 정리한다.  
현재 기준 목표는 "바이너리 HWP 직접 파싱"이 아니라, 운영 가능한 변환 경로를 빠르게 고정하는 것이다.

## 현재 결론

- 제품 기본 전략은 그대로 `manual-convert-to-hwpx` 다.
- 즉 사용자가 `.hwp` 를 `.hwpx`, `.pdf`, `.docx`, `.txt` 중 하나로 변환한 뒤 업로드하게 안내한다.
- 코드와 UI도 이미 이 전략에 맞춰 `.hwp` 선택 시 변환 안내 문구를 보여준다.

## 후보 우선순위

### 1. LibreOffice headless

- 명령 후보: `soffice`, `libreoffice`
- 역할: `.hwp -> .pdf` 또는 `.hwp -> .docx`
- 장점:
  - 기존 PDF/DOCX parser 경로를 그대로 재사용 가능
  - 서버 측 자동 변환 파이프라인으로 확장하기 쉽다
- 단점:
  - 운영 환경마다 설치 편차가 크다
  - 변환 품질과 글꼴 의존성이 남는다

현재 판단:

- 로컬 환경에서 명령이 있으면 가장 먼저 붙일 후보다
- 없으면 설치 비용까지 포함해 운영 판단이 필요하다

### 2. pyhwp / hwp5txt

- 명령 후보: `hwp5txt`
- 역할: `.hwp -> plain text`
- 장점:
  - `manual-preview` 목적에는 텍스트만 뽑아도 충분한 경우가 많다
  - 가장 얇은 경로로 backend parser에 연결하기 쉽다
- 단점:
  - 레이아웃, 표, 문단 구조 보존은 약하다
  - 운영 환경에 별도 설치가 필요하다

현재 판단:

- "텍스트 추출만 되면 된다"는 목적에는 유력한 후보다
- 다만 실제 운영 도입 전 샘플 품질 검증이 먼저 필요하다

### 3. PDF OCR fallback chain

- 현재 보유 도구: `pdftoppm`, `tesseract`
- 역할: `.hwp -> .pdf` 변환이 가능한 환경이 생기면 기존 OCR fallback 경로 재사용
- 장점:
  - 이미 프로젝트 안에 OCR 경로가 존재한다
  - 스캔형 PDF 대응과 한 줄로 이어진다
- 단점:
  - `.hwp -> .pdf` 앞단 변환기가 여전히 필요하다
  - OCR 노이즈로 품질 손실이 있다

현재 판단:

- 단독 후보가 아니라 1번 보조 경로다

## 로컬 프로브

현재 저장소에는 변환 도구 존재 여부를 빠르게 확인하는 스크립트를 추가했다.

```bash
cd /mnt/g/Ddrive/BatangD/task/workdiary/24-1-ipu-ai-firewall
python3 scripts/probe_hwp_conversion_tools.py
python3 scripts/probe_hwp_conversion_tools.py --json
```

이 스크립트는 아래를 확인한다.

- `soffice`
- `libreoffice`
- `hwp5txt`
- `tesseract`
- `pdftoppm`
- `pdftocairo`

## 현재 재시작 지점

다음 구현을 시작할 때는 아래 순서로 가는 것이 맞다.

1. `scripts/probe_hwp_conversion_tools.py` 실행
2. `soffice` 가 있으면 `.hwp -> .pdf` 자동 변환 PoC부터 시도
3. `hwp5txt` 가 있으면 plain text 추출 PoC를 별도로 비교
4. 둘 다 없으면 현재처럼 변환 안내 전략 유지

## 보류 기준

아래 중 하나라도 만족하지 못하면 `.hwp` 자동 변환을 기본값으로 열지 않는다.

- 로컬/운영 환경에서 재현 가능한 변환기 존재
- 샘플 문서 기준 텍스트 품질 확인
- 실패 시 사용자 안내 문구와 fallback 경로 정리
