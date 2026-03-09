<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import Lightbox from '$lib/components/Lightbox.svelte';
	import { authState } from '$lib/stores/auth.svelte';

	type Message = { id: string; author: string; text: string; createdAt: string; photoUrl?: string };

	let messages = $state<Message[]>([]);
	let loading = $state(true);
	let author = $state('');
	let text = $state('');
	let submitting = $state(false);
	let submitted = $state(false);
	let error = $state('');
	let loadError = $state('');
	let photoFile = $state<File | null>(null);
	let photoPreview = $state('');
	let fileInput = $state<HTMLInputElement | null>(null);
	let lightboxUrl = $state('');

	async function handleDeleteMessage(id: string) {
		try {
			await api.deleteMessage(id);
			messages = messages.filter((m) => m.id !== id);
		} catch (e) {
			console.error('Failed to delete message', e);
		}
	}

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

	onMount(async () => {
		try {
			const data = await api.getMessages();
			messages = data.messages;
		} catch (e) {
			console.error('Failed to load messages', e);
			loadError = 'Could not load messages. Please refresh the page.';
		} finally {
			loading = false;
		}
	});

	async function handleSubmit() {
		if (!author.trim() || !text.trim()) return;
		submitting = true;
		error = '';
		try {
			let photoKey: string | undefined;
			if (photoFile) {
				const { uploadUrl, s3Key } = await api.getMessageUploadUrl(photoFile.name, photoFile.type);
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
</script>

<svelte:head>
	<title>Messages - Dad's 80th Birthday</title>
</svelte:head>

<div class="mx-auto max-w-3xl px-4 py-8">
	<h1 class="font-display text-brown mb-8 text-center text-4xl">Birthday Wishes</h1>

	<!-- Gallery link banner -->
	<a
		href="/gallery"
		class="border-gold/40 bg-cream-dark/80 text-brown hover:bg-gold/20 mb-8 flex items-center justify-center gap-3 rounded-lg border px-5 py-4 transition-colors"
	>
		<svg class="h-5 w-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
			/>
		</svg>
		<span class="font-display text-lg">View the Photo Gallery</span>
		<svg class="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
		</svg>
	</a>

	<!-- Message form -->
	<div class="border-gold/30 mb-10 rounded-lg border bg-white/80 p-6 shadow-md">
		<h2 class="font-display text-brown mb-4 text-2xl">Leave a Message</h2>
		<form onsubmit={handleSubmit} class="space-y-4">
			<div>
				<label for="author" class="text-brown mb-1 block text-sm font-medium">Your name</label>
				<input
					id="author"
					type="text"
					bind:value={author}
					class="border-gold/40 text-brown placeholder:text-brown-light/50 focus:border-gold focus:ring-gold bg-cream/50 w-full rounded-md border px-4 py-2"
					maxlength="100"
				/>
			</div>
			<div>
				<label for="message" class="text-brown mb-1 block text-sm font-medium">Your message</label>
				<textarea
					id="message"
					bind:value={text}
					placeholder="Write your birthday message..."
					rows="4"
					class="border-gold/40 text-brown placeholder:text-brown-light/50 focus:border-gold focus:ring-gold bg-cream/50 w-full rounded-md border px-4 py-2"
					maxlength="1000"
				></textarea>
			</div>
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
							class="border-gold/40 h-16 w-16 rounded-full border-2 object-cover"
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
			<button
				type="submit"
				disabled={submitting || !author.trim() || !text.trim()}
				class="bg-brown hover:bg-brown-light text-cream rounded-md px-6 py-2 transition-colors disabled:opacity-50"
			>
				{submitting ? 'Sending...' : 'Send Birthday Wish'}
			</button>
			{#if submitted}
				<p class="text-gold text-sm">Thank you for your message!</p>
			{/if}
			{#if error}
				<p class="text-sm text-red-600">{error}</p>
			{/if}
		</form>
	</div>

	<!-- Message wall -->
	{#if loading}
		<p class="text-brown-light text-center italic">Loading messages...</p>
	{:else if loadError}
		<p class="text-center text-red-600">{loadError}</p>
	{:else if messages.length === 0}
		<p class="text-brown-light text-center">No messages yet. Be the first!</p>
	{:else}
		<div class="space-y-4">
			{#each messages as msg (msg.id)}
				<div class="border-gold/20 rounded-lg border bg-white/70 p-5 shadow-sm">
					<p class="font-handwriting text-brown text-xl leading-relaxed">{msg.text}</p>
					<div class="mt-3 flex items-center gap-3">
						{#if msg.photoUrl}
							<button onclick={() => (lightboxUrl = msg.photoUrl || '')}>
								<img
									src={msg.photoUrl}
									alt="{msg.author}'s photo"
									class="border-gold/30 hover:border-gold h-10 w-10 rounded-full border-2 object-cover transition-colors"
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
								class="ml-auto text-xs text-red-600 hover:text-red-800">Delete</button
							>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

{#if lightboxUrl}
	<Lightbox
		item={{ id: '', url: lightboxUrl, type: 'photo', caption: '' }}
		onclose={() => (lightboxUrl = '')}
	/>
{/if}
