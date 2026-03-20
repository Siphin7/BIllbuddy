"""
BillBuddy AI 💸
A smart group expense splitting app built with CustomTkinter.
Install: pip install customtkinter pyperclip
Run:     python billbuddy_ai.py
"""

import customtkinter as ctk
from tkinter import messagebox

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C = {
    "bg":     "#0f1117",
    "card":   "#1a1d27",
    "card2":  "#21253a",
    "accent": "#6c63ff",
    "green":  "#00d9a3",
    "red":    "#ff5e7a",
    "gold":   "#ffd700",
    "text":   "#e8eaf6",
    "sub":    "#8892b0",
    "border": "#2d3154",
}

F = {
    "title":  ("Segoe UI", 24, "bold"),
    "sub":    ("Segoe UI", 11),
    "label":  ("Segoe UI", 12, "bold"),
    "body":   ("Segoe UI", 11),
    "big":    ("Segoe UI", 15, "bold"),
    "result": ("Segoe UI", 13, "bold"),
}


# ── LOGIC ────────────────────────────────────

def calc_balances(people, expenses):
    total = sum(e["amount"] for e in expenses)
    if not people or total == 0:
        return {p: 0.0 for p in people}
    share = total / len(people)
    paid = {p: 0.0 for p in people}
    for e in expenses:
        paid[e["payer"]] += e["amount"]
    return {p: round(paid[p] - share, 2) for p in people}


def smart_settle(balances):
    cred = sorted([(p, b) for p, b in balances.items() if b > 0.001],  key=lambda x: -x[1])
    debt = sorted([(p,-b) for p, b in balances.items() if b < -0.001], key=lambda x: -x[1])
    cred = [list(x) for x in cred]
    debt = [list(x) for x in debt]
    txns, i, j = [], 0, 0
    while i < len(cred) and j < len(debt):
        amt = min(cred[i][1], debt[j][1])
        txns.append({"from": debt[j][0], "to": cred[i][0], "amount": round(amt, 2)})
        cred[i][1] -= amt
        debt[j][1] -= amt
        if cred[i][1] < 0.001: i += 1
        if debt[j][1] < 0.001: j += 1
    return txns


def wa_text(txns, share):
    lines = ["💸 *BillBuddy Settlement*", ""]
    for t in txns:
        lines.append(f"  {t['from']} pays Rs.{t['amount']:.2f} to {t['to']}")
    lines += ["", f"Everyone paid equally (Rs.{share:.2f} each).", "Settled with BillBuddy AI"]
    return "\n".join(lines)


