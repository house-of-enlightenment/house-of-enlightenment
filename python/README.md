This package is the pattern logic driving the House of Enlightment LEDs.

# Install

1. Setting up a virtualenvironment is highly recommended. TODO: provide instructions
2. Install the requirements: `pip install -r requirements.txt`
3. Install the library: `pip install -e .`
   - Development mode (`-e`) is recommended so that any changes made to the code
	 are reflected immediately and you don't need to install the package again

# Running the application
```
# Simplest way to start up with all default values (uses local servers and default layout)
python ./python/hoe/houseOfEnlightenment.py
# Start on a specific scene:
python ./python/hoe/houseOfEnlightenment.py <scenename>
# To run with customized layout or server list, use (below are default values): 
python ./python/hoe/houseOfEnlightenment.py -l layout/hoeLayout.json -s layout/servers_local.json
# To change the FPS:
python ./python/hoe/houseOfEnlightenment.py -f 30
# To run in verbose mode (not much supports this yet):
python ./python/hoe/houseOfEnlightenment.py -v
# To load scenes with tags
python ./python/hoe/houseOfEnlightenment.py -t test -t background
```

## Tags
Scenes can be given a set of tags to differentiate test scenes and demo ones from production-worthy ones. Currently, the following tags are supported:
- background
- game
- test
- example
- wip
The default is [] which will load all scenes. There is currently no exclusion of tags set up.

# Interaction
The python application allows for some command prompt input to assist in development and scene control. Currently the following are supported:

| Command | Description | Syntax | Example |
| ------- | ----------- | ------ | ------- |
| quit | exit the application | quit | N/A |
| next | change to the 'next' scene | next | N/A |
| scene | change to a specific scene | scene <scene_name> | scene funkrainbow |
| osc msg | anything else is sent as an osc message | /osc/path [arg1] [arg2] ... [argN] | See below |
| osc button | simulate pressing a button | /input/button <station> <button> | /input/button 1 2 |
| osc fader | simulate changing a fader | /input/fader <station> <fader> <value> | /input/fader 2 0 57 |
| osc timeouts | change the timeouts for changing a scene | /set/timeouts <no_interaction> <max_time_on_one_scene> | /input/timeouts 300 600 |
| lidar | replay lidar data | lidar <filename> | lidar lidar/newbag.sample |

# Lidar
Upstream of the python layer is a lidar and a roscore application doing object recognition. That data can be sent to the server via OSC messages. The OSC messages come with 7 values: id, x, y, z, width, height depth. The id is NOT unique across scans - it is just an enumeration of the objects found in each cycle.

We have captured some of these messages to a sample file using the python/scripts/capture_lidar.py script. You can replay it one of two ways:
- Run the python/hoe/play_lidar.py script. You'll need to supply --filename, --host, and --port
- From the command prompt of a launched animation framework (hoe/houseOfEnlightenment) type "lidar <path_to_file>"
Sample data is in the <repo_root>/lidar/data directory

# Contributing
## Before you commit
Reformat your code:
```yapf --in-place -r hoe```
