# Admin Inline Caption Editing

**Date**: 2026-03-08
**Status**: Approved

## Change

In the admin media list, make the caption text clickable. When clicked, it becomes an input field pre-filled with the current caption. Pressing Enter or blur saves the change via `PUT /api/admin/media/{id}`. Pressing Escape cancels the edit.

## Backend

No changes needed — `PUT /api/admin/media/{id}` with `{ "caption": "new text" }` already works.

## Frontend

- Admin page only: media list item caption becomes editable inline
- Visual hint that it's editable (e.g., cursor pointer on hover)
- On click: swap text for input, auto-focus
- On Enter or blur: save via API, update local state
- On Escape: cancel, revert to original text

## What stays the same

- Delete button
- Media thumbnails
- Everything else on the admin page
