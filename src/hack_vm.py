import os
import glob
from parser import Parser
from code_writer import CodeWriter

class HackVM:
    def translate(self, path: str, emit_bootstrap: bool = None) -> str:
        path = path.rstrip(os.sep)
        if os.path.isdir(path):
            vm_files = sorted(glob.glob(os.path.join(path, "*.vm")))
            if not vm_files:
                raise FileNotFoundError(f"No .vm files found in {path!r}")
            out_name = os.path.basename(path)
            out_path = os.path.join(path, out_name + ".asm")
            need_boot = emit_bootstrap if emit_bootstrap is not None else \
                        any("Sys.vm" in f for f in vm_files)
        elif path.endswith(".vm") and os.path.isfile(path):
            vm_files = [path]
            out_path = path.replace(".vm", ".asm")
            need_boot = emit_bootstrap if emit_bootstrap is not None else False
        else:
            raise ValueError(f"Path must be a .vm file or directory: {path!r}")

        writer = CodeWriter(out_path)
        if need_boot:
            writer.write_init()

        for vm_file in vm_files:
            writer.set_filename(vm_file)
            parser = Parser(vm_file)
            while parser.has_more_commands():
                cmd = parser.advance()
                writer.write_command(cmd)

        writer.close()
        return out_path
