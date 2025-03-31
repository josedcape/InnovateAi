"""
Service for autonomous browser navigation using OpenAI computer-use-preview model.
This service creates a virtual browser window that can be controlled by AI to perform tasks.
"""
import os
import base64
import json
import logging
import time
from io import BytesIO
from PIL import Image
import tempfile

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

# Define a mock for simulation if playwright is not available
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
        """Return a placeholder screenshot"""
        try:
            # Create a blank image
            img = Image.new('RGB', (self.width, self.height), color=(240, 240, 240))
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            
            # Save to a file
            screenshot_file = os.path.join(self.temp_dir, f"screenshot_{int(time.time())}.png")
            with open(screenshot_file, "wb") as f:
                f.write(buffer.getvalue())
            self.screenshot_path = screenshot_file
            
            return base64.b64encode(buffer.getvalue()).decode("utf-8")
        except Exception as e:
            logger.error(f"Error creating mock screenshot: {e}")
            return None
            
    def execute_action(self, action):
        """Simulate executing a browser action"""
        self.mock_actions.append(action)
        logger.info(f"Simulated action: {action}")
        return True
        
    def get_current_url(self):
        """Return the simulated current URL"""
        if "type" in self.mock_actions[-1] if self.mock_actions else {}:
            if self.mock_actions[-1]["type"] == "type" and "text" in self.mock_actions[-1]:
                if self.mock_actions[-1]["text"].startswith("http"):
                    self.current_url = self.mock_actions[-1]["text"]
        return self.current_url
        
    def cleanup(self):
        """Cleanup simulated resources"""
        self.is_running = False
        logger.info("Mock browser resources cleaned up")

class VirtualBrowser:
    """
    Class for managing a virtual browser instance that can be controlled by OpenAI's computer-use-preview model.
    """
    def __init__(self, width=1024, height=768):
        """Initialize the virtual browser with specified dimensions."""
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
                headless=False,  # Set to True for production
                chromium_sandbox=True,
                env={},
                args=[
                    "--disable-extensions",
                    "--disable-file-system"
                ]
            )
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            self.page.set_viewport_size({"width": self.width, "height": self.height})
            self.page.goto("https://www.google.com")  # Start with Google
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
            # Create a unique filename for the screenshot
            screenshot_file = os.path.join(self.temp_dir, f"screenshot_{int(time.time())}.png")
            self.page.screenshot(path=screenshot_file)
            self.screenshot_path = screenshot_file
            
            # Convert to base64 for API calls
            with open(screenshot_file, "rb") as img_file:
                screenshot_base64 = base64.b64encode(img_file.read()).decode("utf-8")
            
            return screenshot_base64
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
                
            elif action_type == "scroll":
                delta_x = action.get("delta_x", 0)
                delta_y = action.get("delta_y", 0)
                self.page.mouse.wheel(delta_x, delta_y)
                logger.info(f"Scrolled by ({delta_x}, {delta_y})")
                
            elif action_type == "wait":
                duration = action.get("duration", 1000)
                self.page.wait_for_timeout(duration)
                logger.info(f"Waited for {duration}ms")
                
            else:
                logger.warning(f"Unknown action type: {action_type}")
                return False
                
            # Allow time for the browser to update after the action
            self.page.wait_for_timeout(500)
            return True
        except Exception as e:
            logger.error(f"Failed to execute action {action}: {e}")
            return False
    
    def get_current_url(self):
        """Get the current URL of the browser."""
        if not self.is_running or not self.page:
            return "Browser not running"
        return self.page.url()
    
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
    """
    Process autonomous navigation instructions using OpenAI's computer-use-preview model.
    
    Args:
        client: OpenAI client instance
        instructions: Text instructions for navigation
        browser: Optional existing VirtualBrowser instance
    
    Returns:
        Tuple (instructions, summary, screenshot_path)
    """
    # Check if we have a valid browser instance, or create a new one
    created_browser = False
    if not browser or not browser.is_running:
        # Check if Playwright is available
        if PLAYWRIGHT_AVAILABLE:
            browser = VirtualBrowser()
            if not browser.start():
                logger.warning("Failed to start real browser, falling back to mock browser")
                browser = MockBrowser()
                if not browser.start():
                    return instructions, "No se pudo iniciar el navegador virtual.", None
        else:
            # Use mock browser if Playwright is not available
            logger.info("Playwright not available, using mock browser")
            browser = MockBrowser()
            if not browser.start():
                return instructions, "No se pudo iniciar el navegador virtual simulado.", None
        created_browser = True
    
    try:
        # Take a screenshot of the current state
        screenshot_base64 = browser.take_screenshot()
        if not screenshot_base64:
            return instructions, "No se pudo capturar el estado actual del navegador.", None
        
        # First API call with instructions and screenshot
        response = client.responses.create(
            model="computer-use-preview",
            tools=[{
                "type": "computer_use_preview",
                "display_width": browser.width,
                "display_height": browser.height,
                "environment": "browser"
            }],
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": instructions
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_base64}"
                            }
                        }
                    ]
                }
            ],
            reasoning={
                "generate_summary": "concise",
            },
            truncation="auto"
        )
        
        # Process the initial response
        actions_summary = []
        
        # Track maximum interaction rounds to prevent infinite loops
        max_rounds = 15
        current_round = 0
        
        # Continue processing actions until completion or max rounds reached
        while current_round < max_rounds:
            current_round += 1
            
            # Check for computer_call items in the response
            has_action = False
            
            for item in response.output:
                # Extract reasoning summary
                if item.type == "reasoning" and hasattr(item, "summary"):
                    for summary_item in item.summary:
                        if summary_item.type == "summary_text":
                            actions_summary.append(f"Paso {current_round}: {summary_item.text}")
                
                # Process computer action
                if item.type == "computer_call" and hasattr(item, "action"):
                    has_action = True
                    action = item.action
                    
                    # Execute the action
                    success = browser.execute_action(action)
                    if not success:
                        actions_summary.append(f"Error al ejecutar acción: {action}")
                        break
                    
                    # Take a new screenshot after the action
                    new_screenshot_base64 = browser.take_screenshot()
                    if not new_screenshot_base64:
                        actions_summary.append("Error al capturar pantalla después de la acción")
                        break
                    
                    # Send the result back to the model with updated format
                    response = client.responses.create(
                        model="computer-use-preview",
                        tools=[{
                            "type": "computer_use_preview",
                            "display_width": browser.width,
                            "display_height": browser.height,
                            "environment": "browser"
                        }],
                        input=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "Continúa con la tarea: " + instructions
                                    }
                                ]
                            }
                        ],
                        computer_call_output={
                            "call_id": item.call_id,
                            "image_url": {
                                "url": f"data:image/png;base64,{new_screenshot_base64}"
                            }
                        },
                        reasoning={
                            "generate_summary": "concise",
                        },
                        truncation="auto"
                    )
                    break  # Only process one action at a time
            
            # If no more actions or reached text response, end the loop
            if not has_action:
                # Check if we have a text response
                for item in response.output:
                    if item.type == "text":
                        actions_summary.append(f"Resultado: {item.text}")
                break
        
        # Final summary
        summary = "\n".join(actions_summary)
        if current_round >= max_rounds:
            summary += "\n\nNota: Se alcanzó el límite máximo de interacciones."
        
        # Return the final state
        return instructions, summary, browser.screenshot_path
        
    except Exception as e:
        logger.error(f"Error in autonomous navigation: {e}")
        return instructions, f"Error durante la navegación autónoma: {str(e)}", None
    
    finally:
        # Clean up resources if we created the browser instance
        if created_browser and browser:
            browser.cleanup()