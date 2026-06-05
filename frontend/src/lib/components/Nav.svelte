<script lang="ts">
	import { authState } from '$lib/stores/auth.svelte';
	import { page } from '$app/stores';

	let menuOpen = $state(false);

	function isActive(path: string) {
		return $page.url.pathname === path;
	}
</script>

<nav class="border-accent/20 bg-surface/90 border-b backdrop-blur-sm">
	<div class="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
		<a href="/messages" class="font-display text-primary text-xl font-bold"> My Site </a>

		<!-- Desktop nav -->
		<div class="hidden gap-6 sm:flex">
			<a
				href="/messages"
				class="text-primary hover:text-accent transition-colors"
				class:font-bold={isActive('/messages')}>Messages</a
			>
			<a
				href="/gallery"
				class="text-primary hover:text-accent transition-colors"
				class:font-bold={isActive('/gallery')}>Gallery</a
			>
			{#if authState.role === 'admin'}
				<a
					href="/admin"
					class="text-accent hover:text-accent-light transition-colors"
					class:font-bold={isActive('/admin')}>Admin</a
				>
			{/if}
			<a href="/" class="text-primary/60 hover:text-primary transition-colors">Logout</a>
		</div>

		<!-- Mobile hamburger -->
		<button class="text-primary p-2 sm:hidden" onclick={() => (menuOpen = !menuOpen)}>
			<svg class="h-7 w-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				{#if menuOpen}
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M6 18L18 6M6 6l12 12"
					/>
				{:else}
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M4 6h16M4 12h16M4 18h16"
					/>
				{/if}
			</svg>
		</button>
	</div>

	<!-- Mobile menu -->
	{#if menuOpen}
		<div class="border-accent/20 border-t px-4 pb-3 sm:hidden">
			<a href="/messages" class="text-primary block py-2" onclick={() => (menuOpen = false)}
				>Messages</a
			>
			<a href="/gallery" class="text-primary block py-2" onclick={() => (menuOpen = false)}>Gallery</a
			>
			{#if authState.role === 'admin'}
				<a href="/admin" class="text-accent block py-2" onclick={() => (menuOpen = false)}>Admin</a>
			{/if}
			<a href="/" class="text-primary/60 block py-2" onclick={() => (menuOpen = false)}>Logout</a>
		</div>
	{/if}
</nav>
