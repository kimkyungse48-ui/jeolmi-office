#!/usr/bin/env python3
"""Jeolmi Office 앱 아이콘 + 경량 배경 이미지 생성 (PIL).

- assets/icon-512.png / icon-192.png / icon-180.png : 오피스 배경에서 대표(핑크
  마스코트)가 앉은 지휘실 부분을 잘라 둥근 모서리 앱 아이콘으로 만든다.
- assets/office-bg.jpg : 원본 office-bg.png(2.4MB)를 1100px JPEG(약 196KB)로
  줄인 경량 버전. 앱 화면은 <picture>로 이 파일을 먼저 쓴다.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "office-bg.png"
OUT_512 = ROOT / "assets" / "icon-512.png"
OUT_192 = ROOT / "assets" / "icon-192.png"
OUT_180 = ROOT / "assets" / "icon-180.png"
OUT_JPG = ROOT / "assets" / "office-bg.jpg"


def main() -> None:
    src = Image.open(SRC).convert("RGB")
    w, h = src.size
    # 지휘실(핑크 마스코트 + 책상) 부분을 정사각형으로 자른다
    box_size = int(min(w, h) * 0.42)
    cx, cy = int(w * 0.53), int(h * 0.245)
    left = max(0, min(w - box_size, cx - box_size // 2))
    top = max(0, min(h - box_size, cy - box_size // 2))
    crop = src.crop((left, top, left + box_size, top + box_size))

    size = 900
    crop = crop.resize((size, size), Image.LANCZOS)
    crop = ImageEnhance.Brightness(crop).enhance(1.03)
    crop = ImageEnhance.Color(crop).enhance(1.04)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=208, fill=255)

    icon = Image.new("RGB", (size, size), (247, 239, 226))
    icon.paste(crop, (0, 0), mask)

    icon.resize((512, 512), Image.LANCZOS).save(OUT_512, "PNG", optimize=True)
    icon.resize((192, 192), Image.LANCZOS).save(OUT_192, "PNG", optimize=True)
    icon.resize((180, 180), Image.LANCZOS).save(OUT_180, "PNG", optimize=True)

    # 모바일에서 내려받는 배경은 경량 JPEG를 쓴다
    src.resize((1100, 1100), Image.LANCZOS).save(
        OUT_JPG, "JPEG", quality=86, optimize=True, progressive=True
    )
    print("saved", OUT_512, OUT_192, OUT_180, OUT_JPG)


if __name__ == "__main__":
    main()
