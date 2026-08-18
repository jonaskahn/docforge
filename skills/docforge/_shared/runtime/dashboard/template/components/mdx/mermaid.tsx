'use client';
import { Component, type ReactNode, use, useEffect, useId, useState } from 'react';
import { useTheme } from 'next-themes';
import { Callout } from 'fumadocs-ui/components/callout';

export function Mermaid({ chart }: { chart: string }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <MermaidErrorBoundary chart={chart} key={chart}>
      <MermaidContent chart={chart} />
    </MermaidErrorBoundary>
  );
}

// `mermaid.render()` needs real text layout (`getBBox`) that docforge's
// headless validation gate cannot check -- that gate only runs
// `mermaid.parse()` (syntax only; see the dashboard's `invalid_mermaid` scan
// finding) since jsdom has no layout engine. A diagram can still fail here,
// and `use()` re-throws a rejected promise during render, which only a
// class-based error boundary can catch (no hook equivalent exists).
type MermaidErrorBoundaryState = { error: Error | null };

class MermaidErrorBoundary extends Component<{ chart: string; children: ReactNode }, MermaidErrorBoundaryState> {
  state: MermaidErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): MermaidErrorBoundaryState {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <Callout type="error" title="Diagram failed to render">
          <p>{this.state.error.message}</p>
          <pre>
            <code>{this.props.chart}</code>
          </pre>
        </Callout>
      );
    }
    return this.props.children;
  }
}

const cache = new Map<string, Promise<unknown>>();

function cachePromise<T>(key: string, setPromise: () => Promise<T>): Promise<T> {
  const cached = cache.get(key);
  if (cached) return cached as Promise<T>;
  const promise = setPromise();
  cache.set(key, promise);
  return promise;
}

function MermaidContent({ chart }: { chart: string }) {
  const id = useId();
  const { resolvedTheme } = useTheme();
  const { default: mermaid } = use(cachePromise('mermaid', () => import('mermaid')));
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'loose',
    fontFamily: 'inherit',
    themeCSS: 'margin: 1.5rem auto 0;',
    theme: resolvedTheme === 'dark' ? 'dark' : 'default',
  });
  const { svg, bindFunctions } = use(
    cachePromise(`${chart}-${resolvedTheme}`, () => {
      return mermaid.render(id, chart.replaceAll('\\n', '\n'));
    }),
  );

  return (
    <div
      ref={(container) => {
        if (container) bindFunctions?.(container);
      }}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
