# Message Photos + Admin Delete Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow guests to attach an optional photo when submitting birthday messages, display photos as circular avatars on the message wall with lightbox support, and let admins delete messages.

**Architecture:** New guest-accessible upload URL endpoint, updated message endpoints to handle photoKey, new delete message endpoint (admin-only), frontend changes to message form and message wall. Reuses existing Lightbox component.

**Tech Stack:** Python 3.13 (Lambda), Svelte 5, SvelteKit 2, Tailwind CSS 4, DynamoDB, S3

---

### Task 1: Add guest-accessible upload URL endpoint (backend)

**Files:**
- Modify: `dad-birthday-backend/api/app.py:25-61` (routes + new handler)
- Modify: `dad-birthday-backend/template.yaml` (new API event)
- Modify: `dad-birthday-backend/tests/unit/test_messages.py`

**Step 1: Write the test**

In `dad-birthday-backend/tests/unit/test_messages.py`, add a new test class at the end of the file:

```python
class TestMessageUploadUrl:
    @patch("boto3.client")
    def test_guest_can_get_upload_url(self, mock_boto, make_event):
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/presigned"
        mock_boto.return_value = mock_s3

        event = make_event(
            "POST", "/api/messages/upload-url",
            body={"filename": "selfie.jpg", "contentType": "image/jpeg"},
            headers={"Cookie": _auth_cookie("guest")},
        )
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 200
        data = json.loads(result["body"])
        assert "uploadUrl" in data
        assert "s3Key" in data
        assert data["s3Key"].startswith("message-photos/")

    def test_unauthenticated_returns_401(self, make_event):
        event = make_event(
            "POST", "/api/messages/upload-url",
            body={"filename": "selfie.jpg", "contentType": "image/jpeg"},
        )
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 401
```

**Step 2: Run test to verify it fails**

