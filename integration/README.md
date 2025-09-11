# Integration Repository

Artifacts for partners and customers to integrate without source access.

## Contents

- OpenAPI spec: `openapi/openapi.json`
- Postman collection: `postman/collection.json`
- Theming schema and examples: `theming/brand.schema.json`, `theming/examples/*.brand.json`
- Environment template: `env/.env.example`
- Webhook docs and examples: `webhooks/`
- Sample data and seed scripts: `seeds/`

## Getting started

1. Obtain Docker image tags and registry access from your contact.
2. Copy `env/.env.example` and set your environment variables.
3. Import `openapi/openapi.json` into your API tooling or generate client SDKs.
4. Use `postman/collection.json` or the curl samples in `webhooks/` to test.
5. Provide a `brand.json` per tenant following `theming/brand.schema.json`.

## Security

- Do not share service keys. Use environment variables provided to you.
- Webhooks must be HMAC-signed and sent from allowlisted IPs.
- Images are immutable; deployments should pull from the registry only.