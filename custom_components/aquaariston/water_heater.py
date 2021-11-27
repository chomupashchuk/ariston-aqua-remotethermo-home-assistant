"""Support for Ariston Aqua water heaters."""
import logging
from datetime import timedelta

from homeassistant.components.water_heater import (
    SUPPORT_OPERATION_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    WaterHeaterEntity,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_NAME,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)

from .const import (
    DATA_ARISTONAQUA,
    DEVICES,
    DOMAIN,
    VALUE,
    PARAM_ON,
    PARAM_REQUIRED_TEMPERATURE,
    PARAM_CURRENT_TEMPERATURE,
    PARAM_HEATING,
    PARAM_MODE,
)

ACTION_IDLE = "idle"
ACTION_HEATING = "heating"
UNKNOWN_TEMP = 0.0

SCAN_INTERVAL = timedelta(seconds=2)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Ariston Aqua water heater devices."""
    if discovery_info is None:
        return

    name = discovery_info[CONF_NAME]
    device = hass.data[DATA_ARISTONAQUA][DEVICES][name]

    add_entities([AristonAquaWaterHeater(name, device)])


class AristonAquaWaterHeater(WaterHeaterEntity):
    """Ariston Aqua Water Heater Device."""

    def __init__(self, name, device):
        """Initialize the thermostat."""
        self._name = name
        self._api = device.api.ariston_api

    @property
    def unique_id(self):
        """Return the unique ID for this thermostat."""
        return f"{self._name}-water_heater"

    @property
    def name(self):
        """Return the name of the Climate device."""
        return self._name

    @property
    def icon(self):
        """Return the name of the Water Heater device."""
        power_on = False
        try:
            if self._api.available:
                power_on = self._api.sensor_values[PARAM_ON][VALUE]
        except KeyError:
            return "mdi:water-pump-off"
        if power_on:
            return "mdi:water-pump"
        else:
            return "mdi:water-pump-off"

    @property
    def should_poll(self):
        """Polling is required."""
        return True

    @property
    def available(self):
        """Return True if entity is available."""
        return self._api.dhw_available

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE

    @property
    def current_temperature(self):
        """Return the temperature"""
        try:
            current_temp = self._api.sensor_values[PARAM_CURRENT_TEMPERATURE][VALUE]
        except KeyError:
            return None
        return current_temp

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def min_temp(self):
        """Return minimum temperature."""
        try:
            minimum_temp = self._api.supported_sensors_set_values[PARAM_REQUIRED_TEMPERATURE]["min"]
        except KeyError:
            return UNKNOWN_TEMP
        return minimum_temp

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        try:
            maximum_temp = self._api.supported_sensors_set_values[PARAM_REQUIRED_TEMPERATURE]["max"]
        except KeyError:
            return UNKNOWN_TEMP
        return maximum_temp

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        try:
            target_temp = self._api.sensor_values[PARAM_REQUIRED_TEMPERATURE][VALUE]
        except KeyError:
            return UNKNOWN_TEMP
        return target_temp

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        try:
            step = self._api.supported_sensors_set_values[PARAM_REQUIRED_TEMPERATURE]["step"]
        except KeyError:
            return 1.0
        return step

    @property
    def extra_state_attributes(self):
        """Return the supported step of target temperature."""
        try:
            step = self._api.supported_sensors_set_values[PARAM_REQUIRED_TEMPERATURE]["step"]
        except KeyError:
            step = 1.0
        try:
            if self._api.sensor_values[PARAM_HEATING][VALUE]:
                action = ACTION_HEATING
            else:
                action = ACTION_IDLE
        except KeyError:
            action = ACTION_IDLE
        return {"target_temp_step": step, "hvac_action": action}

    @property
    def operation_list(self):
        """List of available operation modes."""
        try:
            op_list = [*self._api.supported_sensors_set_values[PARAM_MODE]]
        except KeyError:
            return []
        return op_list

    @property
    def current_operation(self):
        """Return current operation"""
        try:
            current_op = self._api.sensor_values[PARAM_MODE][VALUE]
        except KeyError:
            return VAL_OFFLINE
        return current_op

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        new_temperature = kwargs.get(ATTR_TEMPERATURE)
        if new_temperature is not None:
            self._api.set_http_data(**{PARAM_REQUIRED_TEMPERATURE: new_temperature})

    def set_operation_mode(self, operation_mode):
        """Set operation mode."""
        self._api.set_http_data(**{PARAM_MODE: operation_mode})

    def update(self):
        """Update all Node data from Hive."""
        return
