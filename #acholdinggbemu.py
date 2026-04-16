import tkinter as tk
from tkinter import filedialog, messagebox

GB_WIDTH = 160
GB_HEIGHT = 144
SCALE = 3

BG = "#1a1a1a"
PANEL = "#101820"
ACCENT = "#4aa3ff"
TEXT = "#cfe9ff"


# ===================== MMU =====================
class MMU:
    def __init__(self):
        self.mem = [0] * 0x10000

    def load_rom(self, rom):
        size = min(len(rom), 0x8000)
        for i in range(size):
            self.mem[i] = rom[i]

    def read(self, addr):
        return self.mem[addr & 0xFFFF]


# ===================== CPU =====================
class CPU:
    def __init__(self):
        self.mmu = MMU()
        self.reset()

    def reset(self):
        self.A = 0x01
        self.F = 0
        self.B = 0
        self.C = 0
        self.D = 0
        self.E = 0
        self.H = 0
        self.L = 0

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

        # LD HL, d16
        if op == 0x21:
            v = self.read16()
            self.H = (v >> 8) & 0xFF
            self.L = v & 0xFF

        # LD SP, d16
        elif op == 0x31:
            self.SP = self.read16()

        # XOR A
        elif op == 0xAF:
            self.A ^= self.A
            self.F = 0x80

        # HALT
        elif op == 0x76:
            self.halted = True


# ===================== PPU (ROM VISUAL MODE) =====================
class PPU:
    def __init__(self, cpu):
        self.cpu = cpu

    def render(self):
        fb = self.cpu.fb

        for y in range(GB_HEIGHT):
            base = y * GB_WIDTH
            tile_y = y // 8

            for x in range(GB_WIDTH):
                tile_x = x // 8
                addr = 0x8000 + ((tile_y * 16 + tile_x) % 0x7FFF)

                val = self.cpu.mmu.read(addr)
                fb[base + x] = (val >> (x % 8)) & 1


# ===================== EMULATOR =====================
class Emulator:
    def __init__(self, root):
        self.root = root
        self.cpu = CPU()
        self.ppu = PPU(self.cpu)
        self.running = False

        self.root.title("ChatGPT + Gemini GameBoy Emulator")
        self.root.geometry("1100x720")
        self.root.configure(bg=BG)

        # ================= MENU =================
        menu = tk.Menu(root)

        filemenu = tk.Menu(menu, tearoff=0)
        filemenu.add_command(label="Play ROM", command=self.load_rom)
        filemenu.add_command(label="Reset", command=self.reset)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=root.quit)
        menu.add_cascade(label="File", menu=filemenu)

        emu = tk.Menu(menu, tearoff=0)
        emu.add_command(label="Run", command=self.start)
        emu.add_command(label="Pause", command=self.pause)
        menu.add_cascade(label="Emulation", menu=emu)

        helpmenu = tk.Menu(menu, tearoff=0)
        helpmenu.add_command(label="Controls", command=self.controls)
        helpmenu.add_command(label="About", command=self.about)
        menu.add_cascade(label="Help", menu=helpmenu)

        root.config(menu=menu)

        # ================= MAIN LAYOUT =================
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
        self.debug = tk.Frame(self.main, bg=PANEL, width=280)
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

        self.disasm = tk.Label(
            self.debug,
            fg=ACCENT,
            bg=PANEL,
            font=("Courier", 10),
            justify="left"
        )
        self.disasm.pack(anchor="w", padx=10, pady=10)

        self.loop()

    # ================= ACTIONS =================
    def load_rom(self):
        path = filedialog.askopenfilename()
        if path:
            self.cpu.load_rom(path)

    def start(self):
        self.running = True

    def pause(self):
        self.running = False

    def reset(self):
        self.cpu = CPU()
        self.ppu = PPU(self.cpu)

    def controls(self):
        messagebox.showinfo("Controls", "Z=A | X=B | Enter=Start | Shift=Select | Arrows=Move")

    def about(self):
        messagebox.showinfo(
            "About",
            "ChatGPT + Gemini GameBoy Emulator\n\n"
            "co-authored by ChatGPT\n"
            "vibe prompted by Gemini\n"
            "stitched by A.C"
        )

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
        for i in range(5):
            op = c.mmu.read(c.PC + i)
            out.append(f"{c.PC+i:04X}: {op:02X}")

        self.disasm.config(text="\n".join(out))

    # ================= DRAW =================
    def draw(self):
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
            for _ in range(200):
                self.cpu.step()
            self.ppu.render()

        self.draw()
        self.update_debug()
        self.root.after(16, self.loop)


# ===================== RUN =====================
if __name__ == "__main__":
    root = tk.Tk()
    Emulator(root)
    root.mainloop()
