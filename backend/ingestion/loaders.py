"""
Document loaders for all supported source types.

Each loader reads raw files from a source and returns a list of Document objects.
Supported: Markdown, HTML, PDF (via PyMuPDF), Git repo
"""

import hashlib
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Iterator

import fitz  # PyMuPDF
import structlog
from bs4 import BeautifulSoup
from git import Repo

from models.document import Document

logger = structlog.get_logger()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash(content: str) -> str:
    """MD5 hash of content — used for change detection on re-index."""
    return hashlib.md5(content.encode()).hexdigest()


def _infer_title(content: str, path: str) -> str:
    """Try to extract first heading; fall back to filename."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return Path(path).stem.replace("-", " ").replace("_", " ").title()


# ── Markdown Loader ───────────────────────────────────────────────────────────

class MarkdownLoader:
    """Loads all .md and .mdx files from a local folder (recursive)."""

    def __init__(self, path: str):
        self.path = Path(path)

    def load(self) -> Iterator[Document]:
        if not self.path.exists():
            logger.warning("markdown_loader.path_not_found", path=str(self.path))
            return

        for file in sorted(self.path.rglob("*.md")) + sorted(self.path.rglob("*.mdx")):
            try:
                content = file.read_text(encoding="utf-8", errors="replace").strip()
                if not content:
                    continue

                yield Document(
                    source_type="markdown",
                    title=_infer_title(content, str(file)),
                    content=content,
                    path_or_url=str(file),
                    content_hash=_hash(content),
                    metadata={
                        "filename": file.name,
                        "relative_path": str(file.relative_to(self.path)),
                    },
                )
                logger.info("markdown_loader.loaded", file=str(file))
            except Exception as e:
                logger.error("markdown_loader.error", file=str(file), error=str(e))


# ── HTML Loader ───────────────────────────────────────────────────────────────

class HTMLLoader:
    """Loads all .html files from a local folder, strips tags to plain text."""

    def __init__(self, path: str):
        self.path = Path(path)

    def load(self) -> Iterator[Document]:
        if not self.path.exists():
            logger.warning("html_loader.path_not_found", path=str(self.path))
            return

        for file in sorted(self.path.rglob("*.html")):
            try:
                raw_html = file.read_text(encoding="utf-8", errors="replace")
                soup = BeautifulSoup(raw_html, "html.parser")

                # Extract page title
                title_tag = soup.find("h1") or soup.find("title")
                title = title_tag.get_text(strip=True) if title_tag else file.stem

                # Strip nav/header/footer boilerplate
                for tag in soup(["nav", "header", "footer", "script", "style"]):
                    tag.decompose()

                content = soup.get_text(separator="\n", strip=True)
                # Collapse excessive blank lines
                content = re.sub(r"\n{3,}", "\n\n", content).strip()

                if not content:
                    continue

                yield Document(
                    source_type="html",
                    title=title,
                    content=content,
                    path_or_url=str(file),
                    content_hash=_hash(content),
                    metadata={
                        "filename": file.name,
                        "relative_path": str(file.relative_to(self.path)),
                    },
                )
                logger.info("html_loader.loaded", file=str(file))
            except Exception as e:
                logger.error("html_loader.error", file=str(file), error=str(e))


# ── PDF Loader ────────────────────────────────────────────────────────────────

class PDFLoader:
    """Loads all .pdf files from a local folder using PyMuPDF (fitz)."""

    def __init__(self, path: str):
        self.path = Path(path)

    def load(self) -> Iterator[Document]:
        if not self.path.exists():
            logger.warning("pdf_loader.path_not_found", path=str(self.path))
            return

        for file in sorted(self.path.rglob("*.pdf")):
            try:
                doc = fitz.open(str(file))
                pages_text = []

                for page_num, page in enumerate(doc):
                    text = page.get_text("text")
                    if text.strip():
                        pages_text.append(f"[Page {page_num + 1}]\n{text.strip()}")

                doc.close()

                if not pages_text:
                    logger.warning("pdf_loader.empty_doc", file=str(file))
                    continue

                content = "\n\n".join(pages_text)
                title = file.stem.replace("-", " ").replace("_", " ").title()

                yield Document(
                    source_type="pdf",
                    title=title,
                    content=content,
                    path_or_url=str(file),
                    content_hash=_hash(content),
                    metadata={
                        "filename": file.name,
                        "page_count": len(pages_text),
                    },
                )
                logger.info("pdf_loader.loaded", file=str(file), pages=len(pages_text))
            except Exception as e:
                logger.error("pdf_loader.error", file=str(file), error=str(e))


# ── Git Loader ────────────────────────────────────────────────────────────────

class GitLoader:
    """
    Clones a git repo to a temp dir and extracts Markdown docs from it.
    Reads all .md files inside `docs_path` subfolder + root README.
    Cleans up after itself.
    """

    def __init__(self, repo_url: str, branch: str = "main", docs_path: str = "docs"):
        self.repo_url = repo_url
        self.branch = branch
        self.docs_path = docs_path

    def load(self) -> Iterator[Document]:
        tmp_dir = tempfile.mkdtemp(prefix="rag_git_")
        try:
            logger.info("git_loader.cloning", url=self.repo_url, branch=self.branch)
            repo = Repo.clone_from(
                self.repo_url,
                tmp_dir,
                branch=self.branch,
                depth=1,           # Shallow clone — only latest commit
                single_branch=True,
            )

            target_path = Path(tmp_dir) / self.docs_path
            root_path = Path(tmp_dir)

            # Walk the docs_path subfolder
            files_to_read = list(target_path.rglob("*.md")) if target_path.exists() else []

            # Always include root README if present
            for readme in root_path.glob("README*"):
                if readme.suffix.lower() in (".md", ".mdx", ""):
                    files_to_read.insert(0, readme)

            for file in files_to_read:
                try:
                    content = file.read_text(encoding="utf-8", errors="replace").strip()
                    if not content:
                        continue

                    rel_path = str(file.relative_to(tmp_dir))

                    yield Document(
                        source_type="git",
                        title=_infer_title(content, str(file)),
                        content=content,
                        path_or_url=f"{self.repo_url}/blob/{self.branch}/{rel_path}",
                        content_hash=_hash(content),
                        metadata={
                            "repo_url": self.repo_url,
                            "branch": self.branch,
                            "relative_path": rel_path,
                        },
                    )
                    logger.info("git_loader.file_loaded", file=rel_path)
                except Exception as e:
                    logger.error("git_loader.file_error", file=str(file), error=str(e))

        except Exception as e:
            logger.error("git_loader.clone_error", url=self.repo_url, error=str(e))
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            logger.info("git_loader.cleanup_done", tmp_dir=tmp_dir)


# ── Factory ───────────────────────────────────────────────────────────────────

def get_loader(source_config: dict):
    """
    Returns the right loader based on source type from sources.yaml config entry.

    Example config entry:
      type: markdown
      path: ./data/docs
    """
    source_type = source_config.get("type")
    if source_type == "markdown":
        return MarkdownLoader(path=source_config["path"])
    elif source_type == "html":
        return HTMLLoader(path=source_config["path"])
    elif source_type == "pdf":
        return PDFLoader(path=source_config["path"])
    elif source_type == "git":
        return GitLoader(
            repo_url=source_config["repo_url"],
            branch=source_config.get("branch", "main"),
            docs_path=source_config.get("docs_path", "docs"),
        )
    else:
        raise ValueError(f"Unknown source type: '{source_type}'. Supported: markdown, html, pdf, git")
