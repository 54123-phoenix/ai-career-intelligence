/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    unoptimized: true,
  },
  async redirects() {
    return [
      {
        source: '/career/growth',
        destination: '/analysis',
        permanent: true,
      },
      {
        source: '/career/growth-v2',
        destination: '/analysis',
        permanent: true,
      },
      {
        source: '/career/_growth-lite',
        destination: '/analysis',
        permanent: true,
      },
      {
        source: '/simulation/report',
        destination: '/simulation',
        permanent: true,
      },
    ];
  },
};

module.exports = nextConfig;
