import { source } from '@/lib/source';
import { GlassLayout } from 'fumadocs-ui/layouts/glass';
import { baseOptions } from '@/lib/layout.shared';
import type { ReactNode } from 'react';

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <GlassLayout tree={source.getPageTree()} {...baseOptions()}>
      {children}
    </GlassLayout>
  );
}
