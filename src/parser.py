import re
#command types
C_ARITHMETIC = "C_ARITHMETIC"
C_PUSH       = "C_PUSH"
C_POP        = "C_POP"
C_LABEL      = "C_LABEL"
C_GOTO       = "C_GOTO"
C_IF         = "C_IF"
C_FUNCTION   = "C_FUNCTION"
C_RETURN     = "C_RETURN"
C_CALL       = "C_CALL"
ARITHMETIC_CMDS = {"add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"}

class Parser:
    def __init__(self, filepath: str):
        self.commands: list[dict] = []
        self._load(filepath)
        self._index = 0

    def _strip(self, line: str) -> str:
        """Remove inline comments and whitespace."""
        line = re.sub(r"//.*", "", line)
        return line.strip()

    def _load(self, filepath: str):
        with open(filepath, "r") as f:
            for raw in f:
                line = self._strip(raw)
                if not line:
                    continue
                cmd = self._parse_line(line)
                if cmd:
                    self.commands.append(cmd)

    def _parse_line(self, line: str) -> dict | None:
        parts = line.split()
        keyword = parts[0].lower()
        if keyword in ARITHMETIC_CMDS:
            return {"type": C_ARITHMETIC, "arg1": keyword, "arg2": None}
        if keyword == "push":
            return {"type": C_PUSH, "arg1": parts[1], "arg2": int(parts[2])}
        if keyword == "pop":
            return {"type": C_POP, "arg1": parts[1], "arg2": int(parts[2])}
        if keyword == "label":
            return {"type": C_LABEL, "arg1": parts[1], "arg2": None}
        if keyword == "goto":
            return {"type": C_GOTO, "arg1": parts[1], "arg2": None}
        if keyword == "if-goto":
            return {"type": C_IF, "arg1": parts[1], "arg2": None}
        if keyword == "function":
            return {"type": C_FUNCTION, "arg1": parts[1], "arg2": int(parts[2])}
        if keyword == "call":
            return {"type": C_CALL, "arg1": parts[1], "arg2": int(parts[2])}
        if keyword == "return":
            return {"type": C_RETURN, "arg1": None, "arg2": None}
        
        raise ValueError(f"Unknown VM command: {line!r}")

    def has_more_commands(self) -> bool:
        return self._index < len(self.commands)

    def advance(self) -> dict:
        cmd = self.commands[self._index]
        self._index += 1
        return cmd

    def reset(self):
        self._index = 0
