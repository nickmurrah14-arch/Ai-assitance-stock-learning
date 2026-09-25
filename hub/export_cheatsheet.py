"""Write the call cheat sheet as one standalone HTML file (open it, print it, or save as PDF).

    python hub/export_cheatsheet.py                    # -> sales/cheat-sheet.html
    python hub/export_cheatsheet.py "C:\\path\\Call Cheat Sheet.html"
"""
import sys
from pathlib import Path

from app import PLAYBOOK, ROOT, create_app


def export(out: Path) -> Path:
    app = create_app()
    html = app.jinja_env.get_template("cheatsheet_standalone.html").render(pb=PLAYBOOK)
    out.write_text(html, encoding="utf-8")
    return out


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "sales" / "cheat-sheet.html"
    print("Wrote", export(target))
