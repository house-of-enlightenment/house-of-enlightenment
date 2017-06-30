import * as THREE from "three";

export default function createSphere(store) {

  // create the sphere's material
  const sphereMaterial =
    new THREE.MeshLambertMaterial({
      color: 0xCC0000
    });

  // Set up the sphere vars
  const RADIUS = 50;
  const SEGMENTS = 16;
  const RINGS = 16;

  // Create a new mesh with
  // sphere geometry - we will cover
  // the sphereMaterial next!
  const sphere = new THREE.Mesh(
    new THREE.SphereGeometry(RADIUS, SEGMENTS, RINGS),
    sphereMaterial
  );

  // Move the Sphere back in Z so we can see it.
  sphere.position.z = -300;

  return sphere;
}
