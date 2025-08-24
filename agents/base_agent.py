from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    """
    @abstractmethod
    def run(self, *args, **kwargs) -> dict:
        """
        The main method to execute the agent's task.
        Must be implemented by all subclasses.
        """
        pass 