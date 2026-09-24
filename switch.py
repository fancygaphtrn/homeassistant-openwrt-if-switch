from __future__ import annotations

import logging
from typing import Any

import asyncssh
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
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
        self._attr_available = True
        self._attr_name = f"{device['host']} interface {device['ifname']}"
        self._attr_unique_id = f"{device['host']}_{device['ifname']}"
        self._attr_icon = "mdi:wifi-strength-4"

    async def _async_ssh_execute(self, commands: list[str]) -> list[str]:
        """Open an async connection and execute a sequence of commands.

        Raises HomeAssistantError if the connection or any command
        cannot be completed, so callers can distinguish a real failure
        from a command that legitimately returned no output.
        """
        results: list[str] = []
        try:
            async with asyncssh.connect(
                host=self._device["host"],
                port=self._device.get("port", 22),
                username=self._device.get("username", "root"),
                client_keys=[self._device["key_filename"]],
                # If a known_hosts file was configured, use it to verify
                # the router's host key. Otherwise fall back to no
                # verification at all (known_hosts=None) -- this is
                # equivalent to Paramiko's AutoAddPolicy and accepts any
                # host key, which is a MITM risk. Configure known_hosts
                # to avoid this.
                known_hosts=self._device.get("known_hosts"),
                connect_timeout=5,  # Socket connection timeout
                login_timeout=5     # Authentication handshake timeout
            ) as conn:
                for cmd in commands:
                    result = await conn.run(cmd, check=False)
                    _LOGGER.debug("async_ssh_execute cmd %s result %s", cmd, result)
                    if result.exit_status != 0:
                        raise HomeAssistantError(
                            f"Command '{cmd}' on {self._device['host']} "
                            f"exited with status {result.exit_status}: "
                            f"{result.stderr.strip() if result.stderr else ''}"
                        )
                    results.append(result.stdout.strip())
        except HomeAssistantError:
            raise
        except Exception as err:
            raise HomeAssistantError(
                f"AsyncSSH error on {self._device['host']}: {err}"
            ) from err

        return results

    async def async_update(self) -> None:
        """Fetch the latest visibility state from the OpenWrt router."""
        cmd = f"uci get wireless.{self._device['ifname']}.hidden"
        try:
            outputs = await self._async_ssh_execute([cmd])
        except HomeAssistantError as err:
            # Connection/command genuinely failed: mark the entity
            # unavailable rather than guessing a state.
            _LOGGER.error("Failed to update %s: %s", self._attr_name, err)
            self._attr_available = False
            return

        self._attr_available = True

        if not outputs or not outputs[0]:
            # The 'hidden' option has likely never been set on this
            # interface. Initialize it to a known value (visible).
            setup_cmd = f"uci set wireless.{self._device['ifname']}.hidden=0"
            try:
                await self._async_ssh_execute([setup_cmd, "uci commit wireless"])
            except HomeAssistantError as err:
                _LOGGER.error(
                    "Failed to initialize hidden option for %s: %s",
                    self._attr_name, err,
                )
                self._attr_available = False
                return
            self._attr_is_on = False
            return

        # uci returns '1' if the network hidden configuration is set to true
        self._attr_is_on = outputs[0].strip() == "1"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on (hide the SSID)."""
        cmds = [
            f"uci set wireless.{self._device['ifname']}.hidden=1",
            "uci commit wireless",
            "wifi"
        ]
        try:
            await self._async_ssh_execute(cmds)
        except HomeAssistantError as err:
            _LOGGER.error("Failed to turn on %s: %s", self._attr_name, err)
            self._attr_available = False
            self.async_write_ha_state()
            return

        self._attr_available = True
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off (show the SSID)."""
        cmds = [
            f"uci set wireless.{self._device['ifname']}.hidden=0",
            "uci commit wireless",
            "wifi"
        ]
        try:
            await self._async_ssh_execute(cmds)
        except HomeAssistantError as err:
            _LOGGER.error("Failed to turn off %s: %s", self._attr_name, err)
            self._attr_available = False
            self.async_write_ha_state()
            return

        self._attr_available = True
        self._attr_is_on = False
        self.async_write_ha_state()