import { source } from '@/lib/source';
import { GlassLayout } from 'fumadocs-ui/layouts/glass';
import { baseOptions } from '@/lib/layout.shared';
import { LiquidGlassProvider } from '@/components/liquid-glass/liquid-glass-provider';
import type { ReactNode } from 'react';

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <GlassLayout tree={source.getPageTree()} {...baseOptions()}>
      <LiquidGlassProvider />
      {children}
    </GlassLayout>
  );
}
