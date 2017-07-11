# Lidar Information
HOE is using a 360 degree 8 level IR Lidar to track obects approaching the structure, potentially as far away as 90 feet.  We will use this information to switch between animation modes in the strucutre, and produce interesting lighting effects without users inside the structure.  For example, as people approach, the light can start to move to their direction, inticing them to enter.  

# Link to Cosmos Lidar Trackign repo
Cosmo is developing object tracking.  The repo can be found here
https://github.com/MyNameIsCosmo/lidar_body_tracking

# Lidar limitations
The lidar works with an object as close as 3 feet and as far as 90 feet.  When an object is close than 3 feet it cast a shadow for the portion of the angle is is blocking.  This should not be an issue for us becaue if some one is insde they have alread been detected.  The Lidar is also line of sight, meaning it can not see objects behinde other objects.

# Lidar output format
We will be sending the lidar information as OSC messages to the animation program.  The messages will contain the center point of a box and its deminsions.  This will generalize the size of a person, group of people or larger object like a car.  

An example message will look like the following:
posistion, height, width
...
[(x,y), 
...

# Hardware
- Intel NUC NUC7i7BNH 16 gb ram 250 GB ssd
- LIDAR INFO HERE!>!>!>!
- Switch
