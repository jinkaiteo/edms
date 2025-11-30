const { createProxyMiddleware } = require("http-proxy-middleware");

module.exports = function (app) {
  // Proxy API routes
  app.use(
    "/api",
    createProxyMiddleware({
      target: process.env.PROXY_TARGET || "http://backend:8000",
      changeOrigin: true,
      logLevel: 'debug'
    })
  );
  
  // Proxy health endpoint
  app.use(
    "/health",
    createProxyMiddleware({
      target: process.env.PROXY_TARGET || "http://backend:8000",
      changeOrigin: true,
      logLevel: 'debug'
    })
  );
  
  // Note: WebSocket connections bypass proxy and connect directly to backend
};
