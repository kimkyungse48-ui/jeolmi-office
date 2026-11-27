#!/usr/bin/env python3
"""배포된 GitHub Pages 사이트 콘솔 에러 점검 (로컬 서버 없이 실주소 사용)."""
import sys
from playwright.sync_api import sync_playwright

URL = "https://kimkyungse48-ui.github.io/jeolmi-office/"

console_msgs = []
page_errors = []
failed_requests = []

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--no-sandbox"])
    ctx = browser.new_context(viewport={"width": 390, "height": 844},
                              user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                                          "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"))
    page = ctx.new_page()
    page.on("console", lambda m: console_msgs.append((m.type, m.text)))
    page.on("pageerror", lambda e: page_errors.append(str(e)))
    page.on("requestfailed", lambda r: failed_requests.append(f"{r.url} :: {r.failure}"))

    resp = page.goto(URL, wait_until="networkidle")
    print("HTTP", resp.status, resp.url)
    print("title:", page.title())

    # 서비스워커 등록·제어 대기
    page.wait_for_timeout(1500)
    sw = page.evaluate("async () => (await navigator.serviceWorker.getRegistrations()).length")
    print("SW registrations:", sw)

    print("pins:", page.locator(".pin").count(), "tabs:", page.locator(".tab").count())

    # 5개 핀 모두 눌러 시트 확인
    for room in ["hq", "meet", "work", "event", "lounge"]:
        page.locator(f'.pin[data-room="{room}"]').click(force=True)
        page.wait_for_timeout(250)
        title = page.locator("#sheetTitle").inner_text()
        visible = page.locator("#sheetWrap").is_visible()
        body_len = page.locator("#sheetBody").inner_text().__len__()
        print(f"pin {room}: sheet={visible} title={title!r} body_chars={body_len}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(150)

    # 탭 전환
    for tab in ["office", "meeting", "studio", "status", "memo"]:
        page.locator(f'.tab[data-tab="{tab}"]').click()
        page.wait_for_timeout(200)
        panel_visible = page.locator(f"#panel-{tab}").is_visible()
        active = page.locator(f'.tab[data-tab="{tab}"]').get_attribute("aria-selected")
        print(f"tab {tab}: panel_visible={panel_visible} aria-selected={active}")

    # 칩 동작
    page.locator('.tab[data-tab="office"]').click()
    page.locator("#motionChip").click(); page.wait_for_timeout(150)
    off = page.locator("#motionChip").get_attribute("aria-pressed")
    page.locator("#motionChip").click(); page.wait_for_timeout(150)
    on = page.locator("#motionChip").get_attribute("aria-pressed")
    print("motion toggle:", off, "->", on)
    page.locator("#partsChip").click(); page.wait_for_timeout(250)
    print("parts sheet:", page.locator("#sheetTitle").inner_text())
    page.keyboard.press("Escape")
    page.locator("#levelChip").click(); page.wait_for_timeout(250)
    print("level sheet:", page.locator("#sheetTitle").inner_text())
    page.keyboard.press("Escape")

    browser.close()

errs = [m for m in console_msgs if m[0] in ("error", "warning")]
print("\n--- console (all) ---")
for t, txt in console_msgs:
    print(f"[{t}] {txt[:300]}")
print("console errors:", len([m for m in console_msgs if m[0] == "error"]))
print("console warnings:", len([m for m in console_msgs if m[0] == "warning"]))
print("page errors:", len(page_errors))
for e in page_errors:
    print("  !", e[:300])
print("failed requests:", len(failed_requests))
for f in failed_requests:
    print("  !", f[:300])
sys.exit(0 if not page_errors and not failed_requests and not [m for m in console_msgs if m[0] == "error"] else 1)
