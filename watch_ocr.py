#!/usr/bin/env python3
"""Watch a folder for screenshots saved by UI-TARS and OCR new files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

from ocr_screenshots import (
    IMAGE_EXTENSIONS,
    endpoint_url,
    merge_pages,
    natural_key,
    recognize_image,
)


def load_config(path: Path) -> tuple[str, str, str, str]:
    config = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    api_mode = os.getenv("PADDLEOCR_API_MODE") or config.get("api_mode", "official-api")
    base_url = os.getenv("PADDLEOCR_BASE_URL") or config.get("base_url", "")
    model = os.getenv("PADDLEOCR_MODEL") or config.get("model", "PaddleOCR-VL")
    token = (
        os.getenv("PADDLEOCR_ACCESS_TOKEN")
        or os.getenv("PADDLEOCR_API_KEY")
        or config.get("access_token")
        or config.get("api_key")
        or config.get("accessToken")
        or ""
    )
    token = str(token).strip()
    if not base_url:
        base_url = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
    if api_mode == "official-api" and not token:
        raise RuntimeError(
            f"官方在线 API 需要 Access Token。请填写 {path} 的 access_token，"
            "或设置环境变量 PADDLEOCR_ACCESS_TOKEN。"
        )
    return endpoint_url(base_url, api_mode), api_mode, model, token


def write_output(path: Path, pages: list[str]) -> None:
    merged = merge_pages(pages)
    content = f"# 截图 OCR 汇总\n\n图片数：{len(pages)}\n\n{merged}\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="监控 UI-TARS 保存截图的文件夹，自动 OCR 并合并去重。"
    )
    parser.add_argument("folder", type=Path, help="UI-TARS 保存截图的文件夹")
    parser.add_argument("--output", type=Path, help="汇总 Markdown 文件路径")
    parser.add_argument("--interval", type=float, default=2.0, help="扫描间隔秒数，默认 2")
    parser.add_argument("--once", action="store_true", help="只处理当前已有图片，然后退出")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("ocr_config.json"),
        help="API 配置文件路径",
    )
    args = parser.parse_args()

    args.folder.mkdir(parents=True, exist_ok=True)
    output = args.output or args.folder / "截图 OCR 汇总.md"
    try:
        url, api_mode, model, token = load_config(args.config)
    except (OSError, json.JSONDecodeError, RuntimeError) as error:
        print(f"配置错误：{error}")
        return 1

    print(f"正在监控：{args.folder.resolve()}")
    print(f"OCR 结果：{output.resolve()}")
    print(f"OCR 接口：{url}")
    print(f"OCR 模型：{model}")
    print("请让 UI-TARS 把截图保存到这个文件夹；按 Ctrl+C 停止。")

    processed: set[str] = set()
    pages: list[str] = []
    while True:
        images = sorted(
            (p for p in args.folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS),
            key=natural_key,
        )
        for image in images:
            try:
                digest = hashlib.sha256(image.read_bytes()).hexdigest()
                key = f"{image.name}:{digest}"
            except OSError:
                continue
            if key in processed:
                continue
            # UI-TARS may still be writing the file when it first appears.
            try:
                size = image.stat().st_size
                time.sleep(0.2)
                if image.stat().st_size != size:
                    continue
            except OSError:
                continue

            print(f"正在识别：{image.name}")
            try:
                text = recognize_image(image, url, api_mode, model, token).strip()
                processed.add(key)
                if text:
                    pages.append(text)
                    write_output(output, pages)
                    print(f"已更新：{output}")
                else:
                    print("  未识别到文字")
            except Exception as error:  # keep watching after one failed image
                print(f"  识别失败：{error}")

        if args.once:
            return 0
        try:
            time.sleep(max(args.interval, 0.2))
        except KeyboardInterrupt:
            print("已停止监控。")
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