# ── APP ──────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BillBuddy AI")
        self.geometry("1020x680")
        self.minsize(900, 600)
        self.configure(fg_color=C["bg"])
        self.people   = []
        self.expenses = []
        self._wa      = ""
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=68)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="BillBuddy AI 💸", font=F["title"],
                     text_color=C["accent"]).pack(side="left", padx=22, pady=14)
        ctk.CTkLabel(hdr, text="No more awkward money talks ❤️", font=F["sub"],
                     text_color=C["sub"]).pack(side="left")

        # Body
        body = ctk.CTkFrame(self, fg_color=C["bg"])
        body.pack(fill="both", expand=True, padx=14, pady=10)

        # LEFT column — fixed 400px, uses pack so nothing overflows
        left = ctk.CTkFrame(body, fg_color=C["bg"], width=410)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        # RIGHT column — fills rest
        right = ctk.CTkFrame(body, fg_color=C["bg"])
        right.pack(side="left", fill="both", expand=True)

        self._left(left)
        self._right(right)

    # ── LEFT PANEL ───────────────────────────

    def _left(self, p):
        # --- People card
        pc = self._card(p, "👥  Add People")
        pc.pack(fill="x", pady=(0, 8))

        row = ctk.CTkFrame(pc, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(0, 6))
        self.name_ent = ctk.CTkEntry(row, placeholder_text="Enter name…",
                                     font=F["body"], fg_color=C["card2"],
                                     border_color=C["border"], text_color=C["text"], height=36)
        self.name_ent.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.name_ent.bind("<Return>", lambda e: self._add_person())
        ctk.CTkButton(row, text="Add", width=64, height=36,
                      fg_color=C["accent"], hover_color="#5550d4",
                      font=F["label"], command=self._add_person).pack(side="left")

        self.ppl_box = ctk.CTkScrollableFrame(pc, fg_color=C["card2"],
                                               corner_radius=8, height=85)
        self.ppl_box.pack(fill="x", padx=12, pady=(0, 10))

        # --- Expense card
        ec = self._card(p, "💳  Add Expenses")
        ec.pack(fill="x", pady=(0, 8))

        g = ctk.CTkFrame(ec, fg_color="transparent")
        g.pack(fill="x", padx=12, pady=(0, 6))
        g.columnconfigure(0, weight=2)
        g.columnconfigure(1, weight=1)

        ctk.CTkLabel(g, text="Paid by",     font=F["body"], text_color=C["sub"]).grid(row=0, column=0, sticky="w", pady=(0,2))
        ctk.CTkLabel(g, text="Amount (₹)",  font=F["body"], text_color=C["sub"]).grid(row=0, column=1, sticky="w", pady=(0,2))

        self.payer_var  = ctk.StringVar(value="— select —")
        self.payer_menu = ctk.CTkOptionMenu(g, variable=self.payer_var,
                                             values=["— select —"],
                                             fg_color=C["card2"],
                                             button_color=C["accent"],
                                             button_hover_color="#5550d4",
                                             dropdown_fg_color=C["card2"],
                                             font=F["body"], text_color=C["text"])
        self.payer_menu.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        self.amt_ent = ctk.CTkEntry(g, placeholder_text="0.00",
                                     font=F["body"], fg_color=C["card2"],
                                     border_color=C["border"], text_color=C["text"], height=36)
        self.amt_ent.grid(row=1, column=1, sticky="ew")
        self.amt_ent.bind("<Return>", lambda e: self._add_expense())

        ctk.CTkButton(ec, text="➕  Add Expense", height=36,
                      fg_color=C["green"], hover_color="#00b389",
                      text_color="#000", font=F["label"],
                      command=self._add_expense).pack(fill="x", padx=12, pady=(0, 6))

        self.exp_box = ctk.CTkScrollableFrame(ec, fg_color=C["card2"],
                                               corner_radius=8, height=120)
        self.exp_box.pack(fill="x", padx=12, pady=(0, 10))

        # --- CALCULATE BUTTON — pinned below cards
        ctk.CTkButton(p, text="⚡  Calculate Settlement",
                      height=50, font=("Segoe UI", 14, "bold"),
                      fg_color=C["accent"], hover_color="#5550d4",
                      command=self._calculate).pack(fill="x", pady=(2, 0))

    # ── RIGHT PANEL ──────────────────────────

    def _right(self, p):
        rc = self._card(p, "📊  Results")
        rc.pack(fill="both", expand=True)

        self.res_box = ctk.CTkScrollableFrame(rc, fg_color="transparent")
        self.res_box.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        self._placeholder()

        self.copy_btn = ctk.CTkButton(rc, text="📋  Copy for WhatsApp", height=38,
                                       fg_color=C["card2"], hover_color=C["border"],
                                       border_color=C["green"], border_width=1,
                                       text_color=C["green"], font=F["label"],
                                       state="disabled", command=self._copy)
        self.copy_btn.pack(fill="x", padx=12, pady=(0, 12))

    # ── ACTIONS ──────────────────────────────

    def _add_person(self):
        n = self.name_ent.get().strip()
        if not n or n in self.people:
            return
        self.people.append(n)
        self.name_ent.delete(0, "end")
        self._ref_ppl()
        self._ref_payer()

    def _add_expense(self):
        payer = self.payer_var.get()
        if payer not in self.people:
            messagebox.showwarning("No payer", "Add people first and select a payer.")
            return
        try:
            amt = float(self.amt_ent.get().strip())
            assert amt > 0
        except Exception:
            messagebox.showerror("Bad amount", "Enter a valid positive number.")
            return
        self.expenses.append({"payer": payer, "amount": amt})
        self.amt_ent.delete(0, "end")
        self._ref_exp()

    def _calculate(self):
        if len(self.people) < 2:
            messagebox.showwarning("Not enough people", "Add at least 2 people.")
            return
        if not self.expenses:
            messagebox.showwarning("No expenses", "Add at least one expense.")
            return
        total    = sum(e["amount"] for e in self.expenses)
        share    = total / len(self.people)
        balances = calc_balances(self.people, self.expenses)
        txns     = smart_settle(balances)
        naive    = max(0, len(self.people) - 1)
        self._wa = wa_text(txns, share)
        self._render(total, share, balances, txns, len(txns), naive)
        self.copy_btn.configure(state="normal")

    def _copy(self):
        try:
            if HAS_PYPERCLIP:
                pyperclip.copy(self._wa)
            else:
                self.clipboard_clear()
                self.clipboard_append(self._wa)
            self.copy_btn.configure(text="✅  Copied!")
            self.after(2200, lambda: self.copy_btn.configure(text="📋  Copy for WhatsApp"))
        except Exception as ex:
            messagebox.showerror("Copy failed", str(ex))

    # ── REFRESH ──────────────────────────────

    def _ref_ppl(self):
        for w in self.ppl_box.winfo_children(): w.destroy()
        for person in self.people:
            r = ctk.CTkFrame(self.ppl_box, fg_color="transparent")
            r.pack(fill="x", pady=1)
            ctk.CTkLabel(r, text=f"🧑  {person}", font=F["body"],
                         text_color=C["text"]).pack(side="left", padx=4)
            ctk.CTkButton(r, text="✕", width=26, height=22,
                          fg_color="transparent", hover_color=C["red"],
                          text_color=C["sub"], font=("Segoe UI", 9),
                          command=lambda n=person: self._del_person(n)).pack(side="right")

    def _ref_payer(self):
        opts = self.people or ["— select —"]
        self.payer_menu.configure(values=opts)
        self.payer_var.set(opts[-1])

    def _ref_exp(self):
        for w in self.exp_box.winfo_children(): w.destroy()
        for i, e in enumerate(self.expenses):
            r = ctk.CTkFrame(self.exp_box, fg_color=C["border"], corner_radius=6, height=30)
            r.pack(fill="x", pady=2)
            r.pack_propagate(False)
            ctk.CTkLabel(r, text=f"💳  {e['payer']}  →  ₹{e['amount']:.2f}",
                         font=F["body"], text_color=C["text"]).pack(side="left", padx=8)
            ctk.CTkButton(r, text="✕", width=26, height=22,
                          fg_color="transparent", hover_color=C["red"],
                          text_color=C["sub"], font=("Segoe UI", 9),
                          command=lambda idx=i: self._del_exp(idx)).pack(side="right", padx=4)

    def _del_person(self, name):
        self.people   = [p for p in self.people if p != name]
        self.expenses = [e for e in self.expenses if e["payer"] != name]
        self._ref_ppl(); self._ref_payer(); self._ref_exp()

    def _del_exp(self, idx):
        self.expenses.pop(idx)
        self._ref_exp()

    # ── RENDER RESULTS ───────────────────────

    def _placeholder(self):
        for w in self.res_box.winfo_children(): w.destroy()
        ctk.CTkLabel(self.res_box,
                     text="⚡ Hit  'Calculate Settlement'\nto see the results here",
                     font=("Segoe UI", 13), text_color=C["sub"],
                     justify="center").pack(pady=80)

    def _render(self, total, share, balances, txns, optimized, naive):
        for w in self.res_box.winfo_children(): w.destroy()
        rb = self.res_box

        # Stats
        sr = ctk.CTkFrame(rb, fg_color="transparent")
        sr.pack(fill="x", pady=(4, 10))
        for col, (lbl, val, clr) in enumerate([
            ("Total Spent",  f"₹{total:.2f}",  C["gold"]),
            ("Each Owes",    f"₹{share:.2f}",  C["green"]),
            ("Transactions", str(optimized),    C["accent"]),
        ]):
            sr.columnconfigure(col, weight=1)
            box = ctk.CTkFrame(sr, fg_color=C["card2"], corner_radius=10)
            box.grid(row=0, column=col, padx=4, sticky="ew")
            ctk.CTkLabel(box, text=val, font=F["big"],  text_color=clr).pack(pady=(10, 0))
            ctk.CTkLabel(box, text=lbl, font=F["sub"], text_color=C["sub"]).pack(pady=(0, 10))

        # Balances
        ctk.CTkLabel(rb, text="👤 Individual Balances", font=F["label"],
                     text_color=C["sub"]).pack(anchor="w", padx=6, pady=(6, 3))
        for person, bal in balances.items():
            icon, clr, tag = ("⬆", C["green"], f"+₹{bal:.2f}")    if bal > 0 else \
                             ("⬇", C["red"],   f"-₹{abs(bal):.2f}") if bal < 0 else \
                             ("✓", C["sub"],   "settled")
            row = ctk.CTkFrame(rb, fg_color=C["card2"], corner_radius=8, height=36)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=f"{icon}  {person}", font=F["body"],
                         text_color=C["text"]).pack(side="left", padx=12)
            ctk.CTkLabel(row, text=tag, font=F["label"], text_color=clr).pack(side="right", padx=12)

        # Settlement
        ctk.CTkLabel(rb, text="💸 Settlement Plan", font=F["label"],
                     text_color=C["sub"]).pack(anchor="w", padx=6, pady=(10, 3))
        if not txns:
            ctk.CTkLabel(rb, text="✅ Everyone is already settled!",
                         font=F["body"], text_color=C["green"]).pack(anchor="w", padx=8, pady=4)
        else:
            for t in txns:
                f = ctk.CTkFrame(rb, fg_color=C["card2"], corner_radius=10)
                f.pack(fill="x", pady=3)
                inn = ctk.CTkFrame(f, fg_color="transparent")
                inn.pack(padx=14, pady=10)
                ctk.CTkLabel(inn, text=t["from"], font=F["result"], text_color=C["red"]).pack(side="left")
                ctk.CTkLabel(inn, text=f"  →  ₹{t['amount']:.2f}  →  ",
                             font=F["body"], text_color=C["sub"]).pack(side="left")
                ctk.CTkLabel(inn, text=t["to"], font=F["result"], text_color=C["green"]).pack(side="left")

        # AI tip
        ai = ctk.CTkFrame(rb, fg_color=C["card2"], corner_radius=10)
        ai.pack(fill="x", pady=(10, 4))
        ctk.CTkLabel(ai, text="💡 Smart Suggestion", font=F["label"],
                     text_color=C["gold"]).pack(anchor="w", padx=14, pady=(10, 2))
        saved = naive - optimized
        msg = f"Settled in {optimized} transaction{'s' if optimized!=1 else ''} instead of {naive}."
        msg += f" Saved {saved} step{'s' if saved!=1 else ''}! 🎉" if saved > 0 else " Already optimal!"
        ctk.CTkLabel(ai, text=msg, font=F["body"], text_color=C["text"],
                     wraplength=320, justify="left").pack(anchor="w", padx=14, pady=(0, 10))

    # ── UTILS ────────────────────────────────

    def _card(self, parent, title):
        f = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=12,
                         border_width=1, border_color=C["border"])
        ctk.CTkLabel(f, text=title, font=F["label"],
                     text_color=C["accent"]).pack(anchor="w", padx=14, pady=(12, 4))
        return f


if __name__ == "__main__":
    App().mainloop()
