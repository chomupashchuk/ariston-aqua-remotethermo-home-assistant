# Aqua Ariston NET remotethermo integration
Thin integration is Aqua Ariston NET.
You are free to modify and distribute it. It is distributed 'as is' with no liability for possible damage.

## Integration was tested and works with:
  - Ariston Velis Wifi

## Installation
In `/config` folder create `custom_components` folder and copy folder `aristonaqua` with its contents in it. In `configuration.yaml` include:
```
ariston:
  username: !secret ariston_username
  password: !secret ariston_password
```

### Configuration example with all optional parameters
```
aristonaqua:
    username: !secret ariston_username
    password: !secret ariston_password
    store_config_files: true
    switches:
      - power
      - eco
    binary_sensors:
      - power
      - heating
      - eco
      - antilegionella
      - online
      - changing_data
      - update
    sensors:
      - errors
      - current_temperature
      - required_temperature
      - mode
      - showers
      - remaining_time
      - antilegionella_set_temperature
      - time_program
      - energy_use_in_day
      - energy_use_in_week
      - energy_use_in_month
      - energy_use_in_year
```

## Services
`aristonaqua.set_data` - Sets the requested data.

### Service attributes
  - `entity_id` - mandatory entity of Ariston water heater. For the rest of attributes please see Developer Tools tab Services within Home Assistant and select `aristonaqua.set_data`. You may also directly read services.yaml within the `aristonaqua` folder.
  
### Service use example
```
service: aristonaqua.set_data
data:
    entity_id: 'water_heater.aristonaqua'
    required_temperature: 55
    antilegionella_set_temperature: 75
```
