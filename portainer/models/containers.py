import copy
import ntpath
from collections import namedtuple

from ..errors import (
    DockerException, NotFound
)
from .resource import Collection, Model


class Container(Model):
    """ Local representation of a container object. Detailed configuration may
        be accessed through the :py:attr:`attrs` attribute. Note that local
        attributes are cached; users may call :py:meth:`reload` to
        query the Docker daemon for the current properties, causing
        :py:attr:`attrs` to be refreshed.
    """
    @property
    def name(self):
        """
        The name of the container.
        """
        if self.attrs.get('Name') is not None:
            return self.attrs['Name'].lstrip('/')

    @property
    def image(self):
        """
        The image of the container.
        """
        image_id = self.attrs.get('ImageID', self.attrs['Image'])
        if image_id is None:
            return None
        return self.client.images.get(image_id.split(':')[1])

    @property
    def labels(self):
        """
        The labels of a container as dictionary.
        """
        try:
            result = self.attrs['Config'].get('Labels')
            return result or {}
        except KeyError:
            raise DockerException(
                'Label data is not available for sparse objects. Call reload()'
                ' to retrieve all information'
            )
    
    @property
    def state_dict(self):
        if isinstance(self.attrs['State'], dict):
            return self.attrs['State']
        return None

    @property
    def status(self):
        """
        The status of the container. For example, ``running``, or ``exited``.
        """
        if isinstance(self.attrs['State'], dict):
            return self.attrs['State']['Status']
        return self.attrs['Status']

    @property
    def ports(self):
        """
        The ports that the container exposes as a dictionary.
        """
        return self.attrs.get('NetworkSettings', {}).get('Ports', {})

    @property
    def started_at(self):
        if isinstance(self.attrs['State'], dict):
            return self.attrs['State']['StartedAt']

    async def kill(self, signal=None):
        """
        Kill or send a signal to the container.

        Args:
            signal (str or int): The signal to send. Defaults to ``SIGKILL``

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """

        return await self.client.api.kill(self.id, signal=signal)

    async def pause(self):
        """
        Pauses all processes within this container.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return await self.client.api.pause(self.id)

    async def restart(self, **kwargs):
        """
        Restart this container. Similar to the ``docker restart`` command.

        Args:
            timeout (int): Number of seconds to try to stop for before killing
                the container. Once killed it will then be restarted. Default
                is 10 seconds.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return await self.client.api.restart(self.id, **kwargs)

    async def start(self, **kwargs):
        """
        Start this container. Similar to the ``docker start`` command, but
        doesn't support attach options.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return await self.client.api.start(self.id, **kwargs)

    def stats(self, **kwargs):
        """
        Stream statistics for this container. Similar to the
        ``docker stats`` command.

        Args:
            decode (bool): If set to true, stream will be decoded into dicts
                on the fly. Only applicable if ``stream`` is True.
                False by default.
            stream (bool): If set to false, only the current stats will be
                returned instead of a stream. True by default.

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.stats(self.id, **kwargs)

    async def stop(self, **kwargs):
        """
        Stops a container. Similar to the ``docker stop`` command.

        Args:
            timeout (int): Timeout in seconds to wait for the container to
                stop before sending a ``SIGKILL``. Default: 10

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return await self.client.api.stop(self.id, **kwargs)

    async def top(self, **kwargs):
        """
        Display the running processes of the container.

        Args:
            ps_args (str): An optional arguments passed to ps (e.g. ``aux``)

        Returns:
            (str): The output of the top

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return await self.client.api.top(self.id, **kwargs)


class ContainerCollection(Collection):
    model = Container

    async def get(self, container_id):
        """
        Get a container by name or ID.
        Args:
            container_id (str): Container name or ID.
        Returns:
            A :py:class:`Container` object.
        Raises:
            :py:class:`docker.errors.NotFound`
                If the container does not exist.
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        resp = await self.client.api.inspect_container(container_id)
        return self.prepare_model(resp)

    async def list(self, all=False, before=None, filters=None, limit=-1, since=None,
             sparse=False, ignore_removed=False):
        """
        List containers. Similar to the ``docker ps`` command.

        Args:
            all (bool): Show all containers. Only running containers are shown
                by default
            since (str): Show only containers created since Id or Name, include
                non-running ones
            before (str): Show only container created before Id or Name,
                include non-running ones
            limit (int): Show `limit` last created containers, include
                non-running ones
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

            sparse (bool): Do not inspect containers. Returns partial
                information, but guaranteed not to block. Use
                :py:meth:`Container.reload` on resulting objects to retrieve
                all attributes. Default: ``False``
            ignore_removed (bool): Ignore failures due to missing containers
                when attempting to inspect containers from the original list.
                Set to ``True`` if race conditions are likely. Has no effect
                if ``sparse=True``. Default: ``False``

        Returns:
            (list of :py:class:`Container`)

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        resp = await self.client.api.containers(all=all, before=before,
                                          filters=filters, limit=limit,
                                          since=since)
        if sparse:
            return [self.prepare_model(r) for r in resp]
        else:
            containers = []
            for r in resp:
                try:
                    containers.append(await self.get(r['Id']))
                # a container may have been removed while iterating
                except NotFound:
                    if not ignore_removed:
                        raise
            return containers


ExecResult = namedtuple('ExecResult', 'exit_code,output')
""" A result of Container.exec_run with the properties ``exit_code`` and
    ``output``. """
