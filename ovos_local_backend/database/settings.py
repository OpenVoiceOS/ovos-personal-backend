from json_database import JsonDatabaseXDG

from ovos_local_backend.configuration import CONFIGURATION


class SharedSkillSettings:
    """
    skill settings shared across all devices
    """
    def __init__(self, skill_id, skill_settings=None):
        self.skill_id = skill_id
        self.settings = skill_settings


class DeviceSkillSettings:
    """
    skill settings tied to devices
    """
    def __init__(self, skill_id, device_id, skill_settings=None):
        self.skill_id = skill_id
        self.device_id = device_id
        self.settings = skill_settings


class DeviceSettings:
    """ global device settings
    represent some fields from mycroft.conf but also contain some extra fields
    """

    def __init__(self, device_id, token, name=None, device_location=None, opt_in=False,
                 location=None, lang=None, date_format=None, system_unit=None, time_format=None,
                 email=None):
        self.uuid = device_id
        self.token = token

        # ovos exclusive
        self.isolated_skills = False  # TODO - this will control if shared settings are returned

        # extra device info
        self.name = name or f"Device-{self.uuid}"  # friendly device name
        self.device_location = device_location or "somewhere"  # indoor location
        self.email = email or CONFIGURATION.get("email", {}).get("username")  # email sending api

        # mycroft.conf values
        self.date_format = date_format or CONFIGURATION.get("date_format") or "DMY"
        self.system_unit = system_unit or CONFIGURATION.get("system_unit") or "device"
        self.time_format = time_format or CONFIGURATION.get("time_format") or "full"
        self.opt_in = opt_in
        self.lang = lang or CONFIGURATION.get("lang") or "en-us"
        self.location = location or CONFIGURATION["default_location"]

    @property
    def selene_device(self):
        return {
            "description": self.device_location,
            "uuid": self.uuid,
            "name": self.name,

            # not tracked / meaningless
            # just for api compliance with selene
            'coreVersion': "unknown",
            'platform': 'unknown',
            'enclosureVersion': "",
            "user": {"uuid": self.uuid}  # users not tracked
        }

    @property
    def selene_settings(self):
        return {
            "dateFormat": self.date_format,
            "optIn": self.opt_in,
            "systemUnit": self.system_unit,
            "timeFormat": self.time_format,
            "uuid": self.uuid
        }


class DeviceDatabase(JsonDatabaseXDG):
    def __init__(self):
        super().__init__("ovos_devices")

    def add_device(self, device_id, token, name=None, device_location=None, opt_in=False,
                   location=None, lang=None, date_format=None, system_unit=None,
                   time_format=None, email=None):
        device = DeviceSettings(device_id, token, name, device_location, opt_in,
                                location, lang, date_format, system_unit,
                                time_format, email)
        self.add_item(device)

    def get_device(self, device_id):
        # TODO
        dev = self.get(device_id)
        if dev:
            dev = DeviceSettings(**dev)
        return dev

    def total_devices(self):
        return len(self)

    def __enter__(self):
        """ Context handler """
        return self

    def __exit__(self, _type, value, traceback):
        """ Commits changes and Closes the session """
        try:
            self.commit()
        except Exception as e:
            print(e)


class SharedSettingsDatabase(JsonDatabaseXDG):
    def __init__(self):
        super().__init__("ovos_shared_skill_settings")

    def add_setting(self, skill_id, setting):
        skill = SharedSkillSettings(skill_id, setting)
        self.add_item(skill)

    def get_setting(self, skill_id):
        # TODO
        skill = self.get(skill_id)
        if skill:
            return DeviceSettings(**skill)
        return None

    def total_skills(self):
        return len(self)

    def __enter__(self):
        """ Context handler """
        return self

    def __exit__(self, _type, value, traceback):
        """ Commits changes and Closes the session """
        try:
            self.commit()
        except Exception as e:
            print(e)


class SettingsDatabase(JsonDatabaseXDG):
    def __init__(self):
        super().__init__("ovos_skill_settings")

    def add_setting(self, skill_id, device_id, setting):
        skill = DeviceSkillSettings(skill_id, device_id, setting)
        self.add_item(skill)

    def get_setting(self, skill_id, device_id):
        # TODO
        skill = self.get(skill_id)
        if skill:
            return DeviceSettings(**skill)
        return None

    def total_settings(self):
        return len(self)

    def __enter__(self):
        """ Context handler """
        return self

    def __exit__(self, _type, value, traceback):
        """ Commits changes and Closes the session """
        try:
            self.commit()
        except Exception as e:
            print(e)
