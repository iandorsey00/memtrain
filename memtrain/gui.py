import _tkinter
import platform
import sys

from memtrain.memtrain_gui.__main__ import main

__all__ = ["main"]


def _is_unsupported_macos_tk():
    if sys.platform != "darwin":
        return False

    # Apple's Command Line Tools Python links against the legacy system Tk 8.5,
    # which aborts on newer macOS releases before our app can handle the error.
    return sys.executable.startswith(
        "/Library/Developer/CommandLineTools/"
    ) and _tkinter.TK_VERSION.startswith("8.5")


def _print_gui_runtime_help():
    current = platform.mac_ver()[0] or "unknown macOS version"
    print("memtrain GUI cannot run with the current Python/Tk runtime.")
    print("Detected:")
    print("  Python: {}".format(sys.executable))
    print("  Tk: {}".format(_tkinter.TK_VERSION))
    print("  macOS: {}".format(current))
    print()
    print("Use one of these instead:")
    print("  1. Install Python from python.org, then run: python3 -m memtrain.gui")
    print("  2. Install Homebrew Python and python-tk, then run: python3 -m memtrain.gui")
    print()
    print("The CLI still works with this Python:")
    print("  python3 -m memtrain animals.csv")


if __name__ == "__main__":
    if _is_unsupported_macos_tk():
        _print_gui_runtime_help()
        raise SystemExit(1)
    main()
