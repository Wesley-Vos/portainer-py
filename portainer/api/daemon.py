class DaemonApiMixin:
    def version(self, api_version=True):
        """
        Returns version information from the server. Similar to the ``docker
        version`` command.

        Returns:
            (dict): The server version information

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        url = self._url("/version", versioned_api=api_version)
        return self._result(self._get(url), json=True)
