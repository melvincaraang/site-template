<script lang="ts">
	import { authState } from '$lib/stores/auth.svelte';
	import { page } from '$app/stores';

	let menuOpen = $state(false);

	function isActive(path: string) {
		return $page.url.pathname === path;
	}
</script>

<nav class="border-gold/20 bg-cream/90 border-b backdrop-blur-sm">
	<div class="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
		<a href="/gallery" class="font-display text-brown text-xl font-bold">
			Dad's 80th
		</a>

		<!-- Desktop nav -->
		<div class="hidden gap-6 sm:flex">
			<a
				href="/gallery"
				class="text-brown hover:text-gold transition-colors"
				class:font-bold={isActive('/gallery')}
			>Gallery</a>
			<a
				href="/messages"
				class="text-brown hover:text-gold transition-colors"
				class:font-bold={isActive('/messages')}
			>Messages</a>
			{#if authState.role === 'admin'}
				<a
					href="/admin"
					class="text-gold hover:text-gold-light transition-colors"
					class:font-bold={isActive('/admin')}
				>Admin</a>
			{/if}
		</div>

		<!-- Mobile hamburger -->
		<button class="text-brown sm:hidden" onclick={() => (menuOpen = !menuOpen)}>
			<svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				{#if menuOpen}
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				{:else}
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
				{/if}
			</svg>
		</button>
	</div>

	<!-- Mobile menu -->
	{#if menuOpen}
		<div class="border-gold/20 border-t px-4 pb-3 sm:hidden">
			<a href="/gallery" class="text-brown block py-2" onclick={() => (menuOpen = false)}>Gallery</a>
			<a href="/messages" class="text-brown block py-2" onclick={() => (menuOpen = false)}>Messages</a>
			{#if authState.role === 'admin'}
				<a href="/admin" class="text-gold block py-2" onclick={() => (menuOpen = false)}>Admin</a>
			{/if}
		</div>
	{/if}
</nav>
