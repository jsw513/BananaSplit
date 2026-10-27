# BananaSplit 1.1 Preview

Based on the supplied BananaSplit 2 source. This is a **source build**, not a signed or App Store-ready application.

## New
- **Sequences** tab: interpret `shot-01 through shot-10`, or specify prefix, suffix, range, zero-padding, and step.
- **Nested Excel folders**: check “Build nested folders from all populated columns” to turn each spreadsheet row into a parent/child path. Empty cells are skipped.
- **Nested paths in preview**: paths such as `Client/Project/Selects` can be previewed and created. Traversal and absolute paths are rejected.
- Existing folder creation, file import, naming tools, dark/light themes, and undo are retained.

## Build on Apple Silicon macOS
Open Terminal, type `cd ` and drag this folder into Terminal, then press Return. Run `bash build_mac.sh`. Open `dist/BananaSplit.app` after successful completion.

## Limitations
- The smart email interpreter is still a **conservative rules-based parser**, not a language model. Review the preview carefully; it may miss or misread complicated instructions.
- Nested Excel mode uses all populated columns from left to right, rather than an individually configurable hierarchy.
- Undo only removes empty folders created during the current app session.
- No files are moved or renamed.
- macOS build and appearance must be tested on a Mac; this package was syntax-checked and its pure-Python engine was tested in Linux.
