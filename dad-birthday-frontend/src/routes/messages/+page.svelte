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

	onMount(async () => {
		try {
			const data = await api.getMessages();
			messages = data.messages;
		} catch (e) {
			console.error('Failed to load messages', e);
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
			setTimeout(() => (submitted = false), 3000);
		} catch (e) {
			console.error('Failed to post message', e);
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

	<!-- Message form -->
	<div class="mb-10 rounded-lg border border-gold/30 bg-white/80 p-6 shadow-md">
		<h2 class="font-display text-brown mb-4 text-2xl">Leave a Message</h2>
		<form onsubmit={handleSubmit} class="space-y-4">
			<input
				type="text"
				bind:value={author}
				placeholder="Your name"
				class="border-gold/40 text-brown placeholder:text-brown-light/50 focus:border-gold focus:ring-gold w-full rounded-md border bg-cream/50 px-4 py-2"
				maxlength="100"
			/>
			<textarea
				bind:value={text}
				placeholder="Write your birthday message..."
				rows="4"
				class="border-gold/40 text-brown placeholder:text-brown-light/50 focus:border-gold focus:ring-gold w-full rounded-md border bg-cream/50 px-4 py-2"
				maxlength="1000"
			></textarea>
			<button
				type="submit"
				disabled={submitting || !author.trim() || !text.trim()}
				class="bg-brown hover:bg-brown-light rounded-md px-6 py-2 text-cream transition-colors disabled:opacity-50"
			>
				{submitting ? 'Sending...' : 'Send Birthday Wish'}
			</button>
			{#if submitted}
				<p class="text-gold text-sm">Thank you for your message!</p>
			{/if}
		</form>
	</div>

	<!-- Message wall -->
	{#if loading}
		<p class="text-brown-light text-center italic">Loading messages...</p>
	{:else if messages.length === 0}
		<p class="text-brown-light text-center">No messages yet. Be the first!</p>
	{:else}
		<div class="space-y-4">
			{#each messages as msg (msg.id)}
				<div class="rounded-lg border border-gold/20 bg-white/70 p-5 shadow-sm">
					<p class="font-handwriting text-brown text-xl leading-relaxed">{msg.text}</p>
					<p class="text-brown-light mt-3 text-sm">
						&mdash; {msg.author}
					</p>
				</div>
			{/each}
		</div>
	{/if}
</div>
