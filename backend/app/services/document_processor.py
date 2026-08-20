"""多格式文档处理器：清洗 + 按章节切分。

设计原则：
- PDF 优先按 outline（书签目录）切，无 outline 退化到段落
- DOCX 按 Heading 1/2/3 切
- Markdown 按 # / ## / ### 切
- TXT 无章节信息，退化到段落
- 扫描版 PDF（PyMuPDF 读不到文本层）直接拒绝入库
- 切块目标 200-800 字，短一点更适合语义检索
- 章节信息内嵌到 chunk_text 前缀里：`【《书名》/ 第3章 / 第2节】实际内容`
  这样检索天然带出处，不需要数据库 schema 变更
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from typing import Protocol

from loguru import logger


@dataclass
class Section:
    """文档章节单元：章节路径 + 该段文本。"""
    chapter: str = ""        # 第3章 / 一、概述
    section: str = ""        # 第2节 / 1.1 定义
    text: str = ""


@dataclass
class ProcessResult:
    """文档处理结果：清洗后的章节列表 + 拒绝原因（如有）。"""
    sections: list[Section] = field(default_factory=list)
    rejected: str | None = None  # 非 None 表示拒绝入库（如扫描版 PDF）


# ── 清洗规则（所有格式共用） ────────────────────────────────────────

_REPEATED_SHORT_LINE = re.compile(r"^(.{1,40})$")
_PAGE_NUM_LINE = re.compile(r"^\s*\d+\s*$")
_MULTI_BLANK = re.compile(r"\n{3,}")


def _clean_text(text: str) -> str:
    """清洗文本：去 NULL、去纯数字行（页码）、压缩连续空白。"""
    if not text:
        return ""
    # 去 NULL 字节（PostgreSQL 编码安全）
    text = text.replace("\x00", "")
    # 标准化空白
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # 去纯数字行（页码、行号）
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if _PAGE_NUM_LINE.match(stripped):
            continue
        lines.append(line)
    text = "\n".join(lines)
    # 压缩 3+ 连续换行为 2 个
    text = _MULTI_BLANK.sub("\n\n", text)
    return text.strip()


# ── 切分：章节 → chunk ─────────────────────────────────────────────

_TARGET_CHUNK_MIN = 200
_TARGET_CHUNK_MAX = 800
_PARA_SPLIT = re.compile(r"\n\s*\n")


def _split_section_to_chunks(section_text: str) -> list[str]:
    """章节内文本切分为 chunk：先按段落，过长再按句号。"""
    if not section_text.strip():
        return []
    paragraphs = [p.strip() for p in _PARA_SPLIT.split(section_text) if p.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        # 单段过长：按句号兜底切
        if len(para) > _TARGET_CHUNK_MAX:
            if current:
                chunks.append(current)
                current = ""
            for sub in _split_by_sentence(para, _TARGET_CHUNK_MAX):
                chunks.append(sub)
            continue

        # 累加段落，达到目标长度就封 chunk
        if current and len(current) + len(para) + 1 > _TARGET_CHUNK_MAX:
            chunks.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para

    if current.strip():
        chunks.append(current)
    return chunks


def _split_by_sentence(text: str, max_len: int) -> list[str]:
    """按句号/换行兜底切分超长段落。"""
    if len(text) <= max_len:
        return [text]
    chunks = []
    buf = ""
    for line in text.split("\n"):
        if len(buf) + len(line) > max_len and buf:
            chunks.append(buf.strip())
            buf = ""
        # 行内再按句号兜底
        parts = re.split(r"(?<=[。！？!?])", line)
        for p in parts:
            if len(buf) + len(p) > max_len and buf:
                chunks.append(buf.strip())
                buf = p
            else:
                buf += p
        buf += "\n"
    if buf.strip():
        chunks.append(buf.strip())
    return chunks


def sections_to_chunks(
    sections: list[Section], book_title: str
) -> list[str]:
    """把章节列表转成带出处前缀的 chunk 列表。

    chunk 格式：`【《书名》/ 章节 / 小节】实际内容`
    """
    chunks: list[str] = []
    for sec in sections:
        if not sec.text.strip():
            continue
        # 拼出处前缀
        prefix_parts = [f"《{book_title}》"] if book_title else []
        if sec.chapter:
            prefix_parts.append(sec.chapter)
        if sec.section:
            prefix_parts.append(sec.section)
        prefix = " / ".join(prefix_parts) if prefix_parts else ""

        for chunk in _split_section_to_chunks(sec.text):
            if not chunk.strip():
                continue
            if prefix:
                chunks.append(f"【{prefix}】{chunk}")
            else:
                chunks.append(chunk)
    return chunks


# ── 处理器接口 + 各格式实现 ───────────────────────────────────────

class DocumentProcessor(Protocol):
    def process(self, content: bytes, title: str) -> ProcessResult:
        ...


class PDFProcessor:
    """PDF 处理器：PyMuPDF 读 outline 优先，无 outline 退化到段落。"""

    def process(self, content: bytes, title: str) -> ProcessResult:
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.warning("PyMuPDF not installed, falling back to PyPDF2")
            return self._fallback_pypdf2(content, title)

        try:
            doc = fitz.open(stream=content, filetype="pdf")
        except Exception as e:
            logger.error(f"PDF 打开失败: {e}")
            return ProcessResult(rejected=f"PDF 解析失败: {e}")

        # 检测扫描版：提取前 3 页文本，全是空或极少 → 判定扫描件
        sample_text = ""
        for i in range(min(3, len(doc))):
            sample_text += doc[i].get_text("text") or ""
        if len(sample_text.strip()) < 50:
            return ProcessResult(
                rejected="扫描版 PDF 不支持，请提供电子版（含文本层）的 PDF"
            )

        # 尝试读 outline（书签目录）
        toc = doc.get_toc()  # [[level, title, page], ...]
        if toc:
            sections = self._extract_by_toc(doc, toc)
        else:
            sections = self._extract_by_paragraph(doc)

        # 合并清洗
        cleaned_sections = [
            Section(chapter=s.chapter, section=s.section, text=_clean_text(s.text))
            for s in sections
            if s.text.strip()
        ]
        return ProcessResult(sections=cleaned_sections)

    def _extract_by_toc(self, doc, toc: list) -> list[Section]:
        """按 TOC 切分：每个 level 1 是章节，level 2 是小节。"""
        sections: list[Section] = []
        # [(level, title, page_start, page_end), ...]
        toc_entries = []
        for i, (lvl, ttl, pg) in enumerate(toc):
            next_pg = toc[i + 1][2] if i + 1 < len(toc) else len(doc) + 1
            toc_entries.append((lvl, ttl.strip(), pg - 1, next_pg - 1))  # 转 0-indexed

        current_chapter = ""
        for lvl, ttl, pg_start, pg_end in toc_entries:
            page_end = min(pg_end, len(doc))
            page_start = max(0, pg_start)
            if page_start >= len(doc):
                continue
            text = ""
            for p in range(page_start, page_end):
                text += doc[p].get_text("text") or ""
            if not text.strip():
                continue
            if lvl == 1:
                current_chapter = ttl
                sections.append(Section(chapter=ttl, section="", text=text))
            elif lvl == 2:
                sections.append(Section(chapter=current_chapter, section=ttl, text=text))
            else:
                # level 3+ 当作 section 子内容，归入上一节
                if sections:
                    sections[-1].text += "\n" + text
                else:
                    sections.append(Section(chapter="", section=ttl, text=text))
        return sections

    def _extract_by_paragraph(self, doc) -> list[Section]:
        """无 TOC：整篇按段落（双换行）聚合，无章节信息。"""
        full_text = ""
        for page in doc:
            full_text += page.get_text("text") or ""
        return [Section(chapter="", section="", text=full_text)]

    def _fallback_pypdf2(self, content: bytes, title: str) -> ProcessResult:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(content))
            text = "\n".join([page.extract_text() or "" for page in reader.pages])
            if len(text.strip()) < 50:
                return ProcessResult(rejected="扫描版 PDF 不支持，请提供电子版 PDF")
            cleaned = _clean_text(text)
            return ProcessResult(sections=[Section(text=cleaned)])
        except Exception as e:
            return ProcessResult(rejected=f"PDF 解析失败: {e}")


class DocxProcessor:
    """DOCX 处理器：按 Heading 1/2/3 切章节。"""

    HEADING_STYLES = {"HEADING 1", "HEADING 2", "HEADING 3"}

    def process(self, content: bytes, title: str) -> ProcessResult:
        try:
            from docx import Document
        except ImportError:
            return ProcessResult(rejected="python-docx 未安装，无法解析 DOCX")

        try:
            doc = Document(io.BytesIO(content))
        except Exception as e:
            return ProcessResult(rejected=f"DOCX 解析失败: {e}")

        sections: list[Section] = []
        current_chapter = ""
        current_section = ""
        buf: list[str] = []

        def flush():
            if buf:
                text = "\n".join(buf)
                if text.strip():
                    sections.append(
                        Section(chapter=current_chapter, section=current_section, text=text)
                    )
                buf.clear()

        for para in doc.paragraphs:
            style_name = (para.style.name or "").upper() if para.style else ""
            text = para.text or ""
            if not text.strip():
                continue
            if style_name in self.HEADING_STYLES:
                flush()
                if "1" in style_name:
                    current_chapter = text.strip()
                    current_section = ""
                elif "2" in style_name:
                    current_section = text.strip()
                else:  # heading 3
                    # 当作 section 子标题，归入当前 section
                    buf.append(f"### {text.strip()}")
                continue
            buf.append(text)

        # 表格内容
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(
                    cell.text.strip() for cell in row.cells if cell.text.strip()
                )
                if row_text.strip():
                    buf.append(row_text)

        flush()

        cleaned = [
            Section(chapter=s.chapter, section=s.section, text=_clean_text(s.text))
            for s in sections
            if s.text.strip()
        ]
        return ProcessResult(sections=cleaned)


class MarkdownProcessor:
    """Markdown 处理器：按 # / ## / ### 切章节。代码块不切分。"""

    def process(self, content: bytes, title: str) -> ProcessResult:
        text = content.decode("utf-8", errors="ignore")
        if not text.strip():
            return ProcessResult(rejected="Markdown 内容为空")

        lines = text.split("\n")
        sections: list[Section] = []
        current_chapter = ""
        current_section = ""
        buf: list[str] = []
        in_code_block = False

        def flush():
            if buf:
                t = "\n".join(buf)
                if t.strip():
                    sections.append(
                        Section(chapter=current_chapter, section=current_section, text=t)
                    )
                buf.clear()

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                buf.append(line)
                continue
            if not in_code_block and stripped.startswith("#"):
                flush()
                hashes = len(stripped) - len(stripped.lstrip("#"))
                ttl = stripped.lstrip("#").strip()
                if hashes == 1:
                    current_chapter = ttl
                    current_section = ""
                elif hashes == 2:
                    current_section = ttl
                else:
                    buf.append(f"### {ttl}")
                continue
            buf.append(line)

        flush()

        cleaned = [
            Section(chapter=s.chapter, section=s.section, text=_clean_text(s.text))
            for s in sections
            if s.text.strip()
        ]
        return ProcessResult(sections=cleaned)


class TxtProcessor:
    """TXT 处理器：无章节信息，整篇按段落聚合。"""

    def process(self, content: bytes, title: str) -> ProcessResult:
        text = content.decode("utf-8", errors="ignore")
        cleaned = _clean_text(text)
        if not cleaned.strip():
            return ProcessResult(rejected="TXT 内容为空")
        return ProcessResult(sections=[Section(text=cleaned)])


# ── 入口：根据文件类型选处理器 ───────────────────────────────────

_PROCESSORS: dict[str, DocumentProcessor] = {
    "pdf": PDFProcessor(),
    "docx": DocxProcessor(),
    "doc": DocxProcessor(),
    "md": MarkdownProcessor(),
    "markdown": MarkdownProcessor(),
    "txt": TxtProcessor(),
}


def process_document(
    content: bytes, file_type: str, title: str
) -> ProcessResult:
    """根据文件类型选处理器，返回 ProcessResult。

    file_type 不在支持列表 → 返回 rejected。
    """
    ft = (file_type or "").lower().lstrip(".")
    proc = _PROCESSORS.get(ft)
    if proc is None:
        return ProcessResult(
            rejected=f"不支持的文件类型: {file_type}（支持 pdf/docx/md/txt）"
        )
    return proc.process(content, title)
