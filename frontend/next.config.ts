import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  
  // Optimized for serverless/edge environments
  // Keep default React runtime for best compatibility
  
  // Improved build performance
  productionBrowserSourceMaps: false,
  
  // React strict mode
  reactStrictMode: true,

  // Headers for security and performance
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=3600, must-revalidate",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
        ],
      },
    ];
  },

  // Redirects
  async redirects() {
    return [];
  },

  // Rewrites for API calls
  async rewrites() {
    return {
      beforeFiles: [],
      afterFiles: [],
      fallback: [],
    };
  },
};

export default nextConfig;
