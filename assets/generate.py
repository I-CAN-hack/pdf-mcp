"""Generate test PDF fixtures for the pdf-mcp test suite."""

from pathlib import Path

import fitz

ASSETS = Path(__file__).parent


def create_basic():
    """Simple 3-page PDF with metadata, TOC, headers/footers, and searchable text."""
    doc = fitz.open()
    doc.set_metadata({
        "title": "Test Document",
        "author": "Test Author",
        "subject": "Testing",
        "keywords": "test, pdf, mcp",
        "creator": "generate.py",
    })

    pages_content = [
        "This is the first page.\nIt contains introductory material.",
        "The second page has more detail.\nDatasheet specs go here.",
        "Final page with a summary.\nContact: test@example.com",
    ]

    for i, body in enumerate(pages_content, 1):
        page = doc.new_page(width=595, height=842)  # A4
        # Header
        page.insert_text((72, 30), f"Test Document - Header", fontsize=8, color=(0.5, 0.5, 0.5))
        # Footer
        page.insert_text((72, 820), f"Page {i} of 3", fontsize=8, color=(0.5, 0.5, 0.5))
        # Body
        page.insert_text((72, 80), f"Chapter {i}", fontsize=18)
        y = 120
        for line in body.split("\n"):
            page.insert_text((72, y), line, fontsize=11)
            y += 16

    doc.set_toc([
        [1, "Chapter 1", 1],
        [1, "Chapter 2", 2],
        [1, "Chapter 3", 3],
    ])
    doc.save(ASSETS / "basic.pdf")
    doc.close()


