from parser import (C_ARITHMETIC, C_PUSH, C_POP,C_LABEL, C_GOTO, C_IF, C_FUNCTION, C_RETURN, C_CALL)
class CodeWriter:
    _SEG_BASE = {"local":"LCL", "argument":"ARG", "this":"THIS","that":"THAT"}

    def __init__(self, output_path: str):
        self._out = open(output_path, "w")
        self._filename   = ""        
        self._label_cnt  = 0         
        self._call_cnt   = 0        
        self._cur_func   = ""       

    def set_filename(self, filename: str):
        import os
        self._filename = os.path.splitext(os.path.basename(filename))[0]

    def write_init(self):
        asm = [
            "// Bootstrap: SP=256, call Sys.init",
            "@256",
            "D=A",
            "@SP",
            "M=D",
        ]
        self._emit(asm)
        self.write_call("Sys.init", 0)

    def close(self):
        self._out.close()

    def write_command(self, cmd: dict):
        t = cmd["type"]
        if t == C_ARITHMETIC:
            self.write_arithmetic(cmd["arg1"])
        elif t == C_PUSH:
            self.write_push_pop(C_PUSH, cmd["arg1"], cmd["arg2"])
        elif t == C_POP:
            self.write_push_pop(C_POP,  cmd["arg1"], cmd["arg2"])
        elif t == C_LABEL:
            self.write_label(cmd["arg1"])
        elif t == C_GOTO:
            self.write_goto(cmd["arg1"])
        elif t == C_IF:
            self.write_if(cmd["arg1"])
        elif t == C_FUNCTION:
            self.write_function(cmd["arg1"], cmd["arg2"])
        elif t == C_CALL:
            self.write_call(cmd["arg1"], cmd["arg2"])
        elif t == C_RETURN:
            self.write_return()

    def write_arithmetic(self, op: str):
        self._emit([f"// {op}"])
        if op == "add":
            self._emit(self._pop_d() + self._pop_a_m() + ["D=D+M"] + self._push_d())
        elif op == "sub":
            self._emit(self._pop_d() + self._pop_a_m() + ["D=M-D"] + self._push_d())
        elif op == "and":
            self._emit(self._pop_d() + self._pop_a_m() + ["D=D&M"] + self._push_d())
        elif op == "or":
            self._emit(self._pop_d() + self._pop_a_m() + ["D=D|M"] + self._push_d())
        elif op == "neg":
            self._emit(self._pop_d() + ["D=-D"] + self._push_d())
        elif op == "not":
            self._emit(self._pop_d() + ["D=!D"] + self._push_d())
        elif op in ("eq", "gt", "lt"):
            self._emit(self._cmp_asm(op))

    def _cmp_asm(self, op: str) -> list[str]:
        lbl = f"CMP_{op.upper()}_{self._label_cnt}"
        self._label_cnt += 1
        true_lbl = f"{lbl}_TRUE"
        end_lbl  = f"{lbl}_END"
        jump = {"eq": "JEQ", "gt": "JGT", "lt": "JLT"}[op]
        return (
            self._pop_d() +
            self._pop_a_m() +
            [
                "D=M-D",
                f"@{true_lbl}",
                f"D;{jump}",
                "D=0",
                f"@{end_lbl}",
                "0;JMP",
                f"({true_lbl})",
                "D=-1",         
                f"({end_lbl})",
            ] +
            self._push_d()
        )

    def write_push_pop(self, cmd_type: str, segment: str, index: int):
        tag = "push" if cmd_type == C_PUSH else "pop"
        self._emit([f"// {tag} {segment} {index}"])
        if segment == "constant":
            # only push makes sense for constant
            self._emit([f"@{index}", "D=A"] + self._push_d())
        elif segment in self._SEG_BASE:
            base = self._SEG_BASE[segment]
            if cmd_type == C_PUSH:
                self._emit([
                    f"@{base}", "D=M",
                    f"@{index}", "A=D+A", "D=M",
                ] + self._push_d())
            else:  
                self._emit([
                    f"@{base}", "D=M",
                    f"@{index}", "D=D+A",
                    "@R13", "M=D",
                ] + self._pop_d() + [
                    "@R13", "A=M", "M=D",
                ])

        elif segment == "temp":
            addr = 5 + index          # temp base = RAM[5]
            if cmd_type == C_PUSH:
                self._emit([f"@{addr}", "D=M"] + self._push_d())
            else:
                self._emit(self._pop_d() + [f"@{addr}", "M=D"])

        elif segment == "pointer":
            sym = "THIS" if index == 0 else "THAT"
            if cmd_type == C_PUSH:
                self._emit([f"@{sym}", "D=M"] + self._push_d())
            else:
                self._emit(self._pop_d() + [f"@{sym}", "M=D"])

        elif segment == "static":
            sym = f"{self._filename}.{index}"
            if cmd_type == C_PUSH:
                self._emit([f"@{sym}", "D=M"] + self._push_d())
            else:
                self._emit(self._pop_d() + [f"@{sym}", "M=D"])

        else:
            raise ValueError(f"Unknown segment: {segment!r}")

    def write_label(self, label: str):
        full = self._qualify(label)
        self._emit([f"// label {label}", f"({full})"])

    def write_goto(self, label: str):
        full = self._qualify(label)
        self._emit([f"// goto {label}", f"@{full}", "0;JMP"])

    def write_if(self, label: str):
        full = self._qualify(label)
        self._emit([f"// if-goto {label}"] + self._pop_d() + [f"@{full}", "D;JNE"])

    def write_function(self, func_name: str, n_locals: int):
        self._cur_func = func_name
        asm = [f"// function {func_name} {n_locals}", f"({func_name})"]
        # Initialise all local variables to 0
        for _ in range(n_locals):
            asm += ["D=0"] + self._push_d()
        self._emit(asm)

    def write_call(self, func_name: str, n_args: int):
        ret_label = f"{func_name}$ret.{self._call_cnt}"
        self._call_cnt += 1
        asm = [f"// call {func_name} {n_args}"]

        asm += [f"@{ret_label}", "D=A"] + self._push_d()
        for sym in ("LCL", "ARG", "THIS", "THAT"):
            asm += [f"@{sym}", "D=M"] + self._push_d()
        asm += [
            "@SP", "D=M",
            f"@{n_args + 5}", "D=D-A",
            "@ARG", "M=D",
        ]
        asm += ["@SP", "D=M", "@LCL", "M=D"]
        asm += [f"@{func_name}", "0;JMP"]
        asm += [f"({ret_label})"]
        self._emit(asm)

    def write_return(self):
        asm = ["// return",
            "@LCL", "D=M", "@R14", "M=D",
            "@5", "A=D-A", "D=M", "@R15", "M=D",
        ] + self._pop_d() + [
            "@ARG", "A=M", "M=D",
            "@ARG", "D=M+1", "@SP", "M=D",
        ]
        for i, sym in enumerate(("THAT", "THIS", "ARG", "LCL"), start=1):
            asm += [
                "@R14", "D=M",
                f"@{i}", "A=D-A", "D=M",
                f"@{sym}", "M=D",
            ]
        asm += ["@R15", "A=M", "0;JMP"]
        self._emit(asm)


    def _qualify(self, label: str) -> str:
        return f"{self._cur_func}${label}" if self._cur_func else label

    @staticmethod
    def _push_d() -> list[str]:
        return ["@SP", "A=M", "M=D", "@SP", "M=M+1"]

    @staticmethod
    def _pop_d() -> list[str]:
        return ["@SP", "AM=M-1", "D=M"]

    @staticmethod
    def _pop_a_m() -> list[str]:
        return ["@SP", "AM=M-1"]

    def _emit(self, lines: list[str]):
        for line in lines:
            self._out.write(line + "\n")
