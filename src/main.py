import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from hack_vm import HackVM


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"[ERROR] Path not found: {path!r}", file=sys.stderr)
        sys.exit(1)

    translator = HackVM()
    try:
        out = translator.translate(path)
        print(f"[OK] Translated → {out}")
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
