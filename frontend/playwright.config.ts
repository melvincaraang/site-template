import { defineConfig, devices } from '@playwright/test';

// E2E runs against the local stack: the real Lambda handler (moto-backed
// DynamoDB, dev Google verifier) on :3000 and the Vite dev server on :5173,
// so the dev-only sign-in form is available.
export default defineConfig({
	testDir: 'e2e',
	timeout: 30_000,
	fullyParallel: false,
	workers: 1,
	retries: process.env.CI ? 1 : 0,
	reporter: process.env.CI ? 'github' : 'list',
	use: {
		baseURL: 'http://localhost:5173',
		trace: 'retain-on-failure',
		...devices['Desktop Chrome']
	},
	webServer: [
		{
			command: 'cd ../backend && .venv/bin/python scripts/dev_server.py',
			url: 'http://localhost:3000/api/session',
			reuseExistingServer: !process.env.CI,
			ignoreHTTPSErrors: true,
			// /api/session answers 401 when unauthenticated — that still means "up".
			timeout: 30_000
		},
		{
			command: 'npm run dev',
			url: 'http://localhost:5173',
			reuseExistingServer: !process.env.CI,
			timeout: 60_000
		}
	]
});
