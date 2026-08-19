import urllib.request
import tarfile
import os

url = "https://sourceforge.net/projects/tigervnc/files/stable/1.13.1/tigervnc-1.13.1.x86_64.tar.gz/download"
print("Downloading...")
urllib.request.urlretrieve(url, "tigervnc.tar.gz")
print("Extracting...")
with tarfile.open("tigervnc.tar.gz", "r:gz") as tar:
    tar.extractall("tigervnc")
print("Extracted. Looking for x0vncserver...")
found = False
for root, dirs, files in os.walk("tigervnc"):
    if "x0vncserver" in files:
        print("FOUND:", os.path.join(root, "x0vncserver"))
        found = True

if not found:
    print("NOT FOUND")
