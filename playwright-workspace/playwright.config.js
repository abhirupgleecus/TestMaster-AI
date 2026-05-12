import fs from 'node:fs';
import path from 'node:path';
import { defineConfig } from '@playwright/test';

const workspaceRoot = process.cwd();

function parseKeyValueFile(filePath) {
  if (!fs.existsSync(filePath)) {
    return {};
  }

  const content = fs.readFileSync(filePath, 'utf-8');
  const values = {};

  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;

    const separatorIndex = line.indexOf('=');
    if (separatorIndex === -1) continue;

    const key = line.slice(0, separatorIndex).trim();
    let value = line.slice(separatorIndex + 1).trim();

    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }

    if (key) {
      values[key] = value;
    }
  }

  return values;
}

function loadWorkspaceCredentialContext() {
  const sources = [
    path.join(workspaceRoot, '.env'),
    path.join(workspaceRoot, 'credentials.txt'),
  ];

  for (const source of sources) {
    const parsed = parseKeyValueFile(source);
    for (const [key, value] of Object.entries(parsed)) {
      if (!process.env[key] && value) {
        process.env[key] = value;
      }
    }
  }
}

loadWorkspaceCredentialContext();

const jsonReportPath = process.env.PLAYWRIGHT_JSON_REPORT_PATH || 'reports/results.json';
const htmlReportPath = process.env.PLAYWRIGHT_HTML_REPORT_PATH || 'reports/html';

export default defineConfig({
  testDir: './tests',
  timeout: 30000,
  workers: 1,
  use: {
    headless: true,
    screenshot: 'on',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
  },
  reporter: [
    ['line'],
    ['json', { outputFile: jsonReportPath }],
    ['html', { outputFolder: htmlReportPath, open: 'never' }],
  ],
});
