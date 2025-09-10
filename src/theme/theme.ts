import type { PoolClient } from 'pg';

export type Theme = {
  primaryColor?: string | null;
  secondaryColor?: string | null;
  logoUrl?: string | null;
  faviconUrl?: string | null;
  emailSenderName?: string | null;
  emailSenderId?: string | null;
  pdfFooter?: string | null;
};

export async function loadTheme(client: PoolClient, tenantId: string): Promise<Theme> {
  const { rows } = await client.query('select theme from tenants where id = $1', [tenantId]);
  const base = rows[0]?.theme || {};
  const override = await client.query('select primary_color, secondary_color, logo_url, favicon_url, email_sender_name, email_sender_id, pdf_footer from themes where tenant_id = $1', [tenantId]);
  const o = override.rows[0] || {};
  return {
    primaryColor: o.primary_color ?? base.primaryColor ?? '#0ea5e9',
    secondaryColor: o.secondary_color ?? base.secondaryColor ?? '#111827',
    logoUrl: o.logo_url ?? base.logoUrl ?? null,
    faviconUrl: o.favicon_url ?? base.faviconUrl ?? null,
    emailSenderName: o.email_sender_name ?? base.emailSenderName ?? null,
    emailSenderId: o.email_sender_id ?? base.emailSenderId ?? null,
    pdfFooter: o.pdf_footer ?? base.pdfFooter ?? ''
  } as Theme;
}

