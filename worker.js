const RELEASE = "https://github.com/bryanbrews/steingrimur-biography/releases/download/v1/";

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    // mounted at /steingrimur — map to root-relative asset paths
    let p = url.pathname.replace(/^\/steingrimur\/?/, "/");
    if (p === "/" || p === "") p = "/index.html";

    // audio proxy: GitHub serves m4b as octet-stream, which iOS Safari refuses
    // to play. Stream it through with a real audio MIME + Range passthrough.
    if (p.startsWith("/audio/")) {
      const file = p.slice("/audio/".length);
      if (!/^[A-Za-z0-9._-]+\.m4b$/.test(file)) return new Response("not found", { status: 404 });
      const upHeaders = new Headers();
      const range = req.headers.get("Range");
      if (range) upHeaders.set("Range", range);
      const up = await fetch(RELEASE + file, { headers: upHeaders, redirect: "follow" });
      if (!up.ok && up.status !== 206) return new Response("upstream error", { status: 502 });
      const h = new Headers();
      h.set("Content-Type", "audio/mp4");
      h.set("Accept-Ranges", "bytes");
      for (const k of ["Content-Length", "Content-Range", "ETag", "Last-Modified"]) {
        const v = up.headers.get(k);
        if (v) h.set(k, v);
      }
      h.set("Cache-Control", "public, max-age=3600");
      return new Response(up.body, { status: up.status, headers: h });
    }

    return env.ASSETS.fetch(new URL(p, url.origin));
  },
};
