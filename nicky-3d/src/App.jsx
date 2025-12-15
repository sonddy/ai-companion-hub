import { useState, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, ContactShadows, Html } from '@react-three/drei';
import { SimpleAvatar, VRMAvatar } from './components/VRMAvatar';
import ChatInterface from './components/ChatInterface';
import './App.css';

function LoadingScreen() {
  return (
    <Html center>
      <div className="loading-text">Loading Nicky...</div>
    </Html>
  );
}

function Scene({ isTalking, vrmUrl }) {
  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.4} />
      <directionalLight position={[5, 5, 5]} intensity={1} castShadow />
      <directionalLight position={[-5, 5, -5]} intensity={0.5} color="#7c3aed" />
      <pointLight position={[0, 2, 3]} intensity={0.8} color="#22d3ee" />

      {/* Environment */}
      <Environment preset="night" />

      {/* Avatar - positioned lower */}
      <group position={[0, -0.8, 0]}>
        <Suspense fallback={<LoadingScreen />}>
          {vrmUrl ? (
            <VRMAvatar isTalking={isTalking} modelUrl={vrmUrl} />
          ) : (
            <SimpleAvatar isTalking={isTalking} />
          )}
        </Suspense>
      </group>

      {/* Shadow */}
      <ContactShadows 
        position={[0, -2.3, 0]} 
        opacity={0.5} 
        scale={5} 
        blur={2} 
        far={3}
        color="#7c3aed"
      />

      {/* Camera controls */}
      <OrbitControls 
        enablePan={false}
        enableZoom={true}
        minDistance={2}
        maxDistance={6}
        minPolarAngle={Math.PI / 4}
        maxPolarAngle={Math.PI / 2}
        target={[0, -0.3, 0]}
      />
    </>
  );
}

function App() {
  const [isTalking, setIsTalking] = useState(false);
  const [vrmUrl, setVrmUrl] = useState('/nicky.vrm'); // Default Nicky avatar

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file && file.name.endsWith('.vrm')) {
      const url = URL.createObjectURL(file);
      setVrmUrl(url);
    }
  };

  return (
    <div className="app">
      {/* 3D Canvas */}
      <div className="canvas-container">
        <Canvas
          shadows
          camera={{ position: [0, 0.5, 3], fov: 50 }}
          gl={{ antialias: true, alpha: true }}
        >
          <color attach="background" args={['#0f172a']} />
          <fog attach="fog" args={['#0f172a', 5, 15]} />
          <Scene isTalking={isTalking} vrmUrl={vrmUrl} />
        </Canvas>

        {/* VRM Upload */}
        <div className="vrm-upload">
          <label htmlFor="vrm-input">
            {vrmUrl === '/nicky.vrm' ? '✓ Nicky Loaded' : vrmUrl ? '✓ Custom VRM' : '📁 Load VRM Model'}
          </label>
          <input 
            id="vrm-input"
            type="file" 
            accept=".vrm" 
            onChange={handleFileUpload}
          />
          <p className="vrm-hint">
            Get free VRM models from <a href="https://hub.vroid.com/" target="_blank" rel="noopener">VRoid Hub</a>
          </p>
        </div>

        {/* Title */}
        <div className="title-overlay">
          <h1>Nicky</h1>
          <p>Your 3D AI Companion</p>
        </div>
      </div>

      {/* Chat Interface */}
      <ChatInterface onTalkingChange={setIsTalking} />
      </div>
  );
}

export default App;
