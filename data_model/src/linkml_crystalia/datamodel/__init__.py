from pathlib import Path
from data_model.src.linkml_crystalia.datamodel.linkml_crystalia import *

THIS_PATH = Path(__file__).parent

SCHEMA_DIRECTORY = THIS_PATH.parent / "schema"
MAIN_SCHEMA_PATH = SCHEMA_DIRECTORY / "linkml_crystalia.yaml"
