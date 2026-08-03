import { createMDX } from 'fumadocs-mdx/next';

const withMDX = createMDX();

/** @type {import('next').NextConfig} */
const config = {
  reactStrictMode: true,
  // static HTML export: `next build` emits plain .html files under out/
  output: 'export',
  // every route emits <dir>/index.html (out/docs/index.html,
  // out/docs/<page>/index.html) instead of flat docs.html / <page>.html
  trailingSlash: true,
};

export default withMDX(config);
