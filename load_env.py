"""
Environment Variable Loader
Loads variables from .env file
"""
import os
from pathlib import Path

def load_env():
    """Load environment variables from .env file"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("⚠️  Warning: .env file not found")
        print("Create a .env file with your OPENAI_API_KEY")
        return False
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse key=value
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Set environment variable
                os.environ[key] = value
    
    # Verify OPENAI_API_KEY is set
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        return False
    
    print("✅ Environment variables loaded from .env")
    return True

# Don't call load_env() here - that was the problem!
# if __name__ == "__main__":
#     load_env()