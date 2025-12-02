const { createProxyMiddleware } = require("http-proxy-middleware");

module.exports = function (app) {
  // Proxy API routes
  app.use(
    "/api",
    createProxyMiddleware({
      target: "http://backend:8000",
      changeOrigin: true,
      logLevel: 'debug'
    })
  );
  
  // Proxy health endpoint
  app.use(
    "/health",
    createProxyMiddleware({
      target: "http://backend:8000", 
      changeOrigin: true,
      logLevel: 'debug'
    })
  );
  
  // WebSocket proxy removed - HTTP polling used instead
};
