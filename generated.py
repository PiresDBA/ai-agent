```python
#!/usr/bin/env python3

import sys

def main():
    # Ensure the environment is set up correctly
    if sys.executable is None:
        print("Error: No executable found")
        sys.exit(1)
    
    print("Script executed successfully")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
```