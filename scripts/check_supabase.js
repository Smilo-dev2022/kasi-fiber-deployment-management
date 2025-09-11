#!/usr/bin/env node
require('dotenv').config();
const https = require('https');

const supabaseUrl = process.env.SUPABASE_URL;
const anonKey = process.env.SUPABASE_ANON_KEY;
if (!supabaseUrl) {
	console.error('SUPABASE_URL is not set');
	process.exit(1);
}

const { hostname, pathname, search } = new URL(`${supabaseUrl.replace(/\/$/, '')}/auth/v1/health`);

const options = {
	method: 'GET',
	hostname,
	path: pathname + (search || ''),
	headers: {
		Accept: 'application/json',
		...(anonKey ? { apikey: anonKey, Authorization: `Bearer ${anonKey}` } : {}),
	},
};

const req = https.request(options, (res) => {
	let body = '';
	res.on('data', (chunk) => (body += chunk));
	res.on('end', () => {
		console.log(`Supabase auth health status: ${res.statusCode}`);
		if (res.statusCode === 200) {
			console.log('Supabase is reachable.');
			process.exit(0);
		} else {
			console.error(body || 'Non-200 response');
			process.exit(1);
		}
	});
});

req.on('error', (err) => {
	console.error('Health check error:', err.message);
	process.exit(1);
});

req.end();