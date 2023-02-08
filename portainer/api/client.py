
import asyncio
import async_timeout

from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from functools import partial

import aiohttp
from yarl import URL

from ..constants import (MINIMUM_DOCKER_API_VERSION)
from ..utils import auth
from .container import ContainerApiMixin
from .daemon import DaemonApiMixin

class APIClient(
        ContainerApiMixin,
        DaemonApiMixin):

    def __init__(self, host=None, port=None, env_id=1, username=None, password=None, session=None):
        super().__init__()

        self.host = host
        self.port = port
        self._username = username
        self._password = password
        self._token = None
        self._token_expiry = None
        self._session = None
        self._close_session = False

        self.env_id = env_id

        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._close_session = True
        
    async def _refresh_token(self):
        if self._token is None or datetime.now() >= self._token_expiry:
            data = {
                "username": self._username,
                "password": self._password
            }

            print("Token needs to be refreshed")
            res = await self._request(
                path="/auth",
                abs_path=True,
                method="POST",
                data=data,
            )
            
            self._token = res["jwt"]
            self._token_expiry = datetime.now() + timedelta(hours=7, minutes=59)
    
    @auth
    async def _get(
        self,
        path: str,
        token: str = None,
        query: Any = {}
    ) -> None:
        return await self._request(path=path, query=query, token=token)

    @auth
    async def _post(
        self,
        path: str,
        data: Any = None,
        query: Any = {},
        token: str = None,
    ) -> None:
        return await self._request(path=path, query=query, data=data, token=token, method="POST")
    
    async def _request(
        self,
        path: str,
        *,
        abs_path: bool = False,
        query: Any = {},
        data: Any = None,
        method: str = "GET",
        token: str = None,
    ) -> Any:
        """Handle a request to the Rooted Toon."""
        query = {key: value for key, value in query.items() if value is not None} # filter out None query items
        path = f"/api{path}" if abs_path else f"/api/endpoints/1/docker{path}"
        
        url = URL.build(
            scheme="http",
            host=self.host,
            port=self.port,
            path=path,
            query=query,
        )
        
        headers = {
            "Accept": "application/json",
        }
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"

        try:
            with async_timeout.timeout(60):
                response = await self._session.request(
                    method,
                    url,
                    json=data,
                    headers=headers,
                    ssl=True,
                )
        except asyncio.TimeoutError as exception:
            raise RuntimeError(
                "Timeout occurred while connecting to Docker"
            ) from exception
        except (aiohttp.ClientError) as exception:
            raise RuntimeError(
                "Error occurred while communicating with Docker"
            ) from exception

        content_type = response.headers.get("Content-Type", "")
        
        # Error handling
        if (response.status // 100) in [4, 5]:
            contents = await response.read()
            response.close()

            return ActionResponse(success=False, message=contents.decode("utf8"))

        # Handle empty response
        if response.status == 204:
            return ActionResponse(success=True)

        if "application/json" in content_type:
            return await response.json(content_type="application/json")
        
        return await response.text()
    
    # @property
    # def api_version(self):
    #     return self._version

    async def close(self) -> None:
        """Close open client session."""
        if self._session and self._close_session:
            await self._session.close()


class ActionResponse:
    def __init__(self, success, message=None):
        self.success = success
        self.message = message
    
    def __str__(self) -> str:
        if self.success:
            return "Successfully executed action"
        else:
            return "Failed executing action because " + self.message