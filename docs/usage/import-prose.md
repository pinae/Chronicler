# Importing a book as a story

`import_prose` turns a plain-text book, for example from Project Gutenberg, into the transcript of
a new `literature` fixture story: one narrator utterance per paragraph, numbered by chapter. The
story's beats and entities are drafted afterwards (WP-047) and reviewed by a human.

## Before you start
- The backend is installed (`cd backend && uv sync`).
- The book is a public-domain text or our own material, saved as a UTF-8 text file.

## Import a Project Gutenberg book
1. In `backend/`, run `uv run python manage.py import_prose ~/books/pg11.txt alice`.

**Result:** the command prints `Wrote <n> paragraphs in <m> chapters to …/fixtures/stories/alice/transcript.yaml`.
The transcript's title comes from the book's `Title:` line. The Project Gutenberg header and licence
footer are gone, as are the title page and table of contents before the first chapter, editorial
notes like `[Illustration]` and decorations like `* * *`. Chapters are found by headings such as
`CHAPTER I.` or `Chapter 2: …`; a book without such headings becomes a single chapter.

`fixtures/stories/alice/README.md` is a skeleton: the provenance names the eBook number and its
URL; the licence and the description are marked `TODO` for you to fill in.

## Name a book that has no title line
1. Run `uv run python manage.py import_prose notes.txt lighthouse --title "The Lighthouse"`.

**Result:** the transcript's title is **The Lighthouse**.

## An existing story is not overwritten
1. Run the import of `alice` a second time.

**Result:** the command stops with `alice already has a transcript.yaml; pass --force to replace it`.
With `--force` the transcript and README are written anew.
