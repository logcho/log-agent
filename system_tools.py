import subprocess
import os
import pyautogui
import time
from langchain_core.tools import tool

# Apple native Vision libraries for OCR
import Quartz
import Vision
from Cocoa import NSURL
from Foundation import NSDictionary

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


@tool
def gui_get_screen_text() -> str:
    """Perform native macOS OCR on the entire screen to extract and list all visible text.
    
    Returns a list of all detected text strings and their center coordinates (X, Y) in screen points,
    which is useful to 'see' what is currently on the screen.
    
    Returns:
        str: A formatted list of visible texts and coordinates, or an error.
    """
    try:
        temp_path = os.path.abspath("ocr_screen_temp.png")
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        screenshot = pyautogui.screenshot()
        screenshot.save(temp_path)
        
        try:
            screen_w, screen_h = pyautogui.size()
            input_url = NSURL.fileURLWithPath_(temp_path)
            input_image = Quartz.CIImage.imageWithContentsOfURL_(input_url)
            
            vision_request = Vision.VNRecognizeTextRequest.alloc().init()
            vision_request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
            
            vision_handler = Vision.VNImageRequestHandler.alloc().initWithCIImage_options_(
                input_image, NSDictionary.dictionaryWithDictionary_({})
            )
            
            success, error = vision_handler.performRequests_error_([vision_request], None)
            if not success:
                return f"OCR analysis failed: {error}"
                
            observations = vision_request.results()
            if not observations:
                return "No visible text detected on screen."
                
            lines = [f"Text detected on screen (Resolution: {screen_w}x{screen_h}):"]
            for obs in observations:
                top_candidate = obs.topCandidates_(1)[0]
                text = top_candidate.string()
                confidence = top_candidate.confidence()
                
                if confidence < 0.3:
                    continue
                    
                bbox = obs.boundingBox()
                try:
                    origin, size = bbox
                    norm_x, norm_y = origin
                    norm_w, norm_h = size
                except Exception:
                    norm_x = bbox.origin.x
                    norm_y = bbox.origin.y
                    norm_w = bbox.size.width
                    norm_h = bbox.size.height
                    
                x_center = int((norm_x + norm_w / 2) * screen_w)
                y_center = int((1.0 - (norm_y + norm_h / 2)) * screen_h)
                
                lines.append(f"  • [X={x_center}, Y={y_center}] \"{text}\"")
                
            return "\n".join(lines)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    except Exception as e:
        return f"Error getting screen text: {str(e)}"


@tool
def gui_click_text_on_screen(text_query: str, click_type: str = "single", occurrence: int = 1) -> str:
    """Locate a specific text on screen using OCR and perform a mouse click on it.
    
    Args:
        text_query (str): The text to search for on the screen (case-insensitive).
        click_type (str, optional): Type of click: 'single', 'double', or 'right'. Defaults to 'single'.
        occurrence (int, optional): If multiple instances of the text match, specify which one to click (1-indexed). Defaults to 1.
        
    Returns:
        str: Success message confirming click coordinates, or an error.
    """
    try:
        temp_path = os.path.abspath("ocr_click_temp.png")
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        screenshot = pyautogui.screenshot()
        screenshot.save(temp_path)
        
        try:
            screen_w, screen_h = pyautogui.size()
            input_url = NSURL.fileURLWithPath_(temp_path)
            input_image = Quartz.CIImage.imageWithContentsOfURL_(input_url)
            
            vision_request = Vision.VNRecognizeTextRequest.alloc().init()
            vision_request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
            
            vision_handler = Vision.VNImageRequestHandler.alloc().initWithCIImage_options_(
                input_image, NSDictionary.dictionaryWithDictionary_({})
            )
            
            success, error = vision_handler.performRequests_error_([vision_request], None)
            if not success:
                return f"OCR analysis failed: {error}"
                
            observations = vision_request.results()
            if not observations:
                return "No text detected on screen."
                
            matches = []
            query_lower = text_query.lower()
            
            for obs in observations:
                top_candidate = obs.topCandidates_(1)[0]
                text = top_candidate.string()
                
                if query_lower in text.lower():
                    bbox = obs.boundingBox()
                    try:
                        origin, size = bbox
                        norm_x, norm_y = origin
                        norm_w, norm_h = size
                    except Exception:
                        norm_x = bbox.origin.x
                        norm_y = bbox.origin.y
                        norm_w = bbox.size.width
                        norm_h = bbox.size.height
                        
                    x_center = int((norm_x + norm_w / 2) * screen_w)
                    y_center = int((1.0 - (norm_y + norm_h / 2)) * screen_h)
                    matches.append((text, x_center, y_center))
            
            if not matches:
                return f"Text '{text_query}' not found on the screen."
                
            matches.sort(key=lambda m: (len(m[0]) - len(text_query), -len(m[0])))
            
            if occurrence > len(matches) or occurrence < 1:
                return f"Found {len(matches)} match(es) for '{text_query}', but occurrence={occurrence} is out of range."
                
            matched_text, click_x, click_y = matches[occurrence - 1]
            
            pyautogui.moveTo(click_x, click_y, duration=0.2)
            if click_type == "double":
                pyautogui.doubleClick(click_x, click_y)
            elif click_type == "right":
                pyautogui.rightClick(click_x, click_y)
            else:
                pyautogui.click(click_x, click_y)
                
            return f"Successfully clicked {click_type} on '{matched_text}' at coordinates [X={click_x}, Y={click_y}]."
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    except Exception as e:
        return f"Error clicking text: {str(e)}"


