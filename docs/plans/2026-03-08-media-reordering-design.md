# Media Reordering in Admin Panel

**Date**: 2026-03-08
**Status**: Approved

## UI Changes

Add reorder controls to each media item in the admin list:
- **Move to top** button (double up arrow) — jumps item to position 1
- **Move up** button (up arrow) — swaps with item above
- **Move down** button (down arrow) — swaps with item below
- **Move to bottom** button (double down arrow) — jumps item to last position

Buttons disabled at boundaries (e.g., "move up" disabled for first item).

## How It Works

- Each item has an `order` field (already in the backend)
- On reorder: recalculate order values for affected items, call `PUT /api/admin/media/{id}` with new `{ order }` for each changed item
- Update local state immediately for instant feedback
- Gallery already sorts by `order` (`app.py:189`)

## Backend

No changes needed — `PUT /api/admin/media/{id}` with `{ order: number }` already works.

## What stays the same

- Caption editing
- Delete button
- Thumbnails
- Gallery display logic
