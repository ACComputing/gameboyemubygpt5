import tkinter as tk
from tkinter import filedialog, messagebox

GB_WIDTH = 160
GB_HEIGHT = 144
SCALE = 3

BG = "#1a1a1a"
PANEL = "#2a2a2a"
ACCENT = "#4aa3ff"
TEXT = "#e6e6e6"


# ===================== CPU =====================
class CPU:
    def __init__(self):
        self.reset()

    def reset(self):
        self.memory = [0] * 0x10000
        self.PC = 0x0100
        self.halted = False
        self.IME = False
        self.ppu = PPU(self)

    def load_rom(self, path):
        self.reset()
        with open(path, "rb") as f:
            rom = f.read()
        for i in range(len(rom)):
            self.memory[0x0100 + i] = rom[i]

    def step(self):
        if self.halted:
            self.ppu.step(4)
            return

        op = self.memory[self.PC]
        self.PC = (self.PC + 1) & 0xFFFF

        if op == 0x76:
            self.halted = True
        elif op == 0xFB:
            self.IME = True
        elif op == 0xF3:
            self.IME = False

        self.ppu.step(4)


# ===================== PPU =====================
class PPU:
    def __init__(self, cpu):
        self.cpu = cpu
        self.framebuffer = [0] * (GB_WIDTH * GB_HEIGHT)
        self.clock = 0
        self.scanline = 0

    def step(self, cycles):
        self.clock += cycles

        while self.clock >= 456:
            self.clock -= 456
            self.scanline += 1

            if self.scanline >= GB_HEIGHT:
                self.scanline = 0
                self.render()

    def render(self):
        for y in range(GB_HEIGHT):
            base = y * GB_WIDTH
            for x in range(GB_WIDTH):
                self.framebuffer[base + x] = (x ^ y) & 1


# ===================== GUI =====================
class ChatGPTGameBoyEmulator:
    def __init__(self, root):
        self.root = root
        self.cpu = CPU()
        self.running = False

        # ✔ UPDATED TITLE HERE
        self.root.title("A.C + ChatGPT's GameBoy Emulator 0.1")

        self.root.geometry("980x720")
        self.root.configure(bg=BG)

        # MENU
        menu = tk.Menu(root)

        filemenu = tk.Menu(menu, tearoff=0)
        filemenu.add_command(label="Load ROM", command=self.load_rom)
        filemenu.add_separator()
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

        # LAYOUT
        self.main = tk.Frame(root, bg=BG)
        self.main.pack(expand=True, fill="both")

        self.screen = tk.Frame(self.main, bg=PANEL)
        self.screen.pack(side="left", padx=25, pady=25)

        self.canvas = tk.Canvas(
            self.screen,
            width=GB_WIDTH * SCALE,
            height=GB_HEIGHT * SCALE,
            bg="black",
            highlightthickness=2,
            highlightbackground=ACCENT
        )
        self.canvas.pack()

        self.side = tk.Frame(self.main, bg=PANEL, width=220)
        self.side.pack(side="right", fill="y", padx=25, pady=25)

        tk.Label(
            self.side,
            text="ChatGPT GAMEBOY",
            bg=PANEL,
            fg=ACCENT,
            font=("Courier", 14, "bold")
        ).pack(pady=10)

        self.status = tk.Label(self.side, text="Idle", bg=PANEL, fg=TEXT)
        self.status.pack(pady=10)

        self.make_button("Run", self.start)
        self.make_button("Pause", self.pause)
        self.make_button("Reset", self.reset)

        self.footer = tk.Label(
            root,
            text="A.C + ChatGPT GameBoy Emulator 0.1",
            bg="#111",
            fg=ACCENT,
            anchor="w"
        )
        self.footer.pack(fill="x", side="bottom")

        self.loop()

    def make_button(self, text, cmd):
        tk.Button(
            self.side,
            text=text,
            command=cmd,
            bg="#333",
            fg=TEXT,
            relief="flat",
            width=18
        ).pack(pady=5)

    def load_rom(self):
        path = filedialog.askopenfilename()
        if path:
            self.cpu.load_rom(path)
            self.status.config(text="ROM Loaded")

    def start(self):
        self.running = True
        self.status.config(text="Running")

    def pause(self):
        self.running = False
        self.status.config(text="Paused")

    def reset(self):
        self.cpu = CPU()
        self.status.config(text="Reset")

    def about(self):
        messagebox.showinfo(
            "About",
            "A.C + ChatGPT's GameBoy Emulator 0.1"
        )

    def draw(self):
        self.canvas.delete("all")
        fb = self.cpu.ppu.framebuffer

        for y in range(GB_HEIGHT):
            base = y * GB_WIDTH
            for x in range(GB_WIDTH):
                if fb[base + x]:
                    self.canvas.create_rectangle(
                        x*SCALE, y*SCALE,
                        (x+1)*SCALE, (y+1)*SCALE,
                        fill=ACCENT,
                        outline=""
                    )

    def loop(self):
        if self.running:
            for _ in range(250):
                self.cpu.step()

        self.draw()
        self.root.after(16, self.loop)


if __name__ == "__main__":
    root = tk.Tk()
    ChatGPTGameBoyEmulator(root)
    root.mainloop()
