<script lang="ts">
	import { api } from '$lib/api';
	import { authState } from '$lib/stores/auth.svelte';
	import { goto } from '$app/navigation';

	type Token = { uuid: string; label: string; expiresAt: number; createdAt: string };
	type MediaItem = { id: string; url: string; type: string; caption: string; order: number };

	let activeTab = $state<'media' | 'tokens'>('media');
	let tokens = $state<Token[]>([]);
	let media = $state<MediaItem[]>([]);
	let loading = $state(true);
	let siteUrl = $state('');

	// Upload state
	let uploadFiles = $state<FileList | null>(null);
	let uploadCaption = $state('');
	let uploading = $state(false);

	// Token creation state
	let tokenLabel = $state('');
	let tokenDays = $state(7);
	let creatingToken = $state(false);

	// Wait for session check to complete before verifying admin role
	let dataLoaded = false;
	$effect(() => {
		if (!authState.checking && !dataLoaded) {
			if (authState.role !== 'admin') {
				goto('/');
			} else {
				dataLoaded = true;
				siteUrl = window.location.origin;
				loadData();
			}
		}
	});

	async function loadData() {
		loading = true;
		try {
			const [mediaData, tokenData] = await Promise.all([api.getMedia(), api.getTokens()]);
			media = mediaData.media;
			tokens = tokenData.tokens;
		} catch (e) {
			console.error('Failed to load admin data', e);
		} finally {
			loading = false;
		}
	}

	async function handleUpload() {
		if (!uploadFiles || uploadFiles.length === 0) return;
		uploading = true;
		try {
			let nextOrder = media.length > 0 ? Math.max(...media.map((m) => m.order)) + 1 : 0;
			for (const file of uploadFiles) {
				const isVideo = file.type.startsWith('video/');
				// Get pre-signed URL
				const { uploadUrl, s3Key } = await api.getUploadUrl(file.name, file.type);
				// Upload directly to S3
				await fetch(uploadUrl, {
					method: 'PUT',
					body: file,
					headers: { 'Content-Type': file.type }
				});
				// Save metadata
				await api.saveMedia(s3Key, isVideo ? 'video' : 'photo', uploadCaption, nextOrder++);
			}
			uploadCaption = '';
			uploadFiles = null;
			await loadData();
		} catch (e) {
			console.error('Upload failed', e);
		} finally {
			uploading = false;
		}
	}

	async function handleDeleteMedia(id: string) {
		try {
			await api.deleteMedia(id);
			await loadData();
		} catch (e) {
			console.error('Delete failed', e);
		}
	}

	async function handleCreateToken() {
		if (!tokenLabel.trim()) return;
		creatingToken = true;
		try {
			await api.createToken(tokenLabel.trim(), tokenDays);
			tokenLabel = '';
			await loadData();
		} catch (e) {
			console.error('Token creation failed', e);
		} finally {
			creatingToken = false;
		}
	}

	async function handleDeleteToken(uuid: string) {
		try {
			await api.deleteToken(uuid);
			await loadData();
		} catch (e) {
			console.error('Token deletion failed', e);
		}
	}

	// Caption editing state
	let editingMediaId = $state('');
	let editingCaption = $state('');

	function startEditCaption(item: MediaItem) {
		editingMediaId = item.id;
		editingCaption = item.caption;
	}

	async function saveCaption(id: string) {
		try {
			await api.updateMedia(id, { caption: editingCaption });
			const item = media.find((m) => m.id === id);
			if (item) item.caption = editingCaption;
		} catch (e) {
			console.error('Failed to update caption', e);
		}
		editingMediaId = '';
	}

	function cancelEditCaption() {
		editingMediaId = '';
	}

	// Reorder functions
	async function moveMedia(index: number, target: 'up' | 'down' | 'top' | 'bottom') {
		const items = [...media];
		const item = items[index];

		// Remove item from current position
		items.splice(index, 1);

		// Insert at new position
		if (target === 'top') items.unshift(item);
		else if (target === 'bottom') items.push(item);
		else if (target === 'up') items.splice(index - 1, 0, item);
		else items.splice(index + 1, 0, item);

		// Reassign order values and update local state
		const updates: Promise<unknown>[] = [];
		items.forEach((m, i) => {
			if (m.order !== i) {
				m.order = i;
				updates.push(api.updateMedia(m.id, { order: i }));
			}
		});
		media = items;

		try {
			await Promise.all(updates);
		} catch (e) {
			console.error('Failed to reorder', e);
			await loadData();
		}
	}

	let copiedUuid = $state('');

	async function handleCopyLink(uuid: string) {
		const url = `${siteUrl}/?token=${uuid}`;
		await navigator.clipboard.writeText(url);
		copiedUuid = uuid;
		setTimeout(() => (copiedUuid = ''), 2000);
	}
