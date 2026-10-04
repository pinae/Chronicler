# Browse chronicles

The start page lists every chronicle (play session, literary work or media corpus) with its kind and
how many beats it holds, so a game master or writer can open one.

## Before you start
- The app runs: `cd backend && uv run python manage.py runserver` with the frontend built
  (`cd frontend && yarn build`), or `yarn dev` in `frontend/` for development.
- For the first scenario, the stories `minimal` and `steward` have been replayed
  (`uv run python manage.py replay minimal --reader none`, the same for `steward`).

## See all chronicles
1. Go to **/**.

**Result:** the heading **Chronicles** is shown above a list with, among others, the link
**The Steward of Wend** followed by **session · 24 beats**, and the link **The Minimal Hall**
followed by **session · 5 beats**. The newest chronicle comes first.

## No chronicles yet
1. Start with an empty database.
2. Go to **/**.

**Result:** under the heading **Chronicles** the page says **No chronicles yet**.

## The backend cannot be reached
1. Stop the backend while the development server (`yarn dev`) keeps running (the browser test
   simulates this by failing the request to `/api/chronicles/`).
2. Go to **/**.

**Result:** the page says **Could not load the chronicles.**

## Switch between light and dark
The interface follows the system's light or dark setting until you choose otherwise.

1. Go to **/** and choose **Dark** in **Theme** (top right).

**Result:** the page turns dark (night workshop: dark panels, brass and copper ornament). After
reloading the page, **Theme** still shows **Dark**.

2. Choose **System** in **Theme**.

**Result:** the page follows the system setting again.
