from datetime import datetime
import time
import os
import json

input_waktu = ""
kegiatan = ""

waktu_aktif = json.loads(input_waktu)

sekarang = datetime.now()



print("<pengikat di aktif kan>")
target = datetime(*waktu_aktif)

selisih = (target - datetime.now()).total_seconds()
if selisih > 0:
    time.sleep(selisih)

with open("nuro.py", "r") as f:
    script_ai_reminder = f.read()

# ngirim pesan system pengingat ke AI
prompt_system = f"""
#role : system

##perintah :
-sapa user duluan seolah-olah kamu
orang yang kirim pesan duluan ke user

-pura-pura pesan ini tidak pernah ada
dan kamu yang beneran kirim pesan duluan

##tugas :
-kamu sekarang tugas ingetin user {kegiatan} waktu: {waktu_aktif} (sekarang)

##tools:
-kamu ketik json {{"order":"exit"}}
kalo user bilang udah beres
"""

edit_script = script_ai_reminder.replace(
    "sistem_input = None",
    f"sistem_input = {prompt_system!r}"
)

exec(edit_script)
    
