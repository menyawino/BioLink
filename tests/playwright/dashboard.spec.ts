import { test, expect } from '@playwright/test';

async function login(page: import('@playwright/test').Page) {
  await page.goto('http://localhost:3000');
  await expect(page.getByRole('heading', { name: 'Sign In' })).toBeVisible();
  await page.getByLabel('Username').fill('admin');
  await page.getByLabel('Password').fill('admin');
  await page.getByRole('button', { name: 'Sign In' }).click();
}

test('Login smoke: sign in and load workspace navigation', async ({ page }) => {
  await login(page);

  await expect(page.getByText('MYF Biolink')).toBeVisible();
  await expect(page.getByText('Patient Registry').first()).toBeVisible();
  await expect(page.getByText('Registry Analytics').first()).toBeVisible();
});

test('Chart Builder: embedded Superset workspace loads', async ({ page }) => {
  await login(page);

  const chartBuilderNav = page.locator('.app-sidebar-shell').getByRole('button', { name: /Chart Builder/i });
  await chartBuilderNav.click();

  await expect(chartBuilderNav).toHaveAttribute('data-active', 'true');

  const frame = page.locator('iframe[title="Superset"]');
  await expect(frame).toBeVisible();
  await expect(frame).toHaveAttribute('src', /8088/);
});
