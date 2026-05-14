with open("AGENT_RULES.md", "a") as f:
    f.write("\n11. **Security**: Hard-coded policies like CORS 'allow_origins' MUST NOT exist; they must depend on external environmental variables mapped to dynamically safe domain lists.\n")
