#!/data/data/com.termux/files/usr/bin/python
#!/data/data/com.termux/files/usr/bin/python
import string 
import random
import requests
import json
import time
import re
import os
from humanize import naturaltime
import subprocess
from datetime import datetime


"""this fungtion return text random(salt) for name"""
def get_str_salt(size = 8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=size))
    
def get_config_seting():
    data = {}
    with open("config.txt", "r") as f:
        txt = f.readlines()

    for line in txt:
        line = line.strip()
        if not line or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if value == "True":
            value = True
        elif value == "False":
            value = False
        elif value.isdigit():
            value = int(value)
        data[key] = value
    return data

    
"""there function get data txt change return dict """    
    
def natural_list_time(list_comit):
    for i,comit in enumerate(list_comit):
        waktu_sekarang = datetime.now()
        try:
            if comit["role"] == "model":#karena comit memori di buat sama ai
                text = comit["parts"][0]["text"]
                ada_time = re.search(r"```time\s*(.*?)\s*```\s*(.*)",text,re.S)
                if ada_time:
                    waktu = ada_time.group(1)#ambil str tangal time
                    waktu_di_comit = datetime.fromisoformat(waktu)
                    text = text.replace(ada_time.group(0),naturaltime(waktu_sekarang - waktu_di_comit))
                    list_comit[i]["parts"][0]["text"] = text
        #key eror kalo role nya bukan model             
        except KeyError:
            pass
            
    return list_comit
    
