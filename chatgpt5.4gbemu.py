#!/usr/bin/env python3
"""Tk debugger shell around the stronger DMG core in `acsgameboyemu4k0.2v0.py`."""

import importlib.util
import os
import tkinter as tk
from tkinter import filedialog, messagebox

GB_WIDTH = 160
GB_HEIGHT = 144
SCALE = 3

BG = "#1a1a1a"
PANEL = "#101820"
ACCENT = "#4aa3ff"
TEXT = "#cfe9ff"

REFERENCE_CORE = os.path.join(os.path.dirname(__file__), "acsgameboyemu4k0.2v0.py")


def _load_reference_core():
    spec = importlib.util.spec_from_file_location("acsgameboyemu4k_ref", REFERENCE_CORE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load reference Game Boy core from {REFERENCE_CORE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_ref = _load_reference_core()
CoreEmulator = _ref.Emulator


class EmulatorApp:
    def __init__(self, root):
        self.root = root
        self.core = CoreEmulator()
        self.running = False
        self.after_id = None
        self.current_rom_path = None
        self.current_rom_title = "No ROM loaded"

        self.status_var = tk.StringVar(value="Load a ROM to begin.")

        self.root.title("ChatGPT + Gemini GameBoy Emulator")
        self.root.geometry("1140x720")
        self.root.configure(bg=BG)

        self._build_menu()
        self._build_layout()

        self.root.bind("<KeyPress>", self._key_down)
        self.root.bind("<KeyRelease>", self._key_up)

    def _build_menu(self):
        menu = tk.Menu(self.root)

        filemenu = tk.Menu(menu, tearoff=0)
        filemenu.add_command(label="Play ROM", command=self.load_rom)
        filemenu.add_command(label="Reset", command=self.reset)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.root.quit)
        menu.add_cascade(label="File", menu=filemenu)

        emu = tk.Menu(menu, tearoff=0)
        emu.add_command(label="Run", command=self.start)
        emu.add_command(label="Pause", command=self.pause)
        menu.add_cascade(label="Emulation", menu=emu)

        helpmenu = tk.Menu(menu, tearoff=0)
        helpmenu.add_command(label="Controls", command=self.controls)
        helpmenu.add_command(label="About", command=self.about)
        menu.add_cascade(label="Help", menu=helpmenu)

        self.root.config(menu=menu)

    def _build_layout(self):
        self.main = tk.Frame(self.root, bg=BG)
        self.main.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            self.main,
            width=GB_WIDTH * SCALE,
            height=GB_HEIGHT * SCALE,
            bg="black",
            highlightthickness=0,
        )
        self.canvas.pack(side="left", padx=12, pady=12)

        self._ppm_hdr = f"P6 {GB_WIDTH} {GB_HEIGHT} 255\n".encode()
        self.photo = tk.PhotoImage(width=GB_WIDTH * SCALE, height=GB_HEIGHT * SCALE)
        self.canvas_img = self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

        self.debug = tk.Frame(self.main, bg=PANEL, width=320)
        self.debug.pack(side="right", fill="y", padx=8, pady=8)

        tk.Label(
            self.debug,
            text="DEBUGGER",
            fg=ACCENT,
            bg=PANEL,
            font=("Courier", 14, "bold"),
        ).pack(pady=10)

        self.rom_info = tk.Label(self.debug, fg=TEXT, bg=PANEL, font=("Courier", 10), justify="left", wraplength=300)
        self.rom_info.pack(anchor="w", padx=10, pady=(0, 8))

        self.reg = tk.Label(self.debug, fg=TEXT, bg=PANEL, font=("Courier", 11), justify="left")
        self.reg.pack(anchor="w", padx=10)

        self.pc = tk.Label(self.debug, fg=TEXT, bg=PANEL, font=("Courier", 11), justify="left")
        self.pc.pack(anchor="w", padx=10, pady=(6, 0))

        self.sys = tk.Label(self.debug, fg=TEXT, bg=PANEL, font=("Courier", 10), justify="left")
        self.sys.pack(anchor="w", padx=10, pady=(8, 0))

        self.disasm = tk.Label(
            self.debug,
            fg=ACCENT,
            bg=PANEL,
            font=("Courier", 10),
            justify="left",
        )
        self.disasm.pack(anchor="w", padx=10, pady=10)

        self.status = tk.Label(
            self.debug,
            textvariable=self.status_var,
            fg=TEXT,
            bg=PANEL,
            wraplength=300,
            justify="left",
            font=("Courier", 10),
        )
        self.status.pack(anchor="w", padx=10, pady=10)

    def _get_rom_title(self):
        mbc = self.core.mmu.mbc
        if not mbc or not hasattr(mbc, "rom"):
            return "No ROM loaded"
        rom = mbc.rom
        title_raw = rom[0x134:0x144]
        title = bytes(b for b in title_raw if 32 <= b <= 126).decode("ascii", errors="ignore").strip("\x00 ")
        return title or (os.path.basename(self.current_rom_path) if self.current_rom_path else "Unknown")

    def _draw_frame(self, frame):
        self._raw_photo = tk.PhotoImage(data=self._ppm_hdr + frame, format="PPM")
        self.photo = self._raw_photo.zoom(SCALE, SCALE)
        self.canvas.itemconfig(self.canvas_img, image=self.photo)

    def load_rom(self):
        path = filedialog.askopenfilename(
            title="Select Game Boy ROM",
            filetypes=[("GB ROMs", "*.gb *.gbc"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self.pause()
            self.core.load_rom(path)
            self.current_rom_path = path
            self.current_rom_title = self._get_rom_title()
            self.status_var.set(f"Loaded: {self.current_rom_title}\nBoot core ready. Auto-running ROM.")
            self.start()
        except Exception as exc:
            messagebox.showerror("ROM Load Error", str(exc))

    def start(self):
        if not self.core.rom_loaded:
            self.status_var.set("No ROM loaded.")
            return
        if self.running:
            return
        self.running = True
        self.status_var.set(f"Running: {self.current_rom_title}")
        self.root.focus_set()
        self._loop()

    def pause(self):
        self.running = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        if self.core.rom_loaded:
            self.status_var.set(f"Paused: {self.current_rom_title}")
        else:
            self.status_var.set("Paused.")

    def reset(self):
        if not self.core.rom_loaded:
            self.core.reset()
            self.status_var.set("Reset emulator.")
            self.update_debug()
            return
        self.pause()
        self.core.reset()
        self.status_var.set(f"Reset: {self.current_rom_title}")
        self.update_debug()

    def controls(self):
        messagebox.showinfo(
            "Controls",
            "Z=A | X=B | Enter=Select | Space=Start | Arrows=Move",
        )

    def about(self):
        messagebox.showinfo(
            "About",
            "ChatGPT + Gemini GameBoy Emulator\n\n"
            "By ChatGPT, Cursor agents, Gemini\n"
            "Stitched together by A.C",
        )

    def update_debug(self):
        c = self.core.cpu
        m = self.core.mmu
        p = self.core.ppu

        self.rom_info.config(
            text=(
                f"ROM: {self.current_rom_title}\n"
                f"MBC: {m.mbc.__class__.__name__ if m.mbc else 'None'}\n"
                f"Path: {os.path.basename(self.current_rom_path) if self.current_rom_path else '-'}"
            )
        )

        self.reg.config(
            text=(
                f"A:{c.a:02X} F:{c.f:02X}\n"
                f"B:{c.b:02X} C:{c.c:02X}\n"
                f"D:{c.d:02X} E:{c.e:02X}\n"
                f"H:{c.h:02X} L:{c.l:02X}"
            )
        )

        state = "HALTED" if c.halted else ("RUNNING" if self.running else "IDLE")
        self.pc.config(
            text=(
                f"PC:{c.pc:04X} SP:{c.sp:04X} {state}\n"
                f"IME:{int(c.ime)} IF:{m.io[0x0F]:02X} IE:{m.ie:02X}"
            )
        )

        self.sys.config(
            text=(
                f"LCDC:{m.io[0x40]:02X} STAT:{m.io[0x41]:02X}\n"
                f"LY:{m.io[0x44]:02X} LYC:{m.io[0x45]:02X}\n"
                f"DIV:{m.io[0x04]:02X} TIMA:{m.io[0x05]:02X}\n"
                f"FrameReady:{int(p.frame_ready)}"
            )
        )

        out = []
        for i in range(8):
            addr = (c.pc + i) & 0xFFFF
            op = m.read(addr)
            out.append(f"{addr:04X}: {op:02X}")
        self.disasm.config(text="\n".join(out))

    def _loop(self):
        if not self.running:
            return
        try:
            frame = self.core.run_frame()
            self._draw_frame(frame)
            if self.core.cpu.halted:
                self.status_var.set(f"CPU halted at {self.core.cpu.pc:04X}: {self.current_rom_title}")
        except Exception as exc:
            self.pause()
            self.status_var.set(f"Emulation error: {exc}")
        self.update_debug()
        self.after_id = self.root.after(16, self._loop)

    def _key_down(self, event):
        if self.core.rom_loaded:
            self.core.joypad.press(event.keysym)

    def _key_up(self, event):
        if self.core.rom_loaded:
            self.core.joypad.release(event.keysym)


def main():
    root = tk.Tk()
    EmulatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
