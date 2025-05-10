# test_sdk.py
from cyberdesk import CyberdeskClient
from cyberdesk.actions import click_mouse, ClickMouseButton, type_text
from config import API_KEY
import time

def main():
    client = CyberdeskClient(api_key=API_KEY)
    desktop_id = None
    try:
        desktop = client.launch_desktop()
        print("Launched desktop:", desktop)
        desktop_id = desktop.id
        # Wait for desktop to be running
        print("Waiting for desktop to be running...")
        while True:
            details = client.get_desktop(desktop_id)
            status_str = details.status.value  # status is always an Enum
            print(f"Current status: {status_str}")
            if status_str == "running":
                break
            time.sleep(2)
        print("Desktop is running!")
        # Perform a click_mouse action
        action = click_mouse(x=100, y=100, button=ClickMouseButton.RIGHT)
        action_result = client.execute_computer_action(desktop_id, action)
        print("Click mouse result:", action_result)
        # Perform a type_text action
        action = type_text(text="Hello, World!")
        action_result = client.execute_computer_action(desktop_id, action)
        print("Type text result:", action_result)
    except Exception as e:
        print("Error during SDK usage:", e)
    finally:
        if desktop_id:
            try:
                result = client.terminate_desktop(desktop_id)
                print("Terminated desktop:", result)
                if result.status == "terminated":
                    print("Desktop terminated successfully")
                else:
                    print("Desktop termination failed")
            except Exception as term_e:
                print("Error during desktop termination:", term_e)

if __name__ == "__main__":
    main() 