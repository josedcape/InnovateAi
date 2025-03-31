from enum import Enum
import os

class AgentType(Enum):
    """Enum for different types of agents"""
    DEFAULT = "default"
    WEB_SEARCH = "web_search"
    COMPUTER_USE = "computer_use"
    FILE_SEARCH = "file_search"

class Agent:
    """
    Represents an AI agent with a specific functionality
    """
    def __init__(self, name, agent_type, description, icon=None):
        """
        Initialize a new Agent
        
        Args:
            name (str): Display name of the agent
            agent_type (AgentType): Type of agent
            description (str): Short description of the agent's capabilities
            icon (str, optional): Path to agent icon
        """
        self.name = name
        self.agent_type = agent_type
        self.description = description
        self.icon = icon
    
    def to_dict(self):
        """Convert agent to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "type": self.agent_type.value,
            "description": self.description,
            "icon": self.icon
        }

def get_all_agents():
    """Return all available agents"""
    agents = {
        AgentType.DEFAULT.value: Agent(
            name="INNOVATE AI Assistant",
            agent_type=AgentType.DEFAULT,
            description="General purpose AI assistant with conversation capabilities",
            icon="/static/icons/computer-icon.svg"
        ),
        AgentType.WEB_SEARCH.value: Agent(
            name="Web Search Agent",
            agent_type=AgentType.WEB_SEARCH,
            description="Search the web for current information and provide up-to-date answers",
            icon="/static/icons/search-icon.svg"
        ),
        AgentType.COMPUTER_USE.value: Agent(
            name="Computer Use Agent",
            agent_type=AgentType.COMPUTER_USE,
            description="Provide detailed guidance on using computers, software, and digital technologies",
            icon="/static/icons/computer-icon.svg"
        ),
        AgentType.FILE_SEARCH.value: Agent(
            name="File Search Agent",
            agent_type=AgentType.FILE_SEARCH,
            description="Search through uploaded documents to find specific information",
            icon="/static/icons/file-icon.svg"
        )
    }
    
    return {agent_type: agent.to_dict() for agent_type, agent in agents.items()}

def get_agent_by_type(agent_type):
    """Get agent by type"""
    agents = get_all_agents()
    return agents.get(agent_type)