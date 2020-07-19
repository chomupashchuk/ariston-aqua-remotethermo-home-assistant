# Aqua Ariston NET remotethermo integration
Thin integration is Aqua Ariston NET.
You are free to modify and distribute it. It is distributed 'as is' with no liability for possible damage.

## Integration was tested and works with:
  - Ariston Lydos Wifi
  - Ariston Velis Wifi

## Installation
In `/config` folder create `custom_components` folder and copy folder `aquaariston` with its contents in it. In `configuration.yaml` include:
```
aquaariston:
  username: !secret ariston_username
  password: !secret ariston_password
```

### Configuration example with all optional parameters
```
aquaariston:
    username: !secret ariston_username
    password: !secret ariston_password
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
`aquaariston.aqua_set_data` - Sets the requested data.

### Service attributes
  - `entity_id` - mandatory entity of Ariston water heater. For the rest of attributes please see Developer Tools tab Services within Home Assistant and select `aquaariston.aqua_set_data`. You may also directly read services.yaml within the `aquaariston` folder.
  
### Service use example
```
service: aquaariston.aqua_set_data
data:
    entity_id: 'water_heater.aqua_ariston'
    required_temperature: 55
    antilegionella_set_temperature: 75
```
