# hackFi
HackFi is an automation for breaking Security of Wi-Fi by breaking handshake file using traditional Brute-Force method.

# Requirements

* A Wi-Fi adapter that supports monitor mode.
* A `Linux` based environment.
* `Python3` and `pip3` set-up.
* `Aircrack-ng suite` need to be installed.

# Set-Up and Uses

> Set-Up
```
sudo bash set_env.sh
```
> Use
```
sudo python3 hackFi.py --help
```
[!img](assets/0.png)
* Extract wireless interface you want to use
```
sudo python3 hackFi.py -i <interface> -w <path/to/password_file>
```
[!img](assets/1.png)
