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
	<title>Gallery - Dad's 80th Birthday</title>
</svelte:head>

<div class="mx-auto max-w-6xl px-4 py-8">
	<h1 class="font-display text-brown mb-8 text-center text-4xl">Memories</h1>

	{#if loading}
		<p class="text-brown-light text-center text-lg italic">Loading memories...</p>
	{:else if media.length === 0}
		<p class="text-brown-light text-center text-lg">No photos yet. Check back soon!</p>
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
							<video
								preload="metadata"
								class="w-full sepia-[.3] transition-all group-hover:sepia-0"
								src={item.url}
							></video>
							<div class="absolute inset-0 flex items-center justify-center">
								<div class="rounded-full bg-black/50 p-3 text-white">
									<svg class="h-8 w-8" fill="currentColor" viewBox="0 0 24 24">
										<path d="M8 5v14l11-7z" />
									</svg>
								</div>
							</div>
						</div>
					{:else}
						<img
							src={item.url}
							alt={item.caption}
							class="w-full sepia-[.3] transition-all group-hover:sepia-0"
							loading="lazy"
						/>
					{/if}
					{#if item.caption}
						<p class="font-handwriting text-brown px-3 py-2 text-lg">{item.caption}</p>
					{/if}
				</button>
			{/each}
		</div>
	{/if}
</div>

{#if selectedItem}
	<Lightbox item={selectedItem} onclose={() => (selectedItem = null)} />
{/if}
