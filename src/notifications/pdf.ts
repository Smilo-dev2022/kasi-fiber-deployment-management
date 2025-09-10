import type { PoolClient } from 'pg';
import { loadTheme } from '../theme/theme.js';

export async function renderPdfHtml(client: PoolClient, tenantId: string, templateKey: string, data: Record<string, any>) {
  const theme = await loadTheme(client, tenantId);
  const title = data.title || '';
  const content = data.content || '';
  return `<!doctype html>
  <html>
  <head>
    <meta charset="utf-8" />
    <style>
      body { font-family: system-ui; color: #111; }
      h1 { color: ${theme.primaryColor || '#0ea5e9'} }
      footer { position: fixed; bottom: 0; font-size: 10px; color: #6b7280 }
    </style>
  </head>
  <body>
    <h1>${title}</h1>
    <div>${content}</div>
    <footer>${theme.pdfFooter || ''}</footer>
  </body>
  </html>`;
}

