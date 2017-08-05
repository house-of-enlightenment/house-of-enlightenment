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
python ./python/houseOfEnlightenment.py
# To run with customized layout or server list, use (below are default values): 
python ./python/houseOfEnlightenment.py -l layout/hoeLayout.json -s layout/servers_local.json
# To change the FPS:
python ./python/houseOfEnlightenment.py -f 30
# To run in verbose mode (not much supports this yet):
python ./python/houseOfEnlightenment.py -v
```

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

# Contributing
## Before you commit
Reformat your code:
```yapf --in-place -r hoe```
