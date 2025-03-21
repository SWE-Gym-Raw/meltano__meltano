"""Defines PluginRemoveService."""

from __future__ import annotations

import typing as t

from meltano.core.plugin_location_remove import (
    DbRemoveManager,
    InstallationRemoveManager,
    LockedDefinitionRemoveManager,
    MeltanoYmlRemoveManager,
    PluginLocationRemoveManager,
)
from meltano.core.utils import noop

if t.TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from meltano.core.plugin.project_plugin import ProjectPlugin
    from meltano.core.project import Project


class PluginRemoveService:
    """Handle plugin installation removal operations."""

    def __init__(self, project: Project):
        """Construct a PluginRemoveService instance.

        Args:
            project: The Meltano project.
        """
        self.project = project

    def remove_plugins(
        self,
        plugins: Sequence[ProjectPlugin],
        plugin_status_cb: Callable[[ProjectPlugin], None] = noop,
        removal_manager_status_cb: Callable[
            [PluginLocationRemoveManager],
            None,
        ] = noop,
    ) -> tuple[int, int]:
        """Remove multiple plugins.

        Returns a tuple containing:
        1. The total number of removed plugins
        2. The total number of plugins attempted

        Args:
            plugins: The plugins to remove.
            plugin_status_cb: A callback to call for each plugin.
            removal_manager_status_cb: A callback to call for each removal manager.

        Returns:
            A tuple containing:
            1. The total number of removed plugins
            2. The total number of plugins attempted
        """
        num_plugins: int = len(plugins)
        removed_plugins: int = num_plugins

        for plugin in plugins:
            plugin_status_cb(plugin)

            removal_managers = self.remove_plugin(plugin)

            any_not_removed = False
            for manager in removal_managers:
                any_not_removed = not manager.plugin_removed or any_not_removed
                removal_manager_status_cb(manager)

            if any_not_removed:
                removed_plugins -= 1

        return removed_plugins, num_plugins

    def remove_plugin(
        self,
        plugin: ProjectPlugin,
    ) -> tuple[PluginLocationRemoveManager, ...]:
        """Remove a plugin.

        Removes from `meltano.yml`, its installation in `.meltano`, and its settings in
        the Meltano system database.

        Args:
            plugin: The plugin to remove.

        Returns:
            A tuple containing a remove manager for each location.
        """
        remove_managers = (
            DbRemoveManager(plugin, self.project),
            MeltanoYmlRemoveManager(plugin, self.project),
            InstallationRemoveManager(plugin, self.project),
            LockedDefinitionRemoveManager(plugin, self.project),
        )

        for manager in remove_managers:
            manager.remove()

        return remove_managers
