import { createMDX } from 'fumadocs-mdx/next';

const withMDX = createMDX();

/** @type {import('next').NextConfig} */
const config = {
  reactStrictMode: true,
  // static HTML export: `next build` emits plain .html files under out/
  output: 'export',
};

export default withMDX(config);
