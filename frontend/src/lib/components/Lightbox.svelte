<script lang="ts">
	import VideoPlayer from './VideoPlayer.svelte';

	type MediaItem = { id: string; url: string; type: string; caption: string };

	let {
		item,
		onclose
	}: {
		item: MediaItem;
		onclose: () => void;
	} = $props();

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') onclose();
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4" onclick={onclose}>
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div class="relative max-h-[90vh] max-w-4xl" onclick={(e) => e.stopPropagation()}>
		<button
			class="hover:text-accent absolute -top-10 right-0 text-2xl text-white"
			onclick={onclose}
		>
			&times; Close
		</button>

		{#if item.type === 'video'}
			<VideoPlayer src={item.url} class="max-h-[80vh] rounded-lg" />
		{:else}
			<img src={item.url} alt={item.caption} class="max-h-[80vh] rounded-lg object-contain" />
		{/if}

		{#if item.caption}
			<p class="mt-3 text-center text-xl text-white">
				{item.caption}
			</p>
		{/if}
	</div>
</div>
