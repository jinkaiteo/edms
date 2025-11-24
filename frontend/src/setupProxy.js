const { createProxyMiddleware } = require("http-proxy-middleware");

module.exports = function (app) {
  // Only proxy API routes, not frontend routes
  app.use(
    "/api",
    createProxyMiddleware({
      target: "http://localhost:8000",
      changeOrigin: true,
    })
  );
};
