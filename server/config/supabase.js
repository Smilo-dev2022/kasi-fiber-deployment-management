const { createClient } = require('@supabase/supabase-js');

const SUPABASE_URL = process.env.SUPABASE_URL || 'https://bigbujrinohnmoxuidbx.supabase.co';
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJpZ2J1anJpbm9obm1veHVpZGJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc1NzkxNTAsImV4cCI6MjA3MzE1NTE1MH0.LnszUQtZO9jCJfr5rSfPqGqYHWok6NjrOSWGh7NbdWw';

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.warn('Supabase: SUPABASE_URL or SUPABASE_ANON_KEY not configured');
}

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

module.exports = { supabase, SUPABASE_URL, SUPABASE_ANON_KEY };

