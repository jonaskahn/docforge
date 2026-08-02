'use client';

import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { MeshTransmissionMaterial } from '@react-three/drei';
import { easing } from 'maath';
import { useEffect, useRef } from 'react';
import type { Group } from 'three';

type LensPosition = { x: number; y: number };

function Lens({ active, position }: { active: boolean; position: LensPosition }) {
  const lens = useRef<Group>(null);
  const { viewport } = useThree();

  useFrame((_, delta) => {
    if (!lens.current) return;
    const targetX = (position.x / window.innerWidth - 0.5) * viewport.width;
    const targetY = -(position.y / window.innerHeight - 0.5) * viewport.height;
    easing.damp3(lens.current.position, [targetX, targetY, 0], 0.16, delta);
    easing.damp(lens.current.scale, 'x', active ? 1 : 0, 0.18, delta);
    easing.damp(lens.current.scale, 'y', active ? 1 : 0, 0.18, delta);
  });

  return (
    <group ref={lens} scale={0}>
      <mesh>
        <circleGeometry args={[0.34, 64]} />
        <MeshTransmissionMaterial
          transmission={1}
          roughness={0.04}
          thickness={0.65}
          ior={1.15}
          chromaticAberration={0.045}
          anisotropy={0.08}
          distortion={0.12}
          distortionScale={0.18}
          temporalDistortion={0.08}
          color="#ffffff"
          attenuationColor="#c8e6ff"
          attenuationDistance={0.45}
        />
      </mesh>
      <mesh position={[0, 0, -0.01]}>
        <ringGeometry args={[0.335, 0.35, 64]} />
        <meshBasicMaterial color="#e9f7ff" transparent opacity={0.3} />
      </mesh>
    </group>
  );
}

export default function FluidLens({ active, position }: { active: boolean; position: LensPosition }) {
  const canvas = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const onVisibilityChange = () => {
      if (canvas.current) canvas.current.style.visibility = document.hidden ? 'hidden' : 'visible';
    };
    document.addEventListener('visibilitychange', onVisibilityChange);
    return () => document.removeEventListener('visibilitychange', onVisibilityChange);
  }, []);

  return (
    <Canvas
      ref={canvas}
      aria-hidden="true"
      className="liquid-glass-lens"
      dpr={[1, 1.5]}
      frameloop={active ? 'always' : 'demand'}
      gl={{ alpha: true, antialias: true, powerPreference: 'low-power' }}
      orthographic
      camera={{ position: [0, 0, 5], zoom: 100 }}
    >
      <ambientLight intensity={1.3} />
      <Lens active={active} position={position} />
    </Canvas>
  );
}
