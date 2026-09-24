# OpenWRT WiFi Switch for Home Assistant

Switch your WiFi on and off (by hiding/unhiding the SSID) using Home Assistant.

Connects to your OpenWRT router over SSH using key-based authentication
and toggles the `hidden` option on the given wireless interface via `uci`.

### Requirements

- SSH access to the router with a key pair (password auth is not
  supported; use `ssh-copy-id` or manually add your public key to the
  router's `/etc/dropbear/authorized_keys` or `/etc/ssh/authorized_keys`).

### Installation

Go to this folder `<config_dir>/custom_components/`.

Execute `git clone https://github.com/fancygaphtrn/homeassistant-openwrt-if-switch openwrt_wifi_switch`

Add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
openwrt_wifi_switch:
  - ifname: "<wifi-interface-ifname>"       # e.g. "default_radio0"
    host: "<ssh-host>"
    key_filename: "<path-to-private-key>"
    port: 22                                 # optional, defaults to 22
    username: "root"                         # optional, defaults to "root"
    known_hosts: "<path-to-known-hosts>"     # optional, see note below
```

### A note on `known_hosts`

If you omit `known_hosts`, the integration will **not verify the
router's SSH host key** (equivalent to blindly trusting any server that
answers on that host/port). This is convenient but is a man-in-the-middle
risk on untrusted networks. For better security, generate a known_hosts
file for the router, e.g.:

```
ssh-keyscan -p <port> <host> > /config/openwrt_known_hosts
```

and point `known_hosts` at that file.