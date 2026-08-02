'use client';

import dynamic from 'next/dynamic';
import { useEffect, useRef, useState } from 'react';

const FluidLens = dynamic(() => import('./fluid-lens'), { ssr: false });

const glassSelector = [
  '#nd-sidebar',
  '#fd-glass-layout > div.sticky',
  '#fd-glass-layout button.rounded-full',
  '#fd-glass-layout .inset-e-0',
  '#nd-toc',
].join(', ');

type LensPosition = { x: number; y: number };

function supportsFluidLens() {
  const canvas = document.createElement('canvas');
  const supportsWebGL = Boolean(canvas.getContext('webgl2') || canvas.getContext('webgl'));
  return (
    window.matchMedia('(hover: hover) and (pointer: fine)').matches &&
    !window.matchMedia('(prefers-reduced-motion: reduce)').matches &&
    !window.matchMedia('(prefers-reduced-transparency: reduce)').matches &&
    supportsWebGL
  );
}

export function LiquidGlassProvider() {
  const frame = useRef<number | undefined>(undefined);
  const hovered = useRef<HTMLElement | null>(null);
  const pointer = useRef<LensPosition>({ x: 0, y: 0 });
  const [enabled, setEnabled] = useState(false);
  const [lens, setLens] = useState<{ active: boolean; position: LensPosition }>({
    active: false,
    position: { x: 0, y: 0 },
  });

  useEffect(() => {
    if (!supportsFluidLens()) return;
    setEnabled(true);

    const elements = [...document.querySelectorAll<HTMLElement>(glassSelector)];
    elements.forEach((element) => element.dataset.liquidGlass = '');

    const update = () => {
      frame.current = undefined;
      const element = hovered.current;
      if (!element) return;

      const rect = element.getBoundingClientRect();
      const x = Math.min(1, Math.max(0, (pointer.current.x - rect.left) / rect.width));
      const y = Math.min(1, Math.max(0, (pointer.current.y - rect.top) / rect.height));
      element.style.setProperty('--glass-pointer-x', `${(x * 100).toFixed(2)}%`);
      element.style.setProperty('--glass-pointer-y', `${(y * 100).toFixed(2)}%`);
      element.style.setProperty('--glass-tilt-x', `${((y - 0.5) * -2).toFixed(3)}deg`);
      element.style.setProperty('--glass-tilt-y', `${((x - 0.5) * 2).toFixed(3)}deg`);
      setLens({ active: true, position: pointer.current });
    };

    const onPointerMove = (event: PointerEvent) => {
      const target = event.target instanceof Element ? event.target.closest<HTMLElement>('[data-liquid-glass]') : null;
      if (hovered.current !== target) {
        hovered.current?.removeAttribute('data-liquid-glass-active');
        hovered.current = target;
        target?.setAttribute('data-liquid-glass-active', '');
      }

      pointer.current = { x: event.clientX, y: event.clientY };
      if (target && frame.current === undefined) frame.current = requestAnimationFrame(update);
    };

    const onPointerLeave = () => {
      hovered.current?.removeAttribute('data-liquid-glass-active');
      hovered.current = null;
      setLens((current) => ({ ...current, active: false }));
    };

    document.addEventListener('pointermove', onPointerMove, { passive: true });
    document.addEventListener('pointerleave', onPointerLeave, { passive: true });
    return () => {
      if (frame.current !== undefined) cancelAnimationFrame(frame.current);
      document.removeEventListener('pointermove', onPointerMove);
      document.removeEventListener('pointerleave', onPointerLeave);
      elements.forEach((element) => {
        delete element.dataset.liquidGlass;
        element.removeAttribute('data-liquid-glass-active');
        element.style.removeProperty('--glass-pointer-x');
        element.style.removeProperty('--glass-pointer-y');
        element.style.removeProperty('--glass-tilt-x');
        element.style.removeProperty('--glass-tilt-y');
      });
      setEnabled(false);
    };
  }, []);

  return enabled ? <FluidLens active={lens.active} position={lens.position} /> : null;
}
