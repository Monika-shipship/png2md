import sys

from docpage2md_app.cli import main as cli_main
from docpage2md_app.gui import main as gui_main


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--docpage2md-cli":
        raise SystemExit(cli_main(sys.argv[2:]))
    raise SystemExit(gui_main())
