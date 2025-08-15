/**
 * @file: next.config.ts
 * @description: Configuration file for Next.js application settings.
 */
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  reactStrictMode: true,
  output: 'standalone',
  experimental: {
    optimizePackageImports: ['framer-motion'],
  },
  async rewrites() {
    // Environment-aware API URL determination
    const getApiUrl = () => {
      // In production builds, use the public API URL
      if (process.env.NODE_ENV === 'production') {
        return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      }

      // In development, determine if we're in Docker or local
      // Docker environment will have NEXT_PUBLIC_API_URL set to localhost:8000
      // Local development might need direct service name
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      if (apiUrl && apiUrl.includes('localhost')) {
        return apiUrl;
      }

      // Fallback to Docker service name for server-side rewrites
      return 'http://happyrobot-api:8000';
    };

    const apiUrl = getApiUrl();

    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
  webpack: (config, { isServer }) => {
    // Add alias for pdfjs-dist worker
    config.resolve.alias.canvas = false;

    // Configure to handle PDF.js worker
    config.module.rules.push({
      test: /\.mjs$/,
      include: /node_modules/,
      type: 'javascript/auto',
    });

    // Handle framer-motion imports
    if (!isServer) {
      config.resolve.alias = {
        ...config.resolve.alias,
        'framer-motion': require.resolve('framer-motion'),
      };
    }

    // Add Promise.withResolvers polyfill as entry point
    if (!isServer) {
      const originalEntry = config.entry;
      config.entry = async () => {
        const entries = await originalEntry();

        if (entries['main.js'] && !entries['main.js'].includes('./src/lib/polyfills/promise-with-resolvers.js')) {
          entries['main.js'].unshift('./src/lib/polyfills/promise-with-resolvers.js');
        }

        return entries;
      };
    }

    return config;
  },
  // Copy PDF.js cmaps to public directory
  async headers() {
    return [
      {
        source: '/cmaps/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ];
  },
};

export default nextConfig;
