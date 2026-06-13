"""
MediBot Document Parser — Uses Docling for structure-aware PDF/MD parsing.
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Disable HuggingFace symlinks on Windows (fixes permission issues)
os.environ['HF_HUB_DISABLE_SYMLINK_WARNING'] = '1'
os.environ['HF_HUB_SYMLINK_MODE'] = 'hardlink'  # Use hardlinks instead of symlinks on Windows


def parse_document(file_path: str):
    """
    Parse a PDF or Markdown document using Docling's DocumentConverter.
    Returns a DoclingDocument with hierarchical structure preserved.

    Falls back to PyMuPDF if Docling is unavailable.
    """
    file_path = Path(file_path)
    ext = file_path.suffix.lower()

    try:
        from docling.document_converter import DocumentConverter

        logger.info(f"Parsing {file_path.name} with Docling...")
        converter = DocumentConverter()
        result = converter.convert(str(file_path))
        return result.document
    except ImportError:
        logger.warning("Docling not available, using fallback parser...")
        return _fallback_parse(file_path, ext)
    except Exception as e:
        logger.error(f"Docling failed for {file_path.name}: {e}. Using fallback.")
        return _fallback_parse(file_path, ext)


def _fallback_parse(file_path: Path, ext: str):
    """
    Fallback parser using PyMuPDF for PDFs and plain text for Markdown.
    Returns a simple object with .export_to_markdown() method.
    """
    if ext == ".pdf":
        return _parse_pdf_fallback(file_path)
    elif ext in (".md", ".markdown"):
        return _parse_md_fallback(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _parse_pdf_fallback(file_path: Path):
    """Parse PDF using PyMuPDF (fitz) and return a simple document object."""
    try:
        import fitz  # PyMuPDF
        logger.info(f"Parsing {file_path.name} with PyMuPDF...")
    except ImportError:
        # If PyMuPDF is not available, try pdfplumber
        try:
            import pdfplumber
            logger.info(f"Parsing {file_path.name} with pdfplumber...")
            text = ""
            with pdfplumber.open(str(file_path)) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
                    else:
                        logger.warning(f"  Page {page_num} has no extractable text")
            return SimpleDocument(text, file_path.name)
        except ImportError:
            raise ImportError(
                "Neither PyMuPDF nor pdfplumber is installed. "
                "Install one: pip install PyMuPDF OR pip install pdfplumber"
            )

    # Use PyMuPDF
    try:
        doc = fitz.open(str(file_path))
        text = ""
        for page_num, page in enumerate(doc, 1):
            page_text = page.get_text()
            if page_text:
                text += page_text + "\n\n"
            else:
                logger.warning(f"  Page {page_num} has no extractable text")
        doc.close()
        return SimpleDocument(text, file_path.name)
    except Exception as e:
        logger.error(f"PyMuPDF parsing failed: {e}")
        raise


def _parse_md_fallback(file_path: Path):
    """Parse Markdown file as plain text."""
    text = file_path.read_text(encoding="utf-8")
    return SimpleDocument(text, file_path.name)


class SimpleDocument:
    """Simple document container for fallback parsing."""

    def __init__(self, text: str, filename: str):
        self.text = text
        self.filename = filename
        self._is_fallback = True

    def export_to_markdown(self) -> str:
        return self.text
