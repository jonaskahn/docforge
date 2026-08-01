import defaultMdxComponents from 'fumadocs-ui/mdx';
import { Mermaid } from './mdx/mermaid';
import type { ComponentProps } from 'react';
import type { MDXComponents } from 'mdx/types';

function PlainImg(props: ComponentProps<'img'>) {
  return <img {...props} />;
}

export function getMDXComponents(components?: MDXComponents) {
  return {
    ...defaultMdxComponents,
    Mermaid,
    // Markdown images reference copied assets under /docs-assets; render them
    // as plain <img> so no width/height metadata is required.
    img: PlainImg,
    ...components,
  } satisfies MDXComponents;
}

export const useMDXComponents = getMDXComponents;

declare global {
  type MDXProvidedComponents = ReturnType<typeof getMDXComponents>;
}
