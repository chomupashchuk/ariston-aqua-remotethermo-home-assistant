"""Suppoort for Ariston Aqua."""
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR
from homeassistant.components.sensor import DOMAIN as SENSOR
from homeassistant.components.switch import DOMAIN as SWITCH
from homeassistant.components.select import DOMAIN as SELECT
from homeassistant.components.water_heater import DOMAIN as WATER_HEATER
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_BINARY_SENSORS,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SENSORS,
    CONF_SWITCHES,
    CONF_SELECTOR,
    CONF_USERNAME,
)
from homeassistant.helpers import discovery

from .aristonaqua import AquaAristonHandler

from .binary_sensor import BINARY_SENSORS
from .const import (
    DOMAIN,
    DATA_ARISTONAQUA,
    DEVICES,
    SERVICE_SET_DATA,
    WATER_HEATERS,
    CONF_MAX_RETRIES,
    CONF_STORE_CONFIG_FILES,
    CONF_TYPE,
    CONF_POLLING,
    CONF_LOG,
    CONF_PATH,
    CONF_GW,
    VALUE,
    PARAM_MODE,
    PARAM_ECO,
    PARAM_ON,
    PARAM_CLEANSE_TEMPERATURE,
    PARAM_REQUIRED_TEMPERATURE,
    PARAM_REQUIRED_SHOWERS,
    PARAM_CHANGING_DATA,
    PARAM_ONLINE,
    TYPE_LYDOS,
    TYPE_LYDOS_HYBRID,
    TYPE_VELIS,
)
from .sensor import SENSORS
from .switch import SWITCHES
from .select import SELECTS

DEFAULT_NAME = "Aqua Ariston"
DEFAULT_MAX_RETRIES = 5
DEFAULT_POLLING = 1.0

_LOGGER = logging.getLogger(__name__)

ARISTONAQUA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_TYPE):  vol.In([TYPE_LYDOS, TYPE_LYDOS_HYBRID, TYPE_VELIS]),
        vol.Optional(CONF_GW, default=""): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_BINARY_SENSORS): vol.All(
            cv.ensure_list, [vol.In(BINARY_SENSORS)]
        ),
        vol.Optional(CONF_SENSORS): vol.All(cv.ensure_list, [vol.In(SENSORS)]),
        vol.Optional(CONF_MAX_RETRIES, default=DEFAULT_MAX_RETRIES): vol.All(
            int, vol.Range(min=1, max=65535)
        ),
        vol.Optional(CONF_SWITCHES): vol.All(cv.ensure_list, [vol.In(SWITCHES)]),
        vol.Optional(CONF_SELECTOR): vol.All(cv.ensure_list, [vol.In(SELECTS)]),
        vol.Optional(CONF_STORE_CONFIG_FILES, default=False): cv.boolean,
        vol.Optional(CONF_POLLING, default=DEFAULT_POLLING): vol.All(
            float, vol.Range(min=1, max=5)
        ),
        vol.Optional(CONF_LOG, default="DEBUG"): vol.In(
            ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]
        ),
        vol.Optional(CONF_PATH, default="/config/aquaariston_http_data"): cv.string,
    }
)


def _has_unique_names(devices):
    names = [device[CONF_NAME] for device in devices]
    vol.Schema(vol.Unique())(names)
    return devices


CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [ARISTONAQUA_SCHEMA], _has_unique_names)},
    extra=vol.ALLOW_EXTRA,
)


class AristonAquaChecker:
    """Ariston Aqua checker"""

    def __init__(
        self,
        hass,
        device,
        name,
        username,
        password,
        store_file,
        sensors,
        binary_sensors,
        switches,
        selects,
        boiler_type,
        polling,
        logging,
        path,
        gw
    ):
        """Initialize."""

        self.device = device
        self._hass = hass
        self.name = name

        if not sensors:
            sensors = list()
        if not binary_sensors:
            binary_sensors = list()
        if not switches:
            switches = list()
        if not selects:
            selects = list()

        list_of_sensors = list({*sensors, *binary_sensors, *switches, *selects})
        """ Some sensors or switches are not part of API """
        if PARAM_CHANGING_DATA in list_of_sensors:
            list_of_sensors.remove(PARAM_CHANGING_DATA)
        if PARAM_ONLINE in list_of_sensors:
            list_of_sensors.remove(PARAM_ONLINE)

        self.ariston_api = AquaAristonHandler(
            username=username,
            password=password,
            boiler_type=boiler_type,
            sensors=list_of_sensors,
            store_file=store_file,
            polling=polling,
            logging_level=logging,
            store_folder=path,
            gw=gw
        )


