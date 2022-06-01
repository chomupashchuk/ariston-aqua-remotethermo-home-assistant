"""Suppoort for Ariston Aqua sensors."""
import logging
from datetime import timedelta

from homeassistant.const import CONF_NAME, CONF_SENSORS
from homeassistant.helpers.entity import Entity
from homeassistant.const import (
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_POWER_FACTOR,
    DEVICE_CLASS_PRESSURE,
    DEVICE_CLASS_SIGNAL_STRENGTH,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_TIMESTAMP,
    DEVICE_CLASS_VOLTAGE,
)

from .const import (
    DATA_ARISTONAQUA,
    DEVICES,
    VALUE,
    UNITS,
    PARAM_ERRORS,
    PARAM_CURRENT_TEMPERATURE,
    PARAM_REQUIRED_TEMPERATURE,
    PARAM_MODE,
    PARAM_SHOWERS,
    PARAM_TIMER,
    PARAM_CLEANSE_MIN,
    PARAM_CLEANSE_MAX,
    PARAM_CLEANSE_TEMPERATURE,
    PARAM_TIME_PROGRAM,
    PARAM_ENERGY_USE_DAY,
    PARAM_ENERGY_USE_WEEK,
    PARAM_ENERGY_USE_MONTH,
    PARAM_ENERGY_USE_YEAR,
    PARAM_ENERGY_USE_DAY_PERIODS,
    PARAM_ENERGY_USE_WEEK_PERIODS,
    PARAM_ENERGY_USE_MONTH_PERIODS,
    PARAM_ENERGY_USE_YEAR_PERIODS,
    PARAM_REQUIRED_SHOWERS,
    PARAM_TEMPERATURE_MODE,
    VAL_PROGRAM,
    VAL_SHOWERS,
)

SCAN_INTERVAL = timedelta(seconds=2)

STATE_AVAILABLE = "available"
STATE_GOOD = "good"
STATE_ERRORS = "errors"

SENSOR_ERRORS = "Active Errors"
SENSOR_CURRENT_TEMPERATURE = "Current Temperature"
SENSOR_REQUIRED_TEMPERATURE = "Required Temperature"
SENSOR_MODE = "Mode"
SENSOR_SHOWERS = "Average Showers"
SENSOR_TIMER = "Time Left to Heat"
SENSOR_CLEANSE_TEMPERATURE = "Antilegionella Temperature"
SENSOR_TIME_PROGRAM = "Time Program"
SENSOR_ENERGY_USE_DAY = "Energy Use in the Last Day"
SENSOR_ENERGY_USE_WEEK = "Energy Use in the Last Week"
SENSOR_ENERGY_USE_MONTH = "Energy Use in the Last Month"
SENSOR_ENERGY_USE_YEAR = "Energy Use in the Last Year"
SENSOR_REQUIRED_SHOWERS = "Required Showers"
SENSOR_TEMPERATURE_MODE = "Temperature Mode"

_LOGGER = logging.getLogger(__name__)

