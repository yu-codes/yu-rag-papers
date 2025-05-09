"""
下載 arXiv PDF 並萃取段落文字
"""

import os
from pathlib import Path
import arxiv
from pdfminer.high_level import extract_text
from tqdm import tqdm

PDF_DIR = Path("data/pdf")
TXT_DIR = Path("data/pdf_txt")
PDF_DIR.mkdir(parents=True, exist_ok=True)
TXT_DIR.mkdir(parents=True, exist_ok=True)


def download_pdfs(query: str, max_results: int = 10):
    search = arxiv.Search(query=query, max_results=max_results)
    for result in tqdm(search.results(), desc="Downloading PDFs"):
        pdf_path = PDF_DIR / f"{result.entry_id.split('/')[-1]}.pdf"
        if pdf_path.exists():
            continue
        result.download_pdf(filename=str(pdf_path))


def pdf_to_paragraphs(pdf_path: Path) -> list[str]:
    raw_text = extract_text(pdf_path)
    # 以空白行為段落切分，並去除極短列
    paragraphs = [p.strip() for p in raw_text.split("\n\n") if len(p.strip()) > 30]
    return paragraphs


def crawl(query: str, max_results: int = 10) -> dict[str, list[str]]:
    """
    回傳 {paper_id: [paragraph, ...]}
    並把 txt 備份到 data/pdf_txt
    """
    download_pdfs(query, max_results)
    corpus: dict[str, list[str]] = {}
    for pdf in PDF_DIR.glob("*.pdf"):
        pid = pdf.stem
        paras = pdf_to_paragraphs(pdf)
        corpus[pid] = paras
        # 備份純文字
        (TXT_DIR / f"{pid}.txt").write_text("\n\n".join(paras), encoding="utf-8")
    return corpus


if __name__ == "__main__":
    crawl("cat:cs.CL AND transformers", max_results=5)
