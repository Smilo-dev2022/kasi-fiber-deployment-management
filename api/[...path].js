// Proxy all /api/* requests to an external backend defined by API_PROXY_TARGET
// Usage: set Vercel env var API_PROXY_TARGET (e.g., https://your-backend.example.com)

export default async function handler(req, res) {
  const targetBase = process.env.API_PROXY_TARGET || process.env.FASTAPI_URL || process.env.EXPRESS_URL;

  if (!targetBase) {
    res.status(500).json({
      error: "API proxy target is not configured",
      missing: ["API_PROXY_TARGET"],
      hint: "Set API_PROXY_TARGET in your Vercel Project Environment to your backend base URL",
    });
    return;
  }

  try {
    const originalUrl = req.url || "/api";
    const pathAfterApi = originalUrl.replace(/^\/api\/?/, "");

    // Construct target URL, preserving path and query string
    const targetUrl = new URL(pathAfterApi || "", targetBase.endsWith("/") ? targetBase : targetBase + "/");

    // Forward headers, excluding hop-by-hop or problematic ones
    const forwardedHeaders = {};
    for (const [key, value] of Object.entries(req.headers)) {
      if (value == null) continue;
      const lower = key.toLowerCase();
      if (lower === "host" || lower === "content-length" || lower === "accept-encoding") continue;
      forwardedHeaders[key] = value;
    }

    let bodyBuffer = undefined;
    const method = (req.method || "GET").toUpperCase();
    if (method !== "GET" && method !== "HEAD") {
      bodyBuffer = await new Promise((resolve, reject) => {
        const chunks = [];
        req.on("data", (chunk) => chunks.push(chunk));
        req.on("end", () => resolve(Buffer.concat(chunks)));
        req.on("error", reject);
      });
    }

    const upstreamResponse = await fetch(targetUrl.toString(), {
      method,
      headers: forwardedHeaders,
      // Pass undefined for no-body methods to avoid setting a body accidentally
      body: bodyBuffer,
      redirect: "manual",
    });

    // Copy status and headers
    res.status(upstreamResponse.status);
    upstreamResponse.headers.forEach((value, key) => {
      // Avoid setting content-length explicitly; Node will manage it
      if (key.toLowerCase() === "content-length") return;
      res.setHeader(key, value);
    });

    if (method === "HEAD" || upstreamResponse.status === 204) {
      res.end();
      return;
    }

    const arrayBuffer = await upstreamResponse.arrayBuffer();
    res.end(Buffer.from(arrayBuffer));
  } catch (error) {
    console.error("API proxy error:", error);
    res.status(502).json({ error: "Bad gateway", detail: String(error && error.message ? error.message : error) });
  }
}

