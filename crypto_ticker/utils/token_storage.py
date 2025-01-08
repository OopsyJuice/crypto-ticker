import json
from pathlib import Path
from typing import Dict, Set, Any

class TokenStorage:
    def __init__(self, storage_file: str = 'utils/token_config.json'):
        self.storage_file = Path(storage_file)
        print(f"\n=== Initializing TokenStorage ===")
        print(f"Storage file path: {self.storage_file}")
        print(f"Storage file exists: {self.storage_file.exists()}")
        self.ensure_storage_file()
    
    def ensure_storage_file(self) -> None:
        """Create storage file if it doesn't exist."""
        print(f"\n=== Ensuring Storage File ===")
        print(f"Checking file: {self.storage_file}")
        if not self.storage_file.exists():
            print("File doesn't exist, creating it...")
            self.save_config({
                'selected_tokens': [],
                'priorities': {
                    'high': [],
                    'medium': [],
                    'low': []
                }
            })
        else:
            print("File already exists")
    
    def load_config(self) -> Dict[str, Any]:
        """Load token configuration from file."""
        print("\n=== Loading Config ===")
        print(f"Loading from: {self.storage_file}")
        try:
            with open(self.storage_file, 'r') as f:
                config = json.load(f)
                print(f"Loaded config: {config}")
                return config
        except Exception as e:
            print(f"Error loading token config: {str(e)}")
            return {
                'selected_tokens': [],
                'priorities': {
                    'high': [],
                    'medium': [],
                    'low': []
                }
            }
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save token configuration to file."""
        print("\n=== Saving Config ===")
        print(f"Saving to: {self.storage_file}")
        print(f"Config to save: {config}")
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(config, f, indent=2)
            print("Save completed successfully")
            return True
        except Exception as e:
            print(f"Error saving token config: {str(e)}")
            return False
    
    def save_current_state(self, selected_tokens: Set[str], token_priorities: Dict[str, Set[str]]) -> bool:
        """Save current application state."""
        print("\n=== Saving Token State ===")
        print(f"Selected tokens: {selected_tokens}")
        print(f"Token priorities: {token_priorities}")
        
        config = {
            'selected_tokens': list(selected_tokens),
            'priorities': {
                priority: list(tokens)
                for priority, tokens in token_priorities.items()
            }
        }
        print(f"Prepared config: {config}")
        return self.save_config(config)
    
    def load_current_state(self) -> tuple[set[str], dict[str, set[str]]]:
        """Load application state from storage."""
        print("\n=== Loading Current State ===")
        config = self.load_config()
        selected_tokens = set(config['selected_tokens'])
        token_priorities = {
            priority: set(tokens)
            for priority, tokens in config['priorities'].items()
        }
        print(f"Loaded tokens: {selected_tokens}")
        print(f"Loaded priorities: {token_priorities}")
        return selected_tokens, token_priorities