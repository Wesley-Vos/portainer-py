from datetime import datetime

from .. import utils


class ContainerApiMixin:
    async def containers(self, quiet=False, all=False, trunc=False, latest=False,
                   since=None, before=None, limit=-1, size=False,
                   filters=None):
        """
        List containers. Similar to the ``docker ps`` command.

        Args:
            quiet (bool): Only display numeric Ids
            all (bool): Show all containers. Only running containers are shown
                by default
            trunc (bool): Truncate output
            latest (bool): Show only the latest created container, include
                non-running ones.
            since (str): Show only containers created since Id or Name, include
                non-running ones
            before (str): Show only container created before Id or Name,
                include non-running ones
            limit (int): Show `limit` last created containers, include
                non-running ones
            size (bool): Display sizes
            filters (dict): Filters to be processed on the image list.
                Available filters:

                - `exited` (int): Only containers with specified exit code
                - `status` (str): One of ``restarting``, ``running``,
                    ``paused``, ``exited``
                - `label` (str|list): format either ``"key"``, ``"key=value"``
                    or a list of such.
                - `id` (str): The id of the container.
                - `name` (str): The name of the container.
                - `ancestor` (str): Filter by container ancestor. Format of
                    ``<image-name>[:tag]``, ``<image-id>``, or
                    ``<image@digest>``.
                - `before` (str): Only containers created before a particular
                    container. Give the container name or id.
                - `since` (str): Only containers created after a particular
                    container. Give container name or id.

                A comprehensive list can be found in the documentation for
                `docker ps
                <https://docs.docker.com/engine/reference/commandline/ps>`_.

        Returns:
            A list of dicts, one per container

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        params = {
            'limit': 1 if latest else limit,
            'all': 1 if all else 0,
            'size': 1 if size else 0,
            'trunc_cmd': 1 if trunc else 0,
            'since': since,
            'before': before
        }
        if filters:
            params['filters'] = utils.convert_filters(filters)
        res = await self._get(path="/containers/json", query=params)

        if quiet:
            return [{'Id': x['Id']} for x in res]
        if trunc:
            for x in res:
                x['Id'] = x['Id'][:12]
        return res

    @utils.check_resource('container')
    async def inspect_container(self, container):
        """
        Identical to the `docker inspect` command, but only for containers.

        Args:
            container (str): The container to inspect

        Returns:
            (dict): Similar to the output of `docker inspect`, but as a
            single dict

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return await self._get(f"/containers/{container}/json")

    @utils.check_resource('container')
    async def kill(self, container, signal=None):
        """
        Kill a container or send a signal to a container.

        Args:
            container (str): The container to kill
            signal (str or int): The signal to send. Defaults to ``SIGKILL``

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        params = {}
        if signal is not None:
            if not isinstance(signal, str):
                signal = int(signal)
            params['signal'] = signal

        return await self._post(f"/containers/{container}/kill", query=params)

    @utils.check_resource('container')
    async def pause(self, container):
        """
        Pauses all processes within a container.

        Args:
            container (str): The container to pause

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return await self._post(f"/containers/{container}/pause")

    @utils.check_resource('container')
    async def restart(self, container, timeout=10):
        """
        Restart a container. Similar to the ``docker restart`` command.

        Args:
            container (str or dict): The container to restart. If a dict, the
                ``Id`` key is used.
            timeout (int): Number of seconds to try to stop for before killing
                the container. Once killed it will then be restarted. Default
                is 10 seconds.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        params = {'t': timeout}
        return await self._post(f"/containers/{container}/restart", query=params)

    @utils.check_resource('container')
    async def start(self, container, *args, **kwargs):
        """
        Start a container. Similar to the ``docker start`` command, but
        doesn't support attach options.

        **Deprecation warning:** Passing configuration options in ``start`` is
        no longer supported. Users are expected to provide host config options
        in the ``host_config`` parameter of
        :py:meth:`~ContainerApiMixin.create_container`.


        Args:
            container (str): The container to start

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
            :py:class:`docker.errors.DeprecatedMethod`
                If any argument besides ``container`` are provided.

        Example:

            >>> container = client.api.create_container(
            ...     image='busybox:latest',
            ...     command='/bin/sleep 30')
            >>> client.api.start(container=container.get('Id'))
        """
        if args or kwargs:
            raise errors.DeprecatedMethod(
                'Providing configuration in the start() method is no longer '
                'supported. Use the host_config param in create_container '
                'instead.'
            )
        
        return await self._post(f"/containers/{container}/start")

    @utils.check_resource('container')
    async def stats(self, container):
        """
        Return statistics for a specific container. Similar to the
        ``docker stats`` command.

        Args:
            container (str): The container to stream statistics from
            decode (bool): If set to true, stream will be decoded into dicts
                on the fly. Only applicable if ``stream`` is True.
                False by default.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.

        """
        return await self._get(f"/containers/{container}/stats", query={'stream': "false"})

    @utils.check_resource('container')
    async def stop(self, container, timeout=10):
        """
        Stops a container. Similar to the ``docker stop`` command.

        Args:
            container (str): The container to stop
            timeout (int): Timeout in seconds to wait for the container to
                stop before sending a ``SIGKILL``. If None, then the
                StopTimeout value of the container will be used.
                Default: None

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """

        params = {'t': timeout}
        return await self._post(f"/containers/{container}/stop", query=params)

    @utils.check_resource('container')
    async def top(self, container, ps_args=None):
        """
        Display the running processes of a container.

        Args:
            container (str): The container to inspect
            ps_args (str): An optional arguments passed to ps (e.g. ``aux``)

        Returns:
            (str): The output of the top

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        params = {}
        if ps_args is not None:
            params['ps_args'] = ps_args
        
        return await self._get(f"/containers/{container}/top", query=params)
