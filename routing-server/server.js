const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const SECURE_API_SERVICE_URL = "http://localhost:9001"; 
const PUBLIC_API_SERVICE_URL = "http://localhost:9000"; 

const app = express();
const PORT = 3000;

app.use('/predict-secure/', createProxyMiddleware({
    target: SECURE_API_SERVICE_URL,
    changeOrigin: true,
    pathRewrite: {
        [`^/predict-secure/`]: '/predict/',
    },
}));

app.use('/predict-public/', createProxyMiddleware({
    target: PUBLIC_API_SERVICE_URL,
    changeOrigin: true,
    pathRewrite: {
        [`^/predict-public`]: '/predict/',
    },
}));

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});

