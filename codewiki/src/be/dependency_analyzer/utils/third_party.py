"""
Which files are someone else's code: copied libraries and build output, never the repository's own source.

A repository that ships its front end's libraries beside its own scripts (jQuery, Bootstrap, Chart.js, Font
Awesome, a minified copy of each) had them clustered and documented as its own modules: most of one run's 143
modules, and its only failures (a 1.2M-token library no model can read). The rules are about a file's FORM and
LOCATION, never a list of library names:

- minified: a `.js` / `.css` file whose average line is longer than 110 characters, GitHub Linguist's rule for
  minified files (a person's code averages well under that; one repository's own files averaged 21 to 78), unless
  it also holds at least 200 ordinary lines (non-empty, at most 110 characters): a hand-written file with one long
  embedded data line (meshcentral's agents/meshcmd.js: 2,673 ordinary lines) is code, while minified libraries
  have a few dozen at most (OpenLayers 33, each Bootstrap theme 11);
- a library banner: the file opens with a `/*!` comment, the form minifiers and library builds keep for the
  library's license (`/*! jQuery v3.7.1`, `/*! Bootstrap v5.3.3`); a project's own files open with `/**` or `//`;
- a vendored folder (`vendor`, `third_party`, `bower_components`, …): matched by the walk's own path patterns.

A file the rules cannot read is kept: leaving out code the repository wrote is worse than documenting a library.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

MINIFIED_EXTENSIONS = {'.js', '.mjs', '.cjs', '.css'}
# GitHub Linguist's threshold for a minified file (average characters per line).
MINIFIED_AVERAGE_LINE_LENGTH = 110
# A file this many ordinary lines (non-empty, at most the threshold above) is hand-written whatever its average.
HAND_WRITTEN_MIN_LINES = 200
# How much of a file the ordinary lines are counted in (a long embedded line can fill the first sample alone).
COUNT_BYTES = 16 * 1024 * 1024
# What is read of a file to judge it: enough for any banner and a representative average.
SAMPLE_BYTES = 256 * 1024
# Folders that hold other projects' code by convention (Linguist's vendored directories).
THIRD_PARTY_DIRECTORIES = ('vendor', 'vendors', 'third_party', 'third-party', 'thirdparty', 'bower_components')


def third_party_reason(path: Path) -> Optional[str]:
    """Why a file is someone else's code (`minified`, `library banner`), or None for the repository's own."""
    suffix = path.suffix.lower()
    if suffix not in MINIFIED_EXTENSIONS:
        return None
    try:
        with open(path, 'rb') as handle:
            sample = handle.read(SAMPLE_BYTES)
    except OSError:
        return None
    text = sample.decode('utf-8', errors='replace').lstrip('﻿')
    if text.lstrip().startswith('/*!'):
        return 'library banner'
    lines = text.split('\n')
    if len(text) / max(1, len(lines)) <= MINIFIED_AVERAGE_LINE_LENGTH:
        return None
    try:
        with open(path, 'rb') as handle:
            whole = handle.read(COUNT_BYTES).decode('utf-8', errors='replace')
    except OSError:
        return None
    ordinary = sum(1 for line in whole.split('\n') if line.strip() and len(line) <= MINIFIED_AVERAGE_LINE_LENGTH)
    return None if ordinary >= HAND_WRITTEN_MIN_LINES else 'minified'
