"""
PDF to Markdown converter optimized for Chinese building standards.
Uses pymupdf "text" mode for better reading order, with post-processing
to clean watermarks, join fragments, and detect clause structure.
"""
import fitz  # pymupdf
import re
import sys
import os
from pathlib import Path

# Watermarks to filter
WATERMARKS = [
    'www.bzfxw.com',
    '标准分享网',
    '免费下载',
    'bzfxw',
]

def is_watermark(text):
    """Check if a line is just watermark text"""
    stripped = text.strip().replace(' ', '').lower()
    for wm in WATERMARKS:
        if wm.lower().replace(' ', '') in stripped:
            return True
    return False

def clean_text(text):
    """Clean up common OCR/extraction artifacts"""
    # Fix common character confusion
    fixes = {
        '不低千': '不低于',
        '位千': '位于',
        '等千': '等于',
        '大千': '大于',
        '小千': '小于',
        '高千': '高于',
        '低千': '低于',
        '不少千': '不少于',
        '不大于千': '不大于',
    }
    for wrong, right in fixes.items():
        text = text.replace(wrong, right)
    return text

def detect_heading(line):
    """
    Detect heading level from a line.
    Returns heading level (1-5) or 0 if not a heading.
    """
    line = line.strip()
    if not line or len(line) > 100:
        return 0

    # 第X章 / 第X节
    if re.match(r'^第[一二三四五六七八九十百\d]+[章节]', line):
        return 2

    # Top-level section: "1 总则" or "2 基本规定"
    if re.match(r'^\d+\s+\S', line) and len(line) < 30:
        return 3

    # "2.0.1" style clause numbers at start of line
    if re.match(r'^\d+\.\d+\.\d+\s', line) or re.match(r'^\d+\.\d+\.\d+$', line):
        return 4

    # "2.1" section
    if re.match(r'^\d+\.\d+\s+\S', line) and len(line) < 40:
        return 4

    return 0

def is_clause_number(line):
    """Check if line starts with a clause number like 4.1.6"""
    return bool(re.match(r'^\d+\.\d+\.\d+', line.strip()))

def convert_pdf_to_markdown(pdf_path, output_path=None):
    """Convert PDF to Markdown"""
    pdf_path = Path(pdf_path)
    doc = fitz.open(str(pdf_path))

    if output_path is None:
        output_path = pdf_path.with_suffix('.md')
    else:
        output_path = Path(output_path)

    all_text_parts = []
    all_text_parts.append(f"# {pdf_path.stem}\n")
    all_text_parts.append(f"> 源文件: {pdf_path.name} | 总页数: {len(doc)}\n")

    for page_num, page in enumerate(doc):
        # Use "text" mode for better reading order
        text = page.get_text("text")

        if not text.strip():
            continue

        lines = text.split('\n')

        for line in lines:
            line = line.rstrip()

            # Skip empty lines (but preserve as paragraph breaks)
            if not line.strip():
                all_text_parts.append("")
                continue

            # Skip watermarks
            if is_watermark(line):
                continue

            # Skip page numbers (standalone numbers or "• 13 •" patterns)
            stripped = line.strip()
            if re.match(r'^[•·]?\s*\d+\s*[•·]?$', stripped):
                continue

            # Clean text
            line = clean_text(line)

            all_text_parts.append(line)

        # Page separator (as comment, won't interfere with reading)
        all_text_parts.append(f"<!-- page {page_num + 1} -->")

    doc.close()

    # Join all text
    raw_text = '\n'.join(all_text_parts)

    # Post-processing: merge fragmented lines
    # Join lines that are part of the same paragraph (no clause number, no heading)
    processed_lines = []
    prev_was_heading = False
    prev_was_clause = False
    current_para = []

    raw_lines = raw_text.split('\n')

    for line in raw_lines:
        stripped = line.strip()

        # Skip empty
        if not stripped:
            if current_para:
                processed_lines.append(' '.join(current_para))
                current_para = []
            processed_lines.append("")
            continue

        # Skip page markers in paragraph context
        if stripped.startswith('<!-- page'):
            if current_para:
                processed_lines.append(' '.join(current_para))
                current_para = []
            processed_lines.append(stripped)
            continue

        heading_level = detect_heading(stripped)
        is_clause = is_clause_number(stripped)

        if heading_level >= 2 or is_clause:
            # Flush current paragraph
            if current_para:
                processed_lines.append(' '.join(current_para))
                current_para = []

            # Format heading
            if heading_level > 0:
                prefix = '#' * heading_level
                processed_lines.append(f"{prefix} {stripped}")
            else:
                # Clause number - treat as a paragraph start
                current_para = [stripped]
            continue

        # Regular text line
        if current_para and (prev_was_heading or prev_was_clause):
            # Continue the paragraph
            current_para.append(stripped)
        elif current_para:
            # Check if this looks like a continuation (starts lowercase, no punctuation end)
            current_para.append(stripped)
        else:
            current_para = [stripped]

    # Flush remaining
    if current_para:
        processed_lines.append(' '.join(current_para))

    # Final cleanup: remove excessive blank lines
    result_lines = []
    blank_count = 0
    for line in processed_lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 2:
                result_lines.append(line)
        else:
            blank_count = 0
            result_lines.append(line)

    final_text = '\n'.join(result_lines)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_text)

    return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python pdf2md_v2.py <pdf_path> [output_path]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    print(f"Converting: {pdf_path}")
    result = convert_pdf_to_markdown(pdf_path, output_path)

    pdf_size = os.path.getsize(pdf_path)
    md_size = os.path.getsize(result)

    print(f"Done!")
    print(f"  PDF: {pdf_size/1024/1024:.1f} MB")
    print(f"  MD:  {md_size/1024:.1f} KB")
    print(f"  Ratio: {pdf_size/max(md_size,1):.0f}x")
    print(f"  Output: {result}")


if __name__ == "__main__":
    main()
