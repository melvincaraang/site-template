<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { authState } from '$lib/stores/auth.svelte';
	import { goto } from '$app/navigation';

	type Token = { uuid: string; label: string; expiresAt: number; createdAt: string };
	type MediaItem = { id: string; url: string; type: string; caption: string; order: number };

	let activeTab = $state<'media' | 'tokens'>('media');
	let tokens = $state<Token[]>([]);
	let media = $state<MediaItem[]>([]);
	let loading = $state(true);

	// Upload state
	let uploadFiles = $state<FileList | null>(null);
	let uploadCaption = $state('');
	let uploading = $state(false);

	// Token creation state
	let tokenLabel = $state('');
	let tokenDays = $state(7);
	let creatingToken = $state(false);

	onMount(async () => {
		if (authState.role !== 'admin') {
			goto('/');
			return;
		}
		await loadData();
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
				await api.saveMedia(s3Key, isVideo ? 'video' : 'photo', uploadCaption);
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
</script>

<svelte:head>
	<title>Admin - Dad's 80th Birthday</title>
</svelte:head>

<div class="mx-auto max-w-4xl px-4 py-8">
	<h1 class="font-display text-brown mb-6 text-3xl">Admin Dashboard</h1>

	<!-- Tabs -->
	<div class="border-gold/30 mb-6 flex gap-4 border-b">
		<button
			class="pb-2 transition-colors"
			class:border-b-2={activeTab === 'media'}
			class:border-gold={activeTab === 'media'}
			class:text-brown={activeTab === 'media'}
			class:text-brown-light={activeTab !== 'media'}
			onclick={() => (activeTab = 'media')}>Upload Media</button
		>
		<button
			class="pb-2 transition-colors"
			class:border-b-2={activeTab === 'tokens'}
			class:border-gold={activeTab === 'tokens'}
			class:text-brown={activeTab === 'tokens'}
			class:text-brown-light={activeTab !== 'tokens'}
			onclick={() => (activeTab = 'tokens')}>Access Tokens</button
		>
	</div>

	{#if loading}
		<p class="text-brown-light italic">Loading...</p>
	{:else if activeTab === 'media'}
		<!-- Upload form -->
		<div class="border-gold/30 mb-8 rounded-lg border bg-white/80 p-6">
			<h2 class="font-display text-brown mb-4 text-xl">Upload Photos & Videos</h2>
			<form onsubmit={handleUpload} class="space-y-4">
				<input
					type="file"
					accept="image/*,video/*"
					multiple
					onchange={(e) => (uploadFiles = e.currentTarget.files)}
					class="text-brown w-full"
				/>
				<input
					type="text"
					bind:value={uploadCaption}
					placeholder="Caption (optional)"
					class="border-gold/40 w-full rounded-md border px-4 py-2"
				/>
				<button
					type="submit"
					disabled={uploading || !uploadFiles?.length}
					class="bg-brown hover:bg-brown-light text-cream rounded-md px-6 py-2 disabled:opacity-50"
				>
					{uploading ? 'Uploading...' : 'Upload'}
				</button>
			</form>
		</div>

		<!-- Media list -->
		<div class="space-y-3">
			{#each media as item (item.id)}
				<div class="border-gold/20 flex items-center gap-4 rounded-lg border bg-white/70 p-3">
					{#if item.type === 'video'}
						<div
							class="bg-brown-light/20 flex h-16 w-16 flex-shrink-0 items-center justify-center rounded"
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
						<p class="text-brown text-sm">{item.caption || '(no caption)'}</p>
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
		<div class="border-gold/30 mb-8 rounded-lg border bg-white/80 p-6">
			<h2 class="font-display text-brown mb-4 text-xl">Create Access Link</h2>
			<form onsubmit={handleCreateToken} class="space-y-4">
				<input
					type="text"
					bind:value={tokenLabel}
					placeholder="Label (e.g., 'For Uncle Bob')"
					class="border-gold/40 w-full rounded-md border px-4 py-2"
				/>
				<div class="flex items-center gap-2">
					<label for="days" class="text-brown text-sm">Expires in:</label>
					<select
						id="days"
						bind:value={tokenDays}
						class="border-gold/40 rounded-md border px-3 py-2"
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
					class="bg-brown hover:bg-brown-light text-cream rounded-md px-6 py-2 disabled:opacity-50"
				>
					{creatingToken ? 'Creating...' : 'Create Link'}
				</button>
			</form>
		</div>

		<!-- Token list -->
		<div class="space-y-3">
			{#each tokens as token (token.uuid)}
				<div class="border-gold/20 rounded-lg border bg-white/70 p-4">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-brown font-medium">{token.label || '(no label)'}</p>
							<p class="text-brown-light text-xs">
								Expires: {new Date(token.expiresAt * 1000).toLocaleDateString()}
							</p>
						</div>
						<button
							class="text-sm text-red-600 hover:text-red-800"
							onclick={() => handleDeleteToken(token.uuid)}>Revoke</button
						>
					</div>
					<p class="bg-cream/50 mt-2 rounded p-2 text-xs break-all">
						https://dad.melvinit.com/?token={token.uuid}
					</p>
				</div>
			{/each}
		</div>
	{/if}
</div>
