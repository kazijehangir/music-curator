import os

path = "src/api/main.py"
with open(path, "r") as f:
    content = f.read()

old_code = """app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)"""

new_code = """cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)"""

content = content.replace(old_code, new_code)

with open(path, "w") as f:
    f.write(content)

print("Updated main.py")
