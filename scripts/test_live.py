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

# 디자인 규칙 검사용 JS (배경·카드 HEX / 16·12·16 수치 / 강조색 1가지 / 순수 검정 없음)
DESIGN_JS = """() => {
  const parse = (c) => {
    const n = c.replace(/[^0-9.,]/g, ',').split(',').filter(Boolean).map(Number);
    return { r: n[0], g: n[1], b: n[2], a: n.length > 3 ? n[3] : 1 };
  };
  const hex = (c) => {
    const p = parse(c);
    return '#' + [p.r, p.g, p.b].map((v) => v.toString(16).padStart(2, '0').toUpperCase()).join('');
  };
  const hsl = (p) => {
    const r = p.r / 255, g = p.g / 255, b = p.b / 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b), l = (max + min) / 2, d = max - min;
    let h = 0;
    if (d > 0) {
      if (max === r) h = 60 * (((g - b) / d) % 6);
      else if (max === g) h = 60 * ((b - r) / d + 2);
      else h = 60 * ((r - g) / d + 4);
      if (h < 0) h += 360;
    }
    const s = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1));
    return { h: Math.round(h), s, l };
  };
  const px = (v) => parseFloat(v);
  const cards = Array.from(document.querySelectorAll('.card'))
    .filter((el) => el.offsetParent !== null)
    .map((el) => hex(getComputedStyle(el).backgroundColor));
  const boxes = ['.banner', '.stage', '.tool', '.status-card', '.memo', '.memo-compose', '.list-card'];
  const spacing = boxes.map((sel) => {
    const el = document.querySelector(sel);
    if (!el) return { sel, missing: true };
    const s = getComputedStyle(el);
    return { sel, pad: [s.paddingTop, s.paddingRight, s.paddingBottom, s.paddingLeft].map(px), radius: px(s.borderTopLeftRadius) };
  });
  const gapGrid = ['.tool-grid', '.status-grid', '.memolist']
    .map((sel) => { const el = document.querySelector(sel); return el ? { sel, gap: px(getComputedStyle(el).rowGap) } : { sel, gap: null }; });
  const chromatic = [];
  const black = [];
  document.querySelectorAll('.app *, .sheet *').forEach((el) => {
    const st = getComputedStyle(el);
    if (st.display === 'none' || st.visibility === 'hidden') return;
    const rect = el.getBoundingClientRect();
    if (!rect.width && !rect.height) return;
    ['backgroundColor', 'color', 'borderTopColor'].forEach((prop) => {
      const p = parse(st[prop]);
      if (p.a < 0.05) return;
      if (p.r === 0 && p.g === 0 && p.b === 0) { black.push(String(el.className) + ':' + prop); return; }
      const c = hsl(p);
      if (c.s > 0.25 && c.l > 0.12 && c.l < 0.92) chromatic.push(c.h);
    });
  });
  return { bodyBg: hex(getComputedStyle(document.body).backgroundColor), cards: [...new Set(cards)],
           surfaces: [...new Set(Array.from(document.querySelectorAll('.tool, .status-card, .memo')).map((el) => hex(getComputedStyle(el).backgroundColor)))],
           sheetBg: hex(getComputedStyle(document.querySelector('.sheet')).backgroundColor),
           spacing, gapGrid, hues: [...new Set(chromatic)].sort((a, b) => a - b), black };
}"""


def design_checks(page, night=True):
    d = page.evaluate(DESIGN_JS)
    tag = "야간" if night else "주간"
    check(f"{tag} 배경 HEX", d["bodyBg"] == ("#0F172A" if night else "#F1F5F9"), d["bodyBg"])
    check(f"{tag} 카드 배경 HEX", d["cards"] == (["#1E293B"] if night else ["#FFFFFF"]), str(d["cards"]))
    if night:
        check("야간 서피스 #1E293B", set(d["surfaces"]) <= {"#1E293B"}, str(d["surfaces"]))
        check("야간 바텀시트 #1E293B", d["sheetBg"] == "#1E293B", d["sheetBg"])
    check("순수 검정(#000000) 없음", len(d["black"]) == 0, str(d["black"][:3]))
    pad_bad = [s for s in d["spacing"] if not s.get("missing") and any(v != 16 for v in s["pad"])]
    check("카드 여백 16px", not pad_bad, str(pad_bad))
    rad_bad = [s for s in d["spacing"] if not s.get("missing") and s["radius"] != 16]
    check("카드 라운드 16px", not rad_bad, str(rad_bad))
    check("카드 간격 12px", all(g["gap"] in (None, 12) for g in d["gapGrid"]), str(d["gapGrid"]))
    check("강조색 1가지(블루)", all(200 <= h <= 235 for h in d["hues"]), str(d["hues"]))


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
            page.get_attribute('meta[name="theme-color"]', "content") == "#0F172A",
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
        page.screenshot(path="preview-night-v3.png", full_page=True)
        page.screenshot(path="preview-live-night.png", full_page=True)

        # 디자인 규칙 3종 (배경/카드 HEX, 16·12·16, 단일 강조색)
        design_checks(page, night=True)

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
        design_checks(page, night=False)
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