@tool
def gui_fill_labeled_input(label_text: str, text_to_type: str, direction: str = "right", offset: int = 100) -> str:
    """Locate a labeled text input field on the screen, click on it, and type the specified text.
    
    This works by finding the coordinates of `label_text` (e.g. 'Username' or 'Search'),
    clicking at a specified pixel offset in the given direction where the input box is located,
    clearing the existing text (using command+A, backspace), and typing the new text.
    
    Args:
        label_text (str): The label text identifying the input field.
        text_to_type (str): The text string to enter into the field.
        direction (str, optional): The relative direction of the input field from the label. 
                                   Options: 'right', 'below'. Defaults to 'right'.
        offset (int, optional): The distance in screen points from the center of the label to the click target. Defaults to 100.
        
    Returns:
        str: Success message confirming coordinates and typed text, or an error.
    """
    try:
        temp_path = os.path.abspath("ocr_input_temp.png")
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        screenshot = pyautogui.screenshot()
        screenshot.save(temp_path)
        
        try:
            screen_w, screen_h = pyautogui.size()
            input_url = NSURL.fileURLWithPath_(temp_path)
            input_image = Quartz.CIImage.imageWithContentsOfURL_(input_url)
            
            vision_request = Vision.VNRecognizeTextRequest.alloc().init()
            vision_request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
            
            vision_handler = Vision.VNImageRequestHandler.alloc().initWithCIImage_options_(
                input_image, NSDictionary.dictionaryWithDictionary_({})
            )
            
            success, error = vision_handler.performRequests_error_([vision_request], None)
            if not success:
                return f"OCR analysis failed: {error}"
                
            observations = vision_request.results()
            if not observations:
                return "No text detected on screen."
                
            matches = []
            query_lower = label_text.lower()
            
            for obs in observations:
                top_candidate = obs.topCandidates_(1)[0]
                text = top_candidate.string()
                
                if query_lower in text.lower():
                    bbox = obs.boundingBox()
                    try:
                        origin, size = bbox
                        norm_x, norm_y = origin
                        norm_w, norm_h = size
                    except Exception:
                        norm_x = bbox.origin.x
                        norm_y = bbox.origin.y
                        norm_w = bbox.size.width
                        norm_h = bbox.size.height
                        
                    x_center = int((norm_x + norm_w / 2) * screen_w)
                    y_center = int((1.0 - (norm_y + norm_h / 2)) * screen_h)
                    matches.append((text, x_center, y_center))
                    
            if not matches:
                return f"Label '{label_text}' not found on the screen."
                
            matches.sort(key=lambda m: (len(m[0]) - len(label_text), -len(m[0])))
            matched_label, label_x, label_y = matches[0]
            
            target_x, target_y = label_x, label_y
            direction_clean = direction.lower().strip()
            if direction_clean == "right":
                target_x = label_x + offset
            elif direction_clean == "below":
                target_y = label_y + offset
            else:
                return f"Invalid direction '{direction}'. Supported directions: 'right', 'below'."
                
            pyautogui.moveTo(target_x, target_y, duration=0.2)
            pyautogui.click(target_x, target_y)
            time.sleep(0.1)
            
            pyautogui.hotkey('command', 'a')
            time.sleep(0.05)
            pyautogui.press('backspace')
            time.sleep(0.05)
            
            pyautogui.write(text_to_type, interval=0.01)
            
            return (
                f"Successfully located label '{matched_label}' at [X={label_x}, Y={label_y}]. "
                f"Clicked target field at [X={target_x}, Y={target_y}] ({direction_clean} by {offset}) "
                f"and entered '{text_to_type}'."
            )
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    except Exception as e:
        return f"Error filling input: {str(e)}"


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
    open_application,
    gui_get_screen_text,
    gui_click_text_on_screen,
    gui_fill_labeled_input
]
