#!/usr/bin/env python3
"""Jeolmi Office 로컬 검증 (Playwright + Chromium, 390x844 모바일).

실행:
    LD_LIBRARY_PATH=/workspace/.libs python3 scripts/test_app.py

- 로컬 HTTP 서버를 띄우고 PWA를 띄워 콘솔 에러 0건을 확인한다.
- 탭 전환 / 핀 모달 / 모션 토글 / 체크리스트 / 메모 / 도구 추가 / localStorage 유지 검사.
- preview-office.png, preview-modal.png 스크린샷 저장.
"""
import http.server
import json
import socketserver
import subprocess
import sys
import threading
import time
from functools import partial
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PORT = 8765
BASE = f"http://127.0.0.1:{PORT}/"

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + (("  — " + detail) if detail else ""))


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve():
    handler = partial(QuietHandler, directory=str(ROOT))
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def main():
    httpd = serve()
    time.sleep(0.4)
    ok_all = True
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            ctx = browser.new_context(
                viewport={"width": 390, "height": 844},
                device_scale_factor=2,
                is_mobile=True,
                has_touch=True,
                locale="ko-KR",
                timezone_id="Asia/Seoul",
            )
            page = ctx.new_page()
            console_errors = []
            page_errors = []
            page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: page_errors.append(str(e)))

            page.goto(BASE, wait_until="networkidle")
            page.wait_for_timeout(600)

            # 1) 기본 렌더
            check("페이지 타이틀", page.title().startswith("Jeolmi Office"), page.title())
            check("헤더 타이틀", page.inner_text(".brand h1") == "Jeolmi Office")
            check("부제", "4개 파트 가동 중" in page.inner_text(".brand p"))
            check("LIVE 배지", page.inner_text(".live").strip().upper() == "LIVE")
            check("배너 문구", "대표님, 4개 파트가 대기 중이에요" in page.inner_text(".banner h2"))
            check("탭 5개", page.locator(".tab").count() == 5)
            check("핀 5개", page.locator(".pin").count() == 5, ", ".join(page.locator(".pin").all_inner_texts()))
            check("배경 이미지 로드", page.evaluate("document.querySelector('.office-bg').naturalWidth") > 500)
            check(
                "경량 배경(jpg) 사용",
                "office-bg.jpg" in page.evaluate("document.querySelector('.office-bg').currentSrc"),
                page.evaluate("document.querySelector('.office-bg').currentSrc"),
            )
            check(
                "가로 스크롤 없음",
                page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"),
                f"scrollWidth={page.evaluate('document.documentElement.scrollWidth')}",
            )

            # 핀이 배경 안에 있는지
            stage = page.locator(".stage-inner").bounding_box()
            inside = True
            for i in range(5):
                bb = page.locator(".pin").nth(i).bounding_box()
                if bb["x"] < stage["x"] - 2 or bb["x"] + bb["width"] > stage["x"] + stage["width"] + 2:
                    inside = False
                    print("   핀 넘침:", page.locator(".pin").nth(i).inner_text(), bb, stage)
            check("핀이 오피스 배경 안에 들어옴", inside)

            page.screenshot(path=str(ROOT / "preview-office.png"), full_page=True)

            # 2) 모션 토글
            page.click("#motionChip")
            page.wait_for_timeout(250)
            check("모션 OFF 클래스", page.evaluate("document.body.classList.contains('motion-off')"))
            check("모션 OFF 라벨", "모션 OFF" in page.inner_text("#motionChip"))
            anim = page.evaluate("getComputedStyle(document.querySelector('.pin')).animationName")
            check("모션 OFF 애니메이션 정지", anim == "none", anim)
            page.screenshot(path=str(ROOT / "preview-motion-off.png"), full_page=True)
            page.click("#motionChip")
            page.wait_for_timeout(250)
            check("모션 ON 복귀", page.evaluate("!document.body.classList.contains('motion-off')"))
            check(
                "모션 ON 애니메이션",
                page.evaluate("getComputedStyle(document.querySelector('.pin')).animationName") == "floaty",
            )

            # 3) 핀 → 바텀시트, 항목 추가/체크
            page.locator('.pin[data-room="hq"]').click(force=True)  # 핀이 계속 부유해서 force
            page.wait_for_timeout(450)
            check("핀 클릭 시 시트 열림", page.is_visible("#sheetWrap"))
            check("시트 제목", page.inner_text("#sheetTitle"), page.inner_text("#sheetTitle"))
            before = page.locator("#sheetTaskList .task").count()
            page.fill("#sheetAddInput", "테스트로 추가한 할 일")
            page.click("#sheetAddForm .add-btn")
            page.wait_for_timeout(250)
            after = page.locator("#sheetTaskList .task").count()
            check("시트에서 할 일 추가", after == before + 1, f"{before} → {after}")
            page.click("#sheetTaskList .task:nth-child(1) .box")
            page.wait_for_timeout(250)
            check(
                "시트에서 체크 토글",
                page.locator("#sheetTaskList .task:nth-child(1)").get_attribute("class").find("is-done") >= 0,
            )
            page.screenshot(path=str(ROOT / "preview-modal.png"))
            page.click("#sheetWrap .icon-btn")
            page.wait_for_timeout(300)
            check("시트 닫힘", page.is_hidden("#sheetWrap"))

            # 4) 탭 전환
            for tab, panel in [
                ("meeting", "#panel-meeting"),
                ("studio", "#panel-studio"),
                ("status", "#panel-status"),
                ("memo", "#panel-memo"),
                ("office", "#panel-office"),
            ]:
                page.click(f'.tab[data-tab="{tab}"]')
                page.wait_for_timeout(220)
                check(f"탭 전환: {tab}", page.is_visible(panel))
            # 5) 회의실 체크리스트
            page.click('.tab[data-tab="meeting"]')
            page.wait_for_timeout(250)
            m_before = page.locator("#meetList .task").count()
            page.fill("#meetInput", "회의실 테스트 항목")
            page.click("#meetForm .add-btn")
            page.wait_for_timeout(250)
            check("회의실 항목 추가", page.locator("#meetList .task").count() == m_before + 1)
            page.click("#meetList .task:last-child .box")
            page.wait_for_timeout(250)
            check("회의실 완료 토글", page.locator("#meetList .task:last-child").get_attribute("class").find("is-done") >= 0)
            page.screenshot(path=str(ROOT / "preview-meeting.png"), full_page=True)

            # 6) 작업실 도구 추가
            page.click('.tab[data-tab="studio"]')
            page.wait_for_timeout(250)
            t_before = page.locator(".tool").count()
            page.fill("#toolEmoji", "🧪")
            page.fill("#toolName", "테스트 도구")
            page.fill("#toolUrl", "example.com/tool")
            page.click("#toolForm .full-btn")
            page.wait_for_timeout(250)
            check("도구 추가", page.locator(".tool").count() == t_before + 1)
            href = page.locator(".tool-open").first.get_attribute("href")
            check("도구 URL 정규화", href == "https://example.com/tool", href)
            page.screenshot(path=str(ROOT / "preview-studio.png"), full_page=True)

            # 7) 현황
            page.click('.tab[data-tab="status"]')
            page.wait_for_timeout(250)
            check("현황 카드 4개", page.locator(".status-card").count() == 4)
            check("타임라인 항목 있음", page.locator(".timeline .tl-item").count() >= 3)
            page.screenshot(path=str(ROOT / "preview-status.png"), full_page=True)

            # 8) 메모
            page.click('.tab[data-tab="memo"]')
            page.wait_for_timeout(250)
            page.fill("#memoInput", "테스트 메모입니다")
            page.click("#memoForm .add-btn")
            page.wait_for_timeout(300)
            check("메모 저장", page.locator("#memoList .memo").count() == 1)
            page.click("#memoList .memo .memo-btn")
            page.wait_for_timeout(250)
            check("메모 고정", page.locator("#memoList .memo.is-pinned").count() == 1)
            page.screenshot(path=str(ROOT / "preview-memo.png"), full_page=True)

            # 9) 새로고침 후 유지
            page.reload(wait_until="networkidle")
            page.wait_for_timeout(700)
            page.click('.tab[data-tab="memo"]')
            page.wait_for_timeout(300)
            check("새로고침 후 메모 유지", page.locator("#memoList .memo").count() == 1)
            check(
                "새로고침 후 고정 유지",
                page.locator("#memoList .memo.is-pinned").count() == 1,
            )
            page.click('.tab[data-tab="meeting"]')
            page.wait_for_timeout(250)
            check(
                "새로고침 후 회의실 항목 유지",
                "회의실 테스트 항목" in page.inner_text("#meetList"),
            )
            page.click('.tab[data-tab="studio"]')
            page.wait_for_timeout(250)
            check("새로고침 후 도구 유지", "테스트 도구" in page.inner_text("#toolGrid"))

            # 10) 파트/레벨 모달
            page.click('.tab[data-tab="office"]')
            page.wait_for_timeout(250)
            page.click("#partsChip")
            page.wait_for_timeout(400)
            check("4개 파트 모달", "4개 파트" in page.inner_text("#sheetTitle"))
            check("파트 행 4개", page.locator(".sheet-row").count() == 4)
            page.screenshot(path=str(ROOT / "preview-parts.png"))
            page.click('.sheet-row[data-room="work"]')
            page.wait_for_timeout(400)
            check("파트 모달에서 방 이동", page.inner_text("#sheetTitle") == "작업실", page.inner_text("#sheetTitle"))
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
            check("ESC로 시트 닫힘", page.is_hidden("#sheetWrap"))
            page.click("#levelChip")
            page.wait_for_timeout(400)
            check("레벨 모달", "Lv.3" in page.inner_text("#sheetTitle"))
            page.click("#sheetWrap .icon-btn")
            page.wait_for_timeout(250)

            # 11) PWA 자산
            manifest_status = page.evaluate("fetch('manifest.webmanifest').then(r => r.status)")
            check("manifest 응답", manifest_status == 200, str(manifest_status))
            sw_ready = page.evaluate(
                "navigator.serviceWorker.ready.then(r => !!r.active).catch(() => false)"
            )
            check("서비스워커 활성화", bool(sw_ready), str(sw_ready))

            # 오프라인 수신 확인
            try:
                ctx.set_offline(True)
                page.reload(wait_until="domcontentloaded")
                page.wait_for_timeout(900)
                check(
                    "오프라인에서도 화면 열림",
                    page.is_visible(".stage") and page.locator(".pin").count() == 5,
                )
            except Exception as exc:  # noqa: BLE001
                check("오프라인에서도 화면 열림", False, str(exc)[:160])
            finally:
                ctx.set_offline(False)
                page.reload(wait_until="networkidle")
                page.wait_for_timeout(500)
            meta_theme = page.get_attribute('meta[name="theme-color"]', "content")
            check("테마 컬러", meta_theme == "#F7F3EC", str(meta_theme))

            # 12) localStorage 키
            keys = page.evaluate("Object.keys(localStorage)")
            check("localStorage 저장", "jeolmi-office.v1" in keys, str(keys))

            # 콘솔/페이지 에러
            real_errors = [e for e in console_errors if "favicon" not in e.lower()]
            check("콘솔 에러 0건", len(real_errors) == 0, json.dumps(real_errors, ensure_ascii=False))
            check("페이지 예외 0건", len(page_errors) == 0, json.dumps(page_errors, ensure_ascii=False))

            # 태블릿/데스크톱 폭 확인
            page.set_viewport_size({"width": 430, "height": 900})
            page.wait_for_timeout(300)
            check(
                "430px 반응형 가로 스크롤 없음",
                page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"),
            )
            page.set_viewport_size({"width": 1280, "height": 900})
            page.wait_for_timeout(300)
            check(
                "데스크톱 중앙 정렬",
                page.evaluate("document.querySelector('.app').getBoundingClientRect().width <= 460"),
            )

            browser.close()
    finally:
        httpd.shutdown()

    failed = [r for r in results if not r[1]]
    print("\n=== 결과: %d/%d 통과 ===" % (len(results) - len(failed), len(results)))
    for name, ok, detail in failed:
        print("FAILED:", name, detail)
    ok_all = not failed
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
