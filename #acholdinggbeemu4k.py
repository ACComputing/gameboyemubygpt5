import tkinter as tk
from tkinter import filedialog, messagebox

# ===================== CONFIG =====================
GB_WIDTH = 160
GB_HEIGHT = 144
SCALE = 3

BG = "#1a1a1a"
PANEL = "#101820"
ACCENT = "#4aa3ff"
TEXT = "#cfe9ff"
HEADER = "#0f1720"


# ===================== EMULATOR SPEC (MD → PROMPT CORE) =====================
EMULATOR_SPEC_PROMPT = """
A.C + ChatGPT GameBoy Emulator v0.1-Alpha

MMU Layout:
- 0x0000–0x7FFF ROM
- 0x8000–0x9FFF VRAM
- 0xC000–0xDFFF WRAM
- 0xFF00–0xFF7F IO

CPU:
- Registers: A F B C D E H L
- SP, PC (16-bit)
- Start execution at 0x0100

Instructions:
0x21 LD HL, d16
0x31 LD SP, d16
0xAF XOR A
0x76 HALT

Goal:
Cycle-based emulation with debugger visualization.
"""


# ===================== MMU =====================
class MMU:
    def __init__(self):
        self.mem = [0] * 0x10000

    def load_rom(self, rom):
        size = min(len(rom), 0x8000)
        for i in range(size):
            self.mem[i] = rom[i]

    def read(self, addr):
        return self.mem[addr]


# ===================== CPU =====================
class CPU:
    def __init__(self):
        self.mmu = MMU()
        self.reset()

    def reset(self):
        self.A = self.B = self.C = self.D = self.E = self.H = self.L = 0
        self.F = 0
        self.SP = 0xFFFE
        self.PC = 0x0100
        self.halted = False

        self.fb = [0] * (GB_WIDTH * GB_HEIGHT)

    def load_rom(self, path):
        self.reset()
        with open(path, "rb") as f:
            self.mmu.load_rom(f.read())

    def read8(self):
        v = self.mmu.read(self.PC)
        self.PC = (self.PC + 1) & 0xFFFF
        return v

    def read16(self):
        lo = self.read8()
        hi = self.read8()
        return lo | (hi << 8)

    def step(self):
        if self.halted:
            return

        op = self.read8()

        if op == 0x21:  # LD HL, d16
            v = self.read16()
            self.H = (v >> 8) & 0xFF
            self.L = v & 0xFF

        elif op == 0x31:  # LD SP, d16
            self.SP = self.read16()

        elif op == 0xAF:  # XOR A
            self.A = 0
            self.F = 0x80

        elif op == 0x76:
            self.halted = True


# ===================== PPU =====================
class PPU:
    def __init__(self, cpu):
        self.cpu = cpu

    def render(self):
        fb = self.cpu.fb
        for y in range(GB_HEIGHT):
            base = y * GB_WIDTH
            for x in range(GB_WIDTH):
                fb[base + x] = ((x ^ y ^ self.cpu.A) & 1)


