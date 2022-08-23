import json

from json_database import JsonStorageXDG

from ovos_local_backend.configuration import CONFIGURATION
from copy import deepcopy


class SkillSettings:
    """ represents skill settings for a individual skill"""
    def __init__(self, skill_id, skill_settings=None, meta=None, display_name=None, remote_id=None):
        self.skill_id = skill_id
        self.display_name = display_name or self.skill_id
        self.settings = skill_settings or {}
        self.remote_id = remote_id or skill_id
        if not self.remote_id.startswith("@"):
            self.remote_id = f"@|{self.remote_id}"
        self.meta = meta or {}

    def serialize(self):
        # settings meta with updated placeholder values from settings
        # old style selene db stored skill settings this way
        meta = deepcopy(self.meta)
        for idx, section in enumerate(meta.get('sections', [])):
            for idx2, field in enumerate(section["fields"]):
                if "value" not in field:
                    continue
                if field["name"] in self.settings:
                    meta['sections'][idx]["fields"][idx2]["value"] = self.settings[field["name"]]
        return {'skillMetadata': meta,
                "skill_gid": self.remote_id,
                "display_name": self.display_name}

    @staticmethod
    def deserialize(data):
        if isinstance(data, str):
            data = json.loads(data)

        skill_json = {}
        skill_meta = data.get("skillMetadata") or {}
        for s in skill_meta.get("sections", []):
            for f in s.get("fields", []):
                if "name" in f and "value" in f:
                    val = f["value"]
                    if isinstance(val, str):
                        t = f.get("type", "")
                        if t == "checkbox":
                            if val.lower() == "true" or val == "1":
                                val = True
                            else:
                                val = False
                        elif t == "number":
                            val = float(val)
                        elif val.lower() in ["none", "null", "nan"]:
                            val = None
                        elif val == "[]":
                            val = []
                        elif val == "{}":
                            val = {}
                    skill_json[f["name"]] = val

        remote_id = data.get("skill_gid") or data.get("identifier")
        # this is a mess, possible keys seen by logging data
        # - @|XXX
        # - @{uuid}|XXX
        # - XXX

        # where XXX has been observed to be
        # - {skill_id}  <- ovos-core
        # - {msm_name} <- mycroft-core
        #   - {mycroft_marketplace_name} <- all default skills
        #   - {MycroftSkill.name} <- sometimes sent to msm (very uncommon)
        #   - {skill_id.split(".")[0]} <- fallback msm name
        # - XXX|{branch} <- append by msm (?)
        # - {whatever we feel like uploading} <- SeleneCloud utils
        fields = remote_id.split("|")
        skill_id = fields[0]
        if len(fields) > 1 and fields[0].startswith("@"):
            skill_id = fields[1]

        display_name = data.get("display_name") or \
                       skill_id.split(".")[0].replace("-", " ").replace("_", " ").title()

        return SkillSettings(skill_id, skill_json, skill_meta, display_name,
                             remote_id=remote_id)


class DeviceSettings:
    """ global device settings
    represent some fields from mycroft.conf but also contain some extra fields
    """

    def __init__(self, uuid, token, name=None, device_location=None, opt_in=True,
                 location=None, lang=None, date_format=None, system_unit=None, time_format=None,
                 email=None, isolated_skills=False):
        self.uuid = uuid
        self.token = token

        # ovos exclusive
        # individual skills can also control this via "__shared_settings" flag
        self.isolated_skills = isolated_skills  # control if skill settings should be shared across all devices

        # extra device info
        self.name = name or f"Device-{self.uuid}"  # friendly device name
        self.device_location = device_location or "somewhere"  # indoor location
        mail_cfg = CONFIGURATION.get("email", {})
        self.email = email or \
                     mail_cfg.get("recipient") or \
                     mail_cfg.get("smtp", {}).get("username")
        # mycroft.conf values
        self.date_format = date_format or CONFIGURATION.get("date_format") or "DMY"
        self.system_unit = system_unit or CONFIGURATION.get("system_unit") or "metric"
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
        return DeviceSettings(**data)