# Sensor types are defined like: Name, units, icon
SENSORS = {
    PARAM_ERRORS: [SENSOR_ERRORS, None, "mdi:alert-outline"],
    PARAM_CURRENT_TEMPERATURE: [SENSOR_CURRENT_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:thermometer"],
    PARAM_REQUIRED_TEMPERATURE: [SENSOR_REQUIRED_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:thermometer"],
    PARAM_MODE: [SENSOR_MODE, None, "mdi:cursor-pointer"],
    PARAM_SHOWERS: [SENSOR_SHOWERS, None, "mdi:shower-head"],
    PARAM_TIMER: [SENSOR_TIMER, None, "mdi:timer"],
    PARAM_CLEANSE_TEMPERATURE: [SENSOR_CLEANSE_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:thermometer"],
    PARAM_TIME_PROGRAM: [SENSOR_TIME_PROGRAM, None, "mdi:calendar-month"],
    PARAM_ENERGY_USE_DAY: [SENSOR_ENERGY_USE_DAY, DEVICE_CLASS_ENERGY, "mdi:cash"],
    PARAM_ENERGY_USE_WEEK: [SENSOR_ENERGY_USE_WEEK, DEVICE_CLASS_ENERGY, "mdi:cash"],
    PARAM_ENERGY_USE_MONTH: [SENSOR_ENERGY_USE_MONTH, DEVICE_CLASS_ENERGY, "mdi:cash"],
    PARAM_ENERGY_USE_YEAR: [SENSOR_ENERGY_USE_YEAR, DEVICE_CLASS_ENERGY, "mdi:cash"],
    PARAM_REQUIRED_SHOWERS: [SENSOR_REQUIRED_SHOWERS, None, "mdi:shower-head"],
    PARAM_TEMPERATURE_MODE: [SENSOR_TEMPERATURE_MODE, None, "mdi:thermometer"],
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up a sensor for Ariston Aqua."""
    if discovery_info is None:
        return

    name = discovery_info[CONF_NAME]
    device = hass.data[DATA_ARISTONAQUA][DEVICES][name]
    add_entities(
        [
            AristonAquaSensor(name, device, sensor_type)
            for sensor_type in discovery_info[CONF_SENSORS]
        ],
        True,
    )


class AristonAquaSensor(Entity):
    """A sensor implementation for Ariston Aqua."""

    def __init__(self, name, device, sensor_type):
        """Initialize a sensor for Ariston Aqua."""
        self._name = "{} {}".format(name, SENSORS[sensor_type][0])
        self._signal_name = name
        self._api = device.api.ariston_api
        self._sensor_type = sensor_type
        self._state = None
        self._attrs = {}
        self._icon = SENSORS[sensor_type][2]
        self._device_class = SENSORS[sensor_type][1]

    @property
    def unique_id(self):
        """Return the unique id."""
        return f"{self._name}-{self._sensor_type}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state
        
    @property
    def device_class(self):
        """Return device class."""
        return self._device_class
        
    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attrs

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        if self._sensor_type == PARAM_ERRORS:
            try:
                if self._api.sensor_values[PARAM_ERRORS][VALUE] == []:
                    return "mdi:shield"
            except KeyError:
                pass
        elif self._sensor_type == PARAM_MODE:
            try:
                if self._api.sensor_values[PARAM_MODE][VALUE] == VAL_PROGRAM:
                    return "mdi:clock-outline"
            except KeyError:
                pass
        elif self._sensor_type == PARAM_TEMPERATURE_MODE:
            try:
                if self._api.temperature_mode == VAL_SHOWERS:
                    return "mdi:shower-head"
            except KeyError:
                pass
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        if self._sensor_type == PARAM_TEMPERATURE_MODE:
            return None
        try:
            return self._api.sensor_values[self._sensor_type][UNITS]
        except KeyError:
            return None

    @property
    def available(self):
        """Return True if entity is available."""
        if self._sensor_type == PARAM_TEMPERATURE_MODE:
            return self._api.available
        return self._api.available \
            and not self._api.sensor_values[self._sensor_type][VALUE] is None

    def update(self):
        """Get the latest data and updates the state."""
        try:
            if self._sensor_type == PARAM_TEMPERATURE_MODE:
                self._state = self._api.temperature_mode
                return
            if not self._api.available:
                return
            if not self._api.sensor_values[self._sensor_type][VALUE] is None:
                if self._sensor_type == PARAM_TIME_PROGRAM:
                    if self._api.sensor_values[self._sensor_type][VALUE] != {}:
                        self._state = STATE_AVAILABLE
                    else:
                        self._state = None
                elif self._sensor_type == PARAM_ERRORS:
                    if self._api.sensor_values[self._sensor_type][VALUE] == []:
                        self._state = STATE_GOOD
                    else:
                        self._state = STATE_ERRORS
                else:
                    self._state = self._api.sensor_values[self._sensor_type][VALUE]
            else:
                self._state = None

            self._attrs = {}
            if self._sensor_type in {
                PARAM_CLEANSE_TEMPERATURE,
                PARAM_REQUIRED_TEMPERATURE,
                PARAM_REQUIRED_SHOWERS,
            }:
                try:
                    self._attrs["Min"] = self._api.supported_sensors_set_values[
                        self._sensor_type
                    ]["min"]
                    self._attrs["Max"] = self._api.supported_sensors_set_values[
                        self._sensor_type
                    ]["max"]
                except KeyError:
                    self._attrs["Min"] = None
                    self._attrs["Max"] = None

            elif self._sensor_type == PARAM_ERRORS:
                if self._api.sensor_values[PARAM_ERRORS][VALUE]:
                    for valid_error in self._api.sensor_values[PARAM_ERRORS][VALUE]:
                        self._attrs[valid_error] = ""

            elif self._sensor_type in {
                PARAM_ENERGY_USE_DAY,
                PARAM_ENERGY_USE_WEEK,
                PARAM_ENERGY_USE_MONTH,
                PARAM_ENERGY_USE_YEAR,
            }:
                list_param = self._sensor_type + "_periods"
                self._attrs = self._api.sensor_values[list_param][VALUE]

            elif self._sensor_type == PARAM_TIME_PROGRAM:
                if not self._api.sensor_values[self._sensor_type][VALUE] is None:
                    self._attrs = self._api.sensor_values[self._sensor_type][VALUE]

        except KeyError:
            _LOGGER.warning("Problem updating sensors for Ariston Aqua")
