export default {
  async fetch(request) {
    const backend = "https://bigbrain-backend.onrender.com";
    const url = new URL(request.url);
    const target = backend + url.pathname + url.search;

    return fetch(target, {
      method: request.method,
      headers: request.headers,
      body: request.body
    });
  }
};
