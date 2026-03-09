<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';

	type Message = { id: string; author: string; text: string; createdAt: string };

	let messages = $state<Message[]>([]);
	let loading = $state(true);
	let author = $state('');
	let text = $state('');
	let submitting = $state(false);
	let submitted = $state(false);
	let error = $state('');
	let loadError = $state('');

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
		try {
			await api.postMessage(author.trim(), text.trim());
			// Refresh messages
			const data = await api.getMessages();
			messages = data.messages;
			author = '';
			text = '';
			submitted = true;
			error = '';
			setTimeout(() => (submitted = false), 3000);
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
			<input
				type="text"
				bind:value={author}
				placeholder="Your name"
				class="border-gold/40 text-brown placeholder:text-brown-light/50 focus:border-gold focus:ring-gold bg-cream/50 w-full rounded-md border px-4 py-2"
				maxlength="100"
			/>
			<textarea
				bind:value={text}
				placeholder="Write your birthday message..."
				rows="4"
				class="border-gold/40 text-brown placeholder:text-brown-light/50 focus:border-gold focus:ring-gold bg-cream/50 w-full rounded-md border px-4 py-2"
				maxlength="1000"
			></textarea>
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
					<p class="text-brown-light mt-3 text-sm">
						&mdash; {msg.author}
					</p>
				</div>
			{/each}
		</div>
	{/if}
</div>
