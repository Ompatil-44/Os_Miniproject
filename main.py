import tkinter as tk
from tkinter import ttk, filedialog
import json

class RAIDSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("RAID Simulator (Ultimate Final)")
        self.root.geometry("1000x650")

        self.disk_count = tk.IntVar(value=3)
        self.raid_level = tk.StringVar(value="RAID 0")
        self.data_input = tk.StringVar()

        self.blocks = []
        self.failed_disk = None
        self.max_rows = 25

        self.create_ui()

    # ---------------- UI ----------------
    def create_ui(self):
        top = tk.Frame(self.root)
        top.pack(pady=10)

        tk.Scale(top, from_=2, to=5, orient="horizontal",
                 variable=self.disk_count).grid(row=0, column=0)

        ttk.Combobox(top, textvariable=self.raid_level,
                     values=["RAID 0", "RAID 1", "RAID 3", "RAID 5"],
                     state="readonly").grid(row=0, column=1)

        tk.Entry(top, textvariable=self.data_input, width=25).grid(row=1, column=0)

        tk.Button(top, text="Write", command=self.start_write).grid(row=1, column=1)
        tk.Button(top, text="Add Data", command=self.add_data).grid(row=1, column=2)
        tk.Button(top, text="Read", command=self.read_data).grid(row=1, column=3)

        tk.Button(top, text="Fail Disk", command=self.enable_failure).grid(row=2, column=0)
        tk.Button(top, text="Recover", command=self.recover_data).grid(row=2, column=1)

        tk.Button(top, text="Save", command=self.save_state).grid(row=2, column=2)
        tk.Button(top, text="Load", command=self.load_state).grid(row=2, column=3)

        tk.Button(top, text="Reset", command=self.reset_all).grid(row=2, column=4)

        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Configure>", lambda e: self.draw_disks())

    # ---------------- DRAW ----------------
    def draw_disks(self):
        self.canvas.delete("all")
        self.disks = []

        count = self.disk_count.get()
        width = self.canvas.winfo_width()

        spacing = min(150, width // (count + 1))
        start_x = (width - spacing * count) // 2

        rows = min(self.max_rows, len(self.blocks) + 5)
        height = 100 + rows * 30

        for i in range(count):
            x = start_x + i * spacing
            rect = self.canvas.create_rectangle(x, 100, x+100, height, fill="lightblue")
            self.canvas.create_text(x+50, 80, text=f"Disk {i}")
            self.disks.append(rect)

        for b in self.blocks:
            self.draw_block_visual(b)

    def draw_block_visual(self, block):
        x1, y1, x2, y2 = self.canvas.coords(self.disks[block["disk"]])
        y = y1 + 20 + block["stripe"] * 30

        color = block["color"]
        if block["disk"] == self.failed_disk:
            color = "gray"

        rect = self.canvas.create_rectangle(x1+10, y, x2-10, y+25, fill=color)
        text = self.canvas.create_text((x1+x2)//2, y+12, text=block["char"])

        block["rect"] = rect
        block["text"] = text

    # ---------------- WRITE ----------------
    def start_write(self):
        self.blocks = []
        self.failed_disk = None
        self.write_data(list(self.data_input.get()))

    def add_data(self):
        self.write_data(list(self.data_input.get()))

    def write_data(self, data):
        raid = self.raid_level.get()
        disks = self.disk_count.get()

        ptr = 0
        stripe = 0

        while ptr < len(data):
            xor_val = 0
            stripe_blocks = []

            if raid == "RAID 3":
                parity_disk = disks - 1

                for d in range(disks):
                    if d == parity_disk:
                        continue
                    if ptr < len(data):
                        char = data[ptr]
                        xor_val ^= ord(char)

                        stripe_blocks.append({
                            "disk": d,
                            "char": char,
                            "stripe": stripe,
                            "color": "yellow"
                        })
                        ptr += 1

                stripe_blocks.append({
                    "disk": parity_disk,
                    "char": chr(xor_val),
                    "stripe": stripe,
                    "color": "orange"
                })

            elif raid == "RAID 5":
                parity_disk = stripe % disks

                for d in range(disks):
                    if d == parity_disk:
                        continue
                    if ptr < len(data):
                        char = data[ptr]
                        xor_val ^= ord(char)

                        stripe_blocks.append({
                            "disk": d,
                            "char": char,
                            "stripe": stripe,
                            "color": "yellow"
                        })
                        ptr += 1

                stripe_blocks.append({
                    "disk": parity_disk,
                    "char": chr(xor_val),
                    "stripe": stripe,
                    "color": "orange"
                })

            elif raid == "RAID 1":
                char = data[ptr]
                for d in range(disks):
                    stripe_blocks.append({
                        "disk": d,
                        "char": char,
                        "stripe": stripe,
                        "color": "yellow"
                    })
                ptr += 1

            elif raid == "RAID 0":
                for d in range(disks):
                    if ptr < len(data):
                        stripe_blocks.append({
                            "disk": d,
                            "char": data[ptr],
                            "stripe": stripe,
                            "color": "yellow"
                        })
                        ptr += 1

            self.blocks.extend(stripe_blocks)
            stripe += 1

        self.draw_disks()

    # ---------------- FAILURE ----------------
    def enable_failure(self):
        self.canvas.bind("<Button-1>", self.fail_disk)

    def fail_disk(self, event):
        for i, rect in enumerate(self.disks):
            x1, y1, x2, y2 = self.canvas.coords(rect)
            if x1 < event.x < x2:
                self.failed_disk = i
                self.draw_disks()

    # ---------------- READ ----------------
    def read_data(self):
        raid = self.raid_level.get()

        if raid == "RAID 0" and self.failed_disk is not None:
            self.show_message("DATA LOST")
            return

        result = ""
        stripes = {}

        for b in self.blocks:
            stripes.setdefault(b["stripe"], []).append(b)

        for stripe in sorted(stripes.keys()):
            for b in sorted(stripes[stripe], key=lambda x: x["disk"]):
                if b["disk"] != self.failed_disk and b["color"] == "yellow":
                    result += b["char"]

        self.show_message(f"DATA: {result}")

    # ---------------- RECOVERY ----------------
    def recover_data(self):
        raid = self.raid_level.get()

        if self.failed_disk is None:
            self.show_message("No disk failure")
            return

        stripes = {}
        for b in self.blocks:
            stripes.setdefault(b["stripe"], []).append(b)

        full_data = ""

        if raid == "RAID 1":
            for stripe in stripes.values():
                for b in stripe:
                    if b["disk"] != self.failed_disk:
                        full_data += b["char"]
                        break

        elif raid in ["RAID 3", "RAID 5"]:
            for stripe in sorted(stripes.keys()):
                stripe_blocks = stripes[stripe]

                xor_val = 0
                data_blocks = []
                missing_block = None

                for b in stripe_blocks:
                    if b["disk"] == self.failed_disk:
                        missing_block = b
                    else:
                        xor_val ^= ord(b["char"])

                    if b["color"] == "yellow":
                        data_blocks.append(b)

                if missing_block and missing_block["color"] == "yellow":
                    recovered_char = chr(xor_val)

                    self.canvas.itemconfig(missing_block["rect"], fill="green")
                    self.canvas.itemconfig(missing_block["text"], text=recovered_char)

                    data_blocks.append({
                        "disk": missing_block["disk"],
                        "char": recovered_char
                    })

                data_blocks.sort(key=lambda x: x["disk"])

                for d in data_blocks:
                    full_data += d["char"]

        else:
            self.show_message("Recovery not possible (RAID 0)")
            return

        self.show_message(f"Recovered Full Data: {full_data}")

    # ---------------- SAVE ----------------
    def save_state(self):
        data = {
            "raid": self.raid_level.get(),
            "disks": self.disk_count.get(),
            "blocks": self.blocks,
            "failed": self.failed_disk
        }

        file = filedialog.asksaveasfilename(defaultextension=".json")
        if file:
            with open(file, "w") as f:
                json.dump(data, f)

    # ---------------- LOAD ----------------
    def load_state(self):
        file = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if file:
            with open(file, "r") as f:
                data = json.load(f)

            self.raid_level.set(data["raid"])
            self.disk_count.set(data["disks"])
            self.blocks = data["blocks"]
            self.failed_disk = data["failed"]

            self.draw_disks()

    # ---------------- RESET ----------------
    def reset_all(self):
        self.blocks = []
        self.failed_disk = None
        self.draw_disks()

    # ---------------- MESSAGE ----------------
    def show_message(self, msg):
        self.canvas.delete("msg")
        self.canvas.create_text(500, 50, text=msg, font=("Arial", 16), tags="msg")

# ---------------- RUN ----------------
root = tk.Tk()
app = RAIDSimulator(root)
root.mainloop()