def setup(hass, config):
    """Set up the Ariston Aqua component."""
    if DOMAIN not in config:
        return True
    hass.data.setdefault(DATA_ARISTONAQUA, {DEVICES: {}, WATER_HEATERS: []})
    api_list = []
    dev_gateways = set()
    dev_names = set()
    for device in config[DOMAIN]:
        name = device[CONF_NAME]
        username = device[CONF_USERNAME]
        password = device[CONF_PASSWORD]
        store_file = device[CONF_STORE_CONFIG_FILES]
        binary_sensors = device.get(CONF_BINARY_SENSORS)
        sensors = device.get(CONF_SENSORS)
        switches = device.get(CONF_SWITCHES)
        selects = device.get(CONF_SELECTOR)
        boiler_type = device.get(CONF_TYPE)
        polling = device.get(CONF_POLLING)
        logging = device.get(CONF_LOG)
        path = device.get(CONF_PATH)
        gw = device.get(CONF_GW)
        if gw in dev_gateways:
            _LOGGER.error(f"Duplicate value of 'gw': {gw}")
            raise Exception(f"Duplicate value of 'gw': {gw}")
        if name in dev_names:
            _LOGGER.error(f"Duplicate value of 'name': {name}")
            raise Exception(f"Duplicate value of 'name': {name}")
        dev_gateways.add(gw)
        dev_names.add(name)

        api = AristonAquaChecker(
            hass=hass,
            device=device,
            name=name,
            username=username,
            password=password,
            store_file=store_file,
            sensors=sensors,
            binary_sensors=binary_sensors,
            switches=switches,
            selects=selects,
            boiler_type=boiler_type,
            polling=polling,
            logging=logging,
            path=path,
            gw=gw,
        )

        api_list.append(api)
        # start api execution
        api.ariston_api.start()

        # load all devices
        hass.data[DATA_ARISTONAQUA][DEVICES][name] = AristonAquaDevice(api, device)

        discovery.load_platform(hass, WATER_HEATER, DOMAIN, {CONF_NAME: name}, config)

        if switches:
            discovery.load_platform(
                hass,
                SWITCH,
                DOMAIN,
                {CONF_NAME: name, CONF_SWITCHES: switches},
                config,
            )

        if selects:
            discovery.load_platform(
                hass,
                SELECT,
                DOMAIN,
                {CONF_NAME: name, CONF_SELECTOR: selects},
                config,
            )

        if binary_sensors:
            discovery.load_platform(
                hass,
                BINARY_SENSOR,
                DOMAIN,
                {CONF_NAME: name, CONF_BINARY_SENSORS: binary_sensors},
                config,
            )

        if sensors:
            discovery.load_platform(
                hass, SENSOR, DOMAIN, {CONF_NAME: name, CONF_SENSORS: sensors}, config
            )

    gateways_txt = ", ".join(dev_gateways)
    names_txt = ", ".join(dev_names)
    _LOGGER.info(f"All gateways: {gateways_txt}")
    _LOGGER.info(f"All names: {names_txt}")

    def set_ariston_aqua_data(call):
        """Handle the service call to set the data."""
        # Start with mandatory parameter
        entity_id = call.data.get(ATTR_ENTITY_ID, "")

        try:
            domain = entity_id.split(".")[0]
        except:
            _LOGGER.warning("Invalid entity_id domain for Ariston Aqua")
            raise Exception("Invalid entity_id domain for Ariston Aqua")
        if domain.lower() != "water_heater":
            _LOGGER.warning("Invalid entity_id domain for Ariston Aqua")
            raise Exception("Invalid entity_id domain for Ariston Aqua")
        try:
            device_id = entity_id.split(".")[1]
        except:
            _LOGGER.warning("Invalid entity_id device for Ariston Aqua")
            raise Exception("Invalid entity_id device for Ariston Aqua")

        for api in api_list:
            if api.name.replace(' ', '_').lower() == device_id.lower():
                # water_heater entity is found
                parameter_list = {}

                data = call.data.get(PARAM_MODE, "")
                if data != "":
                    parameter_list[PARAM_MODE] = str(data).lower()

                data = call.data.get(PARAM_ON, "")
                if data != "":
                    parameter_list[PARAM_ON] = str(data).lower()

                data = call.data.get(PARAM_REQUIRED_TEMPERATURE, "")
                if data != "":
                    parameter_list[PARAM_REQUIRED_TEMPERATURE] = str(data).lower()

                data = call.data.get(PARAM_CLEANSE_TEMPERATURE, "")
                if data != "":
                    parameter_list[PARAM_CLEANSE_TEMPERATURE] = str(data).lower()

                data = call.data.get(PARAM_ECO, "")
                if data != "":
                    parameter_list[PARAM_ECO] = str(data).lower()

                data = call.data.get(PARAM_REQUIRED_SHOWERS, "")
                if data != "":
                    parameter_list[PARAM_REQUIRED_SHOWERS] = str(data).lower()

                _LOGGER.debug("Ariston Aqua device found, data to check and send")

                api.ariston_api.set_http_data(**parameter_list)
                return
            raise Exception("Corresponding entity_id for Ariston Aqua not found")
        return

    hass.services.register(DOMAIN, SERVICE_SET_DATA, set_ariston_aqua_data)

    if not hass.data[DATA_ARISTONAQUA][DEVICES]:
        return False
    # Return boolean to indicate that initialization was successful.
    return True


class AristonAquaDevice:
    """Representation of a base Ariston discovery device."""

    def __init__(self, api, device):
        """Initialize the entity."""
        self.api = api
        self.device = device
