import json

from json_database import JsonStorageXDG

from ovos_local_backend.configuration import CONFIGURATION


class SkillSettings:
    def __init__(self, skill_id, skill_settings=None, meta=None, display_name=None):
        self.skill_id = skill_id
        self.display_name = display_name or self.skill_id
        self.settings = skill_settings or {}
        self.meta = meta or {}

    def serialize(self):
        # settings meta with updated placeholder values from settings
        # old style selene db stored skill settings this way
        meta = dict(self.meta)
        for idx, section in enumerate(meta.get('sections', [])):
            for idx2, field in enumerate(section["fields"]):
                if "value" not in field:
                    continue
                if field["name"] in self.settings:
                    meta['sections'][idx]["fields"][idx2] = self.settings[field["name"]]
        return {'skillMetadata': meta,
                "uuid": self.skill_id,  # the uuid from selene is not device id (?)
                "skill_gid": self.skill_id,
                "display_name": self.display_name,
                "identifier": self.skill_id}

    @staticmethod
    def deserialize(data):
        if isinstance(data, str):
            data = json.loads(data)

        skill_json = {}
        skill_meta = data.get("skillMetadata") or data
        for s in skill_meta.get("sections", []):
            for f in s.get("fields", []):
                if "name" in f and "value" in f:
                    skill_json[f["name"]] = f["value"]

        skill_id = data.get("skill_gid") or data.get("identifier")
        # skill_id = skill_id.split("|")[0]
        display_name = data.get("display_name")

        return SkillSettings(skill_id, skill_json, skill_meta, display_name)


class DeviceSettings:
    """ global device settings
    represent some fields from mycroft.conf but also contain some extra fields
    """

    def __init__(self, device_id, token, name=None, device_location=None, opt_in=False,
                 location=None, lang=None, date_format=None, system_unit=None, time_format=None,
                 email=None, isolated_skills=False):
        self.uuid = device_id
        self.token = token

        # ovos exclusive
        self.isolated_skills = isolated_skills  # TODO - this will control if shared settings are returned

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

    def serialize(self):
        return self.__dict__

    @staticmethod
    def deserialize(data):
        if isinstance(data, str):
            data = json.loads(data)
        if "uuid" in data:
            data["device_id"] = data.pop("uuid")
        return DeviceSettings(**data)


class DeviceDatabase(JsonStorageXDG):
    def __init__(self):
        super().__init__("ovos_devices")

    def add_device(self, device_id, token, name=None, device_location=None, opt_in=False,
                   location=None, lang=None, date_format=None, system_unit=None,
                   time_format=None, email=None, isolated_skills=False):
        device = DeviceSettings(device_id, token, name, device_location, opt_in,
                                location, lang, date_format, system_unit,
                                time_format, email, isolated_skills)
        self[device_id] = device.serialize()
        return device

    def get_device(self, device_id):
        # TODO
        dev = self.get(device_id)
        if dev:
            return DeviceSettings.deserialize(dev)
        return None

    def total_devices(self):
        return len(self)

    def __iter__(self):
        for uid, dev in self.items():
            yield DeviceSettings.deserialize(dev)

    def __enter__(self):
        """ Context handler """
        return self

    def __exit__(self, _type, value, traceback):
        """ Commits changes and Closes the session """
        try:
            self.store()
        except Exception as e:
            print(e)


class SettingsDatabase(JsonStorageXDG):
    def __init__(self):
        super().__init__("ovos_skill_settings")

    def add_setting(self, device_id, skill_id, setting, meta, display_name=None):
        skill = SkillSettings(skill_id, setting, meta, display_name)
        if device_id not in self:
            self[device_id] = {}
        self[device_id][skill_id] = skill.serialize()
        return skill

    def get_setting(self, skill_id, device_id):
        if device_id not in self:
            return None
        skill = self[device_id].get(skill_id)
        if skill:
            return SkillSettings.deserialize(skill)
        return None

    def get_device_settings(self, device_id):
        if device_id not in self:
            return None
        for skill_id, skill in self[device_id].items():
            yield SkillSettings.deserialize(skill)

    def __iter__(self):
        for uid in self:
            for skill_id, skill in self[uid].items():
                yield SkillSettings.deserialize(skill)

    def __enter__(self):
        """ Context handler """
        return self

    def __exit__(self, _type, value, traceback):
        """ Commits changes and Closes the session """
        try:
            self.store()
        except Exception as e:
            print(e)
