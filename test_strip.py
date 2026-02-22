content = "```json\n{\"title\": \"A\"}\n```"
content = content.strip("```json").strip("```")
print(repr(content))
