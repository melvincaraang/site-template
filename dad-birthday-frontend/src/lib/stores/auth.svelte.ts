export type AuthRole = 'guest' | 'admin' | null;

export const authState = $state<{ role: AuthRole }>({
	role: null
});
