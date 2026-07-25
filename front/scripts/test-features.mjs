#!/usr/bin/env node
/**
 * Puppeteer smoke: public /features marketing page.
 * Asserts page shell (hero title, at least one category), register CTA or home nav, no pageerrors.
 *
 * Usage (from repo root):
 *   BASE_URL=http://127.0.0.1:4202 npm run test:features --prefix front
 *   node front/scripts/test-features.mjs
 *
 * Env:
 *   BASE_URL   App URL (default: auto-detect port 4203, 4202, 4200 or http://127.0.0.1:4202)
 *   HEADLESS   Default headless; set 0, false, or no for a visible browser.
 */

import { isHeadless } from './puppeteer-headless.mjs';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);
const puppeteer = require('puppeteer-core');

const CHROME_PATH =
  process.env.PUPPETEER_EXECUTABLE_PATH ||
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

async function resolveBaseUrl() {
  if (process.env.BASE_URL) return process.env.BASE_URL.replace(/\/$/, '');
  for (const port of [4203, 4202, 4200]) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/`, {
        method: 'head',
        signal: AbortSignal.timeout(1500),
      });
      if (res.ok || res.status < 500) return `http://127.0.0.1:${port}`;
    } catch (_) {}
  }
  return 'http://127.0.0.1:4202';
}

async function main() {
  const baseUrl = await resolveBaseUrl();
  const headless = isHeadless();
  console.log('BASE_URL:', baseUrl);
  console.log('Headless:', headless);
  console.log('---');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless,
    defaultViewport: headless ? { width: 1280, height: 720 } : null,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();
  const pageErrors = [];
  const badResponses = [];
  page.on('pageerror', (err) => pageErrors.push(err.message));
  page.on('response', (res) => {
    const u = res.url();
    if (!u.includes('/features') && !u.endsWith('/features')) return;
    if (res.status() >= 400) badResponses.push(`${res.status()} ${u}`);
  });

  try {
    console.log('1. Loading /features...');
    const featuresUrl = new URL('/features', baseUrl).href;
    const response = await page.goto(featuresUrl, {
      waitUntil: 'networkidle2',
      timeout: 20000,
    });
    if (!response || response.status() >= 400) {
      console.error('FAIL: HTTP status for /features:', response?.status());
      process.exit(1);
    }
    const path = new URL(page.url()).pathname;
    if (path !== '/features' && !path.startsWith('/features/')) {
      console.error('FAIL: Expected path /features, got:', page.url());
      process.exit(1);
    }

    console.log('2. Waiting for features page shell...');
    await page.waitForSelector('.features-page', { timeout: 15000 });
    await page.waitForSelector('.features-hero__title', { timeout: 10000 });
    await page.waitForSelector('.features-category', { timeout: 10000 });

    const shell = await page.evaluate(() => {
      const titleEl = document.querySelector('.features-hero__title');
      const title = (titleEl?.textContent || '').trim();
      const categories = document.querySelectorAll('.features-category').length;
      const brandHome = document.querySelector('a.features-nav__brand');
      const brandHref = brandHome?.getAttribute('href') || '';
      const registerCtas = Array.from(
        document.querySelectorAll('a.features-nav__cta, a.features-btn--primary')
      );
      const registerOk = registerCtas.some((a) => {
        const href = a.getAttribute('href') || '';
        return href.includes('/register');
      });
      const rawKeyDump =
        title.includes('FEATURES_PAGE.') ||
        (document.body?.innerText || '').includes('FEATURES_PAGE.TITLE');
      return {
        title,
        categories,
        brandHref,
        registerOk,
        rawKeyDump,
      };
    });

    if (!shell.title || shell.rawKeyDump) {
      console.error(
        'FAIL: Hero title missing or untranslated FEATURES_PAGE key. Got:',
        JSON.stringify(shell.title)
      );
      process.exit(1);
    }
    console.log('   Hero title:', shell.title);

    if (shell.categories < 1) {
      console.error('FAIL: Expected at least one .features-category section.');
      process.exit(1);
    }
    console.log('   Category sections:', shell.categories);

    // Angular routerLink="/" usually renders href="/"
    let brandIsHome = false;
    try {
      brandIsHome =
        shell.brandHref === '/' ||
        shell.brandHref === '' ||
        new URL(shell.brandHref, baseUrl).pathname === '/';
    } catch {
      brandIsHome = false;
    }
    if (!brandIsHome && !shell.registerOk) {
      console.error(
        'FAIL: Expected brand link to / or a register CTA. brandHref=',
        JSON.stringify(shell.brandHref),
        'registerOk=',
        shell.registerOk
      );
      process.exit(1);
    }
    if (brandIsHome) console.log('   Brand nav to home: OK');
    if (shell.registerOk) console.log('   Register CTA: OK');

    if (badResponses.length) {
      console.error('FAIL: Bad HTTP for /features document:', badResponses);
      process.exit(1);
    }
    if (pageErrors.length) {
      console.error('FAIL: pageerror(s):', pageErrors);
      process.exit(1);
    }

    await browser.close();
    console.log('\n>>> RESULT: /features loads with hero, categories, and nav/CTA.');
    process.exit(0);
  } catch (err) {
    console.error('Error:', err.message);
    await browser.close();
    process.exit(1);
  }
}

main();
