"""
PDF → Markdown 转换脚本
针对建筑规范 PDF 优化：保留章节层级、条文编号、表格结构
"""
import fitz  # pymupdf
import re
import sys
import os
from pathlib import Path


def extract_tables_from_page(page):
    """提取页面中的表格，返回 (表格文本列表, 占用区域的bbox列表)"""
    tables = []
    table_bboxes = []
    try:
        tabs = page.find_tables()
        for tab in tabs:
            if tab.row_count > 0 and tab.col_count > 0:
                rows = tab.extract()
                if rows and any(any(c for c in row) for row in rows):
                    # 构建 markdown 表格
                    md_rows = []
                    for i, row in enumerate(rows):
                        cells = [str(c).strip().replace('\n', ' ') if c else '' for c in row]
                        md_rows.append(cells)
                    if md_rows:
                        header = md_rows[0]
                        body = md_rows[1:] if len(md_rows) > 1 else []
                        md_table = '| ' + ' | '.join(header) + ' |'
                        md_table += '\n|' + '|'.join(['---'] * len(header)) + '|'
                        for row in body:
                            # 补齐列数
                            while len(row) < len(header):
                                row.append('')
                            md_table += '\n| ' + ' | '.join(row) + ' |'
                        tables.append(md_table)
                        table_bboxes.append(tab.bbox)
    except Exception:
        pass
    return tables, table_bboxes


def is_in_bbox(point, bbox):
    """检查点是否在 bbox 内"""
    if not bbox:
        return False
    x, y = point
    x0, y0, x1, y1 = bbox
    return x0 <= x <= x1 and y0 <= y <= y1


def get_heading_level(text, font_size, bold):
    """根据文本内容和字体大小判断标题层级"""
    text = text.strip()
    if not text:
        return 0

    # 匹配 "第X章" 或 "X 章"
    if re.match(r'^第[一二三四五六七八九十百\d]+[章节]', text):
        return 1

    # 匹配 "1 基本规定" 或 "2.1 术语" 等顶级节标题
    if re.match(r'^\d+\s+\S', text) and font_size > 14:
        return 2

    # 匹配 "3.1 术语" 形式
    if re.match(r'^\d+\.\d+\s+\S', text):
        return 3

    # 匹配 "3.1.1" 条文编号
    if re.match(r'^\d+\.\d+\.\d+', text):
        return 4

    # 匹配 "3.1.1.1" 更深层级
    if re.match(r'^\d+\.\d+\.\d+\.\d+', text):
        return 5

    return 0


def convert_pdf_to_markdown(pdf_path, output_path=None):
    """将 PDF 转换为 Markdown"""
    pdf_path = Path(pdf_path)
    doc = fitz.open(str(pdf_path))

    if output_path is None:
        output_path = pdf_path.with_suffix('.md')
    else:
        output_path = Path(output_path)

    md_lines = []
    # 提取文档基本信息
    md_lines.append(f"# {pdf_path.stem}")
    md_lines.append("")
    md_lines.append(f"> 源文件: {pdf_path.name}")
    md_lines.append(f"> 总页数: {len(doc)}")
    md_lines.append("")

    # 收集所有页面的字体大小信息，用于判断基准字号
    all_font_sizes = []
    for page in doc:
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span.get("text", "").strip()
                        if text and len(text) > 1:
                            all_font_sizes.append(span["size"])

    # 计算基准字号（众数）
    if all_font_sizes:
        from collections import Counter
        size_counter = Counter(round(s, 1) for s in all_font_sizes)
        base_size = size_counter.most_common(1)[0][0]
    else:
        base_size = 10.0

    for page_num, page in enumerate(doc):
        # 跳过封面页（前2页通常是封面/扉页）
        if page_num < 1:
            # 提取封面标题
            text = page.get_text()
            if text.strip():
                md_lines.append(f"<!-- 封面页 (第{page_num+1}页) -->")
                for line in text.strip().split('\n'):
                    if line.strip():
                        md_lines.append(line.strip())
                md_lines.append("")
            continue

        # 提取表格
        tables, table_bboxes = extract_tables_from_page(page)

        # 提取文本块
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

        page_text_added = False

        for block in blocks:
            if "lines" not in block:
                continue

            block_text = ""
            block_size = 0
            block_flags = 0
            block_y = block["bbox"][1]

            # 检查是否在表格区域内
            in_table = False
            for bbox in table_bboxes:
                if is_in_bbox((block["bbox"][0], block["bbox"][1]), bbox) or \
                   is_in_bbox((block["bbox"][2], block["bbox"][3]), bbox):
                    in_table = True
                    break

            if in_table:
                continue  # 表格内容单独处理

            for line in block["lines"]:
                line_text = ""
                for span in line["spans"]:
                    text = span.get("text", "")
                    line_text += text
                    block_size = span.get("size", block_size)
                    block_flags = span.get("flags", block_flags)

                line_text = line_text.strip()
                if not line_text:
                    continue

                block_text += line_text + "\n"

            block_text = block_text.strip()
            if not block_text:
                continue

            # 判断标题层级
            is_bold = bool(block_flags & 2**4)  # bold flag
            heading_level = get_heading_level(block_text, block_size, is_bold)

            # 根据字号判断是否为标题（大于基准字号 1.3 倍以上）
            if heading_level == 0 and block_size > base_size * 1.3 and len(block_text) < 50:
                heading_level = 2

            if heading_level > 0:
                prefix = "#" * min(heading_level + 1, 6)  # 最多 ######
                md_lines.append("")
                md_lines.append(f"{prefix} {block_text}")
                md_lines.append("")
            elif re.match(r'^\d+\.\d+\.\d+', block_text):
                # 条文正文
                md_lines.append(block_text)
            else:
                md_lines.append(block_text)

            page_text_added = True

        # 添加表格
        for table in tables:
            md_lines.append("")
            md_lines.append(table)
            md_lines.append("")

        # 页面分隔（注释形式）
        md_lines.append("")
        md_lines.append(f"<!-- --- 第 {page_num+1} 页 --- -->")
        md_lines.append("")

    doc.close()

    # 写入文件
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    return output_path


def main():
    if len(sys.argv) < 2:
        print("用法: python pdf2md.py <pdf路径> [输出路径]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(pdf_path):
        print(f"文件不存在: {pdf_path}")
        sys.exit(1)

    print(f"开始转换: {pdf_path}")
    result = convert_pdf_to_markdown(pdf_path, output_path)

    # 统计
    pdf_size = os.path.getsize(pdf_path)
    md_size = os.path.getsize(result)

    print(f"转换完成!")
    print(f"  PDF 大小: {pdf_size/1024/1024:.1f} MB")
    print(f"  MD 大小:  {md_size/1024:.1f} KB")
    print(f"  压缩比:   {pdf_size/max(md_size,1):.0f}x")
    print(f"  输出路径: {result}")


if __name__ == "__main__":
    main()
