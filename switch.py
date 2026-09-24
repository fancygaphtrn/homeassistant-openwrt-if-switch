from __future__ import annotations

import logging
from typing import Any

import asyncssh
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'openwrt_wifi_switch'


async def async_setup_platform(hass: HomeAssistant,
                               config: ConfigType,
                               async_add_entities: AddEntitiesCallback,
                               discovery_info: DiscoveryInfoType | None = None
                               ) -> None:
    """Set up the OpenWrt platform asynchronously."""
    if DOMAIN not in hass.data or "devices" not in hass.data[DOMAIN]:
        _LOGGER.error("No device configuration found for domain %s", DOMAIN)
        return
        
    async_add_entities([WifiSwitch(device) for device in hass.data[DOMAIN]["devices"]])


class WifiSwitch(SwitchEntity):
    """Representation of an OpenWrt Wi-Fi Visibility Switch using AsyncSSH."""

    def __init__(self, device: dict[str, Any]) -> None:
        """Initialize the switch."""
        self._device = device
        self._attr_is_on = False
        self._attr_name = f"{device['host']} interface {device['ifname']}"
        self._attr_unique_id = f"{device['host']}_{device['ifname']}"
        self._attr_icon = "mdi:wifi-strength-4"

    async def _async_ssh_execute(self, commands: list[str]) -> list[str]:
        """Safely open an async connection, execute a sequence of commands, and return outputs."""
        results = []
        try:
            # Connect asynchronously without blocking the HA event loop
            async with asyncssh.connect(
                host=self._device["host"],
                port=self._device.get("port", 22),
                username="root",
                client_keys=[self._device["key_filename"]],
                known_hosts=None,  # Equivalent to Paramiko's AutoAddPolicy()
                connect_timeout=5,  # Socket connection timeout
                login_timeout=5     # Authentication handshake timeout
            ) as conn:
                for cmd in commands:
                    result = await conn.run(cmd, check=False)
                    _LOGGER.debug("async_ssh_execute cmd %s result %s", cmd, result)
                    # Strip out trailing/leading whitespaces from the output
                    results.append(result.stdout.strip())
        except Exception as err:
            _LOGGER.error("AsyncSSH error on %s: %s", self._device["host"], err)

        return results

    async def async_update(self) -> None:
        """Fetch the latest visibility state from the OpenWrt router."""
        cmd = f"uci get wireless.{self._device['ifname']}.hidden"
        outputs = await self._async_ssh_execute([cmd])
        
        if not outputs:
            # Handle empty output or initialization fallback
            setup_cmd = f"uci set wireless.{self._device['ifname']}.hidden=0"
            await self._async_ssh_execute([setup_cmd])
            self._attr_is_on = False
            return

        # uci returns '1' if the network hidden configuration is set to true
        self._attr_is_on = "1" in outputs[0]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on (hide the SSID)."""
        cmds = [
            f"uci set wireless.{self._device['ifname']}.hidden=1",
            "uci commit wireless",
            "wifi"
        ]
        await self._async_ssh_execute(cmds)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off (show the SSID)."""
        cmds = [
            f"uci set wireless.{self._device['ifname']}.hidden=0",
            "uci commit wireless",
            "wifi"
        ]
        await self._async_ssh_execute(cmds)
        self._attr_is_on = False
        self.async_write_ha_state()
