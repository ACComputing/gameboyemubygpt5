import tkinter as tk
from tkinter import filedialog, messagebox

GB_WIDTH = 160
GB_HEIGHT = 144
SCALE = 3

BG = "#1a1a1a"
ACCENT = "#4aa3ff"


# ===================== CPU =====================
class CPU:
    def __init__(self):
        self.reset()

    def reset(self):
        self.memory = [0] * 0x10000
        self.PC = 0x0100
        self.halted = False
        self.memory[0xFF00] = 0xFF

        self.keys = {}
        self.ppu = PPU(self)

    def load_rom(self, path):
        self.reset()
        with open(path, "rb") as f:
            rom = f.read()
        for i in range(len(rom)):
            self.memory[0x0100 + i] = rom[i]

    def update_joypad(self):
        def p(k):
            return 0 if self.keys.get(k, 0) else 1

        self.memory[0xFF00] = (
            (p("RIGHT") << 0) |
            (p("LEFT") << 1) |
            (p("UP") << 2) |
            (p("DOWN") << 3) |
            (p("A") << 4) |
            (p("B") << 5) |
            (p("SELECT") << 6) |
            (p("START") << 7)
        )

    def set_input(self, keys):
        self.keys = keys

    def step(self):
        self.update_joypad()

        if self.halted:
            self.ppu.step(4)
            return

        op = self.memory[self.PC]
        self.PC = (self.PC + 1) & 0xFFFF

        if op == 0x76:
            self.halted = True

        self.ppu.step(4)


# ===================== PPU =====================
class PPU:
    def __init__(self, cpu):
        self.cpu = cpu
        self.fb = [0] * (GB_WIDTH * GB_HEIGHT)
        self.clock = 0

    def step(self, cycles):
        self.clock += cycles
        if self.clock >= 456:
            self.clock = 0
            self.render()

    def render(self):
        for y in range(GB_HEIGHT):
            base = y * GB_WIDTH
            for x in range(GB_WIDTH):
                self.fb[base + x] = (x ^ y) & 1


# ===================== EMULATOR =====================
class Emulator:
    def __init__(self, root):
        self.root = root
        self.cpu = CPU()
        self.running = False

        self.keys = {
            "A": 0, "B": 0,
            "START": 0, "SELECT": 0,
            "UP": 0, "DOWN": 0,
            "LEFT": 0, "RIGHT": 0
        }

        self.root.title("A.C + ChatGPT GameBoy Emulator 0.1")
        self.root.geometry("980x720")
        self.root.configure(bg=BG)

        # MENU
        menu = tk.Menu(root)

        filemenu = tk.Menu(menu, tearoff=0)
        filemenu.add_command(label="Load ROM", command=self.load_rom)
        filemenu.add_command(label="Exit", command=root.quit)
        menu.add_cascade(label="File", menu=filemenu)

        emu = tk.Menu(menu, tearoff=0)
        emu.add_command(label="Run", command=self.start)
        emu.add_command(label="Pause", command=self.pause)
        emu.add_command(label="Reset", command=self.reset)
        menu.add_cascade(label="Emulation", menu=emu)

        helpmenu = tk.Menu(menu, tearoff=0)
        helpmenu.add_command(label="About", command=self.about)
        menu.add_cascade(label="Help", menu=helpmenu)

        root.config(menu=menu)

        # INPUT
        root.bind("<KeyPress>", self.key_down)
        root.bind("<KeyRelease>", self.key_up)
        root.focus_set()

        # SCREEN
        self.canvas = tk.Canvas(
            root,
            width=GB_WIDTH * SCALE,
            height=GB_HEIGHT * SCALE,
            bg="black"
        )
        self.canvas.pack()

        self.img = tk.PhotoImage(width=GB_WIDTH, height=GB_HEIGHT)
        self.canvas.create_image(0, 0, anchor="nw", image=self.img)

        self.loop()

    # ================= INPUT =================
    def key_down(self, event):
        k = event.keysym.lower()

        if k == "z": self.keys["A"] = 1
        elif k == "x": self.keys["B"] = 1
        elif k == "return": self.keys["START"] = 1
        elif "shift" in k: self.keys["SELECT"] = 1
        elif k == "up": self.keys["UP"] = 1
        elif k == "down": self.keys["DOWN"] = 1
        elif k == "left": self.keys["LEFT"] = 1
        elif k == "right": self.keys["RIGHT"] = 1

        self.cpu.set_input(self.keys)

    def key_up(self, event):
        k = event.keysym.lower()

        if k == "z": self.keys["A"] = 0
        elif k == "x": self.keys["B"] = 0
        elif k == "return": self.keys["START"] = 0
        elif "shift" in k: self.keys["SELECT"] = 0
        elif k == "up": self.keys["UP"] = 0
        elif k == "down": self.keys["DOWN"] = 0
        elif k == "left": self.keys["LEFT"] = 0
        elif k == "right": self.keys["RIGHT"] = 0

        self.cpu.set_input(self.keys)

    # ================= CONTROLS =================
    def load_rom(self):
        path = filedialog.askopenfilename()
        if path:
            self.cpu.load_rom(path)

    def start(self): self.running = True
    def pause(self): self.running = False
    def reset(self): self.cpu = CPU()

    def about(self):
        messagebox.showinfo(
            "About",
            "A.C + ChatGPT 5 GameBoy Emulator 0.1"
        )

    # ================= FIXED DRAW =================
    def draw(self):
        fb = self.cpu.ppu.fb

        rows = []
        for y in range(GB_HEIGHT):
            row = []
            base = y * GB_WIDTH

            for x in range(GB_WIDTH):
                v = fb[base + x]
                row.append("#ffffff" if v else "#000000")

            rows.append("{" + " ".join(row) + "}")

        self.img.put(" ".join(rows))

    # ================= LOOP =================
    def loop(self):
        if self.running:
            for _ in range(200):
                self.cpu.step()

        self.draw()
        self.root.after(16, self.loop)


# ===================== RUN =====================
if __name__ == "__main__":
    root = tk.Tk()
    Emulator(root)
    root.mainloop()
