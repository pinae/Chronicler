# Inspecting the engine in the admin

The Django admin shows every record the engine keeps: chronicles and their beats, who knows what,
the schemas, hypotheses with the beats that filled them, expectations, the LLM call log and the usage
log. Records the engine derives or logs are read-only; only chronicle titles, players and entities
can be edited.

## Before you start
- The backend runs (`cd backend && uv run python manage.py runserver`) and you have a superuser
  (`uv run python manage.py createsuperuser`).
- A story has been replayed, e.g. `uv run python manage.py replay steward --reader uniform`.

## See which beats filled a hypothesis
1. Go to **/admin/** and log in.
2. Click **Hypotheses**.
3. Click the row starting with **betrayal(** whose status is **complete**.

**Result:** the page shows the hypothesis' fields (read-only) and a **Step fills** table listing, for
each filled step, the step (e.g. **betrayal.harm**) and the beat that filled it (e.g.
**t=13 steals: Aldric steals the seal from Mira.**). There is no **Save** or **Delete** button.

## Read an LLM call
1. Go to **/admin/llm/llmcall/**.
2. Click any row.

**Result:** **Request**, **Response** and **Metadata** are shown as indented JSON. The metadata lists
the beats the reader was shown (`included_beat_ts`) and the candidates of the question.

## Correct an entity's aliases
1. Go to **/admin/chronicle/entity/** and click **Aldric**.
2. Enter `["the steward", "Master Aldric"]` in the **Aliases** field and click **Save**.

**Result:** the message **The entity “Aldric (character)” was changed successfully.** appears.

## Beats cannot be changed
1. Go to **/admin/chronicle/beat/** and click any beat.

**Result:** all fields are read-only and there is no **Save** button: corrections to a chronicle are
new beats, never edits.
