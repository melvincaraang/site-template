<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { authState } from '$lib/stores/auth.svelte';
	import { api } from '$lib/api';
	import Nav from '$lib/components/Nav.svelte';

	let { children } = $props();

	onMount(async () => {
		if (!authState.role) {
			try {
				const data = await api.getSession();
				authState.role = data.role;
			} catch {
				// No valid session — leave role as null
			} finally {
				authState.checking = false;
			}
		}
	});
</script>

<div class="bg-cream min-h-screen">
	{#if authState.role}
		<Nav />
	{/if}
	{@render children?.()}
</div>
