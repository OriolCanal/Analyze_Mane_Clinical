import yaml
import os
from models.log import Log
# current_dir = os.path.dirname(os.path.abspath(__file__))

class Yaml_file():
    def __init__(self, file_path):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            raise ValueError(f"Yaml file: {self.file_path} does not exist!")
        self.params = self.load_yaml()
    
    def load_yaml(self):
        """Loads the YAML file and stores its content in `self.params`."""
        try:
            with open(self.file_path, "r") as f:
                return(yaml.safe_load(f))

        except FileNotFoundError:
            Log.error(f"The file {self.file_path} was not found.")
        except yaml.YAMLError as e:
            Log.error(f"Parsing YAML file {self.file_path}: {e}")
        
    def __str__(self):
        """Returns a string representation of the YAML content."""
        return str(self.params) if self.params else "No data loaded."
    
    def get_param(self, key, default=None):
        """Retrieves a parameter by key, raising an error if the key is not found."""
        if self.params and key in self.params:
            return self.params[key]
        else:
            raise KeyError(f"Key '{key}' not found in the YAML file: {self.file_path}.")


class Runs_yaml(Yaml_file):
    def __init__(self, file_path):
        super().__init__(file_path)

    def add_run(self, run_id):
        # Initialize `runs_analyzed` if it does not exist
        if "runs_analyzed" not in self.params or self.params["runs_analyzed"] is None:
            self.params["runs_analyzed"] = []
        
        # Append `run_id` if it hasn't been added already
        if run_id not in self.params["runs_analyzed"]:
            self.params["runs_analyzed"].append(run_id)

        
    def update_yaml(self):
        Log.info(f"Updating YAML with params: {self.params}")  # Debugging output
        with open(self.file_path, "w") as yaml_file:
            yaml.dump(self.params, yaml_file, default_flow_style=False)