import * as THREE from "three";

export default function createGround() {

  const plane = new THREE.Mesh(
    new THREE.PlaneGeometry( 1000, 1000, 1, 1 ),
    new THREE.MeshLambertMaterial( { color: 0xffffff, side: THREE.DoubleSide } )
  );

  plane.rotation.x = -Math.PI/2; // make it flat instead of on end
  plane.position.y = -20;

  plane.receiveShadow = true;

  return plane;
}
