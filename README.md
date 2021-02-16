# Aqua Ariston NET remotethermo integration
Thin integration is Aqua Ariston NET.
You are free to modify and distribute it. It is distributed 'as is' with no liability for possible damage.

## Donations
If you like this app, please consider donating some sum to your local charity organizations or global organization like Red Cross. I don't mind receiving donations myself (you may conact me for more details if you want to), but please consider charity at first.

## Integration was tested and works with:
  - Ariston Lydos Wifi
  - Ariston Velis Wifi
  - Ariston Lydos Hybrid

## Installation
In `/config` folder create `custom_components` folder and copy folder `aquaariston` with its contents in it. In `configuration.yaml` include:
```
aquaariston:
  username: !secret ariston_username
  password: !secret ariston_password
  type: "lydos"
```
Where `type` is one of:
- `lydos`
- `lydos_hybrid`
- `velis`  <br/>
**Order of Installation:**
- Copy data to `custom_components`;
- Restart Home Assistant to find the component;
- Include data in `configuration.yaml`;
- Restart Home Asistant to see new services.

### Configuration example with all optional parameters
```
aquaariston:
  username: !secret ariston_username
  password: !secret ariston_password
  type: "lydos"
  polling: 1.2                        # indicates relative time for requests waiting. Increase in case of timeouts. Default is 1.0
  store_config_files: true            # indicates if to store API data in a folder
  switches:
    - eco                             # switches ECO mode
    - power                           # switches power
  binary_sensors:
    - antilegionella                  # indicates antilegionella status
    - changing_data                   # indicates ongoing configuration on server by the API
    - eco                             # indicates ECO mode status
    - heating                         # indicates ongoing heating
    - online                          # indicates API online status
    - power                           # indicates power status
    - update                          # indicates API update
  sensors:
    - antilegionella_set_temperature  # antilegionella temperature
    - current_temperature             # current temperature
    - energy_use_in_day               # energy use in last day
    - energy_use_in_month             # energy use in last week
    - energy_use_in_week              # energy use in last month
    - energy_use_in_year              # energy use in last year
    - errors                          # errors
    - mode                            # manual or time program mode
    - remaining_time                  # remaining time for heating
    - required_showers                # required amount of showers (might not work on all models)
    - required_temperature            # required temperature (simulated by API itself for some models)
    - showers                         # estimated amount of average showers
    - temperature_mode                # indicates if required temeparture is based on required temperature or required showers
    - time_program                    # time program schedule
```

## Services
`aquaariston.aqua_set_data` - Sets the requested data.

### Service attributes
  - `entity_id` - mandatory entity of Ariston water heater. For the rest of attributes please see Developer Tools tab Services within Home Assistant and select `aquaariston.aqua_set_data`. You may also directly read services.yaml within the `aquaariston` folder. Note that changing `required_showers` changes `temperature_mode` to `showers` and changing `required_temperature` changes `temperature_mode` to temperature on models that use shower mode (temperature mode is being simulated for some models like Velis wifi).
  
### Service use example
```
service: aquaariston.aqua_set_data
data:
    entity_id: 'water_heater.aqua_ariston'
    antilegionella_set_temperature: 75
```
