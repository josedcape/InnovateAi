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
from PIL import Image, ImageDraw, ImageFont
import tempfile
import random
import uuid
from uuid import uuid4

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
        """Return a visually rich placeholder screenshot"""
        try:
            # Create a blank image with background color
            img = Image.new('RGB', (self.width, self.height), color=(245, 245, 245))
            draw = ImageDraw.Draw(img)
            
            # Add browser chrome (header)
            draw.rectangle([(0, 0), (self.width, 80)], fill=(53, 54, 58))
            
            # Add browser controls
            # Back button
            draw.rectangle([(10, 30), (40, 50)], fill=(70, 70, 70))
            draw.polygon([(15, 40), (25, 30), (25, 50)], fill=(200, 200, 200))
            
            # Forward button
            draw.rectangle([(45, 30), (75, 50)], fill=(70, 70, 70))
            draw.polygon([(70, 40), (60, 30), (60, 50)], fill=(200, 200, 200))
            
            # Reload button
            draw.rectangle([(80, 30), (110, 50)], fill=(70, 70, 70))
            draw.ellipse([(85, 35), (105, 45)], outline=(200, 200, 200), width=2)
            
            # Add address bar
            draw.rectangle([(120, 30), (self.width - 120, 50)], fill=(255, 255, 255), outline=(200, 200, 200))
            draw.text((130, 35), self.current_url, fill=(0, 0, 0))
            
            # Menu button
            draw.rectangle([(self.width - 50, 30), (self.width - 20, 50)], fill=(70, 70, 70))
            draw.rectangle([(self.width - 45, 35), (self.width - 25, 37)], fill=(200, 200, 200))
            draw.rectangle([(self.width - 45, 40), (self.width - 25, 42)], fill=(200, 200, 200))
            draw.rectangle([(self.width - 45, 45), (self.width - 25, 47)], fill=(200, 200, 200))
            
            # Page content based on URL
            if "google.com" in self.current_url:
                # Draw Google-like interface
                # Logo
                draw.rectangle([(self.width/2 - 150, 150), (self.width/2 + 150, 200)], fill=(235, 235, 235))
                draw.text((self.width/2 - 50, 170), "Google", fill=(66, 133, 244), align="center")
                
                # Search box
                draw.rectangle([(self.width/2 - 200, 220), (self.width/2 + 200, 260)], fill=(255, 255, 255), outline=(200, 200, 200), width=1)
                
                # Buttons
                draw.rectangle([(self.width/2 - 100, 290), (self.width/2 - 20, 320)], fill=(240, 240, 240), outline=(220, 220, 220))
                draw.text((self.width/2 - 85, 300), "Search", fill=(0, 0, 0))
                
                draw.rectangle([(self.width/2 + 20, 290), (self.width/2 + 140, 320)], fill=(240, 240, 240), outline=(220, 220, 220))
                draw.text((self.width/2 + 25, 300), "I'm Feeling Lucky", fill=(0, 0, 0))
                
            elif "example.com" in self.current_url:
                # Example.com page
                draw.rectangle([(100, 120), (self.width - 100, 170)], fill=(235, 235, 235))
                draw.text((120, 140), "Example Domain", fill=(0, 0, 0))
                
                for i in range(3):
                    y_pos = 200 + i * 60
                    draw.rectangle([(100, y_pos), (self.width - 100, y_pos + 40)], fill=(245, 245, 245), outline=(220, 220, 220))
                    draw.text((120, y_pos + 15), f"Sample content block {i+1}", fill=(0, 0, 0))
            
            else:
                # Generic page
                draw.rectangle([(100, 120), (self.width - 100, 170)], fill=(235, 235, 235))
                page_title = self.current_url.split('//')[1].split('/')[0] if '//' in self.current_url else "Website"
                draw.text((120, 140), f"{page_title}", fill=(0, 0, 0))
                
                # Menu
                draw.rectangle([(100, 180), (300, 400)], fill=(250, 250, 250), outline=(230, 230, 230))
                menu_items = ["Home", "About", "Products", "Services", "Contact"]
                for i, item in enumerate(menu_items):
                    draw.text((120, 200 + i * 40), item, fill=(0, 0, 0))
                
                # Content area
                draw.rectangle([(320, 180), (self.width - 100, 400)], fill=(255, 255, 255), outline=(230, 230, 230))
                draw.text((340, 200), "Welcome to our website", fill=(0, 0, 0))
                draw.text((340, 240), "This is a simulated browser view for", fill=(0, 0, 0))
                draw.text((340, 260), "demonstrating OpenAI's Computer Use capability", fill=(0, 0, 0))
                
                # Add footer
                draw.rectangle([(100, 420), (self.width - 100, 460)], fill=(240, 240, 240))
                draw.text((120, 435), "© 2025 Simulated Browser | Privacy | Terms", fill=(100, 100, 100))
            
            # Add notification that this is a simulation
            draw.rectangle([(20, self.height - 40), (self.width - 20, self.height - 20)], fill=(255, 240, 200))
            draw.text((30, self.height - 35), 
                     "Simulated Browser - OpenAI Computer Use API - No real web browsing available in this environment", 
                     fill=(150, 100, 50))
            
            # Save to a file
            static_temp_dir = os.path.join(os.getcwd(), "static", "temp")
            os.makedirs(static_temp_dir, exist_ok=True)
            screenshot_file = os.path.join(static_temp_dir, f"screenshot_{int(time.time())}.png")
            img.save(screenshot_file)
            self.screenshot_path = screenshot_file
            
            # Convert to base64 for API
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
                logger.info(f"Navigated to: {self.current_url}")
                
            elif action_type == "click":
                x, y = action.get("x", 0), action.get("y", 0)
                logger.info(f"Clicked at position: ({x}, {y})")
                
                # Simulate navigation based on click position
                if y < 50:  # Browser controls area
                    if 10 <= x <= 40:  # Back button
                        logger.info("Clicked back button")
                    elif 45 <= x <= 75:  # Forward button
                        logger.info("Clicked forward button")
                    elif 80 <= x <= 110:  # Reload button
                        logger.info("Clicked reload button")
                
                # Handle Google-like interface clicks
                elif "google.com" in self.current_url:
                    if 150 <= y <= 260 and (self.width/2 - 200) <= x <= (self.width/2 + 200):
                        # Clicked in search box
                        logger.info("Clicked Google search box")
                    elif 290 <= y <= 320:
                        if (self.width/2 - 100) <= x <= (self.width/2 - 20):
                            # Search button
                            logger.info("Clicked Google Search button")
                            if self.mock_actions and len(self.mock_actions) >= 2:
                                # Check for previous typing action
                                prev_actions = [a for a in self.mock_actions[-2:] if a.get("type") == "type"]
                                if prev_actions:
                                    search_term = prev_actions[0].get("text", "")
                                    self.current_url = f"https://www.google.com/search?q={search_term.replace(' ', '+')}"
                                    logger.info(f"Simulated search for: {search_term}")
                
                # Handle example.com interface clicks
                elif "example.com" in self.current_url:
                    # Just log clicks, no navigation changes
                    logger.info("Clicked on example.com page element")
                
                # Handle generic page clicks
                else:
                    # Check if menu item was clicked
                    if 180 <= y <= 400 and 100 <= x <= 300:
                        menu_index = (y - 200) // 40
                        if 0 <= menu_index < 5:  # We have 5 menu items
                            menu_items = ["Home", "About", "Products", "Services", "Contact"]
                            clicked_item = menu_items[int(menu_index)]
                            logger.info(f"Clicked menu item: {clicked_item}")
                            
                            # Update URL based on clicked menu item
                            domain = self.current_url.split('//')[1].split('/')[0] if '//' in self.current_url else "example.com"
                            self.current_url = f"https://{domain}/{clicked_item.lower()}"
                
            elif action_type == "type":
                text = action.get("text", "")
                logger.info(f"Typed text: {text}")
                
                # If we're typing in an address bar (based on Y position)
                if hasattr(self, "last_click_y") and getattr(self, "last_click_y", 0) < 50:
                    if text.startswith("http") or "." in text:
                        self.current_url = text if text.startswith("http") else f"https://{text}"
                
            elif action_type == "press":
                key = action.get("key", "")
                logger.info(f"Pressed key: {key}")
                
                # Handle Enter key specially
                if key.lower() == "enter":
                    # Check for previous typing action
                    if self.mock_actions and len(self.mock_actions) >= 2:
                        prev_actions = [a for a in self.mock_actions[-2:] if a.get("type") == "type"]
                        if prev_actions:
                            text = prev_actions[0].get("text", "")
                            if text.startswith("http") or "." in text:
                                self.current_url = text if text.startswith("http") else f"https://{text}"
                            elif "google.com" in self.current_url:
                                self.current_url = f"https://www.google.com/search?q={text.replace(' ', '+')}"
            
            # Store last click position for context in future actions
            if action_type == "click":
                self.last_click_x = action.get("x", 0)
                self.last_click_y = action.get("y", 0)
                
            return True
            
        except Exception as e:
            logger.error(f"Error simulating action: {e}")
            return False
        
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
                            "type": "input_text",
                            "text": instructions
                        },
                        {
                            "type": "input_image",
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
                                        "type": "input_text",
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
                    if item.type == "output_text":
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