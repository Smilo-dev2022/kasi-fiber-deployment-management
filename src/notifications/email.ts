import type { PoolClient } from 'pg';
import { loadTheme } from '../theme/theme.js';

export async function renderEmailHtml(client: PoolClient, tenantId: string, templateKey: string, data: Record<string, any>) {
  const theme = await loadTheme(client, tenantId);
  const title = data.title || '';
  const body = data.body || '';
  return `<!doctype html>
  <html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${escapeHtml(title)}</title>
  </head>
  <body style="font-family: system-ui; color: #111;">
    <div style="max-width:640px;margin:0 auto;border:1px solid #e5e7eb">
      <div style="padding:16px;background:${theme.primaryColor || '#0ea5e9'};color:white;">
        <img src="${theme.logoUrl || ''}" alt="logo" style="height:32px" />
      </div>
      <div style="padding:16px">
        ${body}
      </div>
      <div style="padding:16px;background:#f9fafb;color:#6b7280;font-size:12px">
        ${theme.pdfFooter || ''}
      </div>
    </div>
  </body>
  </html>`;
}

function escapeHtml(input: string) {
  return input.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c] as string));
}

