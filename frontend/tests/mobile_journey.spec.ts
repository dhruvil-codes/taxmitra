import { test, expect, Page } from '@playwright/test';

async function runNoticeJourney(page: Page) {
  // 1. Landing Page
  await page.goto('/');
  
  // 2. Demo Login
  await page.locator('.tm-open, button:has-text("Try a sample notice")').first().click();
  await expect(page).toHaveURL(/.*login/);
  
  // 3. Citizen Selection (Aarav Sharma)
  await page.locator('.app-card:has-text("Aarav Sharma") button').click();
  await expect(page).toHaveURL(/.*notices/);
  
  // 4. Select notice N-2026-001 (143(1)(a))
  await page.locator('a[href="/notices/N-2026-001"]').click();
  await expect(page).toHaveURL(/.*notices\/N-2026-001/);
  
  // 5. Step 01: Understand
  await expect(page.locator('.screen-context-step:has-text("Understand")').first()).toBeVisible();
  await page.locator('a:has-text("Continue →"), button:has-text("Continue →")').click();
  
  // 6. Step 02: Questions
  for (let i = 0; i < 3; i++) {
    await expect(page.locator('.screen-context-step:has-text("Question")').first()).toBeVisible();
    await page.locator('label.journey-answer:has-text("Yes")').first().click();
    await page.locator('button:has-text("Continue"), button:has-text("आगे बढ़ें")').click();
  }
  
  // Step 03: Answer the Notice (if notice requisitions present)
  const hasAnswerNotice = await page.locator('.screen-context-step:has-text("Answer the Notice")').first().isVisible().catch(() => false);
  if (hasAnswerNotice) {
    await page.locator('.journey-answer').first().click();
    await page.locator('button:has-text("Continue"), button:has-text("आगे बढ़ें")').click();
  }
  
  // 7. Step 04: Documents (if evidence is required) or Step 05: Response Draft
  const hasDocs = await page.locator('.screen-context-step:has-text("Documents")').first().isVisible().catch(() => false);
  if (hasDocs) {
    await page.locator('button:has-text("Continue to response →")').click();
  }
  
  // 8. Step 04: Response Draft
  await expect(page.locator('.screen-context-step:has-text("Response")').first()).toBeVisible();
  await page.locator('button:has-text("Review & approve →")').click();
  
  // 9. Step 05: Human Review & Approval
  await expect(page.locator('.screen-context-step:has-text("Review")').first()).toBeVisible();
  await page.locator('input[type="checkbox"]').check();
  await page.locator('button:has-text("See portal submission steps →")').click();
  
  // 10. Step 06: Act / Portal Navigation
  await expect(page.locator('.screen-context-step:has-text("Act")').first()).toBeVisible();
  
  // Verify no horizontal overflow across the page
  const bodyWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  const viewportWidth = await page.evaluate(() => window.innerWidth);
  expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 1);
}

test.describe('Mobile Viewport - 375x812 (iPhone SE)', () => {
  test.use({ viewport: { width: 375, height: 812 } });

  test('Complete journey on iPhone SE viewport without clipping', async ({ page }) => {
    await runNoticeJourney(page);
  });
});

test.describe('Mobile Viewport - 390x844 (iPhone 12/13/14)', () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test('Complete journey on iPhone 12/13/14 viewport', async ({ page }) => {
    await runNoticeJourney(page);
  });
});

test.describe('Mobile Viewport - 430x932 (iPhone 14/15/16 Pro Max)', () => {
  test.use({ viewport: { width: 430, height: 932 } });

  test('Complete journey on iPhone Pro Max viewport', async ({ page }) => {
    await runNoticeJourney(page);
  });
});

test.describe('Desktop Viewport - 1366x768 (Standard Laptop)', () => {
  test.use({ viewport: { width: 1366, height: 768 } });

  test('Complete journey on 1366x768 laptop viewport', async ({ page }) => {
    await runNoticeJourney(page);
  });
});

test.describe('Desktop Viewport - 1920x1080 (Full HD)', () => {
  test.use({ viewport: { width: 1920, height: 1080 } });

  test('Complete journey on 1920x1080 Full HD viewport', async ({ page }) => {
    await runNoticeJourney(page);
  });
});