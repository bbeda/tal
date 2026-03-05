---
name: loc-counter
description: Count lines of code in a git repository, broken down by file extension and by actual programming language. Use this skill whenever the user asks about lines of code, LOC, code size, codebase size, how big a repo is, how many lines, code statistics, or language breakdown of a project. Also use when the user wants to understand the composition of a codebase.
---

# Lines of Code Counter

Count lines of code in a git repository with two reports:
1. **By file extension** — files, total lines, and non-blank lines per extension
2. **By language** — actual language used across all file types (e.g. TypeScript inside `.vue` files is counted as TypeScript)

## How to use

Run the bundled Python script from the git repository root:

```bash
python <skill-path>/scripts/loc.py
```

The script automatically:
- Uses `git ls-files` to enumerate tracked files (respects `.gitignore`)
- Excludes `node_modules`, lock files, and minified files
- Parses Vue SFC files (`.vue`) to attribute `<template>` to HTML, `<script>` to TypeScript/JavaScript, and `<style>` to CSS/SCSS
- Reports both total lines and non-blank lines

## Output format

The script prints two tables. Always present BOTH reports to the user — do not omit or merge them:

**Report 1 — By file extension**: grouped by file extension (`.vue`, `.cs`, `.ts`, etc.). Shows how code is distributed across file types.

**Report 2 — By language**: grouped by actual programming language (TypeScript, C#, HTML, CSS, etc.), combining contributions from standalone files AND embedded sections (e.g. TypeScript inside `.vue` files is counted as TypeScript, not as Vue).

Each table shows: Files | Lines | Non-blank lines, with totals at the bottom.

When presenting results, show both tables in full. The two reports serve different purposes — Report 1 shows file organization, Report 2 shows true language composition.

## Customization

If the user wants to exclude or include specific patterns, modify the filter on line 5 of the script. The `EXT_TO_LANG` dictionary on line 12 maps file extensions to language names — add entries for any unlisted extensions.

## Requirements

- Python 3.8+
- Must be run from within a git repository
