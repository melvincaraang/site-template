<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import Lightbox from '$lib/components/Lightbox.svelte';

	type MediaItem = { id: string; url: string; type: string; caption: string; order: number };

	let media = $state<MediaItem[]>([]);
	let loading = $state(true);
	let selectedItem = $state<MediaItem | null>(null);

	onMount(async () => {
		try {
			const data = await api.getMedia();
			media = data.media;
		} catch (e) {
			console.error('Failed to load media', e);
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>Gallery</title>
</svelte:head>

<div class="mx-auto max-w-6xl px-4 py-8">
	<h1 class="font-display text-primary mb-8 text-center text-4xl">Gallery</h1>

	<!-- Messages link banner -->
	<a
		href="/messages"
		class="border-accent/40 bg-surface-dark/80 text-primary hover:bg-accent/10 mb-8 flex items-center justify-center gap-3 rounded-lg border px-5 py-4 transition-colors"
	>
		<svg class="h-5 w-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"
			/>
		</svg>
		<span class="font-display text-lg">Leave a Message</span>
		<svg class="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
		</svg>
	</a>

	{#if loading}
		<p class="text-primary/70 text-center text-lg italic">Loading...</p>
	{:else if media.length === 0}
		<p class="text-primary/70 text-center text-lg">No photos yet. Check back soon!</p>
	{:else}
		<div class="columns-1 gap-4 sm:columns-2 lg:columns-3">
			{#each media as item (item.id)}
				<button
					class="group mb-4 block w-full overflow-hidden rounded-lg border-4 border-white bg-white shadow-md transition-transform hover:scale-[1.02]"
					onclick={() => (selectedItem = item)}
				>
					{#if item.type === 'video'}
						<div class="relative">
							<!-- svelte-ignore a11y_media_has_caption -->
							<video preload="metadata" class="w-full transition-all" src={item.url}></video>
							<div class="absolute inset-0 flex items-center justify-center">
								<div class="rounded-full bg-black/50 p-3 text-white">
									<svg class="h-8 w-8" fill="currentColor" viewBox="0 0 24 24">
										<path d="M8 5v14l11-7z" />
									</svg>
								</div>
							</div>
						</div>
					{:else}
						<img src={item.url} alt={item.caption} class="w-full transition-all" loading="lazy" />
					{/if}
					{#if item.caption}
						<p class="text-primary px-3 py-2 text-lg">{item.caption}</p>
					{/if}
				</button>
			{/each}
		</div>
	{/if}
</div>

{#if selectedItem}
	<Lightbox item={selectedItem} onclose={() => (selectedItem = null)} />
{/if}
