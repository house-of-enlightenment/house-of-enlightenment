"""Launch two processes
- one is just a simple socket reader
- the second runs the scenes
"""


import subprocess

p1 = subprocess.Popen(['python', 'socket_reader.py'])
try:
    subprocess.check_call(['python', 'run_all_scenes.py', '--loops=2'])
finally:
    p1.terminate()
    p1.wait
