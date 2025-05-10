# Cyberdesk PyPI Package Sandbox Test

This folder provides a clean environment to test the published `cyberdesk` Python SDK from PyPI. In the future, we'll add proper tests for all of the SDK's, but for now this will have to do in terms of quick manual test scripts.

## Setup Instructions

1. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

2. **Install the published package from PyPI:**

   ```bash
   pip install cyberdesk
   ```

3. **Set your API key:**

   Edit `config.py` and replace `"your-api-key-here"` with your actual Cyberdesk API key.

4. **Run the test script:**

   ```bash
   python test_sdk.py
   ```

## What This Does
- Launches a desktop via the SDK
- Fetches its details
- Terminates the desktop

If you encounter errors, check your API key and ensure the package is published and available on PyPI. 