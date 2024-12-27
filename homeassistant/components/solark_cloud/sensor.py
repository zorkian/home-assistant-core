"""Sol-Ark Cloud integration sensors."""

from dataclasses import dataclass
import logging
import typing

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SolArkCloudCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class SolArkCloudSensorEntityDescription(SensorEntityDescription):
    """Sensor entity description for SolarEdge."""


SENSOR_TYPES = [
    SolArkCloudSensorEntityDescription(
        key="soc",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Sensors."""
    # This gets the data update coordinator from hass.data as specified in your __init__.py
    coordinator: SolArkCloudCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ].coordinator

    # Enumerate all the sensors in your data value from your DataUpdateCoordinator and add an instance of your sensor class
    # to a list for each one.
    # This maybe different in your specific case, depending on how your data is structured
    sensors = []
    for plant in coordinator.data["plants"].values():
        sensors.extend(
            [PlantSensor(coordinator, plant, sensor) for sensor in SENSOR_TYPES]
        )

    # Create the sensors.
    async_add_entities(sensors)


class PlantSensor(CoordinatorEntity, SensorEntity):
    """Implementation of a sensor."""

    def __init__(
        self,
        coordinator: SolArkCloudCoordinator,
        plant: dict,
        sensor: SolArkCloudSensorEntityDescription,
    ) -> None:
        """Initialise sensor."""
        super().__init__(coordinator)
        self.plant = plant
        self.flow = None
        self.sensor = sensor

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        # This method is called by your DataUpdateCoordinator when a successful update runs.
        self.flow = self.coordinator.data["flows"].get_flow(self.plant["id"])
        self.async_write_ha_state()

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return device class."""
        # https://developers.home-assistant.io/docs/core/entity/sensor/#available-device-classes
        return self.sensor.device_class

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        # Identifiers are what group entities into the same device.
        # If your device is created elsewhere, you can just specify the identifiers parameter.
        # If your device connects via another device, add via_device parameter with the identifiers of that device.
        return DeviceInfo(
            name=f"Sol-Ark Cloud Plant #{self.plant['id']}",
            identifiers={
                (
                    DOMAIN,
                    self.plant["id"],
                )
            },
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"Sol-Ark Cloud Plant #{self.plant['id']} {self.sensor.key}"

    @property
    def native_value(self) -> int | float:
        """Return the state of the entity."""
        # Using native value and native unit of measurement, allows you to change units
        # in Lovelace and HA will automatically calculate the correct value.
        return getattr(self.flow, self.sensor.key)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return unit of temperature."""
        return self.sensor.native_unit_of_measurement

    @property
    def state_class(self) -> str | None:
        """Return state class."""
        # https://developers.home-assistant.io/docs/core/entity/sensor/#available-state-classes
        return self.sensor.state_class

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        # All entities must have a unique id.  Think carefully what you want this to be as
        # changing it later will cause HA to create new entities.
        return f"{DOMAIN}-{self.plant['id']}-{self.sensor.key}"

    @property
    def extra_state_attributes(self) -> dict[str, typing.Any]:
        """Return the extra state attributes."""
        # Add any additional attributes you want on your sensor.
        # attrs = {}
        # attrs["extra_info"] = "Extra Info"
        return {}
