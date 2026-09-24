from __future__ import annotations
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from .const import (IFNAME, HOST, PORT, KEYFILENAME, USERNAME, KNOWN_HOSTS)
import logging


_LOGGER = logging.getLogger(__name__)

DOMAIN = 'openwrt_wifi_switch'

PLATFORM_SCHEMA = vol.Schema(
    {
        vol.Required(IFNAME): cv.string,
        vol.Required(HOST): cv.string,
        vol.Required(KEYFILENAME): cv.string,
        vol.Optional(PORT, default=22): cv.port,
        vol.Optional(USERNAME, default="root"): cv.string,
        # Path to a known_hosts file used to verify the router's SSH host
        # key. If omitted, host key verification is DISABLED (trust on
        # first use / no verification) -- see README for the security
        # implications before leaving this unset.
        vol.Optional(KNOWN_HOSTS): cv.string,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the OpenWrt Wifi Switch component from YAML."""
    devices = []
    for device_config in config[DOMAIN]:
        devices.append({
            "ifname": device_config[IFNAME],
            "host": device_config[HOST],
            "key_filename": device_config[KEYFILENAME],
            "port": device_config[PORT],
            "username": device_config[USERNAME],
            "known_hosts": device_config.get(KNOWN_HOSTS),
        })
 
    hass.data[DOMAIN] = {
        "devices": devices
    }
 
    await async_load_platform(hass, 'switch', DOMAIN, {}, config)

    return True
