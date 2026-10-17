# -*- coding: utf-8 -*-
"""Scan for CJK leaks, convert each project README.md to RTL HTML, then to PDF via Chrome."""
import re
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(r"E:\New folder\uwc-projects")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CJK = re.compile(r"[\u4e00-\u9fff]+")

CSS = """
* { box-sizing: border-box; }
body {
  font-family: "Segoe UI", Tahoma, Arial, sans-serif;
  direction: rtl; text-align: right;
  color: #1a1a1a; line-height: 1.85; font-size: 13.5px;
  margin: 0; padding: 36px 44px;
}
h1 { color: #0b3d5c; font-size: 26px; border-bottom: 3px solid #c9a227; padding-bottom: 10px; margin-bottom: 6px; }
h2 { color: #0b3d5c; font-size: 17px; margin-top: 28px; border-right: 5px solid #c9a227; padding-right: 10px; }
blockquote { margin: 8px 0 16px 0; color: #555; font-style: italic; border-right: 3px solid #ddd; padding-right: 12px; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 12.5px; }
th, td { border: 1px solid #bbb; padding: 7px 10px; text-align: right; vertical-align: top; }
th { background: #0b3d5c; color: #fff; }
tr:nth-child(even) td { background: #f4f7fa; }
a { color: #0b5394; }
ul, ol { padding-right: 24px; }
strong { color: #0b3d5c; }
p { margin: 8px 0; }
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
{body}
</body>
</html>
"""


def main():
    dirs = sorted(d for d in ROOT.iterdir() if d.is_dir())
    print(f"projects: {len(dirs)}")

    # 1) scan CJK
    leaks = 0
    for d in dirs:
        f = d / "README.md"
        t = f.read_text(encoding="utf-8")
        hits = CJK.findall(t)
        if hits:
            print(f"[CJK] {d.name}: {hits}")
            leaks += 1
    if "--fix" in sys.argv and leaks:
        import html as htmlmod

        # replace runs of CJK with a neutral Arabic phrase is unsafe; just strip and note
        for d in dirs:
            f = d / "README.md"
            t = f.read_text(encoding="utf-8")
            new = CJK.sub("", t)
            if new != t:
                f.write_text(new, encoding="utf-8")
                print(f"[fixed] {d.name}")

    # 2) markdown -> html
    import markdown

    for d in dirs:
        f = d / "README.md"
        md_text = f.read_text(encoding="utf-8")
        body = markdown.markdown(md_text, extensions=["tables", "sane_lists"])
        first_line = md_text.strip().splitlines()[0].lstrip("# ").strip()
        html = TEMPLATE.format(title=first_line, css=CSS, body=body)
        (d / "index.html").write_text(html, encoding="utf-8")
    print("html written")

    # 3) html -> pdf
    for d in dirs:
        src = (d / "index.html").as_uri()
        out = str(d / "project.pdf")
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
             f"--print-to-pdf={out}", src],
            capture_output=True, timeout=60,
        )
        size = (d / "project.pdf").stat().st_size if (d / "project.pdf").exists() else 0
        print(f"pdf {d.name}: {size} bytes")


if __name__ == "__main__":
    main()
