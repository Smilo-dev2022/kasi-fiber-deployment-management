import { test, expect } from '@playwright/test';

test('can load login and show heading', async ({ page }) => {
  await page.goto('/login');
  await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();
});

