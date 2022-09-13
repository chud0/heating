import logging

from plugins import MqttPlugin, PluginRunManager, UnderFloorHeatingMixerPlugin

plugins_for_run = [MqttPlugin, UnderFloorHeatingMixerPlugin]
# need save order on  start but revers on stop!

# fixme: send plugins on stop messages!


# fixme: move to settings module
class Settings:
    def __init__(self, mqtt_host):
        self.mqtt_host = mqtt_host
        self.underfloor_heating_mixer = {
            'main_mixer': {
                'temp_topic': '/devices/wb-w1/controls/28-000005fa5c4c',
                'device_topics': ['/devices/wb-gpio/controls/EXT1_K3/on'],
                'target_temp': 28,
                'name': 'main_mixer',
            },
            'slave_mixers': [
                {
                    'temp_topic': '/devices/wb-w1/controls/28-000005fb67b8',
                    'device_topics': ['/devices/wb-gpio/controls/EXT1_K4/on'],
                    'target_temp': 35,
                    'name': 'corridor_mixer',
                },
                {
                    'temp_topic': '/devices/wb-w1/controls/28-000005fb67b8',
                    'device_topics': ['/devices/wb-gpio/controls/EXT1_K5/on'],
                    'target_temp': 32,
                    'name': 'bathroom_mixer',
                },
                {
                    'temp_topic': '/devices/wb-w1/controls/28-000005fb67b8',
                    'device_topics': ['/devices/wb-gpio/controls/EXT1_K6/on'],
                    'target_temp': 35,
                    'name': 'kitchen1_mixer',
                },
                {
                    'temp_topic': '/devices/wb-w1/controls/28-000005fb67b8',
                    'device_topics': ['/devices/wb-gpio/controls/EXT1_K7/on'],
                    'target_temp': 35,
                    'name': 'kitchen2_mixer',
                },
                {
                    'temp_topic': '/devices/wb-w1/controls/28-000005fb67b8',
                    'device_topics': ['/devices/wb-gpio/controls/EXT1_K8/on'],
                    'target_temp': 35,
                    'name': 'kitchen3_mixer',
                },
            ],
            'pump': {
                'device_topics': ['/devices/wb-mr6cu_47/controls/K2/on'],
                'state_changed_timeout': 30,
                'name': 'mixer_pump',
            },
        }


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    settings = Settings(mqtt_host='192.168.0.14')
    # settings = Settings(mqtt_host='127.0.0.1')
    program_manager = PluginRunManager(plugins=plugins_for_run, plugins_settings=settings)
    program_manager.start()

    try:
        program_manager.run()
    except (Exception, KeyboardInterrupt):
        program_manager.stop()
