# Tenant Theming and White-Labeling

- No code access required for partners
- Theme via tenant settings and `brand.json`

## Tenant Settings
- Logo URL or upload reference
- Primary/secondary colors
- Domain and email sender
- PDF header/footer elements

## brand.json Schema
```json
{
  "$schema": "./brand.schema.json",
  "name": "Acme Fiber",
  "logo": "https://cdn.example.com/acme/logo.png",
  "colors": {
    "primary": "#0ea5e9",
    "secondary": "#111827",
    "accent": "#22c55e"
  },
  "domain": "acme.example.com",
  "pdf": {
    "headerText": "Acme Fiber",
    "footerText": "Confidential"
  }
}
```

- Provide a partner portal to submit updates; ops reviews and merges
- Build pipeline bakes assets per tenant at image build time