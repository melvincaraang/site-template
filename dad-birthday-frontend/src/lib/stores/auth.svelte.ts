export type AuthRole = 'guest' | 'admin' | null;

export const authState = $state<{ role: AuthRole; checking: boolean }>({
	role: null,
	checking: true
});
