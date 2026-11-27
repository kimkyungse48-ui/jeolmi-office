#!/usr/bin/env python3
"""배포된 GitHub Pages 사이트의 야간 모드·확대 검증 (Playwright, 390x844).

실행:
    LD_LIBRARY_PATH=/workspace/.libs python3 scripts/test_live.py

- 실주소에서 야간/주간 전환, 밤 배경 이미지 로드, 탭별 가로 스크롤 없음,
  핀 클릭·탭 전환, 콘솔 에러 0건을 확인한다.
- preview-live-night.png 스크린샷 저장.
"""
import json
import sys

from playwright.sync_api import sync_playwright

URL = "https://kimkyungse48-ui.github.io/jeolmi-office/"
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + (("  — " + detail) if detail else ""))


def main():
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
        errors = []
        page_errors = []
        failed = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("requestfailed", lambda r: failed.append(f"{r.url} :: {r.failure}"))

        resp = page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(1200)
        check("HTTP 200", resp.status == 200, str(resp.status))
        check("타이틀", page.title().startswith("Jeolmi Office"), page.title())
        check("핀 5개", page.locator(".pin").count() == 5)
        check("탭 5개", page.locator(".tab").count() == 5)
        day_bg = page.evaluate("document.querySelector('#officeBg').currentSrc")
        check("주간 배경(실주소)", "office-bg.jpg" in day_bg and "night" not in day_bg, day_bg)

        # 주간 상태 기본 점검
        check(
            "주간 가로 스크롤 없음",
            page.evaluate("document.documentElement.scrollWidth <= 390"),
            f"scrollWidth={page.evaluate('document.documentElement.scrollWidth')}",
        )

        # 야간 모드
        page.click("#themeChip")
        page.wait_for_timeout(900)
        check("야간 모드 전환", page.evaluate("document.body.classList.contains('theme-night')"))
        night_bg = page.evaluate("document.querySelector('#officeBg').currentSrc")
        check("야간 배경 주소", "office-bg-night.jpg" in night_bg, night_bg)
        check(
            "야간 배경 실제 로드",
            page.evaluate("document.querySelector('#officeBg').naturalWidth") > 500,
            str(page.evaluate("document.querySelector('#officeBg').naturalWidth")),
        )
        check(
            "야간 테마 컬러",
            page.get_attribute('meta[name="theme-color"]', "content") == "#171310",
            str(page.get_attribute('meta[name="theme-color"]', "content")),
        )
        check(
            "야간 가로 스크롤 없음",
            page.evaluate("document.documentElement.scrollWidth <= 390"),
            f"scrollWidth={page.evaluate('document.documentElement.scrollWidth')}",
        )
        # 배경 이미지 자체도 200으로 받아지는지
        img_status = page.evaluate(
            "fetch('assets/office-bg-night.jpg').then(r => r.status).catch(() => 0)"
        )
        check("야간 이미지 HTTP 200", img_status == 200, str(img_status))

        page.wait_for_timeout(1500)
        page.screenshot(path="preview-live-night.png", full_page=True)

        # 핀 클릭
        page.locator('.pin[data-room="lounge"]').click(force=True)
        page.wait_for_timeout(500)
        check("핀 클릭 시트(라운지)", page.is_visible("#sheetWrap") and page.inner_text("#sheetTitle") == "라운지")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # 탭 전환 + 탭별 가로 스크롤
        for tab in ["meeting", "studio", "status", "memo", "office"]:
            page.click(f'.tab[data-tab="{tab}"]')
            page.wait_for_timeout(250)
            check(f"탭 전환: {tab}", page.is_visible(f"#panel-{tab}"))
            check(
                f"가로 스크롤 없음: {tab}",
                page.evaluate("document.documentElement.scrollWidth <= 390"),
                f"scrollWidth={page.evaluate('document.documentElement.scrollWidth')}",
            )

        # 야간 상태 저장
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(900)
        check("새로고침 후 야간 유지", page.evaluate("document.body.classList.contains('theme-night')"))
        check(
            "새로고침 후 야간 배경",
            "office-bg-night.jpg" in page.evaluate("document.querySelector('#officeBg').currentSrc"),
        )

        # 주간 복귀
        page.click("#themeChip")
        page.wait_for_timeout(700)
        check("주간 복귀", page.evaluate("!document.body.classList.contains('theme-night')"))
        check(
            "주간 배경 복귀",
            "office-bg-night" not in page.evaluate("document.querySelector('#officeBg').currentSrc"),
        )
        page.screenshot(path="preview-live-day.png", full_page=True)

        real_errors = [e for e in errors if "favicon" not in e.lower()]
        check("콘솔 에러 0건", len(real_errors) == 0, json.dumps(real_errors, ensure_ascii=False))
        check("페이지 예외 0건", len(page_errors) == 0, json.dumps(page_errors, ensure_ascii=False))
        check("실패한 요청 0건", len(failed) == 0, json.dumps(failed[:4], ensure_ascii=False))

        browser.close()

    bad = [r for r in results if not r[1]]
    print("\n=== 결과: %d/%d 통과 ===" % (len(results) - len(bad), len(results)))
    for name, _, detail in bad:
        print("FAILED:", name, detail)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
