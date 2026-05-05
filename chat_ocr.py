"""
恋爱军师 - 聊天截图OCR文字提取脚本
支持将微信/QQ等聊天截图转换为可读文本
"""

import sys
import os
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "cases" / "ocr_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def ocr_image(image_path, output_path=None, lang=None):
    """
    Extract text from chat screenshot using EasyOCR.
    Returns the extracted text string.
    """
    try:
        import easyocr
    except ImportError:
        print("[ERROR] 需要安装 easyocr: pip install easyocr")
        print("[INFO] EasyOCR 对中文聊天截图识别效果最好，首次运行会自动下载模型（约100MB）")
        return None

    if not os.path.exists(image_path):
        print(f"[ERROR] 文件不存在: {image_path}")
        return None

    langs = lang or ['ch_sim', 'en']
    reader = easyocr.Reader(langs, gpu=False)
    results = reader.readtext(image_path)

    # Sort by vertical position (top to bottom), then horizontal (left to right)
    # This preserves chat message order
    results.sort(key=lambda r: (r[0][0][1], r[0][0][0]))

    lines = []
    for (bbox, text, confidence) in results:
        if text.strip():
            y_center = (bbox[0][1] + bbox[2][1]) / 2
            lines.append((y_center, text.strip()))

    # Group nearby lines into messages (within ~30px vertically)
    if not lines:
        print("[WARN] 未识别到任何文字，请检查图片是否清晰")
        return ""

    messages = []
    current_msg = [lines[0][1]]
    for i in range(1, len(lines)):
        if abs(lines[i][0] - lines[i-1][0]) < 30:
            current_msg.append(lines[i][1])
        else:
            messages.append(" ".join(current_msg))
            current_msg = [lines[i][1]]
    messages.append(" ".join(current_msg))

    text_output = "\n".join(messages)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text_output)
        print(f"[OK] 文字已保存到: {output_path}")

    return text_output


def ocr_directory(input_dir, output_dir=None, lang=None):
    """Batch process all images in a directory."""
    import glob

    img_extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.webp']
    images = []
    for ext in img_extensions:
        images.extend(glob.glob(os.path.join(input_dir, ext)))
        images.extend(glob.glob(os.path.join(input_dir, ext.upper())))

    if not images:
        print(f"[ERROR] 目录中没有找到图片文件: {input_dir}")
        return

    out_dir = output_dir or os.path.join(input_dir, "ocr_output")
    os.makedirs(out_dir, exist_ok=True)

    for img_path in sorted(images):
        name = os.path.splitext(os.path.basename(img_path))[0]
        out_path = os.path.join(out_dir, f"{name}.txt")
        print(f"\n[PROCESSING] {img_path}")
        ocr_image(img_path, out_path, lang)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="恋爱军师 - 聊天截图OCR文字提取",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 单张图片识别，结果打印到终端
  python chat_ocr.py --image wechat_chat.png

  # 单张图片识别，保存到指定文件
  python chat_ocr.py --image wechat_chat.png --output chat_text.txt

  # 批量处理整个文件夹的聊天截图
  python chat_ocr.py --dir ./screenshots/

  # 指定识别语言（默认中文+英文）
  python chat_ocr.py --image chat.png --lang ch_sim en ja
        """
    )
    parser.add_argument("--image", type=str, help="单张聊天截图路径")
    parser.add_argument("--dir", type=str, help="包含多张聊天截图的文件夹路径")
    parser.add_argument("--output", type=str, help="输出文本文件路径（单张模式）")
    parser.add_argument("--lang", type=str, nargs="+", default=['ch_sim', 'en'],
                        help="OCR识别语言，默认: ch_sim en")

    args = parser.parse_args()

    if args.image:
        out_path = args.output
        if not out_path:
            name = os.path.splitext(os.path.basename(args.image))[0]
            out_path = str(OUTPUT_DIR / f"{name}.txt")
        text = ocr_image(args.image, out_path, args.lang)
        if text:
            print("\n" + "="*50)
            print(text)
            print("="*50)
    elif args.dir:
        ocr_directory(args.dir, args.output, args.lang)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