class DeviceDatabase(JsonStorageXDG):
    """ database of paired devices, used to keep track of individual device settings"""
    def __init__(self):
        super().__init__("ovos_devices")

    def add_device(self, uuid, token, name=None, device_location=None, opt_in=False,
                   location=None, lang=None, date_format=None, system_unit=None,
                   time_format=None, email=None, isolated_skills=False):
        device = DeviceSettings(uuid, token, name, device_location, opt_in,
                                location, lang, date_format, system_unit,
                                time_format, email, isolated_skills)
        self[uuid] = device.serialize()
        return device

    def get_device(self, uuid):
        dev = self.get(uuid)
        if dev:
            return DeviceSettings.deserialize(dev)
        return None

    def update_device(self, device):
        assert isinstance(device, DeviceSettings)
        kwargs = device.serialize()
        self.add_device(**kwargs)

    def total_devices(self):
        return len(self)

    def __iter__(self):
        for dev in self.values():
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
    """ database of device specific skill settings """
    def __init__(self):
        super().__init__("ovos_skill_settings")

    def add_setting(self, uuid, skill_id, setting, meta, display_name=None,
                    remote_id=None):
        remote_id = remote_id or f"@|{skill_id}"
        # check special flag per skill about shared settings
        # this is set by SeleneCloud util, can also be set by individual skills
        shared = setting.get("__shared_settings")

        # check device specific shared settings defaults
        if not shared:
            # check if this device is using "isolated_skills" flag
            # this flag controls if the device keeps it's own unique
            # settings or if skill settings are synced across all devices
            dev = DeviceDatabase().get_device(uuid)
            if dev and not dev.isolated_skills:
                shared = True

        if shared:
            # add setting to shared db
            with SharedSettingsDatabase() as sdb:
                return sdb.add_setting(skill_id, setting,
                                       meta, display_name, remote_id)

        remote_id = f"@{uuid}|{skill_id}"  # tied to device
        # add setting to device specific db
        skill = SkillSettings(skill_id, setting,
                              meta, display_name, remote_id)
        if uuid not in self:
            self[uuid] = {}
        self[uuid][skill_id] = skill.serialize()
        return skill

    def get_setting(self, skill_id, uuid):
        # check if this device is using "isolated_skills" flag
        # this flag controls if the device keeps it's own unique
        # settings or if skill settings are synced across all devices
        dev = DeviceDatabase().get_device(uuid)
        if dev and dev.isolated_skills:
            # get setting from device specific db
            if uuid in self:
                skill = self[uuid].get(skill_id)
                if skill:
                    return SkillSettings.deserialize(skill)

        # get settings from shared db -> default values if not set per device
        return SharedSettingsDatabase().get_setting(skill_id)

    def get_device_settings(self, uuid):
        sets = []
        # get setting from device specific db
        if uuid in self:
            sets += [SkillSettings.deserialize(skill)
                     for skill in self[uuid].values()]

        # get settings from shared db -> default values if not set per device
        skills = [s.skill_id for s in sets]
        sets += [s for s in SharedSettingsDatabase()
                 if s.skill_id not in skills]

        return sets

    def __enter__(self):
        """ Context handler """
        return self

    def __exit__(self, _type, value, traceback):
        """ Commits changes and Closes the session """
        try:
            self.store()
        except Exception as e:
            print(e)


class SharedSettingsDatabase(JsonStorageXDG):
    """ database of skill settings shared across all devices """
    def __init__(self):
        super().__init__("ovos_shared_skill_settings")

    def add_setting(self, skill_id, setting, meta, display_name=None,
                    remote_id=None):
        skill = SkillSettings(skill_id, setting, meta, display_name, remote_id)
        self[skill_id] = skill.serialize()
        return skill

    def get_setting(self, skill_id):
        skill = self.get(skill_id)
        if skill:
            return SkillSettings.deserialize(skill)
        return None

    def __iter__(self):
        for skill in self.values():
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