# ===================== EMULATOR =====================
class Emulator:
    def __init__(self, root):
        self.root = root
        self.cpu = CPU()
        self.ppu = PPU(self.cpu)
        self.running = False

        root.title("A.C + ChatGPT GameBoy Emulator v0.1")
        root.geometry("1100x720")
        root.configure(bg=BG)

        # ================= MENU =================
        menu = tk.Menu(root)

        filemenu = tk.Menu(menu, tearoff=0)
        filemenu.add_command(label="Load ROM", command=self.load_rom)
        filemenu.add_command(label="Exit", command=root.quit)
        menu.add_cascade(label="File", menu=filemenu)

        emu = tk.Menu(menu, tearoff=0)
        emu.add_command(label="Play ROM", command=self.start)
        emu.add_command(label="Pause", command=self.pause)
        emu.add_command(label="Reset", command=self.reset)
        menu.add_cascade(label="Emulation", menu=emu)

        helpmenu = tk.Menu(menu, tearoff=0)
        helpmenu.add_command(label="Controls", command=self.controls)
        helpmenu.add_command(label="About", command=self.about)
        menu.add_cascade(label="Help", menu=helpmenu)

        root.config(menu=menu)

        # ================= LAYOUT =================
        self.main = tk.Frame(root, bg=BG)
        self.main.pack(fill="both", expand=True)

        # SCREEN
        self.canvas = tk.Canvas(
            self.main,
            width=GB_WIDTH * SCALE,
            height=GB_HEIGHT * SCALE,
            bg="black",
            highlightthickness=0
        )
        self.canvas.pack(side="left", padx=10, pady=10)

        self.img = tk.PhotoImage(width=GB_WIDTH, height=GB_HEIGHT)
        self.canvas.create_image(0, 0, anchor="nw", image=self.img)

        # ================= DEBUG PANEL =================
        self.debug = tk.Frame(self.main, bg=PANEL, width=300)
        self.debug.pack(side="right", fill="y")

        tk.Label(
            self.debug,
            text="DEBUGGER",
            fg=ACCENT,
            bg=PANEL,
            font=("Courier", 14, "bold")
        ).pack(pady=10)

        self.reg = tk.Label(self.debug, fg=TEXT, bg=PANEL, font=("Courier", 11))
        self.reg.pack(anchor="w", padx=10)

        self.pc = tk.Label(self.debug, fg=TEXT, bg=PANEL, font=("Courier", 11))
        self.pc.pack(anchor="w", padx=10)

        self.disasm = tk.Label(self.debug, fg=ACCENT, bg=PANEL,
                                font=("Courier", 10), justify="left")
        self.disasm.pack(anchor="w", padx=10, pady=10)

        self.spec = tk.Label(self.debug, fg="#6ee7ff", bg=PANEL,
                             font=("Courier", 8), justify="left", wraplength=280)
        self.spec.pack(anchor="w", padx=10, pady=10)
        self.spec.config(text=EMULATOR_SPEC_PROMPT[:600])

        self.loop()

    # ================= CONTROLS =================
    def load_rom(self):
        path = filedialog.askopenfilename()
        if path:
            self.cpu.load_rom(path)

    def start(self): self.running = True
    def pause(self): self.running = False
    def reset(self): self.cpu = CPU()

    def controls(self):
        messagebox.showinfo("Controls", "Z=A X=B Enter=Start Shift=Select Arrows=Move")

    def about(self):
        messagebox.showinfo("About", "A.C + ChatGPT Emulator v0.1")

    # ================= DEBUG =================
    def update_debug(self):
        c = self.cpu

        self.reg.config(
            text=f"A:{c.A:02X} F:{c.F:02X}\n"
                 f"B:{c.B:02X} C:{c.C:02X}\n"
                 f"D:{c.D:02X} E:{c.E:02X}\n"
                 f"H:{c.H:02X} L:{c.L:02X}"
        )

        self.pc.config(text=f"PC:{c.PC:04X} SP:{c.SP:04X}")

        out = []
        pc = c.PC
        for i in range(5):
            op = c.mmu.read(pc + i)
            out.append(f"{pc+i:04X}: {op:02X}")

        self.disasm.config(text="\n".join(out))

    # ================= DRAW =================
    def draw(self):
        self.ppu.render()
        fb = self.cpu.fb

        rows = []
        for y in range(GB_HEIGHT):
            row = []
            base = y * GB_WIDTH
            for x in range(GB_WIDTH):
                row.append("#ffffff" if fb[base + x] else "#000000")
            rows.append("{" + " ".join(row) + "}")

        self.img.put(" ".join(rows))

    # ================= LOOP =================
    def loop(self):
        if self.running:
            for _ in range(250):
                self.cpu.step()

        self.draw()
        self.update_debug()
        self.root.after(16, self.loop)


# ===================== RUN =====================
if __name__ == "__main__":
    root = tk.Tk()
    Emulator(root)
    root.mainloop()
