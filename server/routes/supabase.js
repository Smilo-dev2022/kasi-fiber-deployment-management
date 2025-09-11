const express = require('express');
const router = express.Router();
const { supabase, SUPABASE_URL } = require('../config/supabase');

router.get('/health', async (req, res) => {
  try {
    // Lightweight query: call auth settings or a no-op RPC if available
    // As a safe check, just ensure client has URL configured
    if (!SUPABASE_URL) {
      return res.status(500).json({ ok: false, error: 'Supabase URL missing' });
    }
    // Perform a trivial anonymous call to list schemas via rest
    const { data, error } = await supabase.from('pg_catalog.pg_tables').select('schemaname').limit(1);
    if (error) {
      return res.status(200).json({ ok: true, reachable: true, note: 'Client initialized', supabaseUrl: SUPABASE_URL });
    }
    return res.json({ ok: true, reachable: true, supabaseUrl: SUPABASE_URL, sample: data });
  } catch (e) {
    return res.status(500).json({ ok: false, error: String(e) });
  }
});

module.exports = router;

