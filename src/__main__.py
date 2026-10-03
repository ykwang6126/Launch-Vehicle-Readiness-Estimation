"""Support `python -m lvreadiness` using the same CLI as the installed command."""

from .cli import main

raise SystemExit(main())
