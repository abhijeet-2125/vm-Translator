# Assignment 2 — Hack VM Translator


---

## My project structure

```
vm_translator/
├── src/
│   ├── main.py          CLI entry point
│   ├── hack_vm.py       HackVM module
│   ├── parser.py        .vm file parser
│   └── code_writer.py   Hack assembly emitter
└── examples/
    ├── SimpleAdd.vm     push constant + add
    ├── StackTest.vm     all arithmetic/comparison ops
    └── MatrixMAC/
        ├── Sys.vm       
        ├── Main.vm      
        └── MAC.vm       
```

---


## How to Run
### To translate a single `.vm` file

```bash
cd src
python main.py ../examples/SimpleAdd.vm
# Produces: ../examples/SimpleAdd.asm
```

### To translate a directory 

```bash
python main.py ../examples/MatrixMAC/
# Produces: ../examples/MatrixMAC/MatrixMAC.asm
#           (with Sys.init bootstrap injected automatically)
```

### To use the HackVM library in the script

```python
from hack_vm import HackVM

vm = HackVM()
out = vm.translate("path/to/Foo.vm")          # single file
out = vm.translate("path/to/MyProject/")      # directory
print("Written to:", out)
```

---

## Supported VM Commands

| Category          | Commands                                      |
|-------------------|-----------------------------------------------|
| Stack Arithmetic  | `add sub neg eq gt lt and or not`             |
| Memory Access     | `push pop` × all 8 segments                  |
| Program Flow      | `label goto if-goto`                          |
| Function Calls    | `function call return`                        |

### Memory Segments

| Segment    | Hack address / mechanism           |
|------------|------------------------------------|
| `constant` | Inline immediate value             |
| `local`    | `RAM[LCL + index]`                 |
| `argument` | `RAM[ARG + index]`                 |
| `this`     | `RAM[THIS + index]`                |
| `that`     | `RAM[THAT + index]`                |
| `pointer`  | `THIS` (0) / `THAT` (1) directly  |
| `temp`     | `RAM[5 + index]`                   |
| `static`   | `Filename.index` global symbol     |

---

## Testing

The translator is compatible with all standard Nand2Tetris test suites:

- **Project 07**: `MemoryAccess/`, `StackArithmetic/`
- **Project 08**: `ProgramFlow/`, `FunctionCalls/`

To point the HACK HDL Simulator at the produced `.asm` file and run the
corresponding `.tst` / `.cmp` scripts.

```bash
# Translate the Nand2Tetris FibonacciSeries test bundle
python src/main.py nand2tetris/projects/08/FunctionCalls/FibonacciSeries/
```

---

## Architecture Notes

### `parser.py`
Tokenises each line, strips comments, and returns a list of command dicts
with fields `type`, `arg1`, `arg2`.

### `code_writer.py`
Stateful emitter that keeps track of:
- Current filename (for `static` segment label namespacing)
- Current function name (for local-label qualification)
- Unique counters for comparison jump labels and return-address labels

### Bootstrap
When translating a **directory** that contains `Sys.vm`, the translator
automatically prepends bootstrap code that sets `SP = 256` and calls
`Sys.init 0`.  Single-file translations skip the bootstrap.

---

## Example Output (SimpleAdd.vm → SimpleAdd.asm)

```asm
// push constant 7
@7
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 8
@8
D=A
@SP
A=M
M=D
@SP
M=M+1
// add
@SP
AM=M-1
D=M
@SP
AM=M-1
D=D+M
@SP
A=M
M=D
@SP
M=M+1
```
