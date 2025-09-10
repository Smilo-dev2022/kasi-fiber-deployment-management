### White-label Guide

- Remove vendor names from UI, emails, PDFs
- Theme variables: colors, logo, favicon, PDF footer, sender IDs
- Mobile: app icon set and splash screens per tenant bundle
- Email/SMS sender IDs configurable per tenant

Theme loading

- Fetch `/theme` to render UI and inject into templates
- For PDFs/emails, resolve at render-time using `tenant_id`

