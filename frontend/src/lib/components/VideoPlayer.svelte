<script lang="ts">
	let { src, class: className = '' }: { src: string; class?: string } = $props();
</script>

<!-- svelte-ignore a11y_media_has_caption -->
<video controls preload="metadata" class={className} {src}>
	Your browser does not support the video tag.
</video>
