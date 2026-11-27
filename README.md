# 🏢 Jeolmi Office — 절미 본부 오피스 PWA

경세 님의 개인 비서 절미가 4개 파트를 돌리는 모습을 아이소메트릭 미니어처 오피스로 보여 주는 모바일 웹앱(PWA)입니다. 설치하면 폰 홈 화면에서 앱처럼 열리고, 한 번 열면 오프라인에서도 뜹니다.

## 화면

| 탭 | 내용 |
| --- | --- |
| **오피스** | 미니어처 오피스 배경 위 5개 핀(🎯 지휘실 · 🏛️ 대회의실 · 💻 작업실 · 🎁 이벤트·주식 · ☕ 라운지). 핀을 누르면 바텀시트에서 상태와 할 일을 보고 바로 추가·체크 |
| **회의실** | 오늘 날짜와 오늘의 일정·할 일 체크리스트(추가 / 완료 / 삭제) |
| **작업실** | 절미와 만든 웹앱 바로가기(스틱맨 계산기 · 마이스탁 · 세이브클립 · 링크네스트) + 새 도구 링크 추가 |
| **현황** | 4개 파트 가동 카드(진행률) + 최근 업데이트 타임라인 |
| **메모** | 빠른 메모 작성 · 고정(📌) · 삭제 |

상단 칩: **🌙 야간 / ☀️ 주간**(야간 모드), **✨ 모션 ON/OFF**(핀 부유·빛 효과), **🟢 4개 파트 가동**(파트 목록), **🩷 Lv.3 절미**(레벨 안내).

모든 변경은 `localStorage`(`jeolmi-office.v1`)에 저장돼 새로고침·재실행해도 남습니다.

### 야간 모드

오피스 탭 상단 칩의 **🌙 야간**을 누르면 화면이 어두운 웜 차콜·다크 브라운 톤으로 바뀌고, 오피스 배경도 창밖이 밤이고 스탠드·벽등만 켜진 `office-bg-night.jpg`로 전환됩니다. 버튼은 **☀️ 주간**으로 바뀌고, 선택은 `localStorage`의 `theme`에 저장돼 다음에 열 때도 유지됩니다(첫 화면 깜빡임을 막으려고 `index.html` 맨 앞에서 저장값을 먼저 적용). 테마에 맞춰 `<meta name="theme-color">`도 함께 바뀝니다.

화면은 이전보다 넓고 크게 잡혀 있습니다 — 좌우 여백을 16px→10px로 줄여 오피스 맵과 카드가 더 넓게 쓰고, 본문 15→16px, 배너 제목 19→21.5px, 탭 13→14.5px, 핀 라벨 11→12px, 바텀시트 할 일 13.5→15px로 한 단계씩 키웠습니다.

## 파일 구성

```
jeolmi-office/
├── index.html              화면 뼈대
├── styles.css              디자인(화이트/웜 베이지, 반응형)
├── app.js                  상태·렌더·바텀시트·localStorage 로직
├── manifest.webmanifest    PWA 매니페스트
├── sw.js                   서비스워커(오프라인 캐시)
├── assets/
│   ├── office-bg.png       아이소메트릭 오피스 원본(생성 이미지, 1254px)
│   ├── office-bg.jpg       경량 버전(1100px, 약 196KB) — 화면은 이 파일을 먼저 사용
│   ├── office-bg-night.png 야간 오피스 원본(같은 구도·캐릭터, 창밖 밤·스탠드 조명만 켜짐)
│   ├── office-bg-night.jpg 야간 경량 버전(1100px, 약 144KB) — 야간 모드 배경
│   ├── icon-192.png        앱 아이콘
│   ├── icon-512.png        앱 아이콘(설치·maskable)
│   └── icon-180.png        iOS 홈 화면 아이콘
├── scripts/
│   ├── make_icons.py       아이콘 + 경량 배경 재생성
│   ├── test_app.py         Playwright 자동 검증(390x844, 로컬)
│   ├── test_live.py        배포 주소 야간 모드·확대 검증
│   └── deploy_pages.sh     GitHub Pages(gh-pages) 배포
└── preview-*.png           화면 캡처(로컬 검증용, 저장소에는 올리지 않음)
```

## 로컬에서 열기

```bash
cd jeolmi-office
python3 -m http.server 8765
# 브라우저에서 http://127.0.0.1:8765
```

`index.html`을 파일로 직접 열어도 화면은 뜨지만, 서비스워커·매니페스트는 `http://` 또는 `https://`에서만 동작합니다.

## 검증

```bash
LD_LIBRARY_PATH=/workspace/.libs python3 scripts/test_app.py   # 로컬 (84개 항목)
LD_LIBRARY_PATH=/workspace/.libs python3 scripts/test_live.py  # 실주소 (30개 항목)
```

390x844 모바일 뷰포트에서 콘솔 에러 0건, 탭 전환, 핀 모달, 모션 토글, 체크리스트·메모·도구 추가/유지, 야간 모드(전환·배경·대비·유지·글씨 크기), 탭별 가로 스크롤 없음, 오프라인 재실행까지 84개 항목을 확인합니다. `preview-*.png`(야간 메인은 `preview-night.png`)가 다시 찍힙니다.

## 배포 (GitHub Pages)

저장소를 먼저 만든 뒤(`github.com/new`), 아래를 실행합니다.

```bash
./scripts/deploy_pages.sh                                # 기본: kimkyungse48-ui/jeolmi-office
./scripts/deploy_pages.sh git@github.com:계정/저장소.git    # 다른 저장소
DRY_RUN=1 ./scripts/deploy_pages.sh                      # 푸시 없이 결과만 확인
```

`sw.js`의 `CACHE` 이름(`jeolmi-office-v2`)과 `index.html`의 `styles.css?v=2`·`app.js?v=2`는 함께 올려야 합니다. 그래야 이미 앱을 설치한 폰에서도 예전 캐시가 아니라 새 화면이 바로 뜹니다.

`gh-pages` 브랜치에 배포본만(미리보기·스크립트 제외, `.nojekyll` 포함) 올라갑니다. 저장소 **Settings → Pages**에서 Source = *Deploy from a branch*, Branch = **gh-pages / (root)** 로 한 번만 지정하면 `https://<계정>.github.io/<저장소>/`에서 열립니다.

폰에서 그 주소를 연 뒤 브라우저 메뉴의 **홈 화면에 추가**를 누르면 앱처럼 설치됩니다.
