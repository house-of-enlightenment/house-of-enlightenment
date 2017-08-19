#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

virtualenv venv
# the activate script has unbound variables so we need to stop
# checking for those
set +u
source venv/bin/activate
set -u

# it is useful to see the trace so that when things fail we can see why
set -o xtrace

cd python
pip install -r requirements.txt
pip install pylint pep8
# editable mode means that the effects are available
# otherwise the hoe library doesn't know where to find them at
pip install -e .

pytest tests

cd tests
python run_all_scenes_with_reader.py
cd -

pylint -E --extension-pkg-whitelist=numpy hoe scripts/*.py effects/*.py
pep8 hoe scripts effects