</script>

<svelte:head>
	<title>Admin</title>
</svelte:head>

<div class="mx-auto max-w-4xl px-4 py-8">
	<h1 class="font-display text-primary mb-6 text-3xl">Admin Dashboard</h1>

	<!-- Tabs -->
	<div class="border-accent/30 mb-6 flex gap-4 border-b">
		<button
			class="pb-2 transition-colors"
			class:border-b-2={activeTab === 'media'}
			class:border-accent={activeTab === 'media'}
			class:text-primary={activeTab === 'media'}
			class:text-primary/50={activeTab !== 'media'}
			onclick={() => (activeTab = 'media')}>Upload Media</button
		>
		<button
			class="pb-2 transition-colors"
			class:border-b-2={activeTab === 'tokens'}
			class:border-accent={activeTab === 'tokens'}
			class:text-primary={activeTab === 'tokens'}
			class:text-primary/50={activeTab !== 'tokens'}
			onclick={() => (activeTab = 'tokens')}>Access Tokens</button
		>
	</div>

	{#if loading}
		<p class="text-primary/60 italic">Loading...</p>
	{:else if activeTab === 'media'}
		<!-- Upload form -->
		<div class="border-accent/30 mb-8 rounded-lg border bg-white/80 p-6">
			<h2 class="font-display text-primary mb-4 text-xl">Upload Photos & Videos</h2>
			<form onsubmit={handleUpload} class="space-y-4">
				<input
					type="file"
					accept="image/*,video/*"
					multiple
					onchange={(e) => (uploadFiles = e.currentTarget.files)}
					class="text-primary w-full"
				/>
				<input
					type="text"
					bind:value={uploadCaption}
					placeholder="Caption (optional)"
					class="border-accent/40 w-full rounded-md border px-4 py-2"
				/>
				<button
					type="submit"
					disabled={uploading || !uploadFiles?.length}
					class="bg-accent hover:bg-accent-light text-white rounded-md px-6 py-2 disabled:opacity-50"
				>
					{uploading ? 'Uploading...' : 'Upload'}
				</button>
			</form>
		</div>

		<!-- Media list -->
		<div class="space-y-3">
			{#each media as item, index (item.id)}
				<div class="border-accent/20 flex items-center gap-3 rounded-lg border bg-white/70 p-3">
					{#if item.type === 'video'}
						<div
							class="bg-primary/10 flex h-16 w-16 flex-shrink-0 items-center justify-center rounded"
						>
							<span class="text-sm">Video</span>
						</div>
					{:else}
						<img
							src={item.url}
							alt={item.caption}
							class="h-16 w-16 flex-shrink-0 rounded object-cover"
						/>
					{/if}
					<div class="flex-1">
						{#if editingMediaId === item.id}
							<input
								type="text"
								bind:value={editingCaption}
								onblur={() => saveCaption(item.id)}
								onkeydown={(e) => {
									if (e.key === 'Enter') e.currentTarget.blur();
									if (e.key === 'Escape') cancelEditCaption();
								}}
								class="border-accent/40 text-primary w-full rounded border px-2 py-1 text-sm"
								autofocus
							/>
						{:else}
							<button
								onclick={() => startEditCaption(item)}
								class="text-primary cursor-pointer text-left text-sm underline decoration-dotted underline-offset-2 hover:decoration-solid"
							>
								{item.caption || '(no caption)'}
							</button>
						{/if}
					</div>
					<div class="flex flex-col gap-0.5">
						<button
							disabled={index === 0}
							onclick={() => moveMedia(index, 'top')}
							class="text-primary/40 hover:text-primary p-0.5 disabled:opacity-20"
							title="Move to top"
						>
							<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M5 11l7-7 7 7M5 19l7-7 7 7"
								/>
							</svg>
						</button>
						<button
							disabled={index === 0}
							onclick={() => moveMedia(index, 'up')}
							class="text-primary/40 hover:text-primary p-0.5 disabled:opacity-20"
							title="Move up"
						>
							<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M5 15l7-7 7 7"
								/>
							</svg>
						</button>
						<button
							disabled={index === media.length - 1}
							onclick={() => moveMedia(index, 'down')}
							class="text-primary/40 hover:text-primary p-0.5 disabled:opacity-20"
							title="Move down"
						>
							<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M19 9l-7 7-7-7"
								/>
							</svg>
						</button>
						<button
							disabled={index === media.length - 1}
							onclick={() => moveMedia(index, 'bottom')}
							class="text-primary/40 hover:text-primary p-0.5 disabled:opacity-20"
							title="Move to bottom"
						>
							<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M19 5l-7 7-7-7M19 13l-7 7-7-7"
								/>
							</svg>
						</button>
					</div>
					<button
						class="text-sm text-red-600 hover:text-red-800"
						onclick={() => handleDeleteMedia(item.id)}>Delete</button
					>
				</div>
			{/each}
		</div>
	{:else}
		<!-- Token creation -->
		<div class="border-accent/30 mb-8 rounded-lg border bg-white/80 p-6">
			<h2 class="font-display text-primary mb-4 text-xl">Create Access Link</h2>
			<form onsubmit={handleCreateToken} class="space-y-4">
				<input
					type="text"
					bind:value={tokenLabel}
					placeholder="Label (e.g., 'For Uncle Bob')"
					class="border-accent/40 w-full rounded-md border px-4 py-2"
				/>
				<div class="flex items-center gap-2">
					<label for="days" class="text-primary text-sm">Expires in:</label>
					<select
						id="days"
						bind:value={tokenDays}
						class="border-accent/40 rounded-md border px-3 py-2"
					>
						<option value={1}>1 day</option>
						<option value={3}>3 days</option>
						<option value={7}>7 days</option>
						<option value={14}>14 days</option>
						<option value={30}>30 days</option>
					</select>
				</div>
				<button
					type="submit"
					disabled={creatingToken || !tokenLabel.trim()}
					class="bg-accent hover:bg-accent-light text-white rounded-md px-6 py-2 disabled:opacity-50"
				>
					{creatingToken ? 'Creating...' : 'Create Link'}
				</button>
			</form>
		</div>

		<!-- Token list -->
		<div class="space-y-3">
			{#each tokens as token (token.uuid)}
				<div class="border-accent/20 rounded-lg border bg-white/70 p-4">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-primary font-medium">{token.label || '(no label)'}</p>
							<p class="text-primary/60 text-xs">
								Expires: {new Date(token.expiresAt * 1000).toLocaleDateString()}
							</p>
						</div>
						<button
							class="text-sm text-red-600 hover:text-red-800"
							onclick={() => handleDeleteToken(token.uuid)}>Revoke</button
						>
					</div>
					<div class="bg-surface/50 mt-2 flex items-center gap-2 rounded p-2">
						<p class="flex-1 text-xs break-all">
							{siteUrl}/?token={token.uuid}
						</p>
						<button
							onclick={() => handleCopyLink(token.uuid)}
							class="bg-accent hover:bg-accent-light text-white shrink-0 rounded px-3 py-1 text-xs transition-colors"
						>
							{copiedUuid === token.uuid ? 'Copied!' : 'Copy'}
						</button>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
