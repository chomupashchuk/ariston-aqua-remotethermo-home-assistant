"""Suppoort for Ariston."""
import copy
import json
import logging
import math
import os
import re
import threading
import time
from typing import Union
import requests


class AquaAristonHandler:
    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Aqua Ariston NET Remotethermo API

    'username' - mandatory username;

    'password' - mandatory password;

    'boiler_type' - mandatory boiler type:
        - 'velis'
        - 'lydos'
        - 'lydos_hybrid'

    'sensors' - list of supported.
        - 'errors' - list of active errors.
        - 'current_temperature' - current temperature.
        - 'required_temperature' - required temperature.
        - 'mode' - mode (manual or program).
        - 'power' - power status.
        - 'showers' - average estimated number of showers.
        - 'required_showers' - required amount of showers.
        - 'max_required_showers' - maximum allowed required number of showers.
        - 'heating' - indicates ongoing heating.
        - 'antilegionella'- indicates antilegionella function status.
        - 'eco' - indicates eco function status.
        - 'remaining_time' - remaining time for heating.
        - 'antilegionella_minimum_temperature' - minimum temperature for antilegionella.
        - 'antilegionella_maximum_temperature' - maximum temperature for antilegionella.
        - 'antilegionella_set_temperature' - set temperature for antilegionella.
        - 'time_program' - time schedule program.
        - 'energy_use_in_day' - energy use in the last day.
        - 'energy_use_in_week' - energy use in the last week.
        - 'energy_use_in_month' - energy use in the last month.
        - 'energy_use_in_year' - energy use in the last year.
        - 'energy_use_in_day_periods' - energy use in the last day in periods.
        - 'energy_use_in_week_periods' - energy use in the last week in periods.
        - 'energy_use_in_month_periods' - energy use in the last month in periods.
        - 'energy_use_in_year_periods' - energy use in the last year in periods.
        - API specific 'online_version' - API version online.
        - API specific 'update' - API update is available.

    'retries' - number of retries to set the data;

    'polling' - defines multiplication factor for waiting periods to get or set the data;

    'store_file' - indicates if HTTP and internal data to be stored as files for troubleshooting purposes;

    'store_folder' - folder to store HTTP and internal data to. If empty string is used, then current working directory
    is used with a folder 'http_logs' within it.

    'logging_level' - defines level of logging - allowed values [CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET=(default)]

    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    _VERSION = "1.0.49"

    _LOGGER = logging.getLogger(__name__)
    _LEVEL_CRITICAL = "CRITICAL"
    _LEVEL_ERROR = "ERROR"
    _LEVEL_WARNING = "WARNING"
    _LEVEL_INFO = "INFO"
    _LEVEL_DEBUG = "DEBUG"
    _LEVEL_NOTSET = "NOTSET"

    _LOGGING_LEVELS = [
        _LEVEL_CRITICAL,
        _LEVEL_ERROR,
        _LEVEL_WARNING,
        _LEVEL_INFO,
        _LEVEL_DEBUG,
        _LEVEL_NOTSET
    ]

    _VALUE = "value"
    _UNITS = "units"

    # parameter values
    _PARAM_ERRORS = "errors"
    _PARAM_CURRENT_TEMPERATURE = "current_temperature"
    _PARAM_REQUIRED_TEMPERATURE = "required_temperature"
    _PARAM_MODE = "mode"
    _PARAM_ON = "power"
    _PARAM_SHOWERS = "showers"
    _PARAM_REQUIRED_SHOWERS = "required_showers"
    _PARAM_REQUIRED_SHOWERS_MAX = "max_required_showers"
    _PARAM_HEATING = "heating"
    _PARAM_CLEANSE = "antilegionella"
    _PARAM_ECO = "eco"
    _PARAM_TIMER = "remaining_time"
    _PARAM_CLEANSE_MIN = "antilegionella_minimum_temperature"
    _PARAM_CLEANSE_MAX = "antilegionella_maximum_temperature"
    _PARAM_CLEANSE_TEMPERATURE = "antilegionella_set_temperature"
    _PARAM_ONLINE_VERSION = "online_version"
    _PARAM_INSTALLED_VERSION = "installed_version"
    _PARAM_UPDATE = "update"
    _PARAM_TIME_PROGRAM = "time_program"
    _PARAM_ENERGY_USE_DAY = "energy_use_in_day"
    _PARAM_ENERGY_USE_WEEK = "energy_use_in_week"
    _PARAM_ENERGY_USE_MONTH = "energy_use_in_month"
    _PARAM_ENERGY_USE_YEAR = "energy_use_in_year"
    _PARAM_ENERGY_USE_DAY_PERIODS = "energy_use_in_day_periods"
    _PARAM_ENERGY_USE_WEEK_PERIODS = "energy_use_in_week_periods"
    _PARAM_ENERGY_USE_MONTH_PERIODS = "energy_use_in_month_periods"
    _PARAM_ENERGY_USE_YEAR_PERIODS = "energy_use_in_year_periods"

    _GET_REQUEST_MAIN = {
        _PARAM_CURRENT_TEMPERATURE,
        _PARAM_REQUIRED_TEMPERATURE,
        _PARAM_MODE,
        _PARAM_ON,
        _PARAM_SHOWERS,
        _PARAM_HEATING,
        _PARAM_CLEANSE,
        _PARAM_ECO,
        _PARAM_TIMER,
    }
    _GET_REQUEST_SHOWERS = {
        _PARAM_REQUIRED_SHOWERS,
        _PARAM_REQUIRED_SHOWERS_MAX,
    }
    _GET_REQUEST_ERRORS = {
        _PARAM_ERRORS
    }
    _GET_REQUEST_CLEANSE = {
        _PARAM_CLEANSE_MIN,
        _PARAM_CLEANSE_MAX,
        _PARAM_CLEANSE_TEMPERATURE
    }
    _GET_REQUEST_UPDATE = {
        _PARAM_ONLINE_VERSION,
        _PARAM_UPDATE
    }
    _GET_REQUEST_TIME_PROGRAM = {
        _PARAM_TIME_PROGRAM
    }
    _GET_REQUEST_USE = {
        _PARAM_ENERGY_USE_DAY,
        _PARAM_ENERGY_USE_WEEK,
        _PARAM_ENERGY_USE_MONTH,
        _PARAM_ENERGY_USE_YEAR,
        _PARAM_ENERGY_USE_DAY_PERIODS,
        _PARAM_ENERGY_USE_WEEK_PERIODS,
        _PARAM_ENERGY_USE_MONTH_PERIODS,
        _PARAM_ENERGY_USE_YEAR_PERIODS
    }

    _SENSOR_LIST = {
        *_GET_REQUEST_MAIN,
        *_GET_REQUEST_ERRORS,
        *_GET_REQUEST_CLEANSE,
        *_GET_REQUEST_UPDATE,
        *_GET_REQUEST_TIME_PROGRAM,
        *_GET_REQUEST_USE,
        *_GET_REQUEST_SHOWERS,
    }

    _SET_REQUEST_MODE = {
        _PARAM_MODE
    }
    _SET_REQUEST_ON = {
        _PARAM_ON
    }
    _SET_REQUEST_TEMPERATURE = {
        _PARAM_REQUIRED_TEMPERATURE
    }
    _SET_REQUEST_ECO = {
        _PARAM_ECO
    }
    _SET_REQUEST_CLEANSE = {
        _PARAM_CLEANSE_TEMPERATURE
    }
    _SET_REQUEST_SHOWERS = {
        _PARAM_REQUIRED_SHOWERS
    }

    _SENSOR_SET_LIST = {
        *_SET_REQUEST_MODE,
        *_SET_REQUEST_ON,
        *_SET_REQUEST_TEMPERATURE,
        *_SET_REQUEST_ECO,
        *_SET_REQUEST_CLEANSE,
        *_SET_REQUEST_SHOWERS,
    }

    _FILE_FOLDER = "aqua_http_logs"
    _ARISTON_URL = "https://www.ariston-net.remotethermo.com"
    _GITHUB_LATEST_RELEASE = 'https://pypi.python.org/pypi/aquaaristonremotethermo/json'

    _VAL_TEMPERATURE = "temperature"
    _VAL_SHOWERS = "showers"
    _SHOWERS_MODE = "showers_mode"

    _MAX_ERRORS = 10
    _MAX_ERRORS_TIMER_EXTEND = 7

    _HTTP_DELAY_MULTIPLY = 3
    _HTTP_TIMER_SET_LOCK = 20
    _HTTP_TIMER_SET_WAIT = 25
    _HTTP_TIMEOUT_LOGIN = 5.0
    _HTTP_TIMEOUT_GET_LONG = 15.0
    _HTTP_TIMEOUT_GET_MEDIUM = 10.0
    _HTTP_TIMEOUT_GET_SHORT = 7.0
    _HTTP_PARAM_DELAY = 20.0

    _REQUEST_GET_MAIN = "_get_main"
    _REQUEST_GET_ERROR = "_get_error"
    _REQUEST_GET_CLEANSE = "_get_cleanse"
    _REQUEST_GET_TIME_PROG = "_get_time_prog"
    _REQUEST_GET_VERSION = "_get_version"
    _REQUEST_GET_USE = "_get_use"
    _REQUEST_GET_SHOWERS = "_get_showers"

    _REQUEST_SET_MAIN = "_set_main"
    _REQUEST_SET_ON = "_set_on"
    _REQUEST_SET_TEMPERATURE = "_set_temperature"
    _REQUEST_SET_ECO = "_set_eco"
    _REQUEST_SET_CLEANSE = "_set_cleanse"
    _REQUEST_SET_SHOWERS = "_set_showers"

    _TYPE_VELIS = "velis"
    _TYPE_LYDOS = "lydos"
    _TYPE_LYDOS_HYBRID = "lydos_hybrid"

    _SUPPORTED_BOILER_TYPES = {
        _TYPE_VELIS,
        _TYPE_LYDOS,
        _TYPE_LYDOS_HYBRID
    }

    _VALUE_TO_DATE = {
        0: "sunday",
        1: "monday",
        2: "tuesday",
        3: "wednesday",
        4: "thursday",
        5: "friday",
        6: "saturday"
    }

    _MODE_PROGRAM = "program"
    _MODE_MANUAL = "manual"
    _MODE_NIGHT = "night"
    _MODE_IMEMORY = "i-memory"
    _MODE_BOOST = "boost"
    _MODE_GREEN = "green"

    _MODE_TO_VALUE = {
        _MODE_NIGHT: 8,
        _MODE_PROGRAM: 5,
        _MODE_MANUAL: 1
    }
    _VALUE_TO_MODE = {value: key for (key, value) in _MODE_TO_VALUE.items()}

    _MODE_TO_VALUE_LYDOS_HYBRID = {
        _MODE_IMEMORY: 1,
        _MODE_GREEN: 2,
        _MODE_PROGRAM: 6,
        _MODE_BOOST: 7,
    }
    _VALUE_TO_MODE_LYDOS_HYBRID = {value: key for (key, value) in _MODE_TO_VALUE_LYDOS_HYBRID.items()}

    _STRING_TO_VALUE = {
        "true": True,
        "false": False
    }

    def _get_request_for_parameter(self, data):
        if data in self._GET_REQUEST_ERRORS:
            return self._REQUEST_GET_ERROR
        elif data in self._GET_REQUEST_CLEANSE:
            return self._REQUEST_GET_CLEANSE
        elif data in self._GET_REQUEST_UPDATE:
            return self._REQUEST_GET_VERSION
        elif data in self._GET_REQUEST_TIME_PROGRAM:
            return self._REQUEST_GET_TIME_PROG
        elif data in self._GET_REQUEST_USE:
            return self._REQUEST_GET_USE
        elif data in self._GET_REQUEST_SHOWERS:
            return self._REQUEST_GET_SHOWERS
        else:
            return self._REQUEST_GET_MAIN

    def _set_request_for_parameter(self, data):
        if data in self._SET_REQUEST_ON:
            return self._REQUEST_SET_ON
        elif data in self._SET_REQUEST_TEMPERATURE:
            return self._REQUEST_SET_TEMPERATURE
        elif data in self._SET_REQUEST_ECO:
            return self._REQUEST_SET_ECO
        elif data in self._SET_REQUEST_CLEANSE:
            return self._REQUEST_SET_CLEANSE
        elif data in self._SET_REQUEST_SHOWERS:
            return self._REQUEST_SET_SHOWERS
        else:
            return self._REQUEST_SET_MAIN

    def __init__(self,
                 username: str,
                 password: str,
                 boiler_type: str = "",
                 sensors: list = None,
                 retries: int = 5,
                 polling: Union[float, int] = 1.,
                 store_file: bool = False,
                 store_folder: str = "",
                 logging_level: str = _LEVEL_NOTSET,
                 gw: str = "",
                 ) -> None:
        """
        Initialize API.
        """

        if sensors is None:
            sensors = list()

        if not isinstance(retries, int) or retries < 0:
            raise Exception("Invalid retries")

        if not isinstance(polling, float) and not isinstance(polling, int) or polling < 1:
            raise Exception("Invalid poling")

        if not isinstance(store_file, int):
            raise Exception("Invalid store file flag")

        if not isinstance(sensors, list):
            raise Exception("Invalid sensors type")

        if boiler_type not in self._SUPPORTED_BOILER_TYPES:
            raise Exception("Unknown boiler type")

        if logging_level not in self._LOGGING_LEVELS:
            raise Exception("Invalid logging_level")

        if sensors:
            for sensor in sensors:
                if sensor not in self._SENSOR_LIST:
                    sensors.remove(sensor)

        if store_folder != "":
            self._store_folder = store_folder
        else:
            self._store_folder = os.path.join(os.getcwd(), self._FILE_FOLDER)
        if store_file:
            if not os.path.isdir(self._store_folder):
                os.makedirs(self._store_folder)

        """
        Logging settings
        """
        self._logging_level = logging.getLevelName(logging_level)
        self._LOGGER.setLevel(self._logging_level)
        self._console_handler = logging.StreamHandler()
        self._console_handler.setLevel(self._logging_level)
        self._formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self._console_handler.setFormatter(self._formatter)
        self._LOGGER.addHandler(self._console_handler)

        self._available = False
        self._dhw_available = False
        self._changing_data = False

        self._default_gw = gw
        if self._default_gw:
            self._gw_name = self._default_gw + '_'
        else:
            self._gw_name = ""

        self._ariston_sensors = dict()
        self._subscribed_sensors_old = dict()
        for sensor_all in self._SENSOR_LIST:
            self._ariston_sensors[sensor_all] = dict()
            self._ariston_sensors[sensor_all][self._VALUE] = None
            self._ariston_sensors[sensor_all][self._UNITS] = None
            if sensor_all in {
                self._PARAM_CURRENT_TEMPERATURE,
                self._PARAM_REQUIRED_TEMPERATURE,
                self._PARAM_CLEANSE_TEMPERATURE,
                self._PARAM_CLEANSE_MIN,
                self._PARAM_CLEANSE_MAX
            }:
                self._ariston_sensors[sensor_all][self._UNITS] = "°C"
            if sensor_all in {
                self._PARAM_ENERGY_USE_DAY,
                self._PARAM_ENERGY_USE_WEEK,
                self._PARAM_ENERGY_USE_MONTH,
                self._PARAM_ENERGY_USE_YEAR,
                self._PARAM_ENERGY_USE_DAY_PERIODS,
                self._PARAM_ENERGY_USE_WEEK_PERIODS,
                self._PARAM_ENERGY_USE_MONTH_PERIODS,
                self._PARAM_ENERGY_USE_YEAR_PERIODS,
            }:
                self._ariston_sensors[sensor_all][self._UNITS] = "kWh"
            self._subscribed_sensors_old[sensor_all] = copy.deepcopy(self._ariston_sensors[sensor_all])

        self._boiler_type = boiler_type
        if boiler_type == self._TYPE_VELIS:
            self._mode_to_val = self._MODE_TO_VALUE
            self._val_to_mode = self._VALUE_TO_MODE
            self._boiler_str = "med"
        elif boiler_type == self._TYPE_LYDOS:
            self._mode_to_val = self._MODE_TO_VALUE
            self._val_to_mode = self._VALUE_TO_MODE
            self._boiler_str = "med"
        else: # Lydos Hybrid
            self._mode_to_val = self._MODE_TO_VALUE_LYDOS_HYBRID
            self._val_to_mode = self._VALUE_TO_MODE_LYDOS_HYBRID
            self._boiler_str = "se"

        self._max_temp_boiler = 80
        self._max_temp_green = 53
        self._showers_required_temp = 0
        self._showers_mode = self._VAL_SHOWERS
        # clear configuration data
        self._ariston_main_data = {}
        self._ariston_error_data = []
        self._ariston_cleanse_data = {}
        self._ariston_time_prog_data = {}
        self._ariston_use_data = {}
        self._ariston_shower_data = {}
        # initiate all other data
        self._timer_periodic_read = threading.Timer(1, self._queue_get_data)
        self._timer_queue_delay = threading.Timer(1, self._control_availability_state, [self._REQUEST_GET_MAIN])
        self._timer_periodic_set = threading.Timer(1, self._preparing_setting_http_data)
        self._timer_set_delay = threading.Timer(1, self._preparing_setting_http_data)
        self._data_lock = threading.Lock()
        self._errors = 0
        self._get_request_number_low_prio = 0
        self._get_request_number_high_prio = 0
        self._get_time_start = {
            self._REQUEST_GET_MAIN: 0.,
            self._REQUEST_GET_ERROR: 0.,
            self._REQUEST_GET_CLEANSE: 0.,
            self._REQUEST_GET_TIME_PROG: 0.,
            self._REQUEST_GET_USE: 0.,
            self._REQUEST_GET_SHOWERS: 0.,
        }
        self._get_time_end = {
            self._REQUEST_GET_MAIN: 0.,
            self._REQUEST_GET_ERROR: 0.,
            self._REQUEST_GET_CLEANSE: 0.,
            self._REQUEST_GET_TIME_PROG: 0.,
            self._REQUEST_GET_USE: 0.,
            self._REQUEST_GET_SHOWERS: 0.,
        }
        self._lock = threading.Lock()
        self._login = False
        self._password = password
        self._plant_id = ""
        self._plant_id_lock = threading.Lock()
        self._session = requests.Session()
        self._set_param = {}
        self._set_param_group = {
            self._REQUEST_GET_MAIN: False,
            self._REQUEST_GET_CLEANSE: False,
            self._REQUEST_GET_SHOWERS: False,
        }
        self._set_retry = {
            self._REQUEST_SET_MAIN: 0,
            self._REQUEST_SET_ON: 0,
            self._REQUEST_SET_TEMPERATURE: 0,
            self._REQUEST_SET_ECO: 0,
            self._REQUEST_SET_CLEANSE: 0,
            self._REQUEST_SET_SHOWERS: 0,
        }
        self._set_max_retries = retries
        self._set_new_data_pending = False
        self._set_scheduled = False
        self._set_time_start = {
            self._REQUEST_SET_MAIN: 0.,
            self._REQUEST_SET_ON: 0.,
            self._REQUEST_SET_TEMPERATURE: 0.,
            self._REQUEST_SET_ECO: 0.,
            self._REQUEST_SET_CLEANSE: 0.,
            self._REQUEST_SET_SHOWERS: 0.,
        }
        self._set_time_end = {
            self._REQUEST_SET_MAIN: 0.,
            self._REQUEST_SET_ON: 0.,
            self._REQUEST_SET_TEMPERATURE: 0.,
            self._REQUEST_SET_ECO: 0.,
            self._REQUEST_SET_CLEANSE: 0.,
            self._REQUEST_SET_SHOWERS: 0.,
        }
        self._store_file = store_file

        self._subscribed = list()
        self._subscribed_args = list()
        self._subscribed_kwargs = list()
        self._subscribed_thread = list()

        self._subscribed2 = list()
        self._subscribed2_args = list()
        self._subscribed2_kwargs = list()
        self._subscribed2_thread = list()

        self._temp_lock = threading.Lock()
        self._token_lock = threading.Lock()
        self._token = None
        self._url = self._ARISTON_URL
        self._user = username
        self._verify = True
        self._version = ""
        # check which requests should be used
        # note that main and other are mandatory for climate and water_heater operations
        self._valid_requests = {
            self._REQUEST_GET_MAIN: True,
            self._REQUEST_GET_ERROR: False,
            self._REQUEST_GET_CLEANSE: False,
            self._REQUEST_GET_TIME_PROG: False,
            self._REQUEST_GET_VERSION: False,
            self._REQUEST_GET_USE: False,
            self._REQUEST_GET_SHOWERS: False,
        }
        # prepare lists of requests
        if sensors:
            for item in sensors:
                self._valid_requests[self._get_request_for_parameter(item)] = True
        # prepare list of higher priority
        self._request_list_high_prio = []
        if self._valid_requests[self._REQUEST_GET_MAIN]:
            self._request_list_high_prio.append(self._REQUEST_GET_MAIN)
        if self._valid_requests[self._REQUEST_GET_SHOWERS]:
            self._request_list_high_prio.append(self._REQUEST_GET_SHOWERS)
        if self._valid_requests[self._REQUEST_GET_CLEANSE]:
            self._request_list_high_prio.append(self._REQUEST_GET_CLEANSE)
        if self._valid_requests[self._REQUEST_GET_ERROR]:
            self._request_list_high_prio.append(self._REQUEST_GET_ERROR)
        # prepare list of lower priority
        self._request_list_low_prio = []
        if self._valid_requests[self._REQUEST_GET_TIME_PROG]:
            self._request_list_low_prio.append(self._REQUEST_GET_TIME_PROG)
        if self._valid_requests[self._REQUEST_GET_USE]:
            self._request_list_low_prio.append(self._REQUEST_GET_USE)
        if self._valid_requests[self._REQUEST_GET_VERSION]:
            self._request_list_low_prio.append(self._REQUEST_GET_VERSION)

        # initiate timer between requests within one loop
        self._timer_between_param_delay = self._HTTP_PARAM_DELAY * polling

        # initiate timers for http requests to reading or setting of data
        self._timeout_long = self._HTTP_TIMEOUT_GET_LONG * polling
        self._timeout_medium = self._HTTP_TIMEOUT_GET_MEDIUM * polling
        self._timeout_short = self._HTTP_TIMEOUT_GET_SHORT * polling

        # initiate timer between set request attempts
        self._timer_between_set = self._timer_between_param_delay + self._HTTP_TIMER_SET_WAIT

        self._current_temp_economy_ch = None
        self._current_temp_economy_dhw = None

        self._started = False

        self._LOGGER.info("API initiated")

        if self._boiler_type == self._TYPE_VELIS:
            # presumably it is Velis, which uses showers instead of temperatures
            self._valid_requests[self._REQUEST_GET_SHOWERS] = True
            if self._REQUEST_GET_SHOWERS not in self._request_list_high_prio:
                self._request_list_high_prio.insert(1, self._REQUEST_GET_SHOWERS)
                self._showers_mode = self._VAL_SHOWERS
                self._read_showers_temp()
                if not os.path.isdir(self._store_folder):
                    os.makedirs(self._store_folder)

        if self._store_file:
            if not os.path.isdir(self._store_folder):
                os.makedirs(self._store_folder)
            store_file = self._gw_name + 'data_ariston_valid_requests.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump(self._valid_requests, ariston_fetched)

    @staticmethod
    def _json_validator(data):
        try:
            if isinstance(data, dict):
                if data == {}:
                    return False
                else:
                    return True
            if isinstance(data, list):
                if not data:
                    return True
                else:
                    for item in data:
                        if not isinstance(item, dict):
                            return False
                    return True
            else:
                return False
        except KeyError:
            return False

    def subscribe_sensors(self, func, *args, **kwargs):
        """
        Subscribe to change of sensors value in:
            - sensor_values

        Function will be called when sensors' values are being changed.
        Actual changed values are being returned as a dictionary in a first argument.
        """
        self._subscribed.append(func)
        self._subscribed_args.append(args)
        self._subscribed_kwargs.append(kwargs)

    def subscribe_statuses(self, func, *args, **kwargs):
        """
        Subscribe to change of API statuses such as:
            - available
            - dhw_available
            - setting_data

        Called function will receive same data as sent and shall also include
        first argument, which will be a list of changed properties.
        """
        self._subscribed2.append(func)
        self._subscribed2_args.append(args)
        self._subscribed2_kwargs.append(kwargs)

    def _subscribers_sensors_inform(self):
        """
        Inform subscribers about changed sensors
        first argument is a dictionary of changed sensors
        """

        changed_data = dict()

        for sensor in self._SENSOR_LIST:
            if sensor in self._ariston_sensors:
                if self._ariston_sensors[sensor][self._VALUE] != self._subscribed_sensors_old[sensor][self._VALUE] or \
                    self._ariston_sensors[sensor][self._UNITS] != self._subscribed_sensors_old[sensor][self._UNITS]:
                    
                    if isinstance(self._ariston_sensors[sensor][self._VALUE], dict) and isinstance(self._subscribed_sensors_old[sensor][self._VALUE], dict):
                        if self._ariston_sensors[sensor][self._VALUE] == {} or self._subscribed_sensors_old[sensor][self._VALUE] == {}:
                            inform = True
                        elif len(self._ariston_sensors[sensor][self._VALUE]) != len(self._subscribed_sensors_old[sensor][self._VALUE]):
                            inform = True
                        else:
                            inform = False
                            for key, value in self._ariston_sensors[sensor][self._VALUE].items():
                                if self._subscribed_sensors_old[sensor][self._VALUE][key] != value:
                                    inform = True
                    else:
                        inform = True

                    if inform:
                        self._subscribed_sensors_old[sensor] = copy.deepcopy(self._ariston_sensors[sensor])
                        changed_data[sensor] = self._ariston_sensors[sensor]

        if changed_data:
            for iteration in range(len(self._subscribed)):
                self._subscribed_thread = threading.Timer(
                    0, self._subscribed[iteration], args=(changed_data, *self._subscribed_args[iteration]), kwargs=self._subscribed_kwargs[iteration])
                self._subscribed_thread.start()

    def _subscribers_statuses_inform(self, changed_data):
        """Inform subscribers about changed API statuses"""
        for iteration in range(len(self._subscribed2)):
            self._subscribed2_thread = threading.Timer(
                0, self._subscribed2[iteration], args=(changed_data, *self._subscribed2_args[iteration]), kwargs=self._subscribed2_kwargs[iteration])
            self._subscribed2_thread.start()

    def _set_statuses(self):
        """Set availablility states"""
        old_available = self._available
        old_dhw_available = self._dhw_available
        old_changing = self._changing_data

        changed_data = dict()

        self._available = self._errors <= self._MAX_ERRORS and self._login and self._plant_id != "" and self._ariston_main_data != {}

        if self._boiler_type == self._TYPE_VELIS and not self._ariston_shower_data:
            self._dhw_available = False
        else:
            self._dhw_available = self._available

        self._changing_data = self._set_param != {}

        if old_available != self._available:
            changed_data['available'] = self._available

        if old_dhw_available != self._dhw_available:
            changed_data['dhw_available'] = self._dhw_available

        if old_changing != self._changing_data:
            changed_data['setting_data'] = self._changing_data

        if changed_data:
            self._subscribers_statuses_inform(changed_data)

    @classmethod
    def api_data(cls):
        """
        Get API data as a tuple:
          - API version
          - supported sensors by API (actual list of supported sensors by the model cannot be identified and must be chosen manually)
          - supported parameters to be changed by API (actual list of supported parameters by the model cannot be identified and must be chosen manually)
        """
        return cls._VERSION, cls._SENSOR_LIST, cls._SENSOR_SET_LIST

    @property
    def plant_id(self) -> str:
        """Return the unique plant_id."""
        return self._plant_id

    @property
    def available(self) -> bool:
        """Return if Aristons's API is responding."""
        return self._available

    @property
    def dhw_available(self) -> bool:
        """Return if Aristons's DHW is responding."""
        return self._dhw_available

    @property
    def temperature_mode(self) -> str:
        """
        Return how temperature setting works. Some models use amount of showers and some use temperature.
        'temperature' indicates that temperature being controlled by required temperature;
        'showers' indicates that temperature being controlled by amount of required showers;

        For models using amount of showers it is possible to change modes:
            to 'temperature' by changing 'required_temperature' in set_http_data.
            to 'showers' by changing 'required_showers' in set_http_data.
        """
        return self._showers_mode

    @property
    def version(self) -> str:
        """Return version of the API in use."""
        return self._VERSION

    @property
    def sensor_values(self) -> dict:
        """
        Return dictionary of sensors and their values.

        'value' key is used to fetch value of the specific sensor/parameter.
        Some sensors/parameters might return dictionaries.

        'units' key is used to fetch units of measurement for specific sensor/parameter.

        """
        return self._ariston_sensors

    @property
    def setting_data(self) -> bool:
        """Return if setting of data is in progress."""
        return self._changing_data

    @property
    def supported_sensors_get(self) -> set:
        """
        Return set of all supported sensors/parameters in API.
        Note that it is sensors supported by API, not the server, so some might never have valid values.
        """
        return self._SENSOR_LIST

    @property
    def supported_sensors_set(self) -> set:
        """
        Return set of all parameters that potentially can be set by API.
        Note that it is parameters supported by API, not the server, so some might be impossible to be set.
        use property 'supported_sensors_set_values' to find allowed values to be set.
        """
        return self._SENSOR_SET_LIST

    @property
    def supported_sensors_set_values(self) -> dict:
        """
        Return dictionary of sensors/parameters to be set and allowed values.
        Allowed values can be returned as:
            - set of allowed options;
            - dictionary with following keys:
                - 'min' is used to indicate minimum value in the range;
                - 'max' is used to indicate maximum value in the range;
                - 'step' is used to indicate step;

        data from this property is used for 'set_http_data' method.
        """
        sensors_dictionary = {}
        for parameter in self._SENSOR_SET_LIST:
            if parameter == self._PARAM_MODE:
                sensors_dictionary[parameter] = {*self._mode_to_val}
            elif parameter == self._PARAM_ON:
                sensors_dictionary[parameter] = {*self._STRING_TO_VALUE}
            elif parameter == self._PARAM_CLEANSE_TEMPERATURE:
                param_values = dict()
                if self._ariston_cleanse_data:
                    if self._boiler_type != self._TYPE_LYDOS_HYBRID:
                        param_values["min"] = self._ariston_cleanse_data["MedMaxSetpointTemperatureMin"]
                        param_values["max"] = self._ariston_cleanse_data["MedMaxSetpointTemperatureMax"]
                    else:
                        param_values["min"] = 70.
                        param_values["max"] = 40.
                    param_values["step"] = 1.
                sensors_dictionary[parameter] = param_values
            elif parameter == self._PARAM_ECO:
                sensors_dictionary[parameter] = {*self._STRING_TO_VALUE}
            elif parameter == self._PARAM_REQUIRED_TEMPERATURE:
                param_values = dict()
                param_values["min"] = 40.
                param_values["max"] = self._max_temp_boiler
                if self._boiler_type == self._TYPE_LYDOS_HYBRID:
                    if self._ariston_sensors and self._PARAM_MODE in self._ariston_sensors:
                        if self._ariston_sensors[self._PARAM_MODE][self._VALUE] in {self._MODE_GREEN}:
                            param_values["max"] = self._max_temp_green
                param_values["step"] = 1.
                sensors_dictionary[parameter] = param_values
            elif parameter == self._PARAM_REQUIRED_SHOWERS:
                param_values = dict()
                if self._ariston_shower_data:
                    if self._boiler_type == self._TYPE_VELIS:
                        param_values["min"] = 1
                    else:
                        param_values["min"] = 0
                    param_values["max"] = self._ariston_shower_data["maxReqShw"]
                    param_values["step"] = 1
                sensors_dictionary[parameter] = param_values
        return sensors_dictionary

    def _write_showers_temp(self):
        if self._boiler_type == self._TYPE_VELIS and self._gw_name:
            with self._temp_lock:
                if not os.path.isdir(self._store_folder):
                    os.makedirs(self._store_folder)
                store_file = self._gw_name + 'required_shower_temperature.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as req_temp:
                    json.dump({self._PARAM_REQUIRED_TEMPERATURE: self._showers_required_temp,
                               self._SHOWERS_MODE: self._showers_mode
                               }, req_temp)

    def _read_showers_temp(self):
        if self._boiler_type == self._TYPE_VELIS and self._gw_name:
            with self._temp_lock:
                store_file = self._gw_name + 'required_shower_temperature.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                try:
                    with open(store_file_path) as req_temp:
                        temperature_data = json.load(req_temp)
                    temperature = temperature_data[self._PARAM_REQUIRED_TEMPERATURE]
                    self._showers_mode = temperature_data[self._SHOWERS_MODE]
                except:
                    temperature = 0
            if not temperature and self._ariston_main_data:
                temperature = self._ariston_main_data["reqTemp"]
            self._showers_required_temp = temperature
            self._write_showers_temp()

    def _check_showers_temp(self):
        if self._boiler_type == self._TYPE_VELIS and self._showers_mode == self._VAL_TEMPERATURE \
                and self._ariston_main_data and self._ariston_shower_data and self._showers_required_temp:
            try:
                current_temp = self.sensor_values[self._PARAM_CURRENT_TEMPERATURE][self._VALUE]
                current_showers = self.sensor_values[self._PARAM_REQUIRED_SHOWERS][self._VALUE]
                max_showers = self.supported_sensors_set_values[self._PARAM_REQUIRED_SHOWERS]["max"]
                min_showers = self.supported_sensors_set_values[self._PARAM_REQUIRED_SHOWERS]["max"]
                heating = self.sensor_values[self._PARAM_HEATING][self._VALUE]
                power = self.sensor_values[self._PARAM_ON][self._VALUE]
                required_showers = current_showers
                if current_temp and current_showers and max_showers and min_showers:
                    if current_temp > self._showers_required_temp:
                        # decrease showers
                        if current_showers > min_showers and power:
                            required_showers = current_showers - 1
                    elif current_temp < self._showers_required_temp - 2:
                        # increase showers
                        if current_showers < max_showers and not heating and power:
                            required_showers = current_showers + 1
                    if current_showers != required_showers:
                        self._set_param[self._PARAM_REQUIRED_SHOWERS] = required_showers
                        self._set_visible_data()
                        self._set_new_data_pending = True
                        # set after short delay to not affect switch or climate or water_heater
                        self._timer_set_delay.cancel()
                        if self._started:
                            self._timer_set_delay = threading.Timer(1, self._preparing_setting_http_data)
                            self._timer_set_delay.start()
            except KeyError:
                self._LOGGER.info("%s check showers exception", self)
        return

    def _get_plant_id(self, resp):
        plant_id = ""
        if resp.url.startswith(self._url + "/PlantDashboard/Index/") or resp.url.startswith(
            self._url + "/PlantManagement/Index/") or resp.url.startswith(
            self._url + "/PlantPreference/Index/") or resp.url.startswith(
            self._url + "/Error/Active/") or resp.url.startswith(
            self._url + "/PlantGuest/Index/") or resp.url.startswith(
            self._url + "/TimeProg/Index/"):
            plant_id = resp.url.split("/")[5]
        elif resp.url.startswith(self._url + "/PlantData/Index/") or resp.url.startswith(
            self._url + "/UserData/Index/"):
            plant_id_attribute = resp.url.split("/")[5]
            plant_id = plant_id_attribute.split("?")[0]
        elif resp.url.startswith(self._url + "/Menu/User/Index/"):
            plant_id = resp.url.split("/")[6]
        elif resp.url.startswith(self._url + "/R2/Plant/Index/"):
            plant_id = resp.url.split("/")[6].split("?")[0]
        else:
            self._LOGGER.warning('%s Authentication login error', self)
            raise Exception("Login parsing of URL failed")
        if plant_id:
            if self._default_gw:
                # If GW is specified, it can differ from the default
                url = self._url + "/R2/PlantManagement/Index/" + plant_id
                try:
                    resp = self._session.get(
                            url,
                            auth=self._token,
                            timeout=self._HTTP_TIMEOUT_LOGIN,
                            verify=True)
                except requests.exceptions.RequestException:
                    self._LOGGER.warning('%s Checking gateways error', self)
                    raise Exception("Checking gateways error")
                if resp.status_code != 200:
                    self._LOGGER.warning('%s Checking gateways error', self)
                    raise Exception("Checking gateways error")
                gateways = set()
                for item in re.findall(r'"GwId":"[a-zA-Z0-9]+"', resp.text):
                    detected_gw = item.replace('"GwId"', '').replace(':', '').replace('"', '').replace(' ', '')
                    gateways.add(detected_gw)
                gateways_txt = ", ".join(gateways)
                if self._default_gw not in gateways:
                    self._LOGGER.error(f'Gateway "{self._default_gw}" is not in the list of allowed gateways: {gateways_txt}')
                    raise Exception(f'Gateway "{self._default_gw}" is not in the list of allowed gateways: {gateways_txt}')
                else:
                    self._LOGGER.info(f'Allowed gateways: {gateways_txt}')
                plant_id = self._default_gw

        return plant_id


    def _login_session(self):
        """Login to fetch Ariston Plant ID and confirm login"""
        if not self._login and self._started:
            url = f"{self._url}/R2/Account/Login?returnUrl=%2FR2%2FHome"
            login_data = {"email": self._user, "password": self._password, "rememberMe": False, "language": "English_Us"}
            try:
                with self._token_lock:
                    self._token = requests.auth.HTTPDigestAuth(self._user, self._password)
                resp = self._session.post(
                    url,
                    auth=self._token,
                    timeout=self._HTTP_TIMEOUT_LOGIN,
                    json=login_data,
                    verify=True)
            except requests.exceptions.RequestException:
                self._LOGGER.warning('%s Authentication login error', self)
                raise Exception("Login request exception")
            if resp.status_code != 200:
                if self._store_file:
                    if not os.path.isdir(self._store_folder):
                        os.makedirs(self._store_folder)
                    store_file = self._gw_name + "data_ariston_login_" + str(resp.status_code) + "_error.txt"
                    store_file_path = os.path.join(self._store_folder, store_file)
                    with open(store_file_path, "w") as f:
                        f.write(resp.text)
                self._LOGGER.warning('%s Unexpected reply during login: %s', self, resp.status_code)
                raise Exception("Login unexpected reply code")

            plant_id = self._get_plant_id(resp)  

            if plant_id:
                with self._plant_id_lock:
                    self._plant_id = plant_id
                    self._gw_name = plant_id + '_'
                # self._model_fetch()
                if self._boiler_type == self._TYPE_LYDOS_HYBRID:
                    self._fetch_max_temp()
                with self._plant_id_lock:
                    self._login = True
                    self._LOGGER.info('%s Plant ID is %s', self, self._plant_id)
        return

    def _model_fetch(self):
        """Fetch model data"""
        url = f"{self._url}/api/v2/velis/plants?appId=com.remotethermo.velis"
        try:
            resp = self._session.get(
                url,
                auth=self._token,
                timeout=self._timeout_long,
                verify=True)
        except requests.exceptions.RequestException:
            self._LOGGER.warning('%s Authentication model fetch error', self)
            raise Exception("Model fetch exception")
        if resp.status_code != 200:
            if self._store_file:
                if not os.path.isdir(self._store_folder):
                    os.makedirs(self._store_folder)
                store_file = self._gw_name + "data_ariston_model_" + str(resp.status_code) + "_error.txt"
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, "w") as f:
                    f.write(resp.text)
            self._LOGGER.warning('%s Unexpected reply during model fetch: %s', self, resp.status_code)
            raise Exception("Model unexpected reply code")
        if self._json_validator(resp.json()):
            for plant_instance in resp.json():
                if self._store_file:
                    if not os.path.isdir(self._store_folder):
                        os.makedirs(self._store_folder)
                    store_file = self._gw_name + 'data_ariston_model_data.json'
                    store_file_path = os.path.join(self._store_folder, store_file)
                    with open(store_file_path, 'w') as ariston_fetched:
                        json.dump(resp.json(), ariston_fetched)

    def _fetch_max_temp(self):
        """Fetch maximum temperature"""
        url = f"{self._url}/api/v2/velis/sePlantData/{self._plant_id}/plantSettings?appId=com.remotethermo.velis"
        for attempt in range(5):
            try:
                resp = self._session.get(
                    url,
                    auth=self._token,
                    timeout=self._timeout_long,
                    verify=True)
            except requests.exceptions.RequestException as ex:
                self._LOGGER.warning('%s Could not fetch maximum: %s', self, ex)
                time.sleep(5)
                continue
            else:

                if resp.status_code != 200 or not self._json_validator(resp.json()):
                    self._LOGGER.warning('%s Could not fetch maximum', self)
                    time.sleep(5)
                    continue

                try:
                    self._max_temp_boiler = resp.json()["SeMaxSetpointTemperature"]
                    self._max_temp_green = resp.json()["SeMaxGreenSetpointTemperature"]

                    if self._store_file:
                        if not os.path.isdir(self._store_folder):
                            os.makedirs(self._store_folder)
                        store_file = self._gw_name + 'lydos_max_temperatures.json'
                        store_file_path = os.path.join(self._store_folder, store_file)
                        with open(store_file_path, 'w') as ariston_fetched:
                            json.dump(resp.json(), ariston_fetched)
                    break

                except Exception:
                    self._max_temp_boiler = 75
                    continue

    def _set_sensors(self, request_type=""):

        self._LOGGER.info('Setting sensors based on request %s', request_type)

        if request_type == self._REQUEST_GET_MAIN:
            
            if self.available and self._ariston_main_data != {}:

                try:
                    self._ariston_sensors[self._PARAM_MODE][self._VALUE] = \
                        self._val_to_mode[self._ariston_main_data["mode"]]
                except KeyError:
                    self._ariston_sensors[self._PARAM_MODE][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_ON][self._VALUE] = \
                        self._ariston_main_data["on"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_ON][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_CURRENT_TEMPERATURE][self._VALUE] = \
                        self._ariston_main_data["temp"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_CURRENT_TEMPERATURE][self._VALUE] = None

                try:
                    required_temp = self._ariston_main_data["reqTemp"]
                    if self._boiler_type == self._TYPE_VELIS:
                        if self._showers_mode == self._VAL_TEMPERATURE:
                            self._read_showers_temp()
                            # mode to base on temperature for boiler using only showers
                            required_temp = self._showers_required_temp
                    self._ariston_sensors[self._PARAM_REQUIRED_TEMPERATURE][self._VALUE] = required_temp
                except KeyError:
                    self._ariston_sensors[self._PARAM_REQUIRED_TEMPERATURE][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_SHOWERS][self._VALUE] = \
                        self._ariston_main_data["avShw"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_SHOWERS][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_HEATING][self._VALUE] = \
                        self._ariston_main_data["heatReq"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_HEATING][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_CLEANSE][self._VALUE] = \
                        self._ariston_main_data["antiLeg"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_CLEANSE][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_ECO][self._VALUE] = \
                        self._ariston_main_data["eco"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_ECO][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_TIMER][self._VALUE] = \
                        self._ariston_main_data["rmTm"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_TIMER][self._VALUE] = None

            else:
                self._ariston_sensors[self._PARAM_MODE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_ON][self._VALUE] = None
                self._ariston_sensors[self._PARAM_CURRENT_TEMPERATURE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_REQUIRED_TEMPERATURE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_SHOWERS][self._VALUE] = None
                self._ariston_sensors[self._PARAM_HEATING][self._VALUE] = None
                self._ariston_sensors[self._PARAM_CLEANSE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_ECO][self._VALUE] = None
                self._ariston_sensors[self._PARAM_TIMER][self._VALUE] = None

        elif request_type == self._REQUEST_GET_SHOWERS:

            if self.available and self._ariston_shower_data:

                try:
                    self._ariston_sensors[self._PARAM_REQUIRED_SHOWERS][self._VALUE] = \
                        self._ariston_shower_data["reqShw"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_REQUIRED_SHOWERS][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_REQUIRED_SHOWERS_MAX][self._VALUE] = \
                        self._ariston_shower_data["maxReqShw"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_REQUIRED_SHOWERS_MAX][self._VALUE] = None

            else:
                self._ariston_sensors[self._PARAM_REQUIRED_SHOWERS][self._VALUE] = None
                self._ariston_sensors[self._PARAM_REQUIRED_SHOWERS_MAX][self._VALUE] = None

        elif request_type == self._REQUEST_GET_ERROR:

            if self.available:

                try:
                    self._ariston_sensors[self._PARAM_ERRORS][self._VALUE] = self._ariston_error_data
                except KeyError:
                    self._ariston_sensors[self._PARAM_ERRORS][self._VALUE] = None

            else:
                self._ariston_sensors[self._PARAM_ERRORS][self._VALUE] = None

        elif request_type == self._REQUEST_GET_CLEANSE:

            if self.available and self._ariston_cleanse_data != []:

                try:
                    self._ariston_sensors[self._PARAM_CLEANSE_MIN][self._VALUE] = \
                        self._ariston_cleanse_data["MedMaxSetpointTemperatureMin"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_CLEANSE_MIN][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_CLEANSE_MAX][self._VALUE] = \
                        self._ariston_cleanse_data["MedMaxSetpointTemperatureMax"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_CLEANSE_MAX][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_CLEANSE_TEMPERATURE][self._VALUE] = \
                        self._ariston_cleanse_data["MedMaxSetpointTemperature"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_CLEANSE_TEMPERATURE][self._VALUE] = None

            else:
                self._ariston_sensors[self._PARAM_CLEANSE_MIN][self._VALUE] = None
                self._ariston_sensors[self._PARAM_CLEANSE_MAX][self._VALUE] = None
                self._ariston_sensors[self._PARAM_CLEANSE_TEMPERATURE][self._VALUE] = None

        elif request_type == self._REQUEST_GET_TIME_PROG:

            if self.available and self._ariston_time_prog_data != []:

                try:
                    time_prog = {}
                    for plan in self._ariston_time_prog_data:
                        for list_in_plan in self._ariston_time_prog_data[plan]:
                            converted_days = [self._VALUE_TO_DATE[i] for i in list_in_plan["days"]]
                            for showers in list_in_plan["shws"]:
                                time_prog[plan + " on " + " ".join(converted_days) + " at " + showers["time"]] = \
                                    str(showers["temp"]) + "°C"
                    if not time_prog:
                        time_prog = None
                    self._ariston_sensors[self._PARAM_TIME_PROGRAM][self._VALUE] = time_prog
                except KeyError:
                    self._ariston_sensors[self._PARAM_TIME_PROGRAM][self._VALUE] = None

            else:
                self._ariston_sensors[self._PARAM_TIME_PROGRAM][self._VALUE] = None

        elif request_type == self._REQUEST_GET_USE:

            if self.available and self._ariston_use_data != {}:

                try:
                    total_use = 0
                    self._ariston_sensors[self._PARAM_ENERGY_USE_DAY_PERIODS][self._VALUE] = {}
                    for iteration, item in enumerate(self._ariston_use_data[0]['v'], 1):
                        self._ariston_sensors[self._PARAM_ENERGY_USE_DAY_PERIODS][self._VALUE][
                            'Period' + str(iteration)] = round(item, 2)
                        total_use += item
                    self._ariston_sensors[self._PARAM_ENERGY_USE_DAY][self._VALUE] = round(total_use, 2)
                except KeyError:
                    self._ariston_sensors[self._PARAM_ENERGY_USE_DAY][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_ENERGY_USE_DAY_PERIODS][self._VALUE] = None

                try:
                    total_use = 0
                    self._ariston_sensors[self._PARAM_ENERGY_USE_WEEK_PERIODS][self._VALUE] = {}
                    for iteration, item in enumerate(self._ariston_use_data[1]['v'], 1):
                        self._ariston_sensors[self._PARAM_ENERGY_USE_WEEK_PERIODS][self._VALUE][
                            'Period' + str(iteration)] = round(item, 2)
                        total_use += item
                    self._ariston_sensors[self._PARAM_ENERGY_USE_WEEK][self._VALUE] = round(total_use, 2)
                except KeyError:
                    self._ariston_sensors[self._PARAM_ENERGY_USE_WEEK][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_ENERGY_USE_WEEK_PERIODS][self._VALUE] = None

                try:
                    total_use = 0
                    self._ariston_sensors[self._PARAM_ENERGY_USE_MONTH_PERIODS][self._VALUE] = {}
                    for iteration, item in enumerate(self._ariston_use_data[2]['v'], 1):
                        self._ariston_sensors[self._PARAM_ENERGY_USE_MONTH_PERIODS][self._VALUE][
                            'Period' + str(iteration)] = round(item, 2)
                        total_use += item
                    self._ariston_sensors[self._PARAM_ENERGY_USE_MONTH][self._VALUE] = round(total_use, 2)
                except KeyError:
                    self._ariston_sensors[self._PARAM_ENERGY_USE_MONTH][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_ENERGY_USE_MONTH_PERIODS][self._VALUE] = None

                try:
                    total_use = 0
                    self._ariston_sensors[self._PARAM_ENERGY_USE_YEAR_PERIODS][self._VALUE] = {}
                    for iteration, item in enumerate(self._ariston_use_data[3]['v'], 1):
                        self._ariston_sensors[self._PARAM_ENERGY_USE_YEAR_PERIODS][self._VALUE][
                            'Period' + str(iteration)] = round(item, 2)
                        total_use += item
                    self._ariston_sensors[self._PARAM_ENERGY_USE_YEAR][self._VALUE] = round(total_use, 2)
                except KeyError:
                    self._ariston_sensors[self._PARAM_ENERGY_USE_YEAR][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_ENERGY_USE_YEAR_PERIODS][self._VALUE] = None

            else:
                self._ariston_sensors[self._PARAM_ENERGY_USE_DAY][self._VALUE] = None
                self._ariston_sensors[self._PARAM_ENERGY_USE_WEEK][self._VALUE] = None
                self._ariston_sensors[self._PARAM_ENERGY_USE_MONTH][self._VALUE] = None
                self._ariston_sensors[self._PARAM_ENERGY_USE_YEAR][self._VALUE] = None
                self._ariston_sensors[self._PARAM_ENERGY_USE_DAY_PERIODS][self._VALUE] = None
                self._ariston_sensors[self._PARAM_ENERGY_USE_WEEK_PERIODS][self._VALUE] = None
                self._ariston_sensors[self._PARAM_ENERGY_USE_MONTH_PERIODS][self._VALUE] = None
                self._ariston_sensors[self._PARAM_ENERGY_USE_YEAR_PERIODS][self._VALUE] = None

        elif request_type == self._REQUEST_GET_VERSION:
            try:
                if self._version != "":
                    self._ariston_sensors[self._PARAM_ONLINE_VERSION][self._VALUE] = self._version
                    web_version = self._version.split(".")
                    installed_version = self._VERSION.split(".")
                    web_symbols = len(web_version)
                    installed_symbols = len(installed_version)
                    if web_symbols <= installed_symbols:
                        # same amount of symbols to check, update available if web has higher value
                        for symbol in range(0, web_symbols):
                            if int(web_version[symbol]) > int(installed_version[symbol]):
                                self._ariston_sensors[self._PARAM_UPDATE][self._VALUE] = True
                                break
                        else:
                            self._ariston_sensors[self._PARAM_UPDATE][self._VALUE] = False
                    else:
                        # update available if web has higher value
                        self._ariston_sensors[self._PARAM_UPDATE][self._VALUE] = True
                else:
                    self._ariston_sensors[self._PARAM_UPDATE][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_ONLINE_VERSION][self._VALUE] = None

            except KeyError:
                self._ariston_sensors[self._PARAM_UPDATE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_ONLINE_VERSION][self._VALUE] = None

    def _set_visible_data(self):
        # set visible values as if they have in fact changed
        for parameter, value in self._set_param.items():
            try:
                if parameter in self._SENSOR_SET_LIST:
                    if parameter in self._ariston_sensors \
                            and self._valid_requests[self._get_request_for_parameter(parameter)]:

                        if parameter == self._PARAM_MODE:

                            self._ariston_sensors[parameter][self._VALUE] = self._val_to_mode[value]

                        elif parameter == self._PARAM_ON:

                            self._ariston_sensors[parameter][self._VALUE] = value

                        elif parameter == self._PARAM_REQUIRED_TEMPERATURE:

                            self._ariston_sensors[parameter][self._VALUE] = value

                        elif parameter == self._PARAM_ECO:

                            self._ariston_sensors[parameter][self._VALUE] = value

                        elif parameter == self._PARAM_CLEANSE_TEMPERATURE:

                            self._ariston_sensors[parameter][self._VALUE] = value

                        elif parameter == self._PARAM_REQUIRED_SHOWERS:

                            self._ariston_sensors[parameter][self._VALUE] = value

            except KeyError:
                continue
        
        self._subscribers_sensors_inform()


    def _store_data(self, resp, request_type=""):
        """Store received dictionary"""
        if resp.status_code != 200:
            if self._store_file:
                if not os.path.isdir(self._store_folder):
                    os.makedirs(self._store_folder)
                store_file = self._gw_name + "data_ariston" + request_type + "_" + str(resp.status_code) + "_error.txt"
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, "w") as f:
                    f.write(resp.text)
            self._LOGGER.warning('%s %s invalid reply code %s', self, request_type, resp.status_code)
            raise Exception("Unexpected code {} received for the request {}".format(resp.status_code, request_type))
        if not self._json_validator(resp.json()):
            if self._store_file:
                if not os.path.isdir(self._store_folder):
                    os.makedirs(self._store_folder)
                store_file = self._gw_name + "data_ariston" + request_type + "_non_json_error.txt"
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, "w") as f:
                    f.write(resp.text)
            self._LOGGER.warning('%s %s No json detected', self, request_type)
            raise Exception("JSON did not pass validation for the request {}".format(request_type))
        if request_type == self._REQUEST_GET_MAIN:
            try:
                self._ariston_main_data = copy.deepcopy(resp.json())
            except copy.error:
                self._ariston_main_data = {}
                self._set_statuses()
                self._LOGGER.warning("%s Invalid data received for Main, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_statuses()
            self._set_sensors(request_type)
            self._set_sensors(self._REQUEST_GET_VERSION)
            self._set_visible_data()
            self._read_showers_temp()
            self._check_showers_temp()

        elif request_type == self._REQUEST_GET_ERROR:
            try:
                self._ariston_error_data = copy.deepcopy(resp.json())
            except copy.error:
                self._ariston_error_data = []
                self._LOGGER.warning("%s Invalid data received for Errors, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_sensors(request_type)
            self._set_visible_data()

        elif request_type == self._REQUEST_GET_CLEANSE:

            try:
                self._ariston_cleanse_data = copy.deepcopy(resp.json())
            except copy.error:
                self._ariston_cleanse_data = {}
                self._LOGGER.warning("%s Invalid data received for cleanse, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_sensors(request_type)
            self._set_visible_data()

        elif request_type == self._REQUEST_GET_TIME_PROG:

            try:
                self._ariston_time_prog_data = copy.deepcopy(resp.json())
            except copy.error:
                self._ariston_time_prog_data = {}
                self._LOGGER.warning("%s Invalid data received for schedule, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_sensors(request_type)
            self._set_visible_data()

        elif request_type == self._REQUEST_GET_USE:

            try:
                self._ariston_use_data = copy.deepcopy(resp.json())
            except copy.error:
                self._ariston_use_data = {}
                self._LOGGER.warning("%s Invalid data received for use, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_sensors(request_type)
            self._set_visible_data()

        elif request_type == self._REQUEST_GET_SHOWERS:

            try:
                self._ariston_shower_data = copy.deepcopy(resp.json())
            except copy.error:
                self._ariston_shower_data = {}
                self._set_statuses()
                self._LOGGER.warning("%s Invalid data received for showers, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_statuses()
            self._set_sensors(request_type)
            self._set_visible_data()

        elif request_type == self._REQUEST_GET_VERSION:
            try:
                self._version = resp.json()["info"]["version"]
            except KeyError:
                self._version = ""
                self._LOGGER.warning("%s Invalid version fetched", self)

            self._set_sensors(request_type)
            self._set_visible_data()

        self._get_time_end[request_type] = time.time()

        if self._store_file:
            if not os.path.isdir(self._store_folder):
                os.makedirs(self._store_folder)
            store_file = self._gw_name + 'data_ariston' + request_type + '.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                if request_type == self._REQUEST_GET_MAIN:
                    json.dump(self._ariston_main_data, ariston_fetched)
                elif request_type == self._REQUEST_GET_ERROR:
                    json.dump(self._ariston_error_data, ariston_fetched)
                elif request_type == self._REQUEST_GET_CLEANSE:
                    json.dump(self._ariston_cleanse_data, ariston_fetched)
                elif request_type == self._REQUEST_GET_TIME_PROG:
                    json.dump(self._ariston_time_prog_data, ariston_fetched)
                elif request_type == self._REQUEST_GET_USE:
                    json.dump(self._ariston_use_data, ariston_fetched)
                elif request_type == self._REQUEST_GET_SHOWERS:
                    json.dump(self._ariston_shower_data, ariston_fetched)
                elif request_type == self._REQUEST_GET_VERSION:
                    ariston_fetched.write(self._version)
            store_file = self._gw_name + 'data_ariston_timers.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump([self._set_time_start, self._set_time_end, self._get_time_start, self._get_time_end],
                          ariston_fetched)

    def _get_http_data(self, request_type=""):
        """Common fetching of http data"""
        self._login_session()
        if self._login and self._plant_id != "":
            try:
                last_set_of_data = \
                    self._set_time_start[max(self._set_time_start.keys(), key=(lambda k: self._set_time_start[k]))]
            except KeyError:
                last_set_of_data = 0
            if time.time() - last_set_of_data > self._HTTP_TIMER_SET_LOCK:
                # do not read immediately during set attempt
                if request_type == self._REQUEST_GET_CLEANSE:
                    url = f"{self._url}/api/v2/velis/{self._boiler_str}PlantData/{self._plant_id}/plantSettings?wheType=Med&appId=com.remotethermo.velis"
                    http_timeout = self._timeout_medium
                elif request_type == self._REQUEST_GET_ERROR:
                    url = f"{self._url}/api/v2/busErrors?gatewayId={self._plant_id}&culture=en-US&appId=com.remotethermo.velis"
                    http_timeout = self._timeout_medium
                elif request_type == self._REQUEST_GET_TIME_PROG:
                    url = f"{self._url}/api/v2/velis/timeProgs/{self._plant_id}?appId=com.remotethermo.velis"
                    http_timeout = self._timeout_long
                elif request_type == self._REQUEST_GET_USE:
                    url = f"{self._url}/api/v2/velis/reports/{self._plant_id }?usages=Dhw&appId=com.remotethermo.velis"
                    http_timeout = self._timeout_long
                elif request_type == self._REQUEST_GET_SHOWERS:
                    url = f"{self._url}/api/v2/velis/plantData/{self._plant_id}?appId=com.remotethermo.velis"
                    http_timeout = self._timeout_long
                elif request_type == self._REQUEST_GET_VERSION:
                    url = self._GITHUB_LATEST_RELEASE
                    http_timeout = self._timeout_short
                else:
                    # main data
                    url = f"{self._url}/api/v2/velis/{self._boiler_str}PlantData/{self._plant_id}?appId=com.remotethermo.velis"
                    if self.available:
                        http_timeout = self._timeout_long
                    else:
                        # for not available give a bit more time
                        http_timeout = self._timeout_long + 4
                with self._data_lock:
                    try:
                        self._get_time_start[request_type] = time.time()
                        resp = self._session.get(
                            url,
                            auth=self._token,
                            timeout=http_timeout,
                            verify=True)
                    except requests.exceptions.RequestException:
                        self._LOGGER.warning("%s %s Problem reading data", self, request_type)
                        raise Exception("Request {} has failed with an exception".format(request_type))
                    self._store_data(resp, request_type)
            else:
                self._LOGGER.debug("%s %s Still setting data, read restricted", self, request_type)
                return False
        else:
            self._LOGGER.warning("%s %s Not properly logged in to get the data", self, request_type)
            raise Exception("Not logged in to fetch the data")
        self._LOGGER.info('Data fetched')
        return True

    def _queue_get_data(self):
        """Queue all request items"""
        with self._data_lock:
            # schedule next get request
            if self._errors >= self._MAX_ERRORS_TIMER_EXTEND:
                # give a little rest to the system if too many errors
                retry_in = self._timer_between_param_delay * self._HTTP_DELAY_MULTIPLY
                self._timer_between_set = self._timer_between_param_delay * self._HTTP_DELAY_MULTIPLY + \
                                          self._HTTP_TIMER_SET_WAIT
                self._LOGGER.warning('%s Retrying in %s seconds', self, retry_in)
            else:
                # work as usual
                retry_in = self._timer_between_param_delay
                self._timer_between_set = self._timer_between_param_delay + self._HTTP_TIMER_SET_WAIT
                self._LOGGER.debug('%s Fetching next data in %s seconds', self, retry_in)
            self._timer_periodic_read.cancel()
            if self._started:
                self._timer_periodic_read = threading.Timer(retry_in, self._queue_get_data)
                self._timer_periodic_read.start()

            if not self.available or self._errors > 0:
                # first always initiate main data
                self._timer_queue_delay.cancel()
                if self._started:
                    self._timer_queue_delay = threading.Timer(1, self._control_availability_state,
                                                              [self._REQUEST_GET_MAIN])
                    self._timer_queue_delay.start()
                # force skip after fetching data
                self._get_request_number_high_prio = 1
            # next trigger fetching parameters that are being changed
            elif self._set_param_group[self._REQUEST_GET_MAIN]:
                # setting of main data is ongoing, prioritize it
                self._timer_queue_delay.cancel()
                if self._started:
                    self._timer_queue_delay = threading.Timer(1, self._control_availability_state,
                                                              [self._REQUEST_GET_MAIN])
                    self._timer_queue_delay.start()
                if not self._set_scheduled:
                    self._set_param_group[self._REQUEST_GET_MAIN] = False
            elif self._set_param_group[self._REQUEST_GET_SHOWERS]:
                # setting of main data is ongoing, prioritize it
                self._timer_queue_delay.cancel()
                if self._started:
                    self._timer_queue_delay = threading.Timer(1, self._control_availability_state,
                                                              [self._REQUEST_GET_SHOWERS])
                    self._timer_queue_delay.start()
                if not self._set_scheduled:
                    self._set_param_group[self._REQUEST_GET_SHOWERS] = False
            elif self._set_param_group[self._REQUEST_GET_CLEANSE]:
                # setting of parameter data is ongoing, prioritize it
                self._timer_queue_delay.cancel()
                if self._started:
                    self._timer_queue_delay = threading.Timer(1, self._control_availability_state,
                                                              [self._REQUEST_GET_CLEANSE])
                    self._timer_queue_delay.start()
                if not self._set_scheduled:
                    self._set_param_group[self._REQUEST_GET_CLEANSE] = False
            else:
                # last is fetch higher priority list items
                # select next item from high priority list
                if self._get_request_number_high_prio < len(self._request_list_high_prio):
                    # item is available in the list
                    self._timer_queue_delay.cancel()
                    if self._started:
                        self._timer_queue_delay = threading.Timer(
                            1, self._control_availability_state,
                            [self._request_list_high_prio[self._get_request_number_high_prio]])
                        self._timer_queue_delay.start()
                    self._get_request_number_high_prio += 1
                elif self._get_request_number_high_prio > len(self._request_list_high_prio):
                    # start from the beginning of the list
                    self._get_request_number_high_prio = 0
                else:
                    # third we reserve one place for one of lower priority tasks among higher priority ones
                    self._get_request_number_high_prio += 1
                    if self._errors < self._MAX_ERRORS_TIMER_EXTEND:
                        # skip lower priority requests if too many errors and give time to recover
                        # other data is not that important, so just handle in queue
                        if self._get_request_number_low_prio < len(self._request_list_low_prio):
                            # item is available in the list
                            self._timer_queue_delay.cancel()
                            if self._started:
                                self._timer_queue_delay = threading.Timer(
                                    1, self._control_availability_state,
                                    [self._request_list_low_prio[self._get_request_number_low_prio]])
                                self._timer_queue_delay.start()
                            self._get_request_number_low_prio += 1
                        if self._get_request_number_low_prio >= len(self._request_list_low_prio):
                            self._get_request_number_low_prio = 0

            if self._store_file:
                if not os.path.isdir(self._store_folder):
                    os.makedirs(self._store_folder)
                store_file = self._gw_name + 'data_ariston_all_set_get.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump(self._set_param_group, ariston_fetched)

    def _error_detected(self, request_type):
        """Error detected"""
        if request_type in {
            self._REQUEST_GET_MAIN,
            self._REQUEST_SET_MAIN,
            self._REQUEST_SET_TEMPERATURE,
            self._REQUEST_SET_SHOWERS,
            self._REQUEST_SET_ON
        }:
            with self._lock:
                was_online = self.available
                self._errors += 1
                self._set_statuses()
                self._LOGGER.warning("Connection errors: %i", self._errors)
                offline = not self.available
            if offline and was_online:
                self._clear_data()
                self._LOGGER.error("Ariston is offline: Too many errors")
                
    def _no_error_detected(self, request_type):
        """No errors detected"""
        if request_type in {self._REQUEST_GET_MAIN, self._REQUEST_SET_MAIN}:
            with self._lock:
                was_offline = not self.available
                self._errors = 0
                self._set_statuses()
            if was_offline:
                self._LOGGER.info("No more errors")
                
    def _control_availability_state(self, request_type=""):
        """Control component availability"""
        try:
            result_ok = self._get_http_data(request_type)
            self._LOGGER.info(f"ariston action ok for {request_type}")
        except Exception as ex:
            self._error_detected(request_type)
            self._LOGGER.warning(f"ariston action nok for {request_type}: {ex}")
            return
        if result_ok:
            self._no_error_detected(request_type)
        return

    def _setting_http_data(self, set_data, request_type=""):
        """setting of data"""
        self._LOGGER.info('setting http data')
        try:
            if self._store_file:
                if not os.path.isdir(self._store_folder):
                    os.makedirs(self._store_folder)
                store_file = self._gw_name + 'data_ariston' + request_type + '.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump(set_data, ariston_fetched)
                store_file = self._gw_name + 'data_ariston_all_set.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump(self._set_param, ariston_fetched)
                store_file = self._gw_name + 'data_ariston_timers.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump([self._set_time_start, self._set_time_end, self._get_time_start, self._get_time_end],
                              ariston_fetched)
        except TypeError:
            self._LOGGER.warning('%s Problem storing files', self)
        if request_type == self._REQUEST_SET_CLEANSE:
            url = f"{self._url}/api/v2/velis/{self._boiler_str}PlantData/{self._plant_id}/plantSettings?appId=com.remotethermo.velis"
            http_timeout = self._timeout_medium
        elif request_type == self._REQUEST_SET_ECO:
            url = f"{self._url}/api/v2/velis/{self._boiler_str}PlantData/{self._plant_id}/switchEco?appId=com.remotethermo.velis"
            http_timeout = self._timeout_medium
        elif request_type == self._REQUEST_SET_ON:
            url = f"{self._url}/api/v2/velis/{self._boiler_str}PlantData/{self._plant_id}/switch?appId=com.remotethermo.velis"
            http_timeout = self._timeout_medium
        elif request_type == self._REQUEST_SET_TEMPERATURE:
            boost_str = ""
            if self._boiler_type == self._TYPE_LYDOS_HYBRID and self._ariston_sensors and \
                    self._PARAM_MODE in self._ariston_sensors and \
                    self._ariston_sensors[self._PARAM_MODE][self._VALUE] == self._MODE_BOOST:
                boost_str = "boost"
            url = f"{self._url}/api/v2/velis/{self._boiler_str}PlantData/{self._plant_id}/{boost_str}temperature?appId=com.remotethermo.velis"
            http_timeout = self._timeout_medium
        elif request_type == self._REQUEST_SET_SHOWERS:
            url = f"{self._url}/api/v2/velis/plantData/{self._plant_id}/showers?appId=com.remotethermo.velis"
            http_timeout = self._timeout_medium
        else: # mode
            url = f"{self._url}/api/v2/velis/{self._boiler_str}PlantData/{self._plant_id}/mode?appId=com.remotethermo.velis"
            http_timeout = self._timeout_long
        try:
            self._set_time_start[request_type] = time.time()
            resp = self._session.post(
                url,
                auth=self._token,
                timeout=http_timeout,
                json=set_data,
                verify=True)
        except requests.exceptions.RequestException:
            self._error_detected(request_type)
            self._LOGGER.warning('%s %s error', self, request_type)
            raise Exception("Unexpected error for setting in the request {}".format(request_type))
        if resp.status_code != 200:
            self._error_detected(request_type)
            if self._store_file:
                if not os.path.isdir(self._store_folder):
                    os.makedirs(self._store_folder)
                store_file = self._gw_name + "data_ariston" + request_type + "_" + str(resp.status_code) + "_error.txt"
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, "w") as f:
                    f.write(resp.text)
            self._LOGGER.warning("%s %s Command to set data failed with code: %s", self, request_type, resp.status_code)
            raise Exception("Unexpected code {} for setting in the request {}".format(resp.status_code, request_type))
        self._set_time_end[request_type] = time.time()
        self._no_error_detected(request_type)
        self._LOGGER.info('%s %s Data was presumably changed', self, request_type)

    def _preparing_setting_http_data(self):
        """Preparing and setting http data"""
        self._login_session()
        with self._data_lock:
            if not self._set_new_data_pending:
                # initiated from schedule, no longer scheduled
                self._set_scheduled = False
            else:
                # initiated from set_http_data, no longer pending
                self._set_new_data_pending = False
                for request_item in self._set_retry:
                    self._set_retry[request_item] = 0
                if self._set_scheduled:
                    # we wait for another attempt after timeout, data will be set then
                    return
            if self._login and self.available and self._plant_id != "" and self._ariston_main_data:
                changed_parameter = {
                    self._REQUEST_SET_MAIN: {},
                    self._REQUEST_SET_ON: {},
                    self._REQUEST_SET_TEMPERATURE: {},
                    self._REQUEST_SET_ECO: {},
                    self._REQUEST_SET_CLEANSE: {},
                    self._REQUEST_SET_SHOWERS: {},
                }
                
                set_eco_on = False
                set_power_on = False

                set_mode_data = dict()
                set_mode_data["old"] = self._ariston_main_data["mode"]
                set_mode_data["new"] = self._ariston_main_data["mode"]

                set_temperature_data = dict()
                if self._boiler_type != self._TYPE_LYDOS_HYBRID:
                    set_temperature_data["eco"] = self._ariston_main_data["eco"]
                set_temperature_data["old"] = self._ariston_main_data["reqTemp"]
                set_temperature_data["new"] = self._ariston_main_data["reqTemp"]

                set_cleanse_data = dict()
                set_showers_data = dict()
                if self._PARAM_CLEANSE_TEMPERATURE in self._set_param:
                    try:
                        set_cleanse_data["MedMaxSetpointTemperature"] = dict()
                        set_cleanse_data["MedMaxSetpointTemperature"]["old"] = \
                            self._ariston_cleanse_data["MedMaxSetpointTemperature"]
                        set_cleanse_data["MedMaxSetpointTemperature"]["new"] = \
                            self._ariston_cleanse_data["MedMaxSetpointTemperature"]
                    except KeyError:
                        set_cleanse_data = {}
                        self._LOGGER.error(
                            '%s antilegionella temperature can not be set as no valid sensor data available', self)

                elif self._PARAM_REQUIRED_SHOWERS in self._set_param:
                    try:
                        set_showers_data["old"] = self._ariston_shower_data["reqShw"]
                        set_showers_data["new"] = self._ariston_shower_data["reqShw"]
                    except KeyError:
                        set_showers_data = {}
                        self._LOGGER.error(
                            '%s required showers can not be set as no valid sensor data available', self)

                if self._PARAM_MODE in self._set_param:

                    if set_mode_data["old"] == self._set_param[self._PARAM_MODE]:
                        if self._set_time_start[self._set_request_for_parameter(self._PARAM_MODE)] < \
                                self._get_time_end[self._get_request_for_parameter(self._PARAM_MODE)]:
                            # value should be up to date and match to remove from setting
                            del self._set_param[self._PARAM_MODE]
                        else:
                            # assume data was not yet changed
                            changed_parameter[self._set_request_for_parameter(self._PARAM_MODE)][
                                self._get_request_for_parameter(self._PARAM_MODE)] = True
                    else:
                        set_mode_data["new"] = self._set_param[self._PARAM_MODE]
                        changed_parameter[self._set_request_for_parameter(self._PARAM_MODE)][
                            self._get_request_for_parameter(self._PARAM_MODE)] = True

                if self._PARAM_REQUIRED_SHOWERS in self._set_param:

                    if self._ariston_shower_data and math.isclose(
                            self._ariston_shower_data["reqShw"],
                            self._set_param[self._PARAM_REQUIRED_SHOWERS],
                            abs_tol=0.01):
                        if self._set_time_start[self._set_request_for_parameter(self._PARAM_REQUIRED_SHOWERS)] < \
                                self._get_time_end[self._get_request_for_parameter(self._PARAM_REQUIRED_SHOWERS)]:
                            # value should be up to date and match to remove from setting
                            del self._set_param[self._PARAM_REQUIRED_SHOWERS]
                        else:
                            # assume data was not yet changed
                            changed_parameter[self._set_request_for_parameter(self._PARAM_REQUIRED_SHOWERS)][
                                self._get_request_for_parameter(self._PARAM_REQUIRED_SHOWERS)] = True
                    else:
                        set_showers_data["new"] = self._set_param[self._PARAM_REQUIRED_SHOWERS]
                        changed_parameter[self._set_request_for_parameter(self._PARAM_REQUIRED_SHOWERS)][
                            self._get_request_for_parameter(self._PARAM_REQUIRED_SHOWERS)] = True

                if self._PARAM_ON in self._set_param:

                    if self._ariston_main_data["on"] == self._set_param[self._PARAM_ON]:
                        if self._set_time_start[self._set_request_for_parameter(self._PARAM_ON)] < \
                                self._get_time_end[self._get_request_for_parameter(self._PARAM_ON)]:
                            # value should be up to date and match to remove from setting
                            del self._set_param[self._PARAM_ON]
                        else:
                            # assume data was not yet changed
                            changed_parameter[self._set_request_for_parameter(self._PARAM_ON)][
                                self._get_request_for_parameter(self._PARAM_ON)] = True
                    else:
                        set_power_on = self._set_param[self._PARAM_ON]
                        changed_parameter[self._set_request_for_parameter(self._PARAM_ON)][
                            self._get_request_for_parameter(self._PARAM_ON)] = True

                if self._PARAM_REQUIRED_TEMPERATURE in self._set_param:

                    if math.isclose(
                            self._ariston_main_data["reqTemp"],
                            self._set_param[self._PARAM_REQUIRED_TEMPERATURE],
                            abs_tol=0.01):
                        if self._set_time_start[self._set_request_for_parameter(self._PARAM_REQUIRED_TEMPERATURE)] < \
                                self._get_time_end[self._get_request_for_parameter(self._PARAM_REQUIRED_TEMPERATURE)]:
                            # value should be up to date and match to remove from setting
                            del self._set_param[self._PARAM_REQUIRED_TEMPERATURE]
                        else:
                            # assume data was not yet changed
                            changed_parameter[self._set_request_for_parameter(self._PARAM_REQUIRED_TEMPERATURE)][
                                self._get_request_for_parameter(self._PARAM_REQUIRED_TEMPERATURE)] = True
                    else:
                        set_temperature_data["new"] = self._set_param[self._PARAM_REQUIRED_TEMPERATURE]
                        changed_parameter[self._set_request_for_parameter(self._PARAM_REQUIRED_TEMPERATURE)][
                            self._get_request_for_parameter(self._PARAM_REQUIRED_TEMPERATURE)] = True

                if self._PARAM_ECO in self._set_param:
                
                    if self._set_param[self._PARAM_ECO]:
                        # On differs from Off
                        if self._ariston_main_data["eco"] is True:
                            if self._set_time_start[self._set_request_for_parameter(self._PARAM_ECO)] < \
                                    self._get_time_end[self._get_request_for_parameter(self._PARAM_ECO)]:
                                # value should be up to date and match to remove from setting
                                del self._set_param[self._PARAM_ECO]
                            else:
                                # assume data was not yet changed
                                changed_parameter[self._set_request_for_parameter(self._PARAM_ECO)][
                                    self._get_request_for_parameter(self._PARAM_ECO)] = True
                        else:
                            set_eco_on = True
                            changed_parameter[self._set_request_for_parameter(self._PARAM_ECO)][
                                self._get_request_for_parameter(self._PARAM_ECO)] = True

                    else:
                        # Off is change of mode to the same value
                        if self._ariston_main_data["eco"] is False:
                            if self._set_time_start[self._set_request_for_parameter(self._PARAM_ECO)] < \
                                    self._get_time_end[self._get_request_for_parameter(self._PARAM_ECO)]:
                                # value should be up to date and match to remove from setting
                                del self._set_param[self._PARAM_ECO]
                            else:
                                # assume data was not yet changed
                                changed_parameter[self._REQUEST_SET_MAIN][
                                    self._get_request_for_parameter(self._PARAM_ECO)] = True
                        else:
                            changed_parameter[self._REQUEST_SET_MAIN][
                                self._get_request_for_parameter(self._PARAM_ECO)] = True

                if self._PARAM_CLEANSE_TEMPERATURE in self._set_param:

                    if self._ariston_cleanse_data and math.isclose(
                            self._ariston_cleanse_data["MedMaxSetpointTemperature"],
                            self._set_param[self._PARAM_CLEANSE_TEMPERATURE],
                            abs_tol=0.01):
                        if self._set_time_start[self._set_request_for_parameter(self._PARAM_CLEANSE_TEMPERATURE)] < \
                                self._get_time_end[self._get_request_for_parameter(self._PARAM_CLEANSE_TEMPERATURE)]:
                            # value should be up to date and match to remove from setting
                            del self._set_param[self._PARAM_CLEANSE_TEMPERATURE]
                        else:
                            # assume data was not yet changed
                            changed_parameter[self._set_request_for_parameter(self._PARAM_CLEANSE_TEMPERATURE)][
                                self._get_request_for_parameter(self._PARAM_CLEANSE_TEMPERATURE)] = True
                    else:
                        set_cleanse_data["MedMaxSetpointTemperature"]["new"] = \
                            self._set_param[self._PARAM_CLEANSE_TEMPERATURE]
                        changed_parameter[self._set_request_for_parameter(self._PARAM_CLEANSE_TEMPERATURE)][
                            self._get_request_for_parameter(self._PARAM_CLEANSE_TEMPERATURE)] = True

                for request_item in self._set_param_group:
                    self._set_param_group[request_item] = False

                for key, value in changed_parameter.items():
                    if value != {} and self._set_retry[key] < self._set_max_retries:
                        if not self._set_scheduled:
                            # retry again after enough time
                            retry_in = self._timer_between_set
                            self._timer_periodic_set.cancel()
                            if self._started:
                                self._timer_periodic_set = threading.Timer(retry_in, self._preparing_setting_http_data)
                                self._timer_periodic_set.start()
                            self._set_retry[key] += 1
                            self._set_scheduled = True
                    elif value != {} and self._set_retry[key] == self._set_max_retries:
                        # last retry, we keep changed parameter but do not schedule anything
                        self._set_retry[key] += 1
                    else:
                        changed_parameter[key] = {}
    
                try:
                    for parameter, value in self._set_param.items():
                        if parameter == self._PARAM_ECO and value is False:
                            if self._REQUEST_GET_MAIN not in changed_parameter[self._REQUEST_SET_MAIN]:
                                del self._set_param[parameter]
                        elif self._get_request_for_parameter(parameter) not in \
                                changed_parameter[self._set_request_for_parameter(parameter)]:
                            del self._set_param[parameter]
                except KeyError:
                    self._LOGGER.warning('%s Can not clear set parameters', self)

                # show data as changed in case we were able to read data in between requests
                self._set_visible_data()

                if changed_parameter[self._REQUEST_SET_MAIN] != {}:

                    try:
                        self._setting_http_data(set_mode_data, self._REQUEST_SET_MAIN)
                    except TypeError:
                        self._LOGGER.warning('%s Setting mode failed', self)
                    except requests.exceptions.RequestException:
                        self._LOGGER.warning('%s Setting mode failed', self)
                    except Exception:
                        self._LOGGER.warning('%s Setting mode failed', self)

                elif changed_parameter[self._REQUEST_SET_ON] != {}:

                    try:
                        self._setting_http_data(set_power_on, self._REQUEST_SET_ON)
                    except TypeError:
                        self._LOGGER.warning('%s Setting power failed', self)
                    except requests.exceptions.RequestException:
                        self._LOGGER.warning('%s Setting power failed', self)
                    except Exception:
                        self._LOGGER.warning('%s Setting power failed', self)

                elif changed_parameter[self._REQUEST_SET_TEMPERATURE] != {}:

                    try:
                        self._setting_http_data(set_temperature_data, self._REQUEST_SET_TEMPERATURE)
                    except TypeError:
                        self._LOGGER.warning('%s Setting temperature failed', self)
                    except requests.exceptions.RequestException:
                        self._LOGGER.warning('%s Setting temperature failed', self)
                    except Exception:
                        self._LOGGER.warning('%s Setting temperature failed', self)

                elif changed_parameter[self._REQUEST_SET_SHOWERS] != {}:

                    try:
                        self._setting_http_data(set_showers_data, self._REQUEST_SET_SHOWERS)
                    except TypeError:
                        self._LOGGER.warning('%s Setting showers failed', self)
                    except requests.exceptions.RequestException:
                        self._LOGGER.warning('%s Setting showers failed', self)
                    except Exception:
                        self._LOGGER.warning('%s Setting showers failed', self)

                elif changed_parameter[self._REQUEST_SET_CLEANSE] != {}:

                    try:
                        self._setting_http_data(set_cleanse_data, self._REQUEST_SET_CLEANSE)
                    except TypeError:
                        self._LOGGER.warning('%s Setting antilegionella failed', self)
                    except requests.exceptions.RequestException:
                        self._LOGGER.warning('%s Setting antilegionella failed', self)
                    except Exception:
                        self._LOGGER.warning('%s Setting antilegionella failed', self)

                elif changed_parameter[self._REQUEST_SET_ECO] != {}:

                    try:
                        self._setting_http_data(set_eco_on, self._REQUEST_SET_ECO)
                    except TypeError:
                        self._LOGGER.warning('%s Setting eco failed', self)
                    except requests.exceptions.RequestException:
                        self._LOGGER.warning('%s Setting eco failed', self)
                    except Exception:
                        self._LOGGER.warning('%s Setting eco failed', self)

                else:
                    self._LOGGER.debug('%s Same data was used', self)

                for key, value in changed_parameter.items():
                    if value != {}:
                        for request_item in value:
                            self._set_param_group[request_item] = True

                if not self._set_scheduled:
                    # no more retries or no changes, no need to keep any changed data
                    self._set_param = {}
                    self._set_statuses()

                if self._store_file:
                    if not os.path.isdir(self._store_folder):
                        os.makedirs(self._store_folder)
                    store_file = self._gw_name + 'data_ariston_all_set_get.json'
                    store_file_path = os.path.join(self._store_folder, store_file)
                    with open(store_file_path, 'w') as ariston_fetched:
                        json.dump(self._set_param_group, ariston_fetched)
                    store_file = self._gw_name + 'data_ariston_all_set.json'
                    store_file_path = os.path.join(self._store_folder, store_file)
                    with open(store_file_path, 'w') as ariston_fetched:
                        json.dump(self._set_param, ariston_fetched)

            else:
                # api is down
                if not self._set_scheduled:
                    if self._set_retry[self._REQUEST_SET_MAIN] < self._set_max_retries:
                        # retry again after enough time to fetch data twice
                        retry_in = self._timer_between_set
                        self._timer_periodic_set.cancel()
                        if self._started:
                            self._timer_periodic_set = threading.Timer(retry_in, self._preparing_setting_http_data)
                            self._timer_periodic_set.start()
                        self._set_retry[self._REQUEST_SET_MAIN] += 1
                        self._set_scheduled = True
                    else:
                        # no more retries, no need to keep changed data
                        self._set_param = {}
                        self._set_statuses()

                        for request_item in self._set_param_group:
                            self._set_param_group[request_item] = False

                        self._LOGGER.warning("%s No stable connection to set the data", self)
                        raise Exception("Unstable connection to set the data")

    def set_http_data(self, **parameter_list: Union[str, int, float, bool]) -> None:
        """
        Set data over http, where **parameter_list excepts parameters and wanted values.

        Supported parameters:
            - 'mode'
            - 'power'
            - 'antilegionella_set_temperature'
            - 'eco'
            - 'required_temperature'
            - 'required_showers'

        Supported values must be viewed in the property 'supported_sensors_set_values',
        which are generated dynamically based on reported values.

        Example:
            set_http_data(mode='off',internet_time=True)

        For models using amount of showers it is possible to change mode to 'temperature' by changing
        'required_temperature' and change mode to 'showers' by changing 'required_showers' in set_http_data.
        'required_showers' has higher priority if 2 are used in the same request.
        """

        if self._ariston_main_data != {}:
            with self._data_lock:

                allowed_values = self.supported_sensors_set_values
                good_values = dict()
                bad_values = dict()
                for parameter in parameter_list:
                    value = parameter_list[parameter]
                    try:
                        good_parameter = False
                        if parameter in {
                            self._PARAM_MODE,
                            self._PARAM_ON,
                            self._PARAM_ECO,
                        }:
                            value = str(value).lower()
                            if value in allowed_values[parameter]:
                                good_values[parameter] = value
                                good_parameter = True
                        elif parameter in {
                            self._PARAM_REQUIRED_TEMPERATURE,
                            self._PARAM_CLEANSE_TEMPERATURE,
                            self._PARAM_REQUIRED_SHOWERS,
                        }:
                            value = float(value)
                            if allowed_values[parameter] and allowed_values[parameter]["min"] - 0.01 <= value \
                                    <= allowed_values[parameter]["max"] + 0.01:
                                if parameter == self._PARAM_REQUIRED_SHOWERS:
                                    good_values[parameter] = int(value)
                                else:
                                    good_values[parameter] = value
                                good_parameter = True
                        if not good_parameter:
                            bad_values[parameter] = value
                    except KeyError:
                        bad_values[parameter] = value

                if self._boiler_type == self._TYPE_VELIS:
                    if self._PARAM_REQUIRED_SHOWERS in good_values:
                        self._showers_mode = self._VAL_SHOWERS
                        self._write_showers_temp()
                        try:
                            self._ariston_sensors[self._PARAM_REQUIRED_TEMPERATURE][self._VALUE] = \
                                self._ariston_main_data["reqTemp"]
                        except KeyError:
                            self._LOGGER.warning("%s no temperature during showers set", self)
                    elif self._PARAM_REQUIRED_TEMPERATURE in good_values:
                        self._showers_mode = self._VAL_TEMPERATURE
                        self._showers_required_temp = good_values[self._PARAM_REQUIRED_TEMPERATURE]
                        self._write_showers_temp()
                        self._ariston_sensors[self._PARAM_REQUIRED_TEMPERATURE][self._VALUE] = \
                            self._showers_required_temp
                        del good_values[self._PARAM_REQUIRED_TEMPERATURE]

                # check mode and set it
                if self._PARAM_MODE in good_values:
                    try:
                        self._set_param[self._PARAM_MODE] = self._mode_to_val[good_values[self._PARAM_MODE]]
                        self._LOGGER.info('%s New mode %s', self, good_values[self._PARAM_MODE])
                    except KeyError:
                        self._LOGGER.warning('%s Unknown or unsupported mode or key error: %s', self,
                                        good_values[self._PARAM_MODE])
                        bad_values[self._PARAM_MODE] = good_values[self._PARAM_MODE]

                if self._PARAM_ON in good_values:
                    try:
                        self._set_param[self._PARAM_ON] = self._STRING_TO_VALUE[good_values[self._PARAM_ON]]
                        self._LOGGER.info('%s New mode %s', self, good_values[self._PARAM_ON])
                    except KeyError:
                        self._LOGGER.warning('%s Unknown or unsupported power or key error: %s', self,
                                        good_values[self._PARAM_ON])
                        bad_values[self._PARAM_ON] = good_values[self._PARAM_ON]

                if self._PARAM_ECO in good_values:
                    try:
                        self._set_param[self._PARAM_ECO] = self._STRING_TO_VALUE[good_values[self._PARAM_ECO]]
                        self._LOGGER.info('%s New mode %s', self, good_values[self._PARAM_ECO])
                    except KeyError:
                        self._LOGGER.warning('%s Unknown or unsupported eco or key error: %s', self,
                                        good_values[self._PARAM_ECO])
                        bad_values[self._PARAM_ECO] = good_values[self._PARAM_ECO]

                if self._PARAM_REQUIRED_SHOWERS in good_values:
                    try:
                        self._set_param[self._PARAM_REQUIRED_SHOWERS] = good_values[self._PARAM_REQUIRED_SHOWERS]
                        self._LOGGER.info('%s New mode %s', self, good_values[self._PARAM_REQUIRED_SHOWERS])
                    except KeyError:
                        self._LOGGER.warning('%s Unknown or unsupported showers or key error: %s', self,
                                        good_values[self._PARAM_REQUIRED_SHOWERS])
                        bad_values[self._PARAM_REQUIRED_SHOWERS] = good_values[self._PARAM_REQUIRED_SHOWERS]

                if self._PARAM_REQUIRED_TEMPERATURE in good_values:
                    try:
                        self._set_param[self._PARAM_REQUIRED_TEMPERATURE] = \
                            good_values[self._PARAM_REQUIRED_TEMPERATURE]
                        self._LOGGER.info('%s New mode %s', self, good_values[self._PARAM_REQUIRED_TEMPERATURE])
                    except KeyError:
                        self._LOGGER.warning('%s Unknown or unsupported set temperature or key error: %s', self,
                                             good_values[self._PARAM_REQUIRED_TEMPERATURE])
                        bad_values[self._PARAM_REQUIRED_TEMPERATURE] = good_values[self._PARAM_REQUIRED_TEMPERATURE]

                if self._PARAM_CLEANSE_TEMPERATURE in good_values:
                    try:
                        self._set_param[self._PARAM_CLEANSE_TEMPERATURE] = \
                            good_values[self._PARAM_CLEANSE_TEMPERATURE]
                        self._LOGGER.info('%s New mode %s', self, good_values[self._PARAM_CLEANSE_TEMPERATURE])
                    except KeyError:
                        self._LOGGER.warning('%s Unknown or unsupported antilegionella temperature or key error: %s',
                                             self, good_values[self._PARAM_CLEANSE_TEMPERATURE])
                        bad_values[self._PARAM_CLEANSE_TEMPERATURE] = good_values[self._PARAM_CLEANSE_TEMPERATURE]

                self._set_visible_data()

                self._set_statuses()

                self._set_new_data_pending = True
                # set after short delay to not affect switch or climate or water_heater
                self._timer_set_delay.cancel()
                if self._started:
                    self._timer_set_delay = threading.Timer(1, self._preparing_setting_http_data)
                    self._timer_set_delay.start()

                if bad_values != {}:
                    self._LOGGER.warning("{} Following values could not be set: {}".format(self, bad_values))
                    raise Exception("Following values could not be set: {}".format(bad_values))

        else:
            self._LOGGER.warning("%s No valid data fetched from server to set changes", self)
            raise Exception("Connection data error, problem to set data")

    def _clear_data(self):
        with self._plant_id_lock:
            self._login = False
        self._ariston_main_data = {}
        self._ariston_error_data = []
        self._ariston_cleanse_data = {}
        self._ariston_time_prog_data = {}
        self._ariston_use_data = {}
        self._ariston_shower_data = {}
        for sensor in self._SENSOR_LIST:
            if sensor in self._ariston_sensors:
                self._ariston_sensors[sensor][self._VALUE] = None
        self._subscribers_sensors_inform()

    def start(self) -> None:
        """Start communication with the server."""
        self._timer_periodic_read = threading.Timer(1, self._queue_get_data)
        self._timer_periodic_read.start()
        self._started = True
        self._LOGGER.info("Connection started")

    def stop(self) -> None:
        """Stop communication with the server."""
        self._started = False
        self._timer_periodic_read.cancel()
        self._timer_queue_delay.cancel()
        self._timer_periodic_set.cancel()
        self._timer_set_delay.cancel()

        if self._login and self.available:
            url = self._url + "/Account/Logout"
            try:
                self._session.post(
                    url,
                    auth=self._token,
                    timeout=self._HTTP_TIMEOUT_LOGIN,
                    json={},
                    verify=True)
            except requests.exceptions.RequestException:
                self._LOGGER.warning('%s Logout error', self)
        self._session.close()
        self._clear_data()
        self._set_statuses()
        self._LOGGER.info("Connection stopped")