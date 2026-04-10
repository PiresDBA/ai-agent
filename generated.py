```python
#!/usr/bin/env python3

import sys

# Check if executable environment is properly configured
try:
    if sys.platform.startswith('win') and sys.executable is None:
        print("Error: No executable found")
        sys.exit(1)
        
    print("Script executed successfully")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
```