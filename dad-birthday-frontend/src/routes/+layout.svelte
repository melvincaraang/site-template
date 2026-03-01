<script lang="ts">
	import '../app.css';
	import { authState } from '$lib/stores/auth.svelte';
	import Nav from '$lib/components/Nav.svelte';

	let { children } = $props();
</script>

<div class="min-h-screen bg-cream">
	{#if authState.role}
		<Nav />
	{/if}
	{@render children?.()}
</div>
