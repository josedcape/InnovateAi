"""
Models for AI agents in the INNOVATE AI application
"""
from enum import Enum

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
        self.icon = icon or f"/static/icons/{agent_type.value}-icon.svg"
    
    def to_dict(self):
        """Convert agent to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'type': self.agent_type.value,
            'description': self.description,
            'icon': self.icon
        }


def get_all_agents():
    """Return all available agents"""
    return [
        Agent(
            name="Standard Assistant",
            agent_type=AgentType.DEFAULT,
            description="General-purpose AI assistant with conversation capabilities"
        ),
        Agent(
            name="Web Search Assistant",
            agent_type=AgentType.WEB_SEARCH,
            description="AI assistant that can search the web for the latest information"
        ),
        Agent(
            name="Computer Use Assistant",
            agent_type=AgentType.COMPUTER_USE,
            description="AI assistant that can perform tasks on your computer"
        ),
        Agent(
            name="File Search Assistant",
            agent_type=AgentType.FILE_SEARCH,
            description="AI assistant that can search through your uploaded documents"
        )
    ]


def get_agent_by_type(agent_type):
    """Get agent by type"""
    if isinstance(agent_type, str):
        try:
            agent_type = AgentType(agent_type)
        except ValueError:
            return None
    
    for agent in get_all_agents():
        if agent.agent_type == agent_type:
            return agent
    
    return None