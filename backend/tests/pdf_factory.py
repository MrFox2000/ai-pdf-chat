"""A tiny PDF builder so the test suite needs no binary fixtures."""

from __future__ import annotations


def build_pdf(pages: list[str]) -> bytes:
    """Return a valid single-font PDF containing one page per string."""
    page_count = len(pages)
    kids = " ".join(f"{4 + 2 * i} 0 R" for i in range(page_count))
    font_object = 3 + 2 * page_count

    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {page_count} >>".encode(),
        f"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>".encode(),
    ]

    for index, text in enumerate(pages):
        content_object = 5 + 2 * index
        objects.append(
            (
                "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {font_object} 0 R >> >> "
                f"/Contents {content_object} 0 R >>"
            ).encode()
        )
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode()
        objects.append(
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n"
            + stream
            + b"\nendstream"
        )

    header = b"%PDF-1.4\n"
    body = b""
    offsets: list[int] = []
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(header) + len(body))
        body += f"{number} 0 obj\n".encode() + obj + b"\nendobj\n"

    xref_offset = len(header) + len(body)
    xref = b"xref\n0 " + str(len(objects) + 1).encode() + b"\n"
    xref += b"0000000000 65535 f \n"
    for offset in offsets:
        xref += f"{offset:010d} 00000 n \n".encode()

    trailer = (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode()
    return header + body + xref + trailer
