"""
Service for autonomous browser navigation using OpenAI computer-use-preview model.
This service creates a virtual browser window that can be controlled by AI to perform tasks.
"""
import os
import base64
import logging
import time
from PIL import Image, ImageDraw
import tempfile
from io import BytesIO

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import the necessary browser automation libraries
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    logger.warning("Playwright not available. Virtual browser functionality will be limited.")
    PLAYWRIGHT_AVAILABLE = False
except Exception as e:
    logger.error(f"Error importing Playwright: {e}")
    PLAYWRIGHT_AVAILABLE = False

class MockBrowser:
    """Simulated browser for when Playwright is not available"""
    def __init__(self, width=1024, height=768):
        self.width = width
        self.height = height
        self.is_running = True
        self.screenshot_path = None
        self.temp_dir = tempfile.mkdtemp()
        self.current_url = "https://www.google.com"
        self.mock_actions = []

    def start(self):
        """Start the simulated browser"""
        logger.info("Starting simulated browser (Playwright not available)")
        return True

    def take_screenshot(self):
        """Return a visually rich placeholder screenshot"""
        try:
            # Create a blank image with background color
            img = Image.new('RGB', (self.width, self.height), color=(245, 245, 245))
            draw = ImageDraw.Draw(img)

            # Add mock browser chrome and interface
            draw.rectangle([(0, 0), (self.width, 80)], fill=(53, 54, 58))
            draw.rectangle([(120, 30), (self.width - 120, 50)], fill=(255, 255, 255), outline=(200, 200, 200))
            draw.text((130, 35), self.current_url, fill=(0, 0, 0))

            # Save screenshot
            static_temp_dir = os.path.join(os.getcwd(), "tmp")
            os.makedirs(static_temp_dir, exist_ok=True)
            screenshot_file = os.path.join(static_temp_dir, f"screenshot_{int(time.time())}.png")
            img.save(screenshot_file)
            self.screenshot_path = screenshot_file

            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode("utf-8")

        except Exception as e:
            logger.error(f"Error creating mock screenshot: {e}")
            return None

    def execute_action(self, action):
        """Simulate executing a browser action"""
        self.mock_actions.append(action)
        logger.info(f"Simulated action: {action}")

        try:
            action_type = action.get("type", "")
            if action_type == "navigate":
                self.current_url = action.get("url", "https://www.google.com")
            elif action_type == "click":
                x, y = action.get("x", 0), action.get("y", 0)
                logger.info(f"Clicked at position: ({x}, {y})")
            elif action_type == "type":
                text = action.get("text", "")
                logger.info(f"Typed text: {text}")

            return True

        except Exception as e:
            logger.error(f"Error simulating action: {e}")
            return False

    def get_current_url(self):
        """Return the simulated current URL"""
        return self.current_url

    def cleanup(self):
        """Cleanup simulated resources"""
        self.is_running = False
        logger.info("Mock browser resources cleaned up")

