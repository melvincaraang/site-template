# Optional Photo with Messages + Admin Delete

**Date**: 2026-03-08
**Status**: Approved

## 1. Photo attachment on message form

- Add an "Add a photo" button below the message textarea (standard `<input type="file" accept="image/*">`)
- When a file is selected, show a small thumbnail preview with an X button to remove
- Photo is optional — form still works without one
- On submit: upload photo to S3 via pre-signed URL, then save the S3 key with the message

## 2. Photo display on message wall

- Messages with photos show a small circular avatar next to the author name
- Tapping the avatar opens the Lightbox at full size
- Messages without photos display as they do now

## 3. Admin delete on message wall

- When `authState.role === 'admin'`, show a small "Delete" button on each message card
- Calls `DELETE /api/messages/{id}` (new endpoint)
- Removes the message from the wall immediately

## Backend changes

- `POST /api/messages`: accept optional `photoKey` field, store in DynamoDB
- `GET /api/messages`: return `photoKey` in response, build full CloudFront URL if present
- `DELETE /api/messages/{id}`: new endpoint, admin-only, deletes message from DynamoDB
- New guest-accessible upload URL endpoint for message photos (or relax auth on existing upload-url endpoint)

## What stays the same

- Message form fields (name, text)
- Gallery page
- Admin media management
