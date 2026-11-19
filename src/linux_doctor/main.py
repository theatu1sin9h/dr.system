"""Dr. System (Linux Doctor) Entry Point."""

import sys


def main():
    """Main terminal CLI entrypoint."""
    from linux_doctor.cli.commands import app
    app()


def gui_main():
    """Main GUI entrypoint."""
    from linux_doctor.gui.app import run_gui
    run_gui()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        gui_main()
    else:
        main()
