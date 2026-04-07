#!/usr/bin/env python3
"""Convenience wrapper for the tmux-agents-sidebar UI."""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_SCRIPT = os.path.join(SCRIPT_DIR, "..", "plugins", "tmux-agents-sidebar", "scripts", "agents-sidebar.py")

os.execv(PLUGIN_SCRIPT, [PLUGIN_SCRIPT, *sys.argv[1:]])
