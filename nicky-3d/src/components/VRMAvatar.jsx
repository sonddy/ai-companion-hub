import { useRef, useEffect, useState } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import { VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';

export function VRMAvatar({ isTalking, modelUrl }) {
  const [vrm, setVrm] = useState(null);
  const [mixer, setMixer] = useState(null);
  const groupRef = useRef();
  const { scene } = useThree();
  
  // Mouth animation state
  const mouthOpenRef = useRef(0);
  const targetMouthOpen = useRef(0);

  // Load VRM model
  useEffect(() => {
    if (!modelUrl) return;

    const loader = new GLTFLoader();
    loader.register((parser) => new VRMLoaderPlugin(parser));

    loader.load(
      modelUrl,
      (gltf) => {
        const loadedVrm = gltf.userData.vrm;
        if (loadedVrm) {
          VRMUtils.removeUnnecessaryJoints(loadedVrm.scene);
          VRMUtils.removeUnnecessaryVertices(loadedVrm.scene);
          
          // Rotate to face camera
          loadedVrm.scene.rotation.y = Math.PI;
          
          // SET ARMS DOWN immediately (fix T-pose)
          if (loadedVrm.humanoid) {
            const leftUpperArm = loadedVrm.humanoid.getNormalizedBoneNode('leftUpperArm');
            const rightUpperArm = loadedVrm.humanoid.getNormalizedBoneNode('rightUpperArm');
            const leftLowerArm = loadedVrm.humanoid.getNormalizedBoneNode('leftLowerArm');
            const rightLowerArm = loadedVrm.humanoid.getNormalizedBoneNode('rightLowerArm');
            
            // Arms down at sides
            if (leftUpperArm) {
              leftUpperArm.rotation.z = 1.2; // Arm down
            }
            if (rightUpperArm) {
              rightUpperArm.rotation.z = -1.2; // Arm down
            }
            if (leftLowerArm) {
              leftLowerArm.rotation.y = 0;
            }
            if (rightLowerArm) {
              rightLowerArm.rotation.y = 0;
            }
          }
          
          setVrm(loadedVrm);
          
          // Create animation mixer
          const newMixer = new THREE.AnimationMixer(loadedVrm.scene);
          setMixer(newMixer);
          
          console.log('VRM loaded successfully!');
        }
      },
      (progress) => {
        console.log('Loading VRM...', (progress.loaded / progress.total * 100).toFixed(1) + '%');
      },
      (error) => {
        console.error('Error loading VRM:', error);
      }
    );

    return () => {
      if (vrm) {
        VRMUtils.deepDispose(vrm.scene);
      }
    };
  }, [modelUrl]);

  // Update talking state
  useEffect(() => {
    targetMouthOpen.current = isTalking ? 1 : 0;
  }, [isTalking]);

  // Animation loop
  useFrame((state, delta) => {
    if (!vrm) return;

    // Update VRM
    vrm.update(delta);

    const time = state.clock.getElapsedTime();

    // Smooth mouth animation
    const mouthSpeed = 8;
    if (isTalking) {
      // Animate mouth open/close while talking
      const mouthValue = (Math.sin(time * 15) + 1) / 2 * 0.6 + 0.2;
      mouthOpenRef.current = THREE.MathUtils.lerp(mouthOpenRef.current, mouthValue, delta * mouthSpeed);
    } else {
      mouthOpenRef.current = THREE.MathUtils.lerp(mouthOpenRef.current, 0, delta * mouthSpeed);
    }

    // Apply mouth blend shape
    if (vrm.expressionManager) {
      vrm.expressionManager.setValue('aa', mouthOpenRef.current);
    }

    // Body animations based on talking state
    if (vrm.humanoid) {
      const head = vrm.humanoid.getNormalizedBoneNode('head');
      const neck = vrm.humanoid.getNormalizedBoneNode('neck');
      const spine = vrm.humanoid.getNormalizedBoneNode('spine');
      const chest = vrm.humanoid.getNormalizedBoneNode('chest');
      const leftUpperArm = vrm.humanoid.getNormalizedBoneNode('leftUpperArm');
      const rightUpperArm = vrm.humanoid.getNormalizedBoneNode('rightUpperArm');
      const leftLowerArm = vrm.humanoid.getNormalizedBoneNode('leftLowerArm');
      const rightLowerArm = vrm.humanoid.getNormalizedBoneNode('rightLowerArm');
      const leftHand = vrm.humanoid.getNormalizedBoneNode('leftHand');
      const rightHand = vrm.humanoid.getNormalizedBoneNode('rightHand');
      const leftShoulder = vrm.humanoid.getNormalizedBoneNode('leftShoulder');
      const rightShoulder = vrm.humanoid.getNormalizedBoneNode('rightShoulder');

      if (isTalking) {
        // MORE EXPRESSIVE HEAD MOVEMENT when talking
        if (head) {
          head.rotation.y = Math.sin(time * 2.5) * 0.15 + Math.sin(time * 1.2) * 0.08;
          head.rotation.x = Math.sin(time * 1.8) * 0.08 + Math.cos(time * 0.9) * 0.05;
          head.rotation.z = Math.sin(time * 1.5) * 0.05;
        }

        // Neck follows head slightly
        if (neck) {
          neck.rotation.y = Math.sin(time * 2.2) * 0.06;
          neck.rotation.x = Math.sin(time * 1.5) * 0.04;
        }

        // Body sway when talking
        if (spine) {
          spine.rotation.y = Math.sin(time * 1.2) * 0.03;
          spine.rotation.z = Math.sin(time * 0.8) * 0.02;
        }

        if (chest) {
          chest.rotation.y = Math.sin(time * 1.5) * 0.04;
          chest.rotation.x = Math.sin(time * 1.0) * 0.02;
        }

        // Shoulder slight movement when talking
        if (leftShoulder) {
          leftShoulder.rotation.z = Math.sin(time * 2.0) * 0.03;
        }
        if (rightShoulder) {
          rightShoulder.rotation.z = -Math.sin(time * 2.0 + 0.5) * 0.03;
        }

        // Arms stay DOWN but with subtle gesture movement
        if (leftUpperArm) {
          // Keep arm down (1.2 = down) with small movement
          leftUpperArm.rotation.z = 1.2 + Math.sin(time * 1.5) * 0.1;
          leftUpperArm.rotation.x = Math.sin(time * 1.2) * 0.05;
        }
        if (rightUpperArm) {
          rightUpperArm.rotation.z = -1.2 - Math.sin(time * 1.8) * 0.1;
          rightUpperArm.rotation.x = Math.sin(time * 1.2 + 0.5) * 0.05;
        }

        // Lower arm subtle movement
        if (leftLowerArm) {
          leftLowerArm.rotation.y = Math.sin(time * 2.5) * 0.1;
          leftLowerArm.rotation.z = Math.sin(time * 2) * 0.05;
        }
        if (rightLowerArm) {
          rightLowerArm.rotation.y = -Math.sin(time * 2.5 + 0.5) * 0.1;
          rightLowerArm.rotation.z = -Math.sin(time * 2 + 0.3) * 0.05;
        }

        // Hand gestures - subtle wrist movement
        if (leftHand) {
          leftHand.rotation.z = Math.sin(time * 3) * 0.1;
          leftHand.rotation.x = Math.sin(time * 2.5) * 0.08;
        }
        if (rightHand) {
          rightHand.rotation.z = -Math.sin(time * 3 + 0.3) * 0.1;
          rightHand.rotation.x = Math.sin(time * 2.5 + 0.3) * 0.08;
        }

      } else {
        // IDLE ANIMATION - subtle movement
        if (head) {
          head.rotation.y = THREE.MathUtils.lerp(head.rotation.y, Math.sin(time * 0.5) * 0.05, delta * 3);
          head.rotation.x = THREE.MathUtils.lerp(head.rotation.x, Math.sin(time * 0.3) * 0.02, delta * 3);
          head.rotation.z = THREE.MathUtils.lerp(head.rotation.z, 0, delta * 3);
        }

        if (neck) {
          neck.rotation.y = THREE.MathUtils.lerp(neck.rotation.y, Math.sin(time * 0.4) * 0.02, delta * 3);
          neck.rotation.x = THREE.MathUtils.lerp(neck.rotation.x, 0, delta * 3);
        }

        // Return body to neutral
        if (spine) {
          spine.rotation.y = THREE.MathUtils.lerp(spine.rotation.y, Math.sin(time * 0.3) * 0.01, delta * 3);
          spine.rotation.z = THREE.MathUtils.lerp(spine.rotation.z, 0, delta * 3);
        }

        if (chest) {
          chest.rotation.y = THREE.MathUtils.lerp(chest.rotation.y, 0, delta * 3);
          chest.rotation.x = THREE.MathUtils.lerp(chest.rotation.x, Math.sin(time * 0.5) * 0.01, delta * 3);
        }

        // Arms stay DOWN at sides (natural position)
        if (leftUpperArm) {
          // Arms down: rotation.z = 1.2 = arms at sides
          leftUpperArm.rotation.z = THREE.MathUtils.lerp(leftUpperArm.rotation.z, 1.2, delta * 3);
          leftUpperArm.rotation.x = THREE.MathUtils.lerp(leftUpperArm.rotation.x, 0, delta * 3);
        }
        if (rightUpperArm) {
          rightUpperArm.rotation.z = THREE.MathUtils.lerp(rightUpperArm.rotation.z, -1.2, delta * 3);
          rightUpperArm.rotation.x = THREE.MathUtils.lerp(rightUpperArm.rotation.x, 0, delta * 3);
        }

        // Lower arms relaxed
        if (leftLowerArm) {
          leftLowerArm.rotation.y = THREE.MathUtils.lerp(leftLowerArm.rotation.y, 0, delta * 3);
          leftLowerArm.rotation.z = THREE.MathUtils.lerp(leftLowerArm.rotation.z, 0, delta * 3);
        }
        if (rightLowerArm) {
          rightLowerArm.rotation.y = THREE.MathUtils.lerp(rightLowerArm.rotation.y, 0, delta * 3);
          rightLowerArm.rotation.z = THREE.MathUtils.lerp(rightLowerArm.rotation.z, 0, delta * 3);
        }

        // Hands relaxed
        if (leftHand) {
          leftHand.rotation.z = THREE.MathUtils.lerp(leftHand.rotation.z, 0, delta * 3);
          leftHand.rotation.x = THREE.MathUtils.lerp(leftHand.rotation.x, 0, delta * 3);
          leftHand.rotation.y = THREE.MathUtils.lerp(leftHand.rotation.y, 0, delta * 3);
        }
        if (rightHand) {
          rightHand.rotation.z = THREE.MathUtils.lerp(rightHand.rotation.z, 0, delta * 3);
          rightHand.rotation.x = THREE.MathUtils.lerp(rightHand.rotation.x, 0, delta * 3);
          rightHand.rotation.y = THREE.MathUtils.lerp(rightHand.rotation.y, 0, delta * 3);
        }

        // Shoulders relaxed
        if (leftShoulder) {
          leftShoulder.rotation.z = THREE.MathUtils.lerp(leftShoulder.rotation.z, 0, delta * 3);
        }
        if (rightShoulder) {
          rightShoulder.rotation.z = THREE.MathUtils.lerp(rightShoulder.rotation.z, 0, delta * 3);
        }
      }
    }

    // Eye blinking
    if (vrm.expressionManager) {
      const blinkCycle = Math.sin(time * 0.5) > 0.95;
      vrm.expressionManager.setValue('blink', blinkCycle ? 1 : 0);
      
      // Add expressions when talking
      if (isTalking) {
        // Slight smile/happy expression
        vrm.expressionManager.setValue('happy', 0.3 + Math.sin(time * 2) * 0.1);
      } else {
        vrm.expressionManager.setValue('happy', THREE.MathUtils.lerp(
          vrm.expressionManager.getValue('happy') || 0, 0.1, delta * 2
        ));
      }
    }
  });

  if (!vrm) {
    return (
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[0.5, 32, 32]} />
        <meshStandardMaterial color="#8b5cf6" />
      </mesh>
    );
  }

  return <primitive ref={groupRef} object={vrm.scene} />;
}

