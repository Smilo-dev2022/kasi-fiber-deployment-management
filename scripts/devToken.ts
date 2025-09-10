import 'dotenv/config';
import { issueDevToken } from '../src/auth/devToken.js';

const args = Object.fromEntries(process.argv.slice(2).map(kv => {
  const [k, v] = kv.replace(/^--/, '').split('=');
  return [k, v ?? ''];
}));

const tenantId = args.tenant || args.tenant_id || args.t;
const userId = args.user || args.user_id || args.u || 'dev-user';
if (!tenantId) {
  console.error('Usage: npm run devtoken -- --tenant=<tenant_uuid> [--user=<user_id>]');
  process.exit(1);
}
const token = issueDevToken(tenantId, userId);
console.log(token);