Run: `cd dad-birthday-backend && uv run python -m pytest tests/unit/test_messages.py::TestMessageUploadUrl -v`
Expected: FAIL (404 Not found — route doesn't exist yet)

**Step 3: Add the route and handler**

In `dad-birthday-backend/api/app.py`, add to the routes dict (after line 31):

```python
        ("POST", "/api/messages/upload-url"): handle_message_upload_url,
```

Add the handler function after `handle_post_message` (after line 171):

```python
def handle_message_upload_url(event):
    session = auth.require_auth(event)
    if not session:
        return _response(401, {"error": "Unauthorized"})

    body = _parse_body(event)
    if not body or not body.get("filename") or not body.get("contentType"):
        return _response(400, {"error": "Provide 'filename' and 'contentType'"})

    import ulid as ulid_mod

    ext = body["filename"].rsplit(".", 1)[-1] if "." in body["filename"] else ""
    s3_key = f"message-photos/{ulid_mod.new()}.{ext}" if ext else f"message-photos/{ulid_mod.new()}"

    s3_client = boto3.client("s3")
    presigned_url = s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": os.environ["MEDIA_BUCKET"],
            "Key": s3_key,
            "ContentType": body["contentType"],
        },
        ExpiresIn=3600,
    )
    return _response(200, {"uploadUrl": presigned_url, "s3Key": s3_key})
```

Add the SAM event in `dad-birthday-backend/template.yaml`, after the `PostMessage` event (after line 84):

```yaml
        MessageUploadUrl:
          Type: Api
          Properties:
            Path: /api/messages/upload-url
            Method: post
```

**Step 4: Run test to verify it passes**

Run: `cd dad-birthday-backend && uv run python -m pytest tests/unit/test_messages.py::TestMessageUploadUrl -v`
Expected: PASS

**Step 5: Run full test suite**

Run: `cd dad-birthday-backend && uv run python -m pytest tests/unit -v`
Expected: All pass

**Step 6: Commit**

```bash
git add dad-birthday-backend/api/app.py dad-birthday-backend/template.yaml dad-birthday-backend/tests/unit/test_messages.py
git commit -m "feat: add guest-accessible upload URL endpoint for message photos"
```

---

### Task 2: Update message endpoints to handle photoKey (backend)

**Files:**
- Modify: `dad-birthday-backend/api/app.py:148-171` (handle_post_message, handle_get_messages)
- Modify: `dad-birthday-backend/tests/unit/test_messages.py`

**Step 1: Update the POST test**

In `dad-birthday-backend/tests/unit/test_messages.py`, add a new test in `TestPostMessage`:

```python
    @patch("api.auth.get_dynamodb_table")
    def test_creates_message_with_photo(self, mock_get_table, make_event):
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        event = make_event(
            "POST", "/api/messages",
            body={"author": "Carol", "text": "Cheers!", "photoKey": "message-photos/abc123.jpg"},
            headers={"Cookie": _auth_cookie()},
        )
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 201
        item = mock_table.put_item.call_args[1]["Item"]
        assert item["photoKey"] == "message-photos/abc123.jpg"
```

**Step 2: Update the GET test**

In `TestGetMessages`, update the existing `test_returns_messages` to include photoKey. Change the mock item to:

```python
                {"PK": "MSG", "SK": "MSG#01ABC", "author": "Alice", "text": "Happy birthday!", "createdAt": "2026-03-01T12:00:00Z", "photoKey": "message-photos/photo1.jpg"},
```

And add an assertion:

```python
        assert data["messages"][0]["photoUrl"] == "https://dad.melvinit.com/message-photos/photo1.jpg"
```

**Step 3: Run tests to verify they fail**

Run: `cd dad-birthday-backend && uv run python -m pytest tests/unit/test_messages.py -v`
Expected: FAIL

**Step 4: Update handle_post_message**

In `dad-birthday-backend/api/app.py`, update `handle_post_message` to store optional photoKey. Change the put_item call (lines 164-170):

```python
    item = {
        "PK": "MSG",
        "SK": f"MSG#{message_id}",
        "author": body["author"],
        "text": body["text"],
        "createdAt": now,
    }
    if body.get("photoKey"):
        item["photoKey"] = body["photoKey"]

    table = auth.get_dynamodb_table()
    table.put_item(Item=item)
    return _response(201, {"id": message_id, "createdAt": now})
```

**Step 5: Update handle_get_messages**

Update the messages list comprehension (lines 141-144) to include photoUrl:

```python
    cf_domain = os.environ.get("CLOUDFRONT_DOMAIN", "dad.melvinit.com")
    messages = []
    for item in result.get("Items", []):
        msg = {
            "id": item["SK"].split("#")[1],
            "author": item["author"],
            "text": item["text"],
            "createdAt": item["createdAt"],
        }
        if item.get("photoKey"):
            msg["photoUrl"] = f"https://{cf_domain}/{item['photoKey']}"
        messages.append(msg)
    return _response(200, {"messages": messages})
```

**Step 6: Run tests to verify they pass**

Run: `cd dad-birthday-backend && uv run python -m pytest tests/unit/test_messages.py -v`
Expected: All pass

**Step 7: Run full test suite**

Run: `cd dad-birthday-backend && uv run python -m pytest tests/unit -v`
Expected: All pass

**Step 8: Commit**

```bash
git add dad-birthday-backend/api/app.py dad-birthday-backend/tests/unit/test_messages.py
git commit -m "feat: support optional photoKey in message creation and retrieval"
```

---

### Task 3: Add delete message endpoint (backend)

**Files:**
- Modify: `dad-birthday-backend/api/app.py:19-61` (routes + new handler)
- Modify: `dad-birthday-backend/template.yaml`
- Modify: `dad-birthday-backend/tests/unit/test_messages.py`

**Step 1: Write the tests**

In `dad-birthday-backend/tests/unit/test_messages.py`, add a new test class:

```python
class TestDeleteMessage:
    @patch("api.auth.get_dynamodb_table")
    def test_admin_can_delete_message(self, mock_get_table, make_event):
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        event = make_event(
            "DELETE", "/api/messages/msg-123",
            headers={"Cookie": _auth_cookie("admin")},
        )
        result = app.lambda_handler(event, None)

        assert result["statusCode"] == 200
        mock_table.delete_item.assert_called_once_with(
            Key={"PK": "MSG", "SK": "MSG#msg-123"}
        )

    def test_guest_cannot_delete_message(self, make_event):
        event = make_event(
            "DELETE", "/api/messages/msg-123",
            headers={"Cookie": _auth_cookie("guest")},
        )
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 401
```

**Step 2: Run tests to verify they fail**

Run: `cd dad-birthday-backend && uv run python -m pytest tests/unit/test_messages.py::TestDeleteMessage -v`
Expected: FAIL (404)

**Step 3: Add the route and handler**

In `dad-birthday-backend/api/app.py`, add path-parameter routing (after line 50, before `else:`):

```python
    elif normalized.startswith("/api/messages/") and method == "DELETE":
        handler = handle_delete_message
```

Add the handler function after `handle_message_upload_url`:

```python
def handle_delete_message(event):
    session = auth.require_auth(event, role="admin")
    if not session:
        return _response(401, {"error": "Unauthorized"})

    path = event.get("path", "")
    message_id = path.split("/")[-1]

    table = auth.get_dynamodb_table()
    table.delete_item(Key={"PK": "MSG", "SK": f"MSG#{message_id}"})
    return _response(200, {"message": "Deleted"})
```

Add the SAM event in `template.yaml`, after `MessageUploadUrl`:

```yaml
        DeleteMessage:
          Type: Api
          Properties:
            Path: /api/messages/{id}
            Method: delete
```

**Step 4: Run tests to verify they pass**

Run: `cd dad-birthday-backend && uv run python -m pytest tests/unit/test_messages.py::TestDeleteMessage -v`
Expected: PASS

**Step 5: Run full test suite and rebuild SAM**

Run: `cd dad-birthday-backend && uv run python -m pytest tests/unit -v && sam build --use-container`
Expected: All pass, build succeeds

**Step 6: Commit**

```bash
git add dad-birthday-backend/api/app.py dad-birthday-backend/template.yaml dad-birthday-backend/tests/unit/test_messages.py
git commit -m "feat: add admin-only delete message endpoint"
```

---

### Task 4: Update frontend API client

**Files:**
- Modify: `dad-birthday-frontend/src/lib/api.ts`

**Step 1: Add new API methods**

In `dad-birthday-frontend/src/lib/api.ts`, update `postMessage` to accept optional photoKey, and add `getMessageUploadUrl` and `deleteMessage`:

Change the existing `postMessage`:

```ts
	postMessage: (author: string, text: string, photoKey?: string) =>
		request('/messages', {
			method: 'POST',
			body: JSON.stringify({ author, text, ...(photoKey && { photoKey }) })
		}),
```

Add after `postMessage`:

```ts
	getMessageUploadUrl: (filename: string, contentType: string) =>
		request('/messages/upload-url', {
			method: 'POST',
			body: JSON.stringify({ filename, contentType })
		}),

	deleteMessage: (id: string) => request(`/messages/${id}`, { method: 'DELETE' }),
```

**Step 2: Run lint and type check**

Run: `cd dad-birthday-frontend && npm run lint && npm run check`
Expected: No errors

**Step 3: Commit**

```bash
git add dad-birthday-frontend/src/lib/api.ts
git commit -m "feat: add message upload URL and delete message API methods"
```

---

### Task 5: Add photo attachment to message form (frontend)

**Files:**
- Modify: `dad-birthday-frontend/src/routes/messages/+page.svelte`

**Step 1: Add photo state and upload logic**

In the `<script>` block, update the Message type and add photo state variables. Change line 5:

```ts
	type Message = { id: string; author: string; text: string; createdAt: string; photoUrl?: string };
```

After `let loadError = $state('');` (line 14), add:

```ts
	let photoFile = $state<File | null>(null);
	let photoPreview = $state('');
	let fileInput = $state<HTMLInputElement | null>(null);

	function handlePhotoSelect(e: Event) {
		const input = e.currentTarget as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;
		photoFile = file;
		photoPreview = URL.createObjectURL(file);
	}

	function removePhoto() {
		photoFile = null;
		if (photoPreview) URL.revokeObjectURL(photoPreview);
		photoPreview = '';
		if (fileInput) fileInput.value = '';
	}
```

**Step 2: Update handleSubmit to upload photo**

Replace the `handleSubmit` function with:

```ts
	async function handleSubmit() {
		if (!author.trim() || !text.trim()) return;
		submitting = true;
		error = '';
		try {
			let photoKey: string | undefined;
			if (photoFile) {
				const { uploadUrl, s3Key } = await api.getMessageUploadUrl(
					photoFile.name,
					photoFile.type
				);
				await fetch(uploadUrl, {
					method: 'PUT',
					body: photoFile,
					headers: { 'Content-Type': photoFile.type }
				});
				photoKey = s3Key;
			}
			await api.postMessage(author.trim(), text.trim(), photoKey);
			const data = await api.getMessages();
			messages = data.messages;
			author = '';
			text = '';
			removePhoto();
			submitted = true;
			error = '';
			setTimeout(() => (submitted = false), 5000);
		} catch (e) {
			console.error('Failed to post message', e);
			error = 'Something went wrong. Please try again.';
		} finally {
			submitting = false;
		}
	}
```

**Step 3: Add photo picker UI to the form**

After the textarea `</div>` (after the "Your message" div) and before the submit button, add:

```svelte
			<div>
				<input
					type="file"
					accept="image/*"
					onchange={handlePhotoSelect}
					bind:this={fileInput}
					class="hidden"
					id="photo-input"
				/>
				{#if photoPreview}
					<div class="flex items-center gap-3">
						<img
							src={photoPreview}
							alt="Preview"
							class="h-16 w-16 rounded-full object-cover border-2 border-gold/40"
						/>
						<button
							type="button"
							onclick={removePhoto}
							class="text-sm text-red-600 hover:text-red-800"
						>
							Remove photo
						</button>
					</div>
				{:else}
					<label
						for="photo-input"
						class="text-brown-light hover:text-brown inline-flex cursor-pointer items-center gap-2 text-sm transition-colors"
					>
						<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
							/>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
							/>
						</svg>
						Add a photo (optional)
					</label>
				{/if}
			</div>
```

**Step 4: Run lint and type check**

Run: `cd dad-birthday-frontend && npm run lint && npm run check`
Expected: No errors (may need prettier formatting)

**Step 5: Commit**

```bash
git add dad-birthday-frontend/src/routes/messages/+page.svelte
git commit -m "feat: add optional photo attachment to message form"
```

---

### Task 6: Display photos on message wall + admin delete + lightbox (frontend)

**Files:**
- Modify: `dad-birthday-frontend/src/routes/messages/+page.svelte`

**Step 1: Import Lightbox and authState, add lightbox state**

At the top of the `<script>` block, add imports:

```ts
	import Lightbox from '$lib/components/Lightbox.svelte';
	import { authState } from '$lib/stores/auth.svelte';
```

After the photo-related state variables, add:

```ts
	let lightboxUrl = $state('');

	async function handleDeleteMessage(id: string) {
		try {
			await api.deleteMessage(id);
			messages = messages.filter((m) => m.id !== id);
		} catch (e) {
			console.error('Failed to delete message', e);
		}
	}
```

**Step 2: Update message cards to show photos and delete button**

Replace the message card template (the `{#each}` block) with:

```svelte
			{#each messages as msg (msg.id)}
				<div class="border-gold/20 rounded-lg border bg-white/70 p-5 shadow-sm">
					<p class="font-handwriting text-brown text-xl leading-relaxed">{msg.text}</p>
					<div class="mt-3 flex items-center gap-3">
						{#if msg.photoUrl}
							<button onclick={() => (lightboxUrl = msg.photoUrl || '')}>
								<img
									src={msg.photoUrl}
									alt="{msg.author}'s photo"
									class="h-10 w-10 rounded-full object-cover border-2 border-gold/30 hover:border-gold transition-colors"
								/>
							</button>
						{/if}
						<p class="text-brown-light text-sm">
							&mdash; {msg.author}
							<span class="text-brown-light/60 ml-2">
								{new Date(msg.createdAt).toLocaleDateString('en-US', {
									month: 'long',
									day: 'numeric',
									year: 'numeric'
								})}
							</span>
						</p>
						{#if authState.role === 'admin'}
							<button
								onclick={() => handleDeleteMessage(msg.id)}
								class="ml-auto text-xs text-red-600 hover:text-red-800"
							>Delete</button>
						{/if}
					</div>
				</div>
			{/each}
```

**Step 3: Add Lightbox at the bottom of the template**

Before the closing `</div>` of the page (last line), add:

```svelte
{#if lightboxUrl}
	<Lightbox
		item={{ id: '', url: lightboxUrl, type: 'photo', caption: '' }}
		onclose={() => (lightboxUrl = '')}
	/>
{/if}
```

**Step 4: Run lint and type check**

Run: `cd dad-birthday-frontend && npm run lint && npm run check`
Expected: No errors

**Step 5: Commit**

```bash
git add dad-birthday-frontend/src/routes/messages/+page.svelte
git commit -m "feat: display message photos as avatars with lightbox, add admin delete"
```
