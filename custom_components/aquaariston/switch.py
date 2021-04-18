"""Suppoort for Ariston Aqua switch."""
from datetime import timedelta

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_SWITCHES, CONF_NAME

from .const import (
    DATA_ARISTONAQUA,
    DEVICES,
    VALUE,
    PARAM_ON,
    PARAM_ECO,
)

SWITCH_POWER = "Power"
SWITCH_ECO = "Eco Mode"

SCAN_INTERVAL = timedelta(seconds=2)

SWITCHES = {
    PARAM_ON: (SWITCH_POWER, "mdi:power"),
    PARAM_ECO: (SWITCH_ECO, "mdi:leaf"),
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up a switches for Ariston Aqua."""
    if discovery_info is None:
        return

    name = discovery_info[CONF_NAME]
    device = hass.data[DATA_ARISTONAQUA][DEVICES][name]
    add_entities(
        [
            AristonAquaSwitch(name, device, switch_type)
            for switch_type in discovery_info[CONF_SWITCHES]
        ],
        True,
    )


class AristonAquaSwitch(SwitchEntity):
    """Switch for Ariston Aqua."""

    def __init__(self, name, device, switch_type):
        """Initialize entity."""
        self._api = device.api.ariston_api
        self._icon = SWITCHES[switch_type][1]
        self._name = "{} {}".format(name, SWITCHES[switch_type][0])
        self._switch_type = switch_type
        self._state = None
        self._device = device.device

    @property
    def unique_id(self):
        """Return the unique id."""
        return f"{self._name}-{self._switch_type}"

    @property
    def should_poll(self):
        """Return True if entity has to be polled for state."""
        return True

    @property
    def name(self):
        """Return the name of this Switch device if any."""
        return self._name

    @property
    def icon(self):
        """Return the state attributes."""
        return self._icon

    @property
    def available(self):
        """Return True if entity is available."""
        try:
            return (
                self._api.available
                and not self._api.sensor_values[self._switch_type][VALUE] is None
            )
        except KeyError:
            return False

    @property
    def is_on(self):
        """Return true if switch is on."""
        try:
            if not self._api.available:
                return False
            return self._api.sensor_values[self._switch_type][VALUE]
        except KeyError:
            return False

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self._api.set_http_data(**{self._switch_type: "true"})

    def turn_off(self, **kwargs):
        """Turn the device off."""
        self._api.set_http_data(**{self._switch_type: "false"})

    def update(self):
        """Update data"""
        return