def create_with_diagrams():
    """PDF with vector drawings to test image rendering."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    page.insert_text((72, 60), "Page with Diagrams", fontsize=16)

    # Draw some shapes to simulate a diagram
    # Rectangle
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(72, 100, 250, 200))
    shape.finish(color=(0, 0, 0), fill=(0.9, 0.9, 1), width=1.5)
    shape.commit()

    page.insert_text((110, 160), "Component A", fontsize=10)

    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(320, 100, 500, 200))
    shape.finish(color=(0, 0, 0), fill=(1, 0.9, 0.9), width=1.5)
    shape.commit()

    page.insert_text((360, 160), "Component B", fontsize=10)

    # Arrow between boxes
    shape = page.new_shape()
    shape.draw_line(fitz.Point(250, 150), fitz.Point(320, 150))
    shape.finish(color=(0, 0, 0), width=2)
    shape.commit()

    # Circle
    shape = page.new_shape()
    shape.draw_circle(fitz.Point(286, 350), 80)
    shape.finish(color=(0, 0.4, 0), fill=(0.9, 1, 0.9), width=1.5)
    shape.commit()

    page.insert_text((250, 355), "Sensor Node", fontsize=10)

    # Table-like grid
    page.insert_text((72, 480), "Pin Configuration", fontsize=12)
    y_start = 500
    for row in range(5):
        for col in range(4):
            x = 72 + col * 120
            y = y_start + row * 25
            shape = page.new_shape()
            shape.draw_rect(fitz.Rect(x, y, x + 120, y + 25))
            shape.finish(color=(0, 0, 0), width=0.5)
            shape.commit()
            if row == 0:
                labels = ["Pin", "Name", "Type", "Description"]
                page.insert_text((x + 4, y + 17), labels[col], fontsize=9)
            else:
                vals = [str(row), f"GPIO_{row}", "I/O", f"General purpose {row}"]
                page.insert_text((x + 4, y + 17), vals[col], fontsize=8)

    doc.save(ASSETS / "diagrams.pdf")
    doc.close()


def create_nested_toc():
    """PDF with a multi-level table of contents."""
    doc = fitz.open()

    sections = [
        (1, "Introduction"),
        (1, "Architecture"),
        (2, "Frontend"),
        (2, "Backend"),
        (3, "Database Layer"),
        (3, "API Layer"),
        (1, "Deployment"),
        (2, "Docker Setup"),
        (2, "Kubernetes"),
    ]

    toc = []
    for i, (level, title) in enumerate(sections, 1):
        page = doc.new_page(width=595, height=842)
        indent = "  " * (level - 1)
        page.insert_text((72, 80), f"{indent}{title}", fontsize=max(18 - level * 2, 11))
        page.insert_text((72, 120), f"Content for section: {title}", fontsize=11)
        toc.append([level, title, i])

    doc.set_toc(toc)
    doc.save(ASSETS / "nested_toc.pdf")
    doc.close()


def create_search_targets():
    """PDF with known text patterns for testing search."""
    doc = fitz.open()

    page1 = doc.new_page()
    page1.insert_text((72, 80), "Resistance values and specifications", fontsize=14)
    page1.insert_text((72, 110), "The resistance of R1 is 10kΩ at 25°C.", fontsize=11)
    page1.insert_text((72, 130), "Maximum voltage rating: 3.3V DC.", fontsize=11)
    page1.insert_text((72, 150), "Operating temperature range: -40°C to +85°C.", fontsize=11)
    page1.insert_text((72, 180), "UNIQUE_MARKER_ALPHA found on page 1.", fontsize=11)

    page2 = doc.new_page()
    page2.insert_text((72, 80), "Timing characteristics", fontsize=14)
    page2.insert_text((72, 110), "Clock frequency: 16MHz typical.", fontsize=11)
    page2.insert_text((72, 130), "Rise time: 5ns maximum.", fontsize=11)
    page2.insert_text((72, 150), "UNIQUE_MARKER_BETA found on page 2.", fontsize=11)
    page2.insert_text((72, 170), "The resistance measurement should be verified.", fontsize=11)

    page3 = doc.new_page()
    page3.insert_text((72, 80), "Ordering information", fontsize=14)
    page3.insert_text((72, 110), "Part number: ABC-123-XYZ", fontsize=11)
    page3.insert_text((72, 130), "UNIQUE_MARKER_ALPHA also on page 3.", fontsize=11)

    doc.save(ASSETS / "search_targets.pdf")
    doc.close()


def create_large_toc():
    """PDF with a very large multi-level TOC to test auto-trimming."""
    doc = fitz.open()
    toc = []
    page_num = 0

    for part in range(1, 6):
        page_num += 1
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 80), f"Part {part}", fontsize=18)
        toc.append([1, f"Part {part}", page_num])

        for chapter in range(1, 9):
            page_num += 1
            page = doc.new_page(width=595, height=842)
            title = f"Chapter {part}.{chapter}"
            page.insert_text((72, 80), title, fontsize=14)
            toc.append([2, title, page_num])

            for section in range(1, 5):
                page_num += 1
                page = doc.new_page(width=595, height=842)
                title = f"Section {part}.{chapter}.{section}"
                page.insert_text((72, 80), title, fontsize=12)
                toc.append([3, title, page_num])

    doc.set_toc(toc)
    doc.save(ASSETS / "large_toc.pdf")
    doc.close()


def create_mega_toc():
    """PDF with 400+ pages and 4-level deep TOC for comprehensive auto-trim testing.

    Structure:
      2 volumes (L1) × 8 chapters (L2) × 8 sections (L3) × 2 subsections (L4)

    Entry counts:
      Level 1:  2
      Level 2:  16   (cumulative ≤L2:  18)
      Level 3:  128  (cumulative ≤L3: 146)
      Level 4:  256  (cumulative ≤L4: 402)

    Full-TOC auto-trim (threshold 100):
      ≤L2 = 18 fits → best_level=2, total=18, auto_trimmed_to_level=2

    Volume 1 subtree (parent="Volume 1"):
      8 chapters + 64 sections + 128 subsections = 200 children
      ≤L2 = 8, ≤L3 = 72 fits → best_level=3, total=72, auto_trimmed_to_level=2 (relative)

    Chapter 1.1 subtree (parent="Chapter 1.1"):
      8 sections + 16 subsections = 24 children (< 100, no auto-trim)
    """
    doc = fitz.open()
    toc = []
    page_num = 0

    for vol in range(1, 3):
        page_num += 1
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 80), f"Volume {vol}", fontsize=18)
        toc.append([1, f"Volume {vol}", page_num])

        for ch in range(1, 9):
            page_num += 1
            page = doc.new_page(width=595, height=842)
            title = f"Chapter {vol}.{ch}"
            page.insert_text((72, 80), title, fontsize=14)
            toc.append([2, title, page_num])

            for sec in range(1, 9):
                page_num += 1
                page = doc.new_page(width=595, height=842)
                title = f"Section {vol}.{ch}.{sec}"
                page.insert_text((72, 80), title, fontsize=12)
                toc.append([3, title, page_num])

                for sub in range(1, 3):
                    page_num += 1
                    page = doc.new_page(width=595, height=842)
                    title = f"Subsection {vol}.{ch}.{sec}.{sub}"
                    page.insert_text((72, 80), title, fontsize=11)
                    toc.append([4, title, page_num])

    doc.set_toc(toc)
    doc.save(ASSETS / "mega_toc.pdf")
    doc.close()


if __name__ == "__main__":
    create_basic()
    create_with_diagrams()
    create_nested_toc()
    create_search_targets()
    create_large_toc()
    create_mega_toc()
    print(f"Generated test PDFs in {ASSETS}")
    for f in sorted(ASSETS.glob("*.pdf")):
        print(f"  {f.name}")
