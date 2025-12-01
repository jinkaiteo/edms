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
  
  // Proxy WebSocket connections
  app.use(
    "/ws",
    createProxyMiddleware({
      target: "http://backend:8000",
      changeOrigin: true,
      ws: true,  // Enable WebSocket proxying
      logLevel: 'debug'
    })
  );
};
