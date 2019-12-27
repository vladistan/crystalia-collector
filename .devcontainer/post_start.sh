#!/bin/bash

sudo apt update
sudo apt install -y python3-ament-xmllint

pipx install pre-commit

echo "PWD: $PWD"

if [[ "$PWD" == *"/workspaces/"* ]]; then
  echo "Running in VSCode Dev Container"
elif [[ "$PWD" == *"/IdeaProjects/"* ]]; then
  echo "Running in JetBrains IDE"
fi

echo "----------"
export | grep -i green
echo "----------"

pre-commit install || true

python -m pip install --upgrade pip
python -m pip install '.[dev]'
python -m pip install -e .

pre-commit run -a || true
