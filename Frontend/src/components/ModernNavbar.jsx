import React, { useRef, useMemo, useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Canvas, useFrame } from '@react-three/fiber';
import { MeshDistortMaterial, Sphere } from '@react-three/drei';
import Logo from './Logo';

function AnimatedSphere() {
  const meshRef = useRef();

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = state.clock.elapsedTime * 0.2;
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.3;
    }
  });

  return (
    <Sphere ref={meshRef} args={[1, 32, 32]} position={[0, 0, 0]}>
      <MeshDistortMaterial
        color="#1fc7d4"
        attach="material"
        distort={0.4}
        speed={1.5}
        roughness={0.1}
        metalness={0.8}
        transparent
        opacity={0.3}
      />
    </Sphere>
  );
}

function FloatingParticles({ count = 20 }) {
  const mesh = useRef();

  const particles = useMemo(() => {
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 10;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 5;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 5;
    }
    return positions;
  }, [count]);

  const particleData = useMemo(() => {
    return Array.from({ length: count }, () => ({
      t: Math.random() * 100,
      factor: 10 + Math.random() * 50,
      speed: 0.01 + Math.random() / 200,
      xFactor: (Math.random() - 0.5) * 10,
      yFactor: (Math.random() - 0.5) * 5,
      zFactor: (Math.random() - 0.5) * 5,
    }));
  }, [count]);

  useFrame((state) => {
    if (!mesh.current || !mesh.current.geometry) return;
    const positions = mesh.current.geometry.attributes.position;
    particleData.forEach((particle, i) => {
      particle.t += particle.speed / 2;
      const a = Math.cos(particle.t) + Math.sin(particle.t * 1) / 10;
      const b = Math.sin(particle.t) + Math.cos(particle.t * 2) / 10;
      const s = Math.cos(particle.t);
      positions.setXYZ(
        i,
        particle.xFactor + a * particle.factor * 0.05,
        particle.yFactor + b * particle.factor * 0.05,
        particle.zFactor + s * particle.factor * 0.05
      );
    });
    positions.needsUpdate = true;
  });

  return (
    <points ref={mesh}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={particles}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial size={0.3} color="#1fc7d4" transparent opacity={0.4} />
    </points>
  );
}

function Navbar3DBackground() {
  return (
    <Canvas
      camera={{ position: [0, 0, 5], fov: 75 }}
      style={{ 
        position: 'absolute', 
        top: 0, 
        left: 0, 
        width: '100%', 
        height: '100%',
        pointerEvents: 'none',
        zIndex: 0
      }}
      gl={{ alpha: true, antialias: true, powerPreference: "high-performance" }}
    >
      <ambientLight intensity={0.3} />
      <pointLight position={[5, 5, 5]} intensity={0.5} color="#1fc7d4" />
      <pointLight position={[-5, -5, -5]} intensity={0.3} color="#0033ad" />
      <AnimatedSphere />
      <FloatingParticles count={15} />
    </Canvas>
  );
}

function ModernNavbar() {
  const location = useLocation();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav className={`nav ${scrolled ? 'nav-scrolled' : ''}`}>
      <div className="nav-3d-background">
        <Navbar3DBackground />
      </div>
      <div className="nav-content">
        <div className="nav-brand">
          <Logo size={32} />
          <span>Super Quant</span>
        </div>
        <div className="nav-links">
          <Link to="/agents" className={`nav-link ${location.pathname === '/agents' || location.pathname === '/' ? 'active' : ''}`}>
            Agents
          </Link>
          <Link to="/risk-management" className={`nav-link ${location.pathname === '/risk-management' ? 'active' : ''}`}>
            Risk
          </Link>
        </div>
      </div>
    </nav>
  );
}

export default ModernNavbar;

