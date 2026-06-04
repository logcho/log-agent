import subprocess
import os
import pyautogui
from langchain_core.tools import tool

# Set PyAutoGUI fail-safe to True.
# If the user moves the mouse to any of the four corners of the screen,
# the execution will abort, throwing a pyautogui.FailSafeException.
pyautogui.FAILSAFE = True

# Also set a slight pause between actions to allow the OS to catch up
pyautogui.PAUSE = 0.1


@tool
def run_command(command: str, timeout: int = 30) -> str:
    """Execute a system command in the zsh/bash shell and return its output.
    
    Args:
        command (str): The command string to run on the system.
        timeout (int, optional): Execution timeout in seconds. Defaults to 30.
        
    Returns:
        str: Standard output combined with standard error, or a timeout/error message.
    """
    try:
        # Run command with a shell
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output = []
        if result.stdout:
            output.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            output.append(f"STDERR:\n{result.stderr}")
            
        if not output:
            return f"Command completed successfully with no output (Exit Code: {result.returncode})."
            
        return f"Exit Code: {result.returncode}\n" + "\n".join(output)
        
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds."
    except Exception as e:
        return f"Error running command: {str(e)}"


@tool
def get_screen_size() -> str:
    """Get the screen resolution (width and height in pixels).
    
    Returns:
        str: Width and height of the primary monitor, or error message.
    """
    try:
        width, height = pyautogui.size()
        return f"Screen Resolution: {width}x{height} pixels"
    except Exception as e:
        return f"Error getting screen size: {str(e)}"


@tool
def get_mouse_position() -> str:
    """Get the current coordinates (x, y) of the mouse cursor.
    
    Returns:
        str: Current mouse pointer coordinates.
    """
    try:
        x, y = pyautogui.position()
        return f"Current Mouse Position: X={x}, Y={y}"
    except Exception as e:
        return f"Error getting mouse position: {str(e)}"


@tool
def mouse_move(x: int, y: int, duration: float = 0.2) -> str:
    """Move the mouse pointer to the specified (x, y) screen coordinates.
    
    Args:
        x (int): Target X coordinate (0 starts at top-left).
        y (int): Target Y coordinate (0 starts at top-left).
        duration (float, optional): How long the movement should take in seconds. Defaults to 0.2.
        
    Returns:
        str: Success message or error message.
    """
    try:
        pyautogui.moveTo(x, y, duration=duration)
        return f"Successfully moved mouse pointer to: X={x}, Y={y}"
    except Exception as e:
        return f"Error moving mouse: {str(e)}"


@tool
def mouse_click(x: int, y: int, button: str = "left") -> str:
    """Perform a mouse click at the specified (x, y) screen coordinates.
    
    Args:
        x (int): Target X coordinate.
        y (int): Target Y coordinate.
        button (str, optional): Which mouse button to press ('left', 'right', 'middle'). Defaults to 'left'.
        
    Returns:
        str: Success message or error message.
    """
    try:
        pyautogui.click(x, y, button=button)
        return f"Successfully clicked the {button} mouse button at: X={x}, Y={y}"
    except Exception as e:
        return f"Error clicking mouse: {str(e)}"


@tool
def type_text(text: str, interval: float = 0.05) -> str:
    """Type string characters sequentially as keyboard events.
    
    Args:
        text (str): The text to type.
        interval (float, optional): Pause between keystrokes in seconds. Defaults to 0.05.
        
    Returns:
        str: Success message or error.
    """
    try:
        pyautogui.write(text, interval=interval)
        return f"Successfully typed text: '{text}'"
    except Exception as e:
        return f"Error typing text: {str(e)}"


@tool
def press_key(key: str) -> str:
    """Press a keyboard key or keyboard combination (e.g. 'enter', 'esc', 'tab', or shortcuts like 'ctrl+c').
    
    Args:
        key (str): Key name or combination string. Examples: 'enter', 'space', 'left', 'ctrl', 'command'.
                   For combinations, join with plus sign (e.g., 'command+c', 'ctrl+alt+delete').
        
    Returns:
        str: Success message or error.
    """
    try:
        if '+' in key:
            keys = [k.strip() for k in key.split('+')]
            # Use pyautogui's hotkey context manager to press keys sequentially and release in reverse
            pyautogui.hotkey(*keys)
            return f"Successfully pressed hotkey combination: {keys}"
        else:
            pyautogui.press(key)
            return f"Successfully pressed key: '{key}'"
    except Exception as e:
        return f"Error pressing key: {str(e)}"


@tool
def take_screenshot(filename: str = "screenshot.png") -> str:
    """Capture a screenshot of the main display screen and save it to a file.
    
    Args:
        filename (str, optional): Path where the image file will be saved. Defaults to "screenshot.png".
        
    Returns:
        str: Success message with absolute path, or error message.
    """
    try:
        # Resolve full path
        full_path = os.path.abspath(filename)
        # Create parent directories if they don't exist
        parent_dir = os.path.dirname(full_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
            
        screenshot = pyautogui.screenshot()
        screenshot.save(full_path)
        return f"Successfully captured screen and saved to: {full_path}"
    except Exception as e:
        return (
            f"Error capturing screenshot: {str(e)}. "
            "Note: On macOS, this might require Screen Recording permissions."
        )


@tool
def open_application(app_name_or_path: str) -> str:
    """Open an application or file on the user's system.
    
    On macOS, you can pass the application name (e.g. 'Safari', 'TextEdit', 'Notes')
    or a filepath/URL to open with its default handler. On Windows/Linux, it starts
    the executable or file path.
    
    Args:
        app_name_or_path (str): The name of the application or path to executable/file.
        
    Returns:
        str: Success or error message.
    """
    import sys
    try:
        if sys.platform == "darwin":
            # Attempt to run: open -a "App Name"
            result = subprocess.run(
                ["open", "-a", app_name_or_path],
                capture_output=True,
                text=True,
                check=True
            )
            return f"Successfully opened application: '{app_name_or_path}'"
        elif sys.platform == "win32":
            os.startfile(app_name_or_path)
            return f"Successfully opened application: '{app_name_or_path}'"
        else:
            # Linux: try xdg-open
            subprocess.Popen(["xdg-open", app_name_or_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Successfully opened: '{app_name_or_path}'"
    except Exception as e:
        # Fallback for macOS: try general open path/URL if -a failed
        if sys.platform == "darwin":
            try:
                subprocess.run(["open", app_name_or_path], check=True, capture_output=True)
                return f"Successfully opened: '{app_name_or_path}'"
            except Exception as inner_e:
                pass
        return f"Error opening application/file '{app_name_or_path}': {str(e)}"


# Export all defined system and GUI tools as a list
system_toolset = [
    run_command,
    get_screen_size,
    get_mouse_position,
    mouse_move,
    mouse_click,
    type_text,
    press_key,
    take_screenshot,
    open_application
]
