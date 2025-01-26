# Raytracing engine

This raytracing engine is structured around the Blinn-Phong Model, which combines ambient reflection, diffuse reflection and specular reflection to simulate object-light interaction. 
Compared to the original Phong model, which uses the angle between the viewer and the reflected light, Blinn-Phong uses a halfway-vector (the mid-point between viewer and the light source), to calculate the specular light. This approach is computationally easier (to a minimal degree in this application) and often creates a more "natural-looking" shine. It is also noteworthy to mention that I chose to simulate light diffusion-interaction with each object's specific shadow (referencing row 99) with the help of Lambert's light model. 

## How to run
1. Run the file klotbelysning.py and follow instructions on the userinterface.
2. Click anywhere on the centersphere to project the lightsource in the perpendicular direction realtive to sphere. 

## Object location
In function 'main', you can find the variable 'objects' containing each separate object with respective position and material characteristics.

## Sources
- [Blinn Phong model](https://www.geeksforgeeks.org/phong-model-specular-reflection-in-computer-graphics/)
- Had a lot of use implementing attenuation with the help of [Kaggle](https://www.kaggle.com/code/photunix/ray-tracing-in-python).
- Inspired matrix-code-structure for GUI and vectors: [arunrocks]([https://www.youtube.com/@arunrocks](https://www.youtube.com/watch?v=92tLWv_gajA)).
- [Implementation structure](https://medium.com/@www.seymour/coding-a-3d-ray-tracing-graphics-engine-from-scratch-f914c12bb162)
- [Lambert's light-model](https://en.wikipedia.org/wiki/Lambertian_reflectance)

### Coming soon
This project awaits implementation for multicore-activation for a smoother experience.
