const RELEASE = "https://github.com/bryanbrews/steingrimur-biography/releases/download/v1/";

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    // mounted at /steingrimur — map to root-relative asset paths
    let p = url.pathname.replace(/^\/steingrimur\/?/, "/");
    if (p === "/" || p === "") p = "/index.html";

    // media proxy: GitHub serves files as octet-stream. iOS needs real MIME
    // types — audio/mp4 to play m4b, application/epub+zip so Books accepts
    // epubs handed over via the itms-bookss:// scheme.
    if (p.startsWith("/audio/") || p.startsWith("/books/")) {
      const isBook = p.startsWith("/books/");
      const file = p.slice("/audio/".length);
      if (!/^[A-Za-z0-9._-]+\.(m4b|epub)$/.test(file)) return new Response("not found", { status: 404 });
      const upHeaders = new Headers();
      const range = req.headers.get("Range");
      if (range) upHeaders.set("Range", range);
      const up = await fetch(RELEASE + file, { headers: upHeaders, redirect: "follow" });
      if (!up.ok && up.status !== 206) return new Response("upstream error", { status: 502 });
      const h = new Headers();
      h.set("Content-Type", isBook ? "application/epub+zip" : "audio/mp4");
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
