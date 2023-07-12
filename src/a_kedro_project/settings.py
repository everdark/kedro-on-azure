from dotenv import load_dotenv
from kedro.config import TemplatedConfigLoader

CONFIG_LOADER_CLASS = TemplatedConfigLoader
CONFIG_LOADER_ARGS = {"globals_pattern": "*globals.yml"}

load_dotenv()
