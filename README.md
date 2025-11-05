# OpenWRT WiFi Switch for Home Assistant

Switch your WiFi or network on and off using Home Assistant.

This fork adds VLAN support, key-pair auth and pseudo-commands to enchance security for root access to OpenWRT (and fix [this issue](  https://github.com/multilan-tarek/homeassistant-openwrt-wifi-switch/issues/1#issue-3129391464) 
using [this fix](https://github.com/cozylife/hass_cozylife_local_pull/commit/4c9127d7f303ddd580cd3bc4726792e04868392a)).

> **_NOTE:_**  This Home Assistant component will automatically accept any host fingerprint.

&#x2615; [Buy me a coffee :)](https://paypal.me/davidalind)

## Wifi vs. VLAN

In Home Assistant you will be able to choose to control `wifi` or `network`.

Assuming you install the pseudo-command script on the main router:

* `wifi` will bring the SSID for that interface up/down. If that SSID is connected to a VLAN interface and you have a downstream AP the SSID will still be up on the AP.

* `network` will bring the interface up/down which will affect the VLAN also, BUT the SSID will still be up and you can connect but will not get an IP etc.

You can obviously install the pseudo-command script on the AP router as well and be creative with automations in your Home Assistant to bring up/down interfaces and SSID according to your preferences to make it "look nice", but I will not go into that.



## Setup

### Generate key pair

Run in your terminal of choice on any system where you can get the files.

Generate public/private key pair (select no passphrase when asked):
`ssh-keygen -t ed25519 -C "openwrt-key" -f ~/.ssh/openwrt-key`


### OpenWRT

We will add public key and pseudo-command script to router running OpenWRT.

This assumes you have logged in on your main router running OpenWRT using SSH as `root`.

Tested on OpenWrt 24.10.2.

#### Create pseudo-command script

Target here is to have [ha-commands.sh](./ha-commands.sh) in your root home directory and have it executable. This is one method.


Creat the script  
```
vi ~/ha-commands.sh
```

Paste contents of
[ha-commands.sh](./ha-commands.sh)

Make it executable  
```
chmod +x ~/ha-commands.sh
```

#### Add key to authorized_keys

We will add our public key and restrict it to running the pseudo-command script only.

Ensure `authorized_keys` file exist  
`touch /etc/dropbear/authorized_keys`

Add new public key line  
```
echo 'command="/root/ha-commands.sh",no-port-forwarding,no-x11-forwarding,no-agent-forwarding <key>' >> /etc/dropbear/authorized_keys
```

Replace the `<key>` part of that line with the contents of your public key `openwrt-key.pub`  

The line will end up looking like this (INFO: the trailing ` openwrt-key` is just a comment field)
```
command="/root/ha-commands.sh",no-port-forwarding,no-x11-forwarding,no-agent-forwarding  ssh-ed25519 AAAA... openwrt-key
```

#### Test configuration

Find an wifi-interface by running  
`uci show wireless | grep wifi-iface`  

**On the host where you have the `openwrt` keypair**, go to the directory where you have your openwrt keypair and run (substitute `default_radio0` with an existing interface if it does not exist in you setup):  
```
ssh -o PasswordAuthentication=no  -i openwrt-key root@192.168.1.1 wifi-status default_radio0
```  
which should return `1` or `0` depending on the disabled status of `default_radio0`.



### Home Assistant

Tested on core version 2025.8.3

#### Add custom component (this)

Target here is to have the contents of this repo in the custom_component directory. How you do it exactly is up to you.

For HAOS you can use the Terminal & SSH or File editor add-on. For dockerized maybe theres other options also.

In the terminal create directory for custom_components (or in root folder `homeassistant` in File editor) and enter it:
```
mkdir -p /config/custom_components
cd /config/custom_components
```

Clone this repo (or upload downloaded files using File editor)
```
git clone https://github.com/kludda/homeassistant-openwrt-if-switch.git
```

**Reboot Home Assistant.**


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