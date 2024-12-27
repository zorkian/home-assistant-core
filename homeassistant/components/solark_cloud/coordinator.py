"""DataUpdateCoordinator for Sol-Ark Cloud."""

from datetime import timedelta
import logging
import time

from solark_cloud import AuthenticationError, SolArkCloud

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SolArkCloudCoordinator(DataUpdateCoordinator):
    """My example coordinator."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""

        # Set variables from values entered in config flow setup
        self.username = config_entry.data[CONF_USERNAME]
        self.password = config_entry.data[CONF_PASSWORD]

        # set variables from options.  You need a default here in case options have not been set
        self.poll_interval = config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        # Initialise DataUpdateCoordinator
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({config_entry.unique_id})",
            # Method to call on every update interval.
            update_method=self.async_update_data,
            # Polling interval. Will only be polled if there are subscribers.
            # Using config option here but you can just use a value.
            update_interval=timedelta(seconds=self.poll_interval),
        )

        # Initialise your api here
        self.api = SolArkCloud()

    async def async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        plants, flows = None, None
        try:
            if not self.api.access_token or self.api.expires_at < time.time():
                await self.hass.async_add_executor_job(
                    self.api.login, self.username, self.password
                )
            plants_response = await self.hass.async_add_executor_job(self.api.plants)
            plants = plants_response.plants
            flows = {}
            for plant_id in plants:
                flows[plant_id] = await self.hass.async_add_executor_job(
                    self.api.flow, plant_id
                )
        except AuthenticationError as e:
            _LOGGER.error(e)
            raise UpdateFailed(e) from e
        except Exception as e:
            # This will show entities as unavailable by raising UpdateFailed exception
            _LOGGER.error(e)
            raise UpdateFailed(f"Error communicating with API: {e}") from e

        # What is returned here is stored in self.data by the DataUpdateCoordinator
        return self.data
