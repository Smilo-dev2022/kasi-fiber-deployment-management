import { serve } from "https://deno.land/std@0.224.0/http/server.ts";

const corsHeaders: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
};

function jsonResponse(body: unknown, init?: ResponseInit): Response {
  const headers = new Headers(init?.headers ?? {});
  headers.set("Content-Type", "application/json");
  Object.entries(corsHeaders).forEach(([k, v]) => headers.set(k, v));
  return new Response(JSON.stringify(body), { ...init, headers });
}

serve(async (req: Request): Promise<Response> => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  const url = new URL(req.url);
  const pathname = url.pathname;

  // Health route should work for both /health and /api/health
  if (req.method === "GET" && (pathname === "/health" || pathname === "/api/health")) {
    return jsonResponse({ status: "ok", time: new Date().toISOString() });
  }

  // Placeholder: add more sub-routes here to mirror former Express routes
  // Example:
  // if (req.method === "GET" && pathname === "/reports") { ... }

  return jsonResponse({ error: "Not found", path: pathname }, { status: 404 });
});