class Gemini:
    def __init__(self, file_riwayat,prompt, model,):
        os.makedirs(file_riwayat, exist_ok=True)
        
        self.config_ai = get_config_seting()
        self.output_terminal = ""
        self.file_riwayat = file_riwayat
        self.model = model
        self.prompt = [{"parts":[{"text":prompt}]}]
        self.api_key = ""

        self.url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={self.api_key}"
        )

        self.headers = {"Content-Type": "application/json"}
        self.chat_history = self.prompt + self.get_riwayat_penting()
       
        #ambil jika data chat pausan ada
        try:
            with open(self.file_riwayat + "/short.json","r") as f:#take memori jangka pendek
                data = json.load(f)
            self.percakapan_sekarang = data 
        except (FileNotFoundError,json.JSONDecodeError):
            self.percakapan_sekarang = []
            
    def minta_respone_ai(self,payload):
        response = requests.post(
            self.url,
            headers=self.headers,
            json=payload
        )

        if response.status_code == 429:
            print("limit kena tunggu 60 detik lagi")
            time.sleep(60)
            return
        elif response.status_code == 200:
            data = response.json()
            text_ai = data["candidates"][0]["content"]["parts"][0]["text"]
            return text_ai
        elif response.status_code == 401:
            print("api key kadaluarsa!")
            new_api_key = input("api key new:")
            os.system(f"sed -i 's/{self.api_key}/{new_api_key}/g' ai.py")
        else:
            print("status code",response.status_code, response.reason)
            return "terjadi masalah"
            
    def get_riwayat_penting(self):
        try:
            with open(self.file_riwayat + "/medium.json", "r") as file:
                data = json.load(file)
                return natural_list_time(data)
        except (FileNotFoundError,json.JSONDecodeError):
            return []
            
    def save_riwayat_penting(self):
        time_commit = datetime.now()
        prompt_comit = """
-ringkas apa saja yanh telan di lakukan di termux
-ringas singkat seperlu dan sepentingnya seperti meng isi projek memori
-ringkas minimal 10 beris
-jangan menjelaskan proses berfikir
-hanya tulis hal yang penting dengan pendek dan evisien 

contoh:
*  main.py berjalan di latar belkang memprint halo ke log.txt 
*  Menginstal `vim`.
*  Menginstal `git`.
*  Menghapus `vim`.
*  Menghapus `git`.
        """
        payload_comit = {
            "contents": self.percakapan_sekarang + [{
                "role":"user",
                "parts":[{"text":prompt_comit}]
            }]
        }
        
        comit = [{
                "role":"model",
                "parts":
                [{"text": f"```time{time_commit}```"+ self.minta_respone_ai(payload_comit)}]
            }]
        #simpen comitan ai bentuk json 
        
        with open(self.file_riwayat + "/medium.json", "w") as file:
            json.dump(self.get_riwayat_penting() + comit, file, indent=2)
        
    # Jalankan bash / python / dan ngomong
    def eksekusi_perintah(self, text):
        if text == None:
            return 
        ada_bash = re.search(r"```bash\s*(.*?)\s*```\s*(.*)",text,re.S)
        ada_python = re.search(r"```python\s*(.*?)\s*```\s*(.*)",text,re.S)
        
        if ada_bash:
            code_bash = ada_bash.group(1)
            #hapus Bash nyisa kata kata ai
            text_ai = text.replace(ada_bash.group(0),"")
            self.output_terminal = subprocess.run(
                ["bash", "-c", code_bash],text=True,capture_output=True
                ).stdout[:200]
            print(self.output_terminal)    
        elif ada_python:
            code_python = ada_python.group(1)
            text_ai = text.replace(ada_python.group(0),"")
            exec(code_python)
        else:
            text_ai = text
            
        if self.config_ai["speech"]:
            os.system("termux-tts-speak -l id " + text_ai)
      
    # Kirim prompt ke Gemini
    def kirim(self, text_input):
        #tambahin hasil log Terminal 
        
        self.percakapan_sekarang.append({
            "parts":[{"text":"OUTPUT TERMINAL TERMUX:\n\n" + self.output_terminal}]
            })
        self.percakapan_sekarang.append({
            "role": "user",
            "parts": [{"text":text_input}]
            })
            
        payload = {
            "contents": self.prompt + self.get_riwayat_penting() + self.percakapan_sekarang
        }
        
        text_ai = self.minta_respone_ai(payload)
        
        tools_call = re.search(r"```json\s*(.*?)\s*\s*(.*)```",text_ai,re.S)
        if tools_call:
            string_tools = tools_call.group(2)
            tools = json.loads(string_tools)
            
            if tools["mode"] == "read" and os.path.exists(tools["name"]):
                name_file = tools["name"]
                isi_file = subprocess.check_output(["cat", name_file ], text=True)
                self.percakapan_sekarang.append({
                    "role": "user",
                    "parts": [{"text":f"ISI FILE {name_file} :\n\n +{isi_file}"}]
                })
                text_ai = self.minta_respone_ai(payload)
            elif tools["mode"] == "stop" and tools["name"] == "chat":
                return "stop"
            elif tools["mode"] == "reminder":
                print("<mengikatkan>")  
                task = tools["name"]["task"]  
                active_time = tools["name"]["time"]  
                name_plogram_copy = task[5:].replace(" ","_") + get_str_salt() + ".py"  
              
                #copy templet mnge buat ploglamer timer di latar belakang   
                Bash = f"""  
                touch {name_plogram_copy}
                cat timer_pengaktif.py > {name_plogram_copy}
              
                sed -i 's/input_waktu = ""/input_waktu = "{active_time}"/g' {name_plogram_copy}  
                sed -i 's/kegiatan = ""/kegiatan = "{task}"/g' {name_plogram_copy}  
            
                mv {name_plogram_copy} file-sementara  
             
                python file-sementara/{name_plogram_copy} &  
                echo "menambahkan proses"  
                ps -aux  
              
                """  
                os.system(Bash)
                #os.system(f'printf "{tools["name"]["time"]}\n{tools["name"]["task"]}\n" | python timer_pengaktif_ai.py &')
        
        if self.config_ai["text_output"]:
            print(text_ai)
            
        self.eksekusi_perintah(text_ai)

        self.percakapan_sekarang.append({
            "role": "model",
            "parts": [{"text": text_ai}]
            })
                    
    # Loop chat
    def run(self):
        time_now = datetime.now()
                    
        while True:
            #kalo > 20 bakal di ringkas & perbarui otomatis memori nya
            time_now = datetime.now()
            
            if len(self.percakapan_sekarang) >= 10:
                self.save_riwayat_penting()
                os.system("echo '[]' > state.json && py ai.py")
                #perbarui self self 
                self.chat_history = self.prompt + self.get_riwayat_penting()
                try:
                    with open("state.json","r") as f:
                        data = json.load(f)
                        self.percakapan_sekarang = data 
                except (FileNotFoundError,json.JSONDecodeError):
                    self.percakapan_sekarang = []
                    
            if not self.config_ai["voice_detector"]:
                
                user_input =  input("\033[32mprompt<<").lower()
                print()
            else:
                print("bicara")
                user_input = subprocess.check_output(
                    ["termux-speech-to-text","-l","id-ID"],
                    text=True
                    ).strip()       
            
            if user_input in ["exit", "quit"]:
                
                #simpen dulu chat sekarang 
                with open(self.file_riwayat + "/short.json","w") as f:
                    json.dump(self.percakapan_sekarang[1:],f,indent=2)
                break
            
            try:
                if self.kirim( "WAKTU:" + str(time_now) + "\n" + user_input) == "stop":
                    break
            except requests.exceptions.ConnectionError:
                print("gak ada koneksi internet!")    
                break              
                
