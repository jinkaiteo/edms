const { createProxyMiddleware } = require("http-proxy-middleware");

module.exports = function (app) {
  // Docker container networking fix
  // Frontend container needs to use Docker service name to reach backend
  const backendUrl = "http://backend:8000";
  
  console.log('🔧 Proxy setup - Backend URL:', backendUrl);
  console.log('🔧 Using Docker service name for container networking');

  // Proxy API routes
  app.use(
    "/api",
    createProxyMiddleware({
      target: backendUrl,
      changeOrigin: true,
      logLevel: 'debug',
      onError: (err, req, res) => {
        console.error('❌ Proxy error:', err.message);
        console.error('❌ Request URL:', req.url);
        console.error('❌ Target:', backendUrl);
      }
    })
  );
  
  // Proxy health endpoint
  app.use(
    "/health",
    createProxyMiddleware({
      target: backendUrl, 
      changeOrigin: true,
      logLevel: 'debug',
      onError: (err, req, res) => {
        console.error('❌ Health proxy error:', err.message);
      }
    })
  );

  // Proxy admin endpoints (system reinit etc.)
  app.use(
    "/admin",
    createProxyMiddleware({
      target: backendUrl,
      changeOrigin: true,
      logLevel: 'debug',
      onError: (err, req, res) => {
        console.error('❌ Admin proxy error:', err.message);
      }
    })
  );
  
  // WebSocket proxy removed - HTTP polling used instead
};
