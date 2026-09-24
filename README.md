# OpenWRT WiFi Switch for Home Assistant

Switch your WiFi on and off using Home Assistant.

### Installation

Go to this folder `<config_dir>/custom_components/`.

Execute `git clone https://git.multilan.de/tarek/homeassistant-openwrt-wifi-switch`
or copy all the file to a directory or your choice (i.e. openwrt-if-switch)

Add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
openwrt_wifi_switch:
openwrt_wifi_switch:
- ifname: "wifinet6"
  host: "wan.lan"
  port: "22"
  key_filename: "/config/.ssh/openwrt-key"
```

## Setup

### Generate key pair

Run in your terminal of choice on any system where you can get the files.

Generate public/private key pair (select no passphrase when asked):
`ssh-keygen -t ed25519 -C "openwrt-key" -f ~/.ssh/openwrt-key`

add key to your router(s)

You should not be able to ssh to router without password.

#### Test configuration

Find an wifi-interface by running  
`uci show wireless | grep wifi-iface`  

**On the host where you have the `openwrt` keypair**, go to the directory where you have your openwrt keypair and run (substitute `default_radio0` with an existing interface if it does not exist in you setup):  
```
ssh -o PasswordAuthentication=no  -i openwrt-key root@192.168.1.1 wifi-status default_radio0
```  
which should return `1` or `0` depending on the disabled status of `default_radio0`.




#### Upload private key

Create folder for keys (can probably be anywhere the custom component can access)

```
mkdir -p /config/.ssh
```

Upload the private key `openwrt-key` to that folder.


#### Configure custom component


Add to your `configuration.yaml` file:

```yaml
openwrt_if_switch:
- ifname: "<wifi-interface-ifname>"
  iftype: "'wifi' or 'network'"
  host: "<ssh-host>"
  port: "<ssh-port>"
  key_filename: "<path-to-private-key-file>"
```
If you followed the guide above your path to the key will be:
`key_filename: "/config/.ssh/openwrt-key"`


```yaml
# Example configuration.yaml entry
openwrt_if_switch:
- ifname: "default_radio0"
  iftype: "wifi"
  host: "192.168.1.1"
  port: "22"
  key_filename: "/config/.ssh/openwrt-key"
```


You can have multiple device entries:
```yaml
openwrt_if_switch:
- ifname: "default_radio0"
  ...
- ifname: "wifinet2"
  ...  
```

**Reboot Home Assistant.**


Check your config for errors in Home Assistant and reboot if ok. Look for "OpenWRT Wifi/Network Switch" and you should have your switch entities there.
