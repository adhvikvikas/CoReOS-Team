#!/usr/bin/env python3
"""
Master Builder for CoReOS System Guide PDF
Assembles all chapters, compiles with Typst, and validates output integrity.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add current dir to sys.path so we can import sections
GUIDE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = GUIDE_DIR.parent
if str(GUIDE_DIR) not in sys.path:
    sys.path.insert(0, str(GUIDE_DIR))

from sections.preamble import get_preamble
from sections.ch1_intro import get_chapter_1
from sections.ch2_arch import get_chapter_2
from sections.ch3_journey import get_chapter_3
from sections.ch4_dashboard import get_chapter_4
from sections.ch5_metrics import get_chapter_5
from sections.ch6_visualizations import get_chapter_6
from sections.ch7_relationships import get_chapter_7
from sections.ch8_examples import get_chapter_8
from sections.ch9_research import get_chapter_9
from sections.ch10_quickref import get_chapter_10

TARGET_TYP = GUIDE_DIR / "CoReOS_System_Guide.typ"
TARGET_PDF = GUIDE_DIR / "CoReOS_System_Guide.pdf"

def build():
    print("=" * 60)
    print("Building CoReOS Master System Guide...")
    print("=" * 60)

    parts = [
        get_preamble(),
        get_chapter_1(),
        get_chapter_2(),
        get_chapter_3(),
        get_chapter_4(),
        get_chapter_5(),
        get_chapter_6(),
        get_chapter_7(),
        get_chapter_8(),
        get_chapter_9(),
        get_chapter_10(),
    ]

    full_typst_content = "\n".join(parts)

    print(f"Writing Typst source to: {TARGET_TYP}")
    with open(TARGET_TYP, "w", encoding="utf-8") as f:
        f.write(full_typst_content)

    print(f"Typst source written: {len(full_typst_content)} characters.")

    print(f"Compiling with Typst to: {TARGET_PDF}...")
    cmd = ["typst", "compile", str(TARGET_TYP), str(TARGET_PDF)]
    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.returncode != 0:
        print("ERROR compiling Typst document:")
        print(res.stderr)
        sys.exit(1)

    print("Typst compilation SUCCESSFUL!")

    if not TARGET_PDF.exists():
        print(f"ERROR: Target PDF not found at {TARGET_PDF}")
        sys.exit(1)

    file_size_bytes = TARGET_PDF.stat().st_size
    file_size_kb = file_size_bytes / 1024.0

    print(f"PDF generated successfully: {TARGET_PDF}")
    print(f"PDF size: {file_size_kb:.1f} KB ({file_size_bytes} bytes)")

    # Check page count using pdfinfo or typst query or python pypdf if available
    try:
        pdfinfo_res = subprocess.run(["pdfinfo", str(TARGET_PDF)], capture_output=True, text=True)
        if pdfinfo_res.returncode == 0:
            for line in pdfinfo_res.stdout.splitlines():
                if "Pages:" in line:
                    print(f"Document {line.strip()}")
    except Exception:
        pass

    print("=" * 60)
    print("CoReOS System Guide build complete!")
    print("=" * 60)

if __name__ == "__main__":
    build()
