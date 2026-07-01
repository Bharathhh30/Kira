import os
import sys
import asyncio
import fitz

# Suppress low-level MuPDF warning messages (e.g. FontBBox warnings)
fitz.TOOLS.mupdf_display_warnings(False)

# Ensure the root of the repository is in the python path so that we can import "parser.*"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from parser.pipeline.runner import run_pipeline  # noqa: E402

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Resume Parser Pipeline Orchestrator")
    parser.add_argument(
        "pdf_path",
        nargs="?",
        default="sample_resume.pdf",
        help="Path to the resume PDF file",
    )
    args = parser.parse_args()

    asyncio.run(run_pipeline(args.pdf_path))
