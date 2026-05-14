import os

path = "src/core/config.py"
with open(path, "r") as f:
    content = f.read()

content = content.replace("pocketbase_admin_password: str", "pocketbase_admin_password: str\n    cors_origins: str = \"http://localhost:3000,http://127.0.0.1:3000\"")

with open(path, "w") as f:
    f.write(content)

print("Updated config.py")
