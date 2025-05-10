# cyberdesk

[![PyPI version](https://badge.fury.io/py/cyberdesk.svg)](https://badge.fury.io/py/cyberdesk)

The official Python SDK for Cyberdesk.

## Installation

```bash
pip install cyberdesk
```

## Usage

First, create a Cyberdesk client instance with your API key:

```python
from cyberdesk import CyberdeskClient

client = CyberdeskClient(api_key="YOUR_API_KEY")
```

---

### Launch a Desktop

```python
result = client.launch_desktop(timeout_ms=10000)  # Optional: set a timeout for the desktop session

# Error handling example
if hasattr(result, 'error') and result.error:
    raise Exception('Failed to launch desktop: ' + str(result.error))

# Success
if hasattr(result, 'id'):
    desktop_id = result.id
    print('Launched desktop with ID:', desktop_id)
```

---

### Get Desktop Info

```python
info = client.get_desktop("your-desktop-id")

if hasattr(info, 'error') and info.error:
    raise Exception('Failed to get desktop info: ' + str(info.error))

print('Desktop info:', info)
```

---

### Perform a Computer Action (e.g., Mouse Click)

```python
from cyberdesk.actions import click_mouse, ClickMouseButton

action = click_mouse(x=100, y=150, button=ClickMouseButton.LEFT)
action_result = client.execute_computer_action("your-desktop-id", action)

if hasattr(action_result, 'error') and action_result.error:
    raise Exception('Action failed: ' + str(action_result.error))

print('Action result:', action_result)
```

---

### Run a Bash Command

```python
bash_result = client.execute_bash_action(
    "your-desktop-id",
    "echo Hello, world!"
)

if hasattr(bash_result, 'error') and bash_result.error:
    raise Exception('Bash command failed: ' + str(bash_result.error))

print('Bash output:', getattr(bash_result, 'output', bash_result))
```

---

## Ergonomic, Type-Safe Actions

To create computer actions (mouse, keyboard, etc.), use the factory functions in `cyberdesk.actions`. These provide full type hints and IDE autocompletion for all required and optional fields.

**Example:**
```python
from cyberdesk.actions import click_mouse, type_text, ClickMouseButton

action1 = click_mouse(x=100, y=200, button=ClickMouseButton.LEFT)
action2 = type_text(text="Hello, world!")

client.execute_computer_action("your-desktop-id", action1)
client.execute_computer_action("your-desktop-id", action2)
```

| Action         | Factory Function         | Description                |
|----------------|-------------------------|----------------------------|
| Click Mouse    | `click_mouse`           | Mouse click at (x, y)      |
| Drag Mouse     | `drag_mouse`            | Mouse drag from/to (x, y)  |
| Move Mouse     | `move_mouse`            | Move mouse to (x, y)       |
| Scroll         | `scroll`                | Scroll by dx, dy           |
| Type Text      | `type_text`             | Type text                  |
| Press Keys     | `press_keys`            | Press keyboard keys        |
| Screenshot     | `screenshot`            | Take a screenshot          |
| Wait           | `wait`                  | Wait for ms milliseconds   |
| Get Cursor Pos | `get_cursor_position`   | Get mouse cursor position  |

---

## Async Usage

All methods are also available as async variants (prefixed with `async_`). Example:

```python
import asyncio
from cyberdesk import CyberdeskClient
from cyberdesk.actions import click_mouse, ClickMouseButton

async def main():
    client = CyberdeskClient(api_key="YOUR_API_KEY")
    result = await client.async_launch_desktop(timeout_ms=10000)
    print(result)
    # Example async computer action
    action = click_mouse(x=100, y=200, button=ClickMouseButton.LEFT)
    await client.async_execute_computer_action("your-desktop-id", action)
    # ... use other async_ methods as needed

asyncio.run(main())
```

---

## Type Hints and Models

All request/response types are available from the generated models, and all computer actions are available as factory functions in `cyberdesk.actions` for ergonomic, type-safe usage.

```python
from cyberdesk.actions import click_mouse, drag_mouse, type_text, wait, scroll, move_mouse, press_keys, screenshot, get_cursor_position, ClickMouseButton, ClickMouseActionType, PressKeyActionType, ScrollDirection
```

# Note: All action enums (e.g., ClickMouseButton, ClickMouseActionType, PressKeyActionType, ScrollDirection, etc.) are available from cyberdesk.actions for type-safe usage.

---

## For Cyberdesk Team: Publishing to PyPI

**Recommended:** Always use a [virtual environment](https://docs.python.org/3/library/venv.html) (venv) for building and publishing to avoid dependency conflicts.

To build and publish this package to [PyPI](https://pypi.org/project/cyberdesk/):

1. **Log into PyPI** (get credentials from the Cyberdesk team).

2. **Install dev dependencies** (in a clean venv):
   ```bash
   pip install .[dev]
   # or
   uv pip install .[dev]
   ```

3. **Bump the version number** in `pyproject.toml` (e.g., `version = "0.2.4"`).

4. **Clean your `dist/` directory** before building to avoid 'File already exists' errors:
   ```bash
   rm -rf dist/*
   # On Windows PowerShell:
   Remove-Item dist\* -Force
   ```

5. **Build the package:**
   ```bash
   python -m build
   ```
   This creates a `dist/` directory with `.whl` and `.tar.gz` files.

6. **(Recommended) Set up a `.pypirc` file for easy publishing:**
   - Create a file named `.pypirc` in your home directory (e.g., `C:\Users\yourname\.pypirc` on Windows or `~/.pypirc` on Linux/macOS).
   - Add:
     ```ini
     [distutils]
     index-servers =
         pypi

     [pypi]
     username = __token__
     password = pypi-AgEIcH...   # <-- paste your API token here
     ```

7. **Publish to PyPI:**
   ```bash
   twine upload dist/*
   ```
   - If you set up `.pypirc`, you won't be prompted for credentials.
   - If not, enter `__token__` as the username and paste your API token as the password.

8. **Verify:**
   - Visit https://pypi.org/project/cyberdesk/ to see your published package.
   - Try installing it in a fresh environment:
     ```bash
     pip install cyberdesk
     ```

---

## License

[MIT](LICENSE) 