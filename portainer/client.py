from .api.client import APIClient
from .models.containers import ContainerCollection


class PortainerClient:
    """
    A client for communicating with a Portainer server.

    Example:

        >>> from portainer-py import PortainerClient
        >>> client = PortainerClient(host='localhost', port=9000, username='', password='')

    """
    def __init__(self, *args, **kwargs):
        self.api = APIClient(*args, **kwargs)
    
    # Resources
    @property
    def containers(self):
        """
        An object for managing containers on the server. See the
        :doc:`containers documentation <containers>` for full details.
        """
        return ContainerCollection(client=self)

    # Top-level methods
    def version(self, *args, **kwargs):
        return self.api.version(*args, **kwargs)

    def __getattr__(self, name):
        s = [f"'DockerClient' object has no attribute '{name}'"]
        # If a user calls a method on APIClient, they
        if hasattr(APIClient, name):
            s.append("In Docker SDK for Python 2.0, this method is now on the "
                     "object APIClient. See the low-level API section of the "
                     "documentation for more details.")
        raise AttributeError(' '.join(s))

    async def __aenter__(self):
        """Async enter."""
        return self

    async def __aexit__(self, *exc_info) -> None:
        """Async exit."""
        await self.api.close()
