"""Suppoort for Ariston Aqua binary sensors."""

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_CONNECTIVITY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_HEAT,
    DEVICE_CLASS_UPDATE,
    BinarySensorEntity,
)
from homeassistant.const import CONF_BINARY_SENSORS, CONF_NAME

import logging
from datetime import timedelta

from .const import (
    DATA_ARISTONAQUA,
    DEVICES,
    VALUE,
    PARAM_ON,
    PARAM_HEATING,
    PARAM_CLEANSE,
    PARAM_ECO,
    PARAM_UPDATE,
    PARAM_ONLINE,
    PARAM_CHANGING_DATA,
    PARAM_ONLINE_VERSION,
)

BINARY_SENSOR_ON = "Power"
BINARY_SENSOR_HEATING = "Heating"
BINARY_SENSOR_CLEANSE = "Antilegionella"
BINARY_SENSOR_ECO = "Eco"
BINARY_SENSOR_ONLINE = "Online"
BINARY_SENSOR_UPDATE = "Update Available"
BINARY_SENSOR_CHANGING_DATA = "Changing Data Ongoing"

SCAN_INTERVAL = timedelta(seconds=2)

_LOGGER = logging.getLogger(__name__)

# Binary sensor types are defined like: Name, device class, icon
BINARY_SENSORS = {
    PARAM_ONLINE: (BINARY_SENSOR_ONLINE, DEVICE_CLASS_CONNECTIVITY, None),
    PARAM_CHANGING_DATA: (BINARY_SENSOR_CHANGING_DATA, None, "mdi:cogs"),
    PARAM_UPDATE: (BINARY_SENSOR_UPDATE, DEVICE_CLASS_UPDATE, None),
    PARAM_ON: (BINARY_SENSOR_ON, DEVICE_CLASS_POWER, "mdi:power"),
    PARAM_HEATING: (BINARY_SENSOR_HEATING, DEVICE_CLASS_HEAT, None),
    PARAM_CLEANSE: (BINARY_SENSOR_CLEANSE, None, "mdi:bacteria-outline"),
    PARAM_ECO: (BINARY_SENSOR_ECO, None, "mdi:leaf"),
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up a binary sensor for Ariston Aqua."""
    if discovery_info is None:
        return

    name = discovery_info[CONF_NAME]
    device = hass.data[DATA_ARISTONAQUA][DEVICES][name]
    add_entities(
        [
            AristonAquaBinarySensor(name, device, sensor_type)
            for sensor_type in discovery_info[CONF_BINARY_SENSORS]
        ],
        True,
    )


class AristonAquaBinarySensor(BinarySensorEntity):
    """Binary sensor for Ariston Aqua."""

    def __init__(self, name, device, sensor_type):
        """Initialize entity."""
        self._api = device.api.ariston_api
        self._attrs = {}
        self._device_class = BINARY_SENSORS[sensor_type][1]
        self._icon = BINARY_SENSORS[sensor_type][2]
        self._name = "{} {}".format(name, BINARY_SENSORS[sensor_type][0])
        self._sensor_type = sensor_type
        self._state = None

    @property
    def unique_id(self):
        """Return the unique id."""
        return f"{self._name}-{self._sensor_type}"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attrs

    @property
    def should_poll(self):
        """Return True if entity has to be polled for state."""
        return True

    @property
    def name(self):
        """Return entity name."""
        return self._name

    @property
    def is_on(self):
        """Return if entity is on."""
        return self._state

    @property
    def device_class(self):
        """Return device class."""
        return self._device_class

    @property
    def available(self):
        """Return True if entity is available."""
        if self._sensor_type == PARAM_ONLINE:
            return True
        elif self._sensor_type == PARAM_CHANGING_DATA:
            return self._api.available
        else:
            return (
                self._api.available
                and not self._api.sensor_values[self._sensor_type][VALUE] is None
            )

    @property
    def icon(self):
        """Return the state attributes."""
        return self._icon

    def update(self):
        """Update entity."""
        try:
            if self._sensor_type == PARAM_ONLINE:
                self._state = self._api.available
            elif self._sensor_type == PARAM_CHANGING_DATA:
                self._state = self._api.setting_data
            elif self._sensor_type == PARAM_UPDATE:
                self._attrs["Installed"] = self._api.version
                self._state = self._api.sensor_values[self._sensor_type][VALUE]
                self._attrs["Online"] = self._api.sensor_values[PARAM_ONLINE_VERSION][
                    VALUE
                ]
            else:
                if not self._api.available:
                    return
                if not self._api.sensor_values[self._sensor_type][VALUE] is None:
                    self._state = self._api.sensor_values[self._sensor_type][VALUE]
                else:
                    self._state = False
        except KeyError:
            _LOGGER.warning("Problem updating binary_sensors for Ariston Aqua")
