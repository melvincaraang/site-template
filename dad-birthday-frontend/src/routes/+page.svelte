<script lang="ts">
	import { api } from '$lib/api';
	import { authState } from '$lib/stores/auth.svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';

	let code = $state('');
	let error = $state('');
	let loading = $state(false);
	let adminMode = $state(false);

	// Landing page = logout + check for token
	$effect(() => {
		authState.role = null;
		const token = $page.url.searchParams.get('token');
		if (token) {
			verifyToken(token);
		} else {
			authState.checking = false;
		}
	});

	async function verifyToken(token: string) {
		try {
			await api.verify({ token });
			authState.role = 'guest';
			goto('/gallery');
		} catch {
			authState.checking = false;
			error = 'This link has expired or is invalid.';
		}
	}

	async function handleSubmit() {
		if (!code.trim()) return;
		loading = true;
		error = '';
		try {
			await api.verify({ code: code.trim(), admin: adminMode });
			authState.role = adminMode ? 'admin' : 'guest';
			goto(adminMode ? '/admin' : '/gallery');
		} catch {
			error = adminMode ? 'Invalid admin code.' : 'Invalid code. Please try again.';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Dad's 80th Birthday</title>
</svelte:head>

{#if authState.checking}
	<div class="flex min-h-screen items-center justify-center">
		<p class="text-brown-light text-xl italic">Checking your invitation...</p>
	</div>
{:else}
	<div class="flex min-h-screen flex-col items-center justify-center px-4">
		<div class="w-full max-w-md text-center">
			<h1 class="font-display text-gold mb-2 text-6xl font-bold">80</h1>
			<p class="font-display text-brown mb-8 text-2xl">Years of Love & Memories</p>

			<div class="border-gold/30 rounded-lg border bg-white/80 p-8 shadow-lg backdrop-blur-sm">
				<p class="text-brown-light mb-6 text-lg">
					{adminMode ? 'Enter the admin code' : 'Enter the party code to view the celebration'}
				</p>

				<form onsubmit={handleSubmit} class="space-y-4">
					<input
						type={adminMode ? 'password' : 'text'}
						bind:value={code}
						placeholder={adminMode ? 'Enter admin code' : 'Enter party code'}
						class="border-gold/40 text-brown placeholder:text-brown-light/50 focus:border-gold focus:ring-gold bg-cream/50 w-full rounded-md border px-4 py-3 text-center text-lg"
					/>

					{#if error}
						<p class="text-sm text-red-600">{error}</p>
					{/if}

					<button
						type="submit"
						disabled={loading || !code.trim()}
						class="bg-brown hover:bg-brown-light text-cream w-full rounded-md px-6 py-3 text-lg transition-colors disabled:opacity-50"
					>
						{loading ? 'Verifying...' : adminMode ? 'Sign In' : 'Enter'}
					</button>
				</form>

				<button
					type="button"
					onclick={() => {
						adminMode = !adminMode;
						code = '';
						error = '';
					}}
					class="text-brown-light/60 hover:text-brown-light mt-4 text-sm underline"
				>
					{adminMode ? 'Back to party login' : 'Admin login'}
				</button>
			</div>
		</div>
	</div>
{/if}