// Fallback 3D avatar (animated sphere with face)
export function SimpleAvatar({ isTalking }) {
  const groupRef = useRef();
  const mouthRef = useRef();
  const leftEyeRef = useRef();
  const rightEyeRef = useRef();

  useFrame((state, delta) => {
    const time = state.clock.getElapsedTime();
    
    // Gentle floating animation
    if (groupRef.current) {
      groupRef.current.position.y = Math.sin(time * 0.8) * 0.05;
      groupRef.current.rotation.y = Math.sin(time * 0.3) * 0.1;
    }

    // Mouth animation
    if (mouthRef.current) {
      if (isTalking) {
        const mouthScale = (Math.sin(time * 15) + 1) / 2 * 0.8 + 0.3;
        mouthRef.current.scale.y = mouthScale;
      } else {
        mouthRef.current.scale.y = THREE.MathUtils.lerp(mouthRef.current.scale.y, 0.3, delta * 5);
      }
    }

    // Eye blinking
    const shouldBlink = Math.sin(time * 0.5) > 0.97;
    if (leftEyeRef.current && rightEyeRef.current) {
      const eyeScale = shouldBlink ? 0.1 : 1;
      leftEyeRef.current.scale.y = THREE.MathUtils.lerp(leftEyeRef.current.scale.y, eyeScale, delta * 20);
      rightEyeRef.current.scale.y = THREE.MathUtils.lerp(rightEyeRef.current.scale.y, eyeScale, delta * 20);
    }
  });

  return (
    <group ref={groupRef}>
      {/* Head */}
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[1, 64, 64]} />
        <meshStandardMaterial color="#8b5cf6" />
      </mesh>

      {/* Left Eye */}
      <mesh ref={leftEyeRef} position={[-0.3, 0.2, 0.85]}>
        <sphereGeometry args={[0.15, 32, 32]} />
        <meshStandardMaterial color="#0f172a" />
      </mesh>

      {/* Right Eye */}
      <mesh ref={rightEyeRef} position={[0.3, 0.2, 0.85]}>
        <sphereGeometry args={[0.15, 32, 32]} />
        <meshStandardMaterial color="#0f172a" />
      </mesh>

      {/* Mouth */}
      <mesh ref={mouthRef} position={[0, -0.3, 0.9]}>
        <capsuleGeometry args={[0.15, 0.2, 8, 16]} />
        <meshStandardMaterial color="#0f172a" />
      </mesh>

      {/* Glow effect */}
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[1.1, 32, 32]} />
        <meshBasicMaterial color="#7c3aed" transparent opacity={0.1} />
      </mesh>
    </group>
  );
}

export default VRMAvatar;