gemini_lite = Gemini(
    file_riwayat="memory_ai_1",
    prompt= """
#Prompt system 

##peran:
 -nama kamu gentink
 -Kamu ai genedator bash termux 
 -membuat bash sederhan simpel praktis aman
 -kamu mengubah input peritah user jadi bash

##kontext:
 -kamu ai api yang gw buat di pyhon termux tanpa root
 -saya sudah install termux-api, python , git
 -kamu memiliki akses ke bash termux setiap bash 
  yang kamu hasilkan akan di eksekusi tapo harus di bungkus dengan 
  ```bash [BASH]```
  dan di tampilkan output Terminal nya ke kamu
  sebanyak 1-50 kata 
 -kamu masih dalam pengembangan saya aang 

##tujuan:
 -memudahkan user mengunakan termux tanpa hafal
 seluruh bash 
 -membuat user langsung meng exsekusi bash langsung
 tanpa coppy paste
 
##tools:
 -kamu dapat membaca isi file text dengan cara 
  ```json {"mode":"read","name":"[NAMA-FILE]"}```
  ini akan menampilkan isi file text kepada kamu untuk kamu lihat
  
 -kamu bisa hentikan percakapan dengan:
  ```json {"mode":"stop","name":"chat"}```
  
 -jika user suruh ingatkan sesuatu atau kamu punya inisiatif 
  ```json {"mode":"reminder","name":{"task":"[PERIHAL]","time":"[WAKTU]"}}```
  
  -isi [WAKTU] pake format datetime python!
  -Jangan gunakan karakter khusus Bash dalam [PERIHAL]
  
  *contoh 
  ```json {"mode":"reminder","name":{"task":"beli buku b.jepang buat sekolah","time":[2026,8,8,8,0,0]}```
  ini akan di serahkan ke data base ai pengingat yang bakal 
  telfon dan ingetin gw
  
##larangan:
 -jangan buat perintah bash berbahaya 
 -jangan hasilkan bash atau sript python atau Bash yang ter pisah pisah di keluaran
 -jangan bertinfak melebihi asisten user 
 -jangan bungkus Bash dengan kutip 1 

##keluaran:
-posisikan bash di awal lalu penjelasan 2-5 baris
singkat jelas dan konvirmasi di bawah
""",
    model="gemini-2.5-flash"
)

gemini_lite.run()
    
     
    
    
    
    
