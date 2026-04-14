"""Load the Cybereye4 project onto sys.path without modifying that repository."""

from __future__ import annotations

import os
import sys


def ensure_cybereye_on_path(src_root: str) -> str:
    """
    Insert the Cybereye4 project root at the front of sys.path.

    Validates presence of cybereye_config.py so failures are explicit.
    """
    root = os.path.abspath(os.path.expanduser(src_root))
    if not os.path.isdir(root):
        raise FileNotFoundError(f"CYBEREYE_SRC_ROOT is not a directory: {root}")
    marker = os.path.join(root, "cybereye_config.py")
    if not os.path.isfile(marker):
        raise FileNotFoundError(
            f"Expected Cybereye4 project at {root} (missing cybereye_config.py)."
        )
    if root not in sys.path:
        sys.path.insert(0, root)
    return root
