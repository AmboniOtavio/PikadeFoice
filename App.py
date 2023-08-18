import paramiko
from flask_cors import CORS
import time
import tkinter as tk
from flask import Flask, request, jsonify
from tkinter import messagebox


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/configure-onu', methods=['POST'])
def configure_onu():
    data = request.get_json()
    print(data)
    serial = data["serial"]
    olt = data['olt']
    pon = data["pon"]
    id_livre = data["idLivre"]
    cliente = data["cliente"]
    customVlan = data["customVlan"]
    

    if not serial or not olt or not pon or not id_livre or not cliente:
        messagebox.showerror("Error", "All fields must be filled out.")
        return
    def vlan(customVlan, pon): 
        if customVlan: 
            return customVlan
        
        return int(pon.replace("/", ""))  # Transform "1/2/1" into 121
    commands = [
        f"interface gpon-olt_{pon}",
        f"onu {id_livre} type ZTE-F601 sn {serial}",
        f"!",
        f"interface gpon-onu_{pon}:{id_livre}",
        f"description {cliente}",
        f"tcont 2 name Tcont100M profile OT",
        f"gemport 1 name Gemport1 tcont 2 queue 1",
        f"switchport mode trunk vport 1",
        f"service-port 1 vport 1 user-vlan {vlan(customVlan=customVlan,pon=pon)} vlan {vlan(customVlan=customVlan,pon=pon)}",
        f"!",
        f"pon-onu-mng gpon-onu_{pon}:{id_livre}",
        f"service inter gemport 1 vlan {vlan(customVlan=customVlan,pon=pon)}",
        f"performance ethuni eth_0/1 start",
        f"vlan port eth_0/1 mode tag vlan {vlan(customVlan=customVlan,pon=pon)}",
        f"!"
    ]

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(olt, username="admin", password="OT#internet2018")
        ssh_shell = ssh.invoke_shell()

# Enter configuration mode
        ssh_shell.send("conf t\n")
        time.sleep(1)
        
        for command in commands:
            ssh_shell.send(command + "\n")
            time.sleep(1)
        output = ""
        while ssh_shell.recv_ready():
            output += ssh_shell.recv(1024).decode()
        print(output)
        return jsonify({"Status":"Key"})
    
        return messagebox.showinfo("Success", "ONU configuration completed successfully.")
    except paramiko.AuthenticationException:
        messagebox.showerror("Error", "Authentication failed.")
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        ssh.close()

if __name__ == '__main__':
    app.run(debug=True)