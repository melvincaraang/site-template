<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { authState } from '$lib/stores/auth.svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';

	let code = $state('');
	let error = $state('');
	let loading = $state(false);
	let adminMode = $state(false);

	// Landing page = logout: clear cookie + in-memory state
	onMount(async () => {
		authState.role = null;
		authState.checking = false;
		await api.logout().catch(() => {});

		const token = $page.url.searchParams.get('token');
		if (token) {
			authState.checking = true;
			verifyToken(token);
		}
	});

	async function verifyToken(token: string) {
		try {
			await api.verify({ token });
			authState.role = 'guest';
			goto('/messages');
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
			goto(adminMode ? '/admin' : '/messages');
		} catch {
			error = adminMode ? 'Invalid admin code.' : 'Invalid code. Please try again.';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>My Site</title>
</svelte:head>

{#if authState.checking}
	<div class="flex min-h-screen items-center justify-center">
		<p class="text-primary/60 text-xl italic">Checking your invitation...</p>
	</div>
{:else}
	<div class="flex min-h-screen flex-col items-center justify-center px-4">
		<div class="w-full max-w-md text-center">
			<h1 class="font-display text-accent mb-2 text-5xl font-bold">Welcome</h1>
			<p class="font-display text-primary mb-8 text-xl">Enter your code to continue</p>

			<div class="border-accent/30 rounded-lg border bg-white/80 p-8 shadow-lg backdrop-blur-sm">
				<p class="text-primary/70 mb-6 text-lg">
					{adminMode ? 'Enter the admin code' : 'Enter the access code'}
				</p>

				<form onsubmit={handleSubmit} class="space-y-4">
					<input
						type={adminMode ? 'password' : 'text'}
						bind:value={code}
						placeholder={adminMode ? 'Enter admin code' : 'Enter access code'}
						class="border-accent/40 text-primary placeholder:text-primary/40 focus:border-accent focus:ring-accent bg-surface/50 w-full rounded-md border px-4 py-3 text-center text-lg"
					/>

					{#if error}
						<p class="text-sm text-red-600">{error}</p>
					{/if}

					<button
						type="submit"
						disabled={loading || !code.trim()}
						class="bg-accent hover:bg-accent-light text-white w-full rounded-md px-6 py-3 text-lg transition-colors disabled:opacity-50"
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
					class="text-primary/40 hover:text-primary/70 mt-4 text-sm underline"
				>
					{adminMode ? 'Back to guest login' : 'Admin login'}
				</button>
			</div>
		</div>
	</div>
{/if}