class VirtualBrowser:
    """Class for managing a virtual browser instance that can be controlled by OpenAI's computer-use-preview model."""
    def __init__(self, width=1024, height=768):
        self.width = width
        self.height = height
        self.browser = None
        self.page = None
        self.playwright = None
        self.context = None
        self.is_running = False
        self.screenshot_path = None
        self.temp_dir = tempfile.mkdtemp()

    def start(self):
        """Start the virtual browser instance."""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Cannot start virtual browser: Playwright not installed")
            return False

        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=True,  # Set to True for production
                args=[
                    "--disable-extensions",
                    "--disable-file-system"
                ]
            )
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            self.page.set_viewport_size({"width": self.width, "height": self.height})
            self.page.goto("https://www.google.com")
            self.is_running = True
            logger.info("Virtual browser started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start virtual browser: {e}")
            self.cleanup()
            return False

    def take_screenshot(self):
        """Capture the current state of the browser window."""
        if not self.is_running or not self.page:
            logger.warning("Cannot take screenshot: Browser not running")
            return None

        try:
            # Create screenshot directory
            static_temp_dir = os.path.join(os.getcwd(), "tmp")
            os.makedirs(static_temp_dir, exist_ok=True)
            screenshot_file = os.path.join(static_temp_dir, f"screenshot_{int(time.time())}.png")

            # Take screenshot
            self.page.screenshot(path=screenshot_file)
            self.screenshot_path = screenshot_file

            # Convert to base64
            with open(screenshot_file, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None

    def execute_action(self, action):
        """Execute a browser action based on the model's suggestion."""
        if not self.is_running or not self.page:
            logger.warning("Cannot execute action: Browser not running")
            return False

        try:
            action_type = action.get("type")

            if action_type == "click":
                x, y = action.get("x"), action.get("y")
                self.page.mouse.click(x, y)
                logger.info(f"Clicked at position ({x}, {y})")

            elif action_type == "type":
                text = action.get("text", "")
                self.page.keyboard.type(text)
                logger.info(f"Typed text: {text}")

            elif action_type == "press":
                key = action.get("key", "")
                self.page.keyboard.press(key)
                logger.info(f"Pressed key: {key}")

            elif action_type == "wait":
                duration = action.get("duration", 1000)
                self.page.wait_for_timeout(duration)
                logger.info(f"Waited for {duration}ms")

            # Allow time for the browser to update
            self.page.wait_for_timeout(500)
            return True
        except Exception as e:
            logger.error(f"Failed to execute action {action}: {e}")
            return False

    def get_current_url(self):
        """Get the current URL of the browser."""
        if not self.is_running or not self.page:
            return "Browser not running"
        return self.page.url

    def cleanup(self):
        """Clean up resources."""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()

            self.is_running = False
            logger.info("Virtual browser resources cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up browser resources: {e}")

def process_autonomous_navigation(client, instructions, browser=None):
    """Process autonomous navigation instructions using OpenAI's computer-use-preview model."""
    created_browser = False
    if not browser or not browser.is_running:
        if PLAYWRIGHT_AVAILABLE:
            browser = VirtualBrowser()
            if not browser.start():
                logger.warning("Failed to start real browser, falling back to mock browser")
                browser = MockBrowser()
                if not browser.start():
                    return instructions, "No se pudo iniciar el navegador virtual.", None
        else:
            logger.info("Starting simulated browser (Playwright not available)")
            browser = MockBrowser()
            if not browser.start():
                return instructions, "No se pudo iniciar el navegador virtual simulado.", None
        created_browser = True

    try:
        # Take initial screenshot
        screenshot_base64 = browser.take_screenshot()
        if not screenshot_base64:
            return instructions, "No se pudo capturar el estado actual del navegador.", None

        # Create initial request
        response = client.responses.create(
            model="computer-use-preview",
            tools=[{
                "type": "computer_use_preview",
                "display_width": browser.width,
                "display_height": browser.height,
                "environment": "browser"
            }],
            input=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": instructions},
                    {"type": "image", "image_url": f"data:image/png;base64,{screenshot_base64}"}
                ]
            }],
            truncation="auto"
        )

        actions_summary = []
        max_rounds = 15
        current_round = 0

        # Process actions in a loop
        while current_round < max_rounds:
            current_round += 1

            # Check for computer_call items
            computer_calls = [item for item in response.output if item.type == "computer_call"]
            if not computer_calls:
                break

            computer_call = computer_calls[0]
            action = computer_call.action

            # Handle safety checks if present
            if hasattr(computer_call, 'pending_safety_checks') and computer_call.pending_safety_checks:
                # Log safety checks and acknowledge them
                for check in computer_call.pending_safety_checks:
                    logger.warning(f"Safety check triggered: {check.code} - {check.message}")
                    actions_summary.append(f"⚠️ Advertencia de seguridad: {check.message}")

            # Execute action
            success = browser.execute_action(action)
            if not success:
                actions_summary.append(f"Error al ejecutar acción: {action}")
                break

            # Take new screenshot
            new_screenshot_base64 = browser.take_screenshot()
            if not new_screenshot_base64:
                actions_summary.append("Error al capturar pantalla después de la acción")
                break

            # Send result back to model
            response = client.responses.create(
                model="computer-use-preview",
                previous_response_id=response.id,
                tools=[{
                    "type": "computer_use_preview",
                    "display_width": browser.width,
                    "display_height": browser.height,
                    "environment": "browser"
                }],
                input=[{
                    "type": "computer_call_output",
                    "call_id": computer_call.call_id,
                    "output": {
                        "type": "image",
                        "image_url": f"data:image/png;base64,{new_screenshot_base64}"
                    },
                    "current_url": browser.get_current_url()
                }],
                truncation="auto"
            )

        # Build final summary
        summary = "\n".join(actions_summary)
        if current_round >= max_rounds:
            summary += "\n\nNota: Se alcanzó el límite máximo de interacciones."

        return instructions, summary, browser.screenshot_path

    except Exception as e:
        logger.error(f"Error in autonomous navigation: {e}")
        return instructions, f"Error durante la navegación autónoma: {str(e)}", None

    finally:
        if created_browser and browser:
            browser.cleanup()