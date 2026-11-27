"""Build standalone desktop executables (Windows .exe, macOS, Linux) with embedded resources using Neutralinojs."""
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DESKTOP = ROOT / "desktop"
RES = DESKTOP / "resources"

def build_desktop():
    print("1. Ensuring presentation dist HTML is up to date...")
    import build
    build.build()

    print("2. Syncing presentation into desktop resources...")
    html = (ROOT / "dist/week09-presentation.html").read_text(encoding="utf-8")
    neu_init = """<script src="/js/neutralino.js"></script>
<script>
  if (typeof Neutralino !== 'undefined') {
    Neutralino.init();
    Neutralino.events.on('windowClose', () => {
      Neutralino.app.exit();
    });
  }
</script>"""
    html = html.replace("</body>", neu_init + "\n</body>")
    (RES / "index.html").write_text(html, encoding="utf-8", newline="\n")

    icon = ROOT / "assets/icons/icon-512.png"
    if icon.exists():
        (RES / "icons").mkdir(parents=True, exist_ok=True)
        shutil.copy2(icon, RES / "icons/appIcon.png")

    print("3. Building standalone executable binaries with embedded resources...")
    subprocess.run(
        ["npx", "@neutralinojs/neu", "build", "--release", "--embed-resources"],
        cwd=str(DESKTOP),
        check=True,
        shell=True,
    )
    dist_dir = DESKTOP / "dist" / "ND01-Week09-Seeing-the-Signal"
    exe = dist_dir / "ND01-Week09-Seeing-the-Signal-win_x64.exe"
    if exe.exists():
        print(f"\nSUCCESS! Built standalone Windows desktop executable ({exe.stat().st_size:,} bytes):")
        print(f" -> {exe}")

if __name__ == "__main__":
    build_desktop()
