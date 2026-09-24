from __future__ import annotations
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from .const import (IFNAME, HOST, PORT, KEYFILENAME)
import logging


_LOGGER = logging.getLogger(__name__)

DOMAIN = 'openwrt_wifi_switch'

PLATFORM_SCHEMA = vol.Schema(
    {
        vol.Required(IFNAME): cv.string,
        vol.Required(HOST): cv.string,
        vol.Required(KEYFILENAME): cv.string,
        vol.Required(PORT): cv.string,
    }
)


def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    devices = []
    for device in range(len(config[DOMAIN])):
        devices.append({
            "ifname": config[DOMAIN][device][IFNAME],
            "host": config[DOMAIN][device][HOST],
            "key_filename": config[DOMAIN][device][KEYFILENAME],
            "port": config[DOMAIN][device][PORT]
        })

    hass.data[DOMAIN] = {
        "devices": devices
    }
    hass.loop.call_soon_threadsafe(hass.async_create_task, async_load_platform(hass, 'switch', DOMAIN, {}, config))

    return True
