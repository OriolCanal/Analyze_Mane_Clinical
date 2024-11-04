import yaml
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

class Yaml_file():
    def __init__(self, file_path):
        self.file_path = file_path
        self.params = self.load_yaml()
    
    def load_yaml(self):
        """Loads the YAML file and stores its content in `self.params`."""
        try:
            with open(self.file_path, "r") as f:
                self.params = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: The file {self.file_path} was not found.")
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file {self.file_path}: {e}")
        
    def __str__(self):
        """Returns a string representation of the YAML content."""
        return str(self.params) if self.params else "No data loaded."
    
    def get_param(self, key, default=None):
        """Retrieves a parameter by key, raising an error if the key is not found."""
        if self.params and key in self.params:
            return self.params[key]
        else:
            raise KeyError(f"Key '{key}' not found in the YAML file.")
def parse_yaml_file()
yaml_file_path = os.path.join(current_dir, "yaml", "params.yaml")

with open(yaml_file_path, "r") as f:
    params = yaml.safe_load(f)

print(data)