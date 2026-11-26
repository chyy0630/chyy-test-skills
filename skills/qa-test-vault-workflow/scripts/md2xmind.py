# -*- coding: utf-8 -*-
"""md2xmind.py — 将 vault 中的 测试点.md/测试用例.md 转为 XMind 导图

用法:
    python md2xmind.py <input.md> [-o output.xmind]

结构映射:
    # 一级标题        -> 中心主题
    > 引用行          -> 「口径与依据」分支
    ## / ### / ####   -> 依次下级分支（标题层级即导图层级）
    - [ ] / - 条目    -> 挂在最近标题下；缩进产生下级

输出为 XMind 2020+ 标准双格式：真实内容在 content.json，
content.xml 为官方多语言占位警告（与 XMind 自身保存行为一致），
旧版 XMind 8 打开时会看到"请用 XMind 8 Update 3+"提示而非报错。
"""
import argparse
import json
import re
import sys
import uuid
import zipfile
from pathlib import Path

# XMind 保存 Zen 格式时写入的官方占位 content.xml（多语言警告，内容固定）
_PLACEHOLDER_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
    '<xmap-content xmlns="urn:xmind:xmap:xmlns:content:2.0" '
    'xmlns:fo="http://www.w3.org/1999/XSL/Format" '
    'xmlns:svg="http://www.w3.org/2000/svg" '
    'xmlns:xhtml="http://www.w3.org/1999/xhtml" '
    'xmlns:xlink="http://www.w3.org/1999/xlink" version="2.0">'
    '<sheet id="placeholder-sheet">'
    '<topic id="placeholder-root" structure-class="org.xmind.ui.map.unbalanced">'
    "<title>Warning\n警告\nAttention\nWarnung\n경고</title>"
    "<children><topics type=\"attached\">"
    '<topic id="placeholder-1"><title>'
    "This file can not be opened normally, please do not modify and save, "
    "otherwise the contents will be permanently lost！</title>"
    "<children><topics type=\"attached\">"
    '<topic id="placeholder-2">'
    "<title>You can try using XMind 8 Update 3 or later version to open</title>"
    "</topic></topics></children></topic>"
    '<topic id="placeholder-3"><title>'
    "该文件无法正常打开，请勿修改并保存，否则文件内容将会永久性丢失！</title>"
    "<children><topics type=\"attached\">"
    '<topic id="placeholder-4">'
    "<title>你可以尝试使用 XMind 8 Update 3 或更新版本打开</title>"
    "</topic></topics></children></topic>"
    "</topics></children></topic>"
    "<title>Sheet 1</title></sheet></xmap-content>"
)


def _id() -> str:
    return uuid.uuid4().hex


def _topic(title: str, children=None) -> dict:
    t = {"id": _id(), "title": title}
    if children:
        t["children"] = {"attached": children}
    return t


class _Section:
    def __init__(self, title: str):
        self.title = title
        self.items = []   # [{title, children: [...]}]


def parse_md(md_text: str):
    """解析为 (root_title, notes, [顶层 Section 树])。

    Section 树节点即标题（## / ### / #### ...），items 为其下条目。
    """
    root_title = ""
    notes = []
    top_sections = []          # 顶层（## 级）Section 列表
    stack = []                 # [(heading_level, Section)]

    for raw in md_text.splitlines():
        line = raw.rstrip()

        m_root = re.match(r"^# (.+)$", line)
        if m_root and not stack and not top_sections:
            root_title = m_root.group(1).strip()
            continue

        if not stack and not top_sections and line.startswith("> "):
            notes.append(line[2:].strip().replace("[[需求]]", "需求.md"))
            continue

        m_h = re.match(r"^(#{2,6}) (.+)$", line)
        if m_h:
            level = len(m_h.group(1))
            sec = _Section(m_h.group(2).strip())
            while stack and stack[-1][0] >= level:
                stack.pop()
            if stack:
                stack[-1][1].items.append(sec)
            else:
                top_sections.append(sec)
            stack.append((level, sec))
            continue

        m_item = re.match(r"^(\s*)- \[ \]\s*(.+)$", line) or re.match(r"^(\s*)-\s+(.+)$", line)
        if m_item and stack:
            indent = len(m_item.group(1))
            item = {"title": m_item.group(2).strip(), "children": []}
            cur = stack[-1][1].items
            if indent == 0 or not cur or isinstance(cur[-1], _Section):
                cur.append(item)
            else:
                cur[-1]["children"].append(item)

    return root_title, notes, top_sections


def _build_items(items) -> list:
    out = []
    for it in items:
        if isinstance(it, _Section):
            out.append(_topic(it.title, _build_items(it.items) or None))
        else:
            kids = _build_items(it["children"]) if it["children"] else None
            out.append(_topic(it["title"], kids))
    return out


def build_sheet(root_title: str, notes, sections) -> dict:
    root_children = []
    if notes:
        root_children.append(_topic("口径与依据", [_topic(n) for n in notes]))
    for sec in sections:
        root_children.append(_topic(sec.title, _build_items(sec.items) or None))
    return {
        "id": _id(),
        "class": "sheet",
        "title": root_title or "测试点",
        "rootTopic": {
            "id": _id(),
            "class": "topic",
            "title": root_title or "测试点",
            "structureClass": "org.xmind.ui.map.unbalanced",
            "children": {"attached": root_children},
        },
        "topicPositioning": "fixed",
    }


def _count(items) -> int:
    n = 0
    for it in items:
        n += _count(it.items) if isinstance(it, _Section) else 1 + _count_plain(it["children"])
    return n


def _count_plain(items) -> int:
    return sum(1 + _count_plain(i["children"]) for i in items)


def write_xmind(sheet: dict, out_path: Path):
    content = json.dumps([sheet], ensure_ascii=False)
    manifest = json.dumps({"file-entries": {
        "content.json": {}, "metadata.json": {}, "content.xml": {}}})
    metadata = json.dumps({"creator": {"name": "md2xmind", "version": "2.0"}}, ensure_ascii=False)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("content.json", content)
        zf.writestr("content.xml", _PLACEHOLDER_XML)
        zf.writestr("manifest.json", manifest)
        zf.writestr("metadata.json", metadata)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output", default=None)
    args = ap.parse_args()

    src = Path(args.input)
    out = Path(args.output) if args.output else src.with_suffix(".xmind")

    root_title, notes, sections = parse_md(src.read_text(encoding="utf-8"))
    if not sections:
        sys.exit("未解析到 '## 章节'，请检查 md 格式")
    write_xmind(build_sheet(root_title, notes, sections), out)
    print(f"OK: {out}  ({len(sections)} 个一级分支, "
          f"{sum(_count(s.items) for s in sections)} 条目)")


if __name__ == "__main__":
    main()
