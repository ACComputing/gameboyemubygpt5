import tkinter as tk
from tkinter import filedialog, messagebox

GB_WIDTH = 160
GB_HEIGHT = 144
SCALE = 3

BG = "#0b0f14"
PANEL = "#111a24"
ACCENT = "#00aaff"
TEXT = "#cfe9ff"


# ===================== CPU =====================
class CPU:
    def __init__(self):
        self.memory = [0] * 0x10000
        self.PC = 0x0100
        self.halted = False
        self.IME = False
        self.ppu = PPU(self)

    def load_rom(self, path):
        self.__init__()
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
            for x in range(GB_WIDTH):
                self.framebuffer[x + y * GB_WIDTH] = (x ^ y) & 1


# ===================== GUI =====================
class ChatGPTGameBoyEmulator:
    def __init__(self, root):
        self.root = root
        self.cpu = CPU()
        self.running = False

        # ===== TITLE (REBRANDED) =====
        self.root.title("ChatGPT's GameBoy Emulator by A.C and ChatGPT")
        self.root.geometry("950x700")
        self.root.configure(bg=BG)

        # ===== MENU =====
        menubar = tk.Menu(root)

        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Load ROM", command=self.load_rom)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        emumenu = tk.Menu(menubar, tearoff=0)
        emumenu.add_command(label="Start", command=self.start)
        emumenu.add_command(label="Pause", command=self.pause)
        emumenu.add_command(label="Reset", command=self.reset)
        menubar.add_cascade(label="Emulation", menu=emumenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About", command=self.about)
        menubar.add_cascade(label="Help", menu=helpmenu)

        root.config(menu=menubar)

        # ===== LAYOUT =====
        self.main = tk.Frame(root, bg=BG)
        self.main.pack(expand=True, fill="both")

        self.screen_frame = tk.Frame(self.main, bg=PANEL, padx=10, pady=10)
        self.screen_frame.pack(side="left", padx=20, pady=20)

        self.canvas = tk.Canvas(
            self.screen_frame,
            width=GB_WIDTH * SCALE,
            height=GB_HEIGHT * SCALE,
            bg="black",
            highlightthickness=2,
            highlightbackground=ACCENT
        )
        self.canvas.pack()

        self.side = tk.Frame(self.main, bg=PANEL, width=220)
        self.side.pack(side="right", fill="y", padx=20, pady=20)

        tk.Label(
            self.side,
            text="ChatGPT GAMEBOY",
            bg=PANEL,
            fg=ACCENT,
            font=("Courier", 16, "bold")
        ).pack(pady=10)

        self.status = tk.Label(self.side, text="Status: Idle", bg=PANEL, fg=TEXT)
        self.status.pack(pady=10)

        self.make_button("Start", self.start)
        self.make_button("Pause", self.pause)
        self.make_button("Reset", self.reset)

        self.footer = tk.Label(
            root,
            text="ChatGPT's GameBoy Emulator | by A.C and ChatGPT | [C]1999-2026 A.C Holding",
            bg="#081018",
            fg=ACCENT,
            anchor="w"
        )
        self.footer.pack(fill="x", side="bottom")

        self.loop()

    # ===== BUTTONS =====
    def make_button(self, text, cmd):
        tk.Button(
            self.side,
            text=text,
            command=cmd,
            bg="#0d2233",
            fg=ACCENT,
            activebackground="#123a55",
            activeforeground="white",
            relief="flat",
            width=18
        ).pack(pady=5)

    # ===== ACTIONS =====
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
            "ChatGPT's GameBoy Emulator\n"
            "by A.C and ChatGPT\n"
            "[C]1999-2026 A.C Holding"
        )

    # ===== RENDER =====
    def draw(self):
        self.canvas.delete("all")
        fb = self.cpu.ppu.framebuffer

        for y in range(GB_HEIGHT):
            for x in range(GB_WIDTH):
                if fb[x + y * GB_WIDTH]:
                    self.canvas.create_rectangle(
                        x*SCALE, y*SCALE,
                        (x+1)*SCALE, (y+1)*SCALE,
                        fill=ACCENT,
                        outline=""
                    )

    # ===== LOOP =====
    def loop(self):
        if self.running:
            for _ in range(250):
                self.cpu.step()

        self.draw()
        self.root.after(16, self.loop)


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatGPTGameBoyEmulator(root)
    root.mainloop()
