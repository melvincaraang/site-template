import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

// Runs against the local stack: backend/scripts/dev_server.py (codes: party / admin)
// and the Vite dev server. See playwright.config.ts.

async function checkA11y(page: Page, name: string) {
	const results = await new AxeBuilder({ page })
		.withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
		.analyze();
	const blocking = results.violations.filter(
		(v) => v.impact === 'serious' || v.impact === 'critical'
	);
	for (const v of blocking) {
		console.log(`[axe] ${name}: ${v.id} — ${v.help}`);
		for (const n of v.nodes) console.log(`    ${n.html.slice(0, 160)}`);
	}
	expect(
		blocking.map((v) => `${v.id}: ${v.help} (${v.nodes.length} nodes)`),
		`serious/critical accessibility violations on ${name}`
	).toEqual([]);
}

async function enterCode(page: Page, code: string, admin = false) {
	await page.goto('/');
	if (admin) await page.getByRole('button', { name: 'Admin login' }).click();
	await page.getByPlaceholder(admin ? 'Enter admin code' : 'Enter access code').fill(code);
	await page.getByRole('button', { name: admin ? 'Sign In' : 'Enter' }).click();
}

test('wrong code is refused', async ({ page }) => {
	await enterCode(page, 'not-the-code');
	await expect(page.getByText(/invalid code/i)).toBeVisible();
});

test('guest code opens messages and gallery; admin code opens admin', async ({ page }) => {
	await enterCode(page, 'party');
	await expect(page).toHaveURL(/\/messages$/);
	await checkA11y(page, 'messages');
	await page.goto('/gallery');
	await expect(page.getByRole('heading', { name: 'Gallery' })).toBeVisible();
	await checkA11y(page, 'gallery');
	await expect(page.getByRole('link', { name: 'Admin' })).toHaveCount(0);

	await enterCode(page, 'admin', true);
	await expect(page).toHaveURL(/\/admin$/);
	await checkA11y(page, 'admin');
});

test('sign-in page is accessible', async ({ page }) => {
	await page.goto('/');
	await expect(page.getByPlaceholder('Enter access code')).toBeVisible();
	await checkA11y(page, 'sign-in');
});

test('unauthenticated deep link redirects to sign-in', async ({ page }) => {
	await page.goto('/gallery');
	await expect(page).toHaveURL(/\/$/);
});
