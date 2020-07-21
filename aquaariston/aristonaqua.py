"""Suppoort for Ariston."""
import copy
import json
import logging
import math
import os
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

    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    _VERSION = "1.0.16"

    _LOGGER = logging.getLogger(__name__)

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

    _FILE_FOLDER = "http_logs"
    _ARISTON_URL = "https://www.ariston-net.remotethermo.com"
    _GITHUB_LATEST_RELEASE = 'https://pypi.python.org/pypi/aristonremotethermo/json'

    _MAX_ERRORS = 10
    _MAX_ERRORS_TIMER_EXTEND = 5

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

    _VALUE_TO_DATE = {
        0: "sunday",
        1: "monday",
        2: "tuesday",
        3: "wednesday",
        4: "thursday",
        5: "friday",
        6: "saturday"
    }
    _VALUE_TO_MODE = {
        5: "program",
        1: "manual",
    }
    _MODE_TO_VALUE = {
        "program": 5,
        "manual": 1
    }
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
                 sensors: list = None,
                 retries: int = 5,
                 polling: Union[float, int] = 1.,
                 store_file: bool = False,
                 store_folder: str = "",
                 ) -> None:
        """
        Initialize API.
        """

        if not isinstance(retries, int) or retries < 0:
            raise Exception("Invalid retries")

        if not isinstance(polling, float) and not isinstance(polling, int) or polling < 1:
            raise Exception("Invalid poling")

        if not isinstance(store_file, int):
            raise Exception("Invalid store file flag")

        if not isinstance(sensors, list):
            raise Exception("Invalid sensors type")

        if sensors:
            for sensor in sensors:
                if sensor not in self._SENSOR_LIST:
                    sensors.remove(sensor)

        if store_file:
            if store_folder != "":
                self._store_folder = store_folder
            else:
                self._store_folder = os.path.join(os.getcwd(), self._FILE_FOLDER)
            if not os.path.isdir(self._store_folder):
                os.mkdir(self._store_folder)
        else:
            self._store_folder = ""

        self._ariston_sensors = {}
        for sensor_all in self._SENSOR_LIST:
            self._ariston_sensors[sensor_all] = {}
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

        self._showers_for_temp = False
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

        if self._store_file:
            store_file = 'data_ariston_valid_requests.json'
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

    @property
    def available(self) -> bool:
        """Return if Aristons's API is responding."""
        if not self._login or not self._plant_id or not self._ariston_main_data:
            return False
        return self._errors <= self._MAX_ERRORS

    @property
    def dhw_available(self) -> bool:
        """Return if Aristons's DHW is responding."""
        if self._showers_for_temp:
            if not self._ariston_shower_data:
                return False
        return self.available

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
        return self._set_param != {}

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
                sensors_dictionary[parameter] = {*self._MODE_TO_VALUE}
            elif parameter == self._PARAM_ON:
                sensors_dictionary[parameter] = {*self._STRING_TO_VALUE}
            elif parameter == self._PARAM_CLEANSE_TEMPERATURE:
                param_values = dict()
                if self._ariston_cleanse_data:
                    param_values["min"] = self._ariston_cleanse_data["MedMaxSetpointTemperatureMin"]
                    param_values["max"] = self._ariston_cleanse_data["MedMaxSetpointTemperatureMax"]
                    param_values["step"] = 1.
                sensors_dictionary[parameter] = param_values
            elif parameter == self._PARAM_ECO:
                sensors_dictionary[parameter] = {*self._STRING_TO_VALUE}
            elif parameter == self._PARAM_REQUIRED_TEMPERATURE:
                param_values = dict()
                param_values["min"] = 40.
                param_values["max"] = 80.
                param_values["step"] = 1.
                sensors_dictionary[parameter] = param_values
            elif parameter == self._PARAM_REQUIRED_SHOWERS:
                param_values = dict()
                if self._ariston_shower_data:
                    if self._showers_for_temp:
                        param_values["min"] = 1
                    else:
                        param_values["min"] = 0
                    param_values["max"] = self._ariston_shower_data["maxReqShw"]
                    param_values["step"] = 1
                sensors_dictionary[parameter] = param_values
        return sensors_dictionary

    def _login_session(self):
        """Login to fetch Ariston Plant ID and confirm login"""
        if not self._login and self._started:
            url = self._url + '/Account/Login'
            login_data = {"Email": self._user, "Password": self._password}
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
                self._LOGGER.warning('%s Unexpected reply during login: %s', self, resp.status_code)
                raise Exception("Login unexpected reply code")
            if resp.url.startswith(self._url + "/PlantDashboard/Index/") or resp.url.startswith(
                    self._url + "/PlantManagement/Index/") or resp.url.startswith(
                    self._url + "/PlantPreference/Index/") or resp.url.startswith(
                    self._url + "/Error/Active/") or resp.url.startswith(
                    self._url + "/PlantGuest/Index/") or resp.url.startswith(
                    self._url + "/TimeProg/Index/"):
                plan_id = resp.url.split("/")[5]
            elif resp.url.startswith(self._url + "/PlantData/Index/") or resp.url.startswith(
                    self._url + "/UserData/Index/"):
                plant_id_attribute = resp.url.split("/")[5]
                plan_id = plant_id_attribute.split("?")[0]
            elif resp.url.startswith(self._url + "/Menu/User/Index/"):
                plan_id = resp.url.split("/")[6]
            else:
                self._LOGGER.warning('%s Authentication login error', self)
                raise Exception("Login parsing of URL failed")
            url = self._url + '/api/v2/velis/plants?appId=com.remotethermo.velis'
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
                self._LOGGER.warning('%s Unexpected reply during model fetch: %s', self, resp.status_code)
                raise Exception("Model unexpected reply code")
            if not self._json_validator(resp.json()):
                self._LOGGER.warning('%s Model fetch not JSON', self)
                raise Exception("Model fetch not JSON")
            for plant_instance in resp.json():
                if plant_instance["gw"] == plan_id:
                    if plant_instance["wheType"] == 1 or plant_instance["wheModelType"] == 1:
                        # presumably it is Velis, which uses showers instead of temperatures
                        self._showers_for_temp = True
                        self._valid_requests[self._REQUEST_GET_SHOWERS] = True
                        if self._REQUEST_GET_SHOWERS not in self._request_list_high_prio:
                            self._request_list_high_prio.insert(1, self._REQUEST_GET_SHOWERS)
            with self._plant_id_lock:
                self._plant_id = plan_id
                self._login = True
                self._LOGGER.info('%s Plant ID is %s', self, self._plant_id)
        return

    def _set_sensors(self, request_type=""):

        if request_type == self._REQUEST_GET_MAIN:
            
            if self.available and self._ariston_main_data != {}:

                try:
                    self._ariston_sensors[self._PARAM_MODE][self._VALUE] = \
                        self._VALUE_TO_MODE[self._ariston_main_data["mode"]]
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
                    self._ariston_sensors[self._PARAM_REQUIRED_TEMPERATURE][self._VALUE] = \
                        self._ariston_main_data["reqTemp"]
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

                            self._ariston_sensors[parameter][self._VALUE] = self._VALUE_TO_MODE[value]

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

    def _store_data(self, resp, request_type=""):
        """Store received dictionary"""
        if resp.status_code != 200:
            self._LOGGER.warning('%s %s invalid reply code %s', self, request_type, resp.status_code)
            raise Exception("Unexpected code {} received for the request {}".format(resp.status_code, request_type))
        if not self._json_validator(resp.json()):
            self._LOGGER.warning('%s %s No json detected', self, request_type)
            raise Exception("JSON did not pass validation for the request {}".format(request_type))
        if request_type == self._REQUEST_GET_MAIN:
            try:
                self._ariston_main_data = copy.deepcopy(resp.json())
            except copy.error:
                self._ariston_main_data = {}
                self._LOGGER.warning("%s Invalid data received for Main, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_sensors(request_type)
            self._set_sensors(self._REQUEST_GET_VERSION)
            self._set_visible_data()

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
                self._LOGGER.warning("%s Invalid data received for showers, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

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
            store_file = 'data_ariston' + request_type + '.json'
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
            store_file = 'data_ariston_timers.json'
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
                    url = self._url + '/api/v2/velis/medPlantData/' + self._plant_id + \
                          '/plantSettings?wheType=Med&appId=com.remotethermo.velis'
                    http_timeout = self._timeout_medium
                elif request_type == self._REQUEST_GET_ERROR:
                    url = self._url + '/api/v2/busErrors?gatewayId=' + self._plant_id + \
                          '&culture=en-US&appId=com.remotethermo.velis'
                    http_timeout = self._timeout_medium
                elif request_type == self._REQUEST_GET_TIME_PROG:
                    url = self._url + '/api/v2/velis/timeProgs/' + self._plant_id + \
                          '?appId=com.remotethermo.velis'
                    http_timeout = self._timeout_long
                elif request_type == self._REQUEST_GET_USE:
                    url = self._url + '/api/v2/velis/reports/' + self._plant_id + \
                          '?usages=Dhw&appId=com.remotethermo.velis'
                    http_timeout = self._timeout_long
                elif request_type == self._REQUEST_GET_SHOWERS:
                    url = self._url + '/api/v2/velis/plantData/' + self._plant_id + \
                          '?appId=com.remotethermo.velis'
                    http_timeout = self._timeout_long
                elif request_type == self._REQUEST_GET_VERSION:
                    url = self._GITHUB_LATEST_RELEASE
                    http_timeout = self._timeout_short
                else:
                    # main data
                    url = self._url + '/api/v2/velis/medPlantData/' + self._plant_id + '?appId=com.remotethermo.velis'
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
                self._LOGGER.debug('%s Fetching data in %s seconds', self, retry_in)
            self._timer_periodic_read.cancel()
            if self._started:
                self._timer_periodic_read = threading.Timer(retry_in, self._queue_get_data)
                self._timer_periodic_read.start()

            if not self.available:
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
                store_file = 'data_ariston_all_set_get.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump(self._set_param_group, ariston_fetched)

    def _control_availability_state(self, request_type=""):
        """Control component availability"""
        try:
            self._get_http_data(request_type)
        except Exception:
            with self._lock:
                was_online = self.available
                self._errors += 1
                self._LOGGER.warning("Connection errors: %i", self._errors)
                offline = not self.available
            if offline and was_online:
                with self._plant_id_lock:
                    self._login = False
                self._LOGGER.error("Ariston is offline: Too many errors")
            raise Exception("Getting HTTP data has failed")
        self._LOGGER.info("Data fetched successfully, available %s", self.available)
        with self._lock:
            was_offline = not self.available
            self._errors = 0
        if was_offline:
            self._LOGGER.info("Ariston back online")
        return

    def _setting_http_data(self, set_data, request_type=""):
        """setting of data"""
        self._LOGGER.info('setting http data')
        try:
            if self._store_file:
                store_file = 'data_ariston' + request_type + '.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump(set_data, ariston_fetched)
                store_file = 'data_ariston_all_set.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump(self._set_param, ariston_fetched)
                store_file = 'data_ariston_timers.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump([self._set_time_start, self._set_time_end, self._get_time_start, self._get_time_end],
                              ariston_fetched)
        except TypeError:
            self._LOGGER.warning('%s Problem storing files', self)
        if request_type == self._REQUEST_SET_CLEANSE:
            url = self._url + '/api/v2/velis/medPlantData/' + self._plant_id + \
                  '/plantSettings?appId=com.remotethermo.velis'
            http_timeout = self._timeout_medium
        elif request_type == self._REQUEST_SET_ECO:
            url = self._url + '/api/v2/velis/medPlantData/' + self._plant_id + \
                  '/switchEco?appId=com.remotethermo.velis'
            http_timeout = self._timeout_medium
        elif request_type == self._REQUEST_SET_ON:
            url = self._url + '/api/v2/velis/medPlantData/' + self._plant_id + \
                  '/switch?appId=com.remotethermo.velis'
            http_timeout = self._timeout_medium
        elif request_type == self._REQUEST_SET_TEMPERATURE:
            url = self._url + '/api/v2/velis/medPlantData/' + self._plant_id + \
                  '/temperature?appId=com.remotethermo.velis'
            http_timeout = self._timeout_medium
        elif request_type == self._REQUEST_SET_SHOWERS:
            url = self._url + '/api/v2/velis/plantData/' + self._plant_id + \
                  '/showers?appId=com.remotethermo.velis'
            http_timeout = self._timeout_medium
        else:
            # mode
            url = self._url + '/api/v2/velis/medPlantData/' + self._plant_id + \
                  '/mode?appId=com.remotethermo.velis'
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
            self._LOGGER.warning('%s %s error', self, request_type)
            raise Exception("Unexpected error for setting in the request {}".format(request_type))
        if resp.status_code != 200:
            self._LOGGER.warning("%s %s Command to set data failed with code: %s", self, request_type, resp.status_code)
            raise Exception("Unexpected code {} for setting in the request {}".format(resp.status_code, request_type))
        self._set_time_end[request_type] = time.time()
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

                elif changed_parameter[self._REQUEST_SET_ON] != {}:

                    try:
                        self._setting_http_data(set_power_on, self._REQUEST_SET_ON)
                    except TypeError:
                        self._LOGGER.warning('%s Setting power failed', self)
                    except requests.exceptions.RequestException:
                        self._LOGGER.warning('%s Setting power failed', self)

                elif changed_parameter[self._REQUEST_SET_TEMPERATURE] != {}:

                    try:
                        self._setting_http_data(set_temperature_data, self._REQUEST_SET_TEMPERATURE)
                    except TypeError:
                        self._LOGGER.warning('%s Setting temperature failed', self)
                    except requests.exceptions.RequestException:
                        self._LOGGER.warning('%s Setting temperature failed', self)

                elif changed_parameter[self._REQUEST_SET_SHOWERS] != {}:

                    try:
                        self._setting_http_data(set_showers_data, self._REQUEST_SET_SHOWERS)
                    except TypeError:
                        self._LOGGER.warning('%s Setting showers failed', self)
                    except requests.exceptions.RequestException:
                        self._LOGGER.warning('%s Setting showers failed', self)

                elif changed_parameter[self._REQUEST_SET_CLEANSE] != {}:

                    try:
                        self._setting_http_data(set_cleanse_data, self._REQUEST_SET_CLEANSE)
                    except TypeError:
                        self._LOGGER.warning('%s Setting antilegionella failed', self)
                    except requests.exceptions.RequestException:
                        self._LOGGER.warning('%s Setting antilegionella failed', self)

                elif changed_parameter[self._REQUEST_SET_ECO] != {}:

                    try:
                        self._setting_http_data(set_eco_on, self._REQUEST_SET_ECO)
                    except TypeError:
                        self._LOGGER.warning('%s Setting eco failed', self)
                    except requests.exceptions.RequestException:
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

                if self._store_file:
                    store_file = 'data_ariston_all_set_get.json'
                    store_file_path = os.path.join(self._store_folder, store_file)
                    with open(store_file_path, 'w') as ariston_fetched:
                        json.dump(self._set_param_group, ariston_fetched)
                    store_file = 'data_ariston_all_set.json'
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

                if self._PARAM_REQUIRED_TEMPERATURE in good_values:
                    # if temperature increase use increase of showers
                    if self._showers_for_temp:
                        try:
                            required_showers = self.sensor_values[self._PARAM_REQUIRED_SHOWERS][self._VALUE]
                            max_required_showers = self.sensor_values[self._PARAM_REQUIRED_SHOWERS_MAX][self._VALUE]
                            old_temperature = self.sensor_values[self._PARAM_REQUIRED_TEMPERATURE][self._VALUE]
                            if isinstance(required_showers, int) and isinstance(max_required_showers, int) and (
                                    isinstance(old_temperature, int) or isinstance(old_temperature, float)):
                                if old_temperature > good_values[self._PARAM_REQUIRED_TEMPERATURE]:
                                    # decrease temperature
                                    if required_showers >= \
                                            self.supported_sensors_set_values[self._PARAM_REQUIRED_SHOWERS]["min"] + 1:
                                        required_showers -= 1
                                else:
                                    # increase temperature
                                    if required_showers < max_required_showers:
                                        required_showers += 1
                                good_values[self._PARAM_REQUIRED_SHOWERS] = required_showers
                                del good_values[self._PARAM_REQUIRED_TEMPERATURE]
                                self._LOGGER.info('%s temperature remapped to showers', self)
                            else:
                                self._LOGGER.warning('%s problem reading required showers', self)
                        except KeyError:
                            self._LOGGER.warning('%s problem reading required showers 2', self)

                # check mode and set it
                if self._PARAM_MODE in good_values:
                    try:
                        self._set_param[self._PARAM_MODE] = self._MODE_TO_VALUE[good_values[self._PARAM_MODE]]
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

                self._set_new_data_pending = True
                # set after short delay to not affect switch or climate or water_heater
                self._timer_set_delay.cancel()
                if self._started:
                    self._timer_set_delay = threading.Timer(1, self._preparing_setting_http_data)
                    self._timer_set_delay.start()

                if bad_values != {}:
                    raise Exception("Following values could not be set: {}".format(bad_values))

        else:
            self._LOGGER.warning("%s No valid data fetched from server to set changes", self)
            raise Exception("Connection data error, problem to set data")

    def start(self) -> None:
        """Start communication with the server."""
        self._timer_periodic_read = threading.Timer(1, self._queue_get_data)
        self._timer_periodic_read.start()
        self._started = True

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
        self._login = False
