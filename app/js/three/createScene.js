import * as THREE from "three";


export default function createScene(store, children) {

  const scene = new THREE.Scene();

  // add all the children to the scene
  children.forEach(child => scene.add(child));

  return scene;
}
