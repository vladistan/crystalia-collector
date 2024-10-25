"""Data test."""
import os
import glob
import unittest

from linkml_runtime.loaders import yaml_loader
from crystalia.datamodel import Descriptor

ROOT = os.path.join(os.path.dirname(__file__), '..')
DATA_DIR = os.path.join(ROOT, "src", "data", "examples")

EXAMPLE_FILES = glob.glob(os.path.join(DATA_DIR, '*.yaml'))


def test_load_data():
    """Data test."""
    for path in EXAMPLE_FILES:
        obj = yaml_loader.load(path, target_class=Descriptor)
        assert obj


def test_create_descriptor():
    """Create a descriptor."""
    descriptor = Descriptor(
        id="example:Descriptor", 
        hasType="cryd:sha256-full",
        value="0223",
        offset=0,
        coverage=1.0,
        length=4,
    )


    assert descriptor
