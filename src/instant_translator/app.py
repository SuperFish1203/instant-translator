from __future__ import annotations

from instant_translator.bootstrap import build_application


def main() -> int:
    runtime = build_application()
    runtime.main_window.show()
    runtime.tray_icon.show()
    return runtime.app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
