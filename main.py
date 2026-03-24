"""
BillBuddy AI 💸
────────────────────────────────────────────────
Install : pip install customtkinter
Run     : python billbuddy_ai.py
────────────────────────────────────────────────
Tabs:
  Tab 1  →  Members & Expenses  (merged)
  Tab 2  →  Results
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

try:
    import pyperclip
    _CLIP = True
except ImportError:
    _CLIP = False

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG     = "#0f1117"
CARD   = "#1a1d27"
CARD2  = "#21253a"
ACCENT = "#6c63ff"
GREEN  = "#00d9a3"
RED    = "#ff5e7a"
GOLD   = "#ffd700"
TEXT   = "#e8eaf6"
SUB    = "#8892b0"
BORDER = "#2d3154"
PURPLE = "#9b59b6"

FT = ("Segoe UI", 22, "bold")
FS = ("Segoe UI", 11)
FL = ("Segoe UI", 12, "bold")
FB = ("Segoe UI", 11)
FG = ("Segoe UI", 15, "bold")
FR = ("Segoe UI", 13, "bold")


# ════════════════════════════════════════════════
#  LOGIC
# ════════════════════════════════════════════════

def calc_balances(people, expenses):
    total = sum(e["amount"] for e in expenses)
    if not people or total == 0:
        return {p: 0.0 for p in people}
    share = total / len(people)
    paid  = {p: 0.0 for p in people}
    for e in expenses:
        paid[e["payer"]] = paid.get(e["payer"], 0) + e["amount"]
    return {p: round(paid[p] - share, 2) for p in people}


def smart_settle(balances):
    cred = sorted([[p,  b] for p, b in balances.items() if  b >  0.001], key=lambda x: -x[1])
    debt = sorted([[p, -b] for p, b in balances.items() if  b < -0.001], key=lambda x: -x[1])
    txns, i, j = [], 0, 0
    while i < len(cred) and j < len(debt):
        amt         = min(cred[i][1], debt[j][1])
        txns.append({"from": debt[j][0], "to": cred[i][0], "amount": round(amt, 2)})
        cred[i][1] -= amt
        debt[j][1] -= amt
        if cred[i][1] < 0.001: i += 1
        if debt[j][1] < 0.001: j += 1
    return txns


def build_wa(txns, share, expenses):
    lines = ["💸 *BillBuddy Settlement*", ""]
    for t in txns:
        lines.append(f"  {t['from']}  →  ₹{t['amount']:.2f}  →  {t['to']}")
    lines += ["", f"✅ Everyone pays equally  (₹{share:.2f} each)"]
    if expenses:
        lines += ["", "📋 *Expense Breakdown:*"]
        for e in expenses:
            remark = f"  [{e['remark']}]" if e.get("remark") else ""
            lines.append(f"  {e['payer']} paid ₹{e['amount']:.2f}{remark}")
    lines += ["", "Settled with BillBuddy AI 💸"]
    return "\n".join(lines)


# ════════════════════════════════════════════════
#  MAIN APP
# ════════════════════════════════════════════════

class BillBuddyApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("BillBuddy AI 💸")
        self.geometry("920x680")
        self.minsize(720, 560)
        self.configure(fg_color=BG)
        self.resizable(True, True)

        # shared state
        self.expenses = []   # [{"payer": str, "amount": float, "remark": str}]
        self._wa_text = ""

        self._build_header()
        self._build_tabs()

    # ── HEADER ──────────────────────────────────

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=CARD, corner_radius=0, height=72)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="BillBuddy AI 💸", font=FT,
                     text_color=ACCENT).pack(side="left", padx=24, pady=10)
        ctk.CTkLabel(hdr, text="No more awkward money talks ❤️", font=FS,
                     text_color=SUB).pack(side="left", pady=18)

    # ── TABS ────────────────────────────────────

    def _build_tabs(self):
        self.tabs = ctk.CTkTabview(
            self, fg_color=BG,
            segmented_button_fg_color=CARD,
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color="#5550d4",
            segmented_button_unselected_color=CARD,
            segmented_button_unselected_hover_color=CARD2,
            text_color=TEXT,
            border_color=BORDER, border_width=1)
        self.tabs.pack(fill="both", expand=True, padx=14, pady=(8, 10))

        self.tabs.add("👥💳  Members & Expenses")
        self.tabs.add("📊  Results")

        self._build_main_tab(self.tabs.tab("👥💳  Members & Expenses"))
        self._build_results_tab(self.tabs.tab("📊  Results"))

    # ════════════════════════════════════════════
    #  TAB 1 — MEMBERS & EXPENSES (merged)
    # ════════════════════════════════════════════

    def _build_main_tab(self, tab):
        tab.configure(fg_color=BG)

        # ── Input card ──────────────────────────
        input_card = ctk.CTkFrame(tab, fg_color=CARD, corner_radius=14,
                                   border_width=1, border_color=BORDER)
        input_card.pack(fill="x", padx=4, pady=(8, 10))

        ctk.CTkLabel(input_card, text="➕  Add Member & Expense",
                     font=FL, text_color=ACCENT).pack(anchor="w", padx=16, pady=(14, 10))

        # Row 1: Name + Amount
        r1 = ctk.CTkFrame(input_card, fg_color="transparent")
        r1.pack(fill="x", padx=14, pady=(0, 8))
        r1.columnconfigure(0, weight=2)
        r1.columnconfigure(1, weight=2)
        r1.columnconfigure(2, weight=3)

        ctk.CTkLabel(r1, text="Member Name", font=FS,
                     text_color=SUB).grid(row=0, column=0, sticky="w", pady=(0, 3))
        ctk.CTkLabel(r1, text="Amount Paid (₹)", font=FS,
                     text_color=SUB).grid(row=0, column=1, sticky="w", padx=(12, 0), pady=(0, 3))
        ctk.CTkLabel(r1, text="Remark  (optional — place / time / note)", font=FS,
                     text_color=SUB).grid(row=0, column=2, sticky="w", padx=(12, 0), pady=(0, 3))

        self.name_var   = ctk.StringVar()
        self.amt_var    = ctk.StringVar()
        self.remark_var = ctk.StringVar()

        name_ent = ctk.CTkEntry(r1, textvariable=self.name_var,
                                placeholder_text="e.g. Arjun",
                                font=FB, fg_color=CARD2,
                                border_color=BORDER, text_color=TEXT, height=40)
        name_ent.grid(row=1, column=0, sticky="ew")
        name_ent.bind("<Return>", lambda _: self.amt_ent.focus())

        self.amt_ent = ctk.CTkEntry(r1, textvariable=self.amt_var,
                                    placeholder_text="e.g. 350",
                                    font=FB, fg_color=CARD2,
                                    border_color=BORDER, text_color=TEXT, height=40)
        self.amt_ent.grid(row=1, column=1, sticky="ew", padx=(12, 0))
        self.amt_ent.bind("<Return>", lambda _: self.remark_ent.focus())

        self.remark_ent = ctk.CTkEntry(r1, textvariable=self.remark_var,
                                       placeholder_text="e.g. Dinner at Pizza Hut, 8pm",
                                       font=FB, fg_color=CARD2,
                                       border_color=BORDER, text_color=TEXT, height=40)
        self.remark_ent.grid(row=1, column=2, sticky="ew", padx=(12, 0))
        self.remark_ent.bind("<Return>", lambda _: self._add_entry())

        # Row 2: Add + Calculate buttons
        r2 = ctk.CTkFrame(input_card, fg_color="transparent")
        r2.pack(fill="x", padx=14, pady=(0, 14))
        r2.columnconfigure(0, weight=1)
        r2.columnconfigure(1, weight=2)

        ctk.CTkButton(r2, text="➕  Add Entry", height=42,
                      fg_color=GREEN, hover_color="#00b389",
                      text_color="#000000", font=FL,
                      command=self._add_entry).grid(row=0, column=0, sticky="ew", padx=(0, 10))

        ctk.CTkButton(r2, text="⚡  Calculate Settlement", height=42,
                      fg_color=ACCENT, hover_color="#5550d4",
                      text_color="white", font=("Segoe UI", 13, "bold"),
                      command=self._calculate).grid(row=0, column=1, sticky="ew")

        # ── Entries list ────────────────────────
        list_card = ctk.CTkFrame(tab, fg_color=CARD, corner_radius=14,
                                  border_width=1, border_color=BORDER)
        list_card.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        # Header row for the list
        hrow = ctk.CTkFrame(list_card, fg_color="transparent")
        hrow.pack(fill="x", padx=16, pady=(12, 4))
        hrow.columnconfigure(0, weight=2)
        hrow.columnconfigure(1, weight=1)
        hrow.columnconfigure(2, weight=3)
        hrow.columnconfigure(3, weight=0)

        for col, lbl in enumerate(["Member", "Amount", "Remark", ""]):
            ctk.CTkLabel(hrow, text=lbl, font=("Segoe UI", 11, "bold"),
                         text_color=SUB).grid(row=0, column=col, sticky="w",
                                               padx=(0 if col==0 else 8, 0))

        divider = ctk.CTkFrame(list_card, fg_color=BORDER, height=1)
        divider.pack(fill="x", padx=16, pady=(0, 4))

        self.list_scroll = ctk.CTkScrollableFrame(list_card, fg_color="transparent",
                                                   corner_radius=0)
        self.list_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._empty_lbl = ctk.CTkLabel(self.list_scroll,
            text="No entries yet.\nFill in the form above and click  ➕ Add Entry",
            font=FS, text_color=SUB, justify="center")
        self._empty_lbl.pack(pady=40)

        # Summary footer inside list card
        self.summary_bar = ctk.CTkFrame(list_card, fg_color=CARD2,
                                         corner_radius=10, height=40)
        self.summary_bar.pack(fill="x", padx=14, pady=(0, 12))
        self.summary_bar.pack_propagate(False)
        self.summary_lbl = ctk.CTkLabel(self.summary_bar,
            text="Total: ₹0.00  |  Members: 0  |  Entries: 0",
            font=FB, text_color=SUB)
        self.summary_lbl.pack(side="left", padx=14)

    # ════════════════════════════════════════════
    #  TAB 2 — RESULTS
    # ════════════════════════════════════════════

    def _build_results_tab(self, tab):
        tab.configure(fg_color=BG)

        self.res_scroll = ctk.CTkScrollableFrame(tab, fg_color=BG)
        self.res_scroll.pack(fill="both", expand=True, padx=4, pady=(4, 6))

        self._show_placeholder()

        self.copy_btn = ctk.CTkButton(
            tab, text="📋  Copy for WhatsApp", height=46,
            fg_color=CARD2, hover_color=BORDER,
            border_color=GREEN, border_width=2,
            text_color=GREEN, font=FL,
            state="disabled", command=self._copy_clipboard)
        self.copy_btn.pack(fill="x", padx=4, pady=(0, 4))

    # ════════════════════════════════════════════
    #  ACTIONS
    # ════════════════════════════════════════════

    def _add_entry(self):
        name   = self.name_var.get().strip()
        remark = self.remark_var.get().strip()
        raw    = self.amt_var.get().strip()

        if not name:
            messagebox.showwarning("Missing Name", "Please enter a member name.")
            return
        try:
            amount = float(raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Amount",
                                 "Enter a valid positive number for the amount.")
            return

        self.expenses.append({"payer": name, "amount": amount, "remark": remark})
        self.name_var.set("")
        self.amt_var.set("")
        self.remark_var.set("")
        self.name_var.set("")  # ensure clear
        self._refresh_list()

        # focus back to name for fast multi-entry
        # find the name entry widget and focus it
        for w in self.winfo_children():
            pass  # just trigger refresh
        self.after(50, lambda: self.focus_get())

    def _remove_entry(self, idx):
        if 0 <= idx < len(self.expenses):
            self.expenses.pop(idx)
            self._refresh_list()

    def _calculate(self):
        if not self.expenses:
            messagebox.showwarning("No Data", "Add at least one entry first.")
            return

        # get unique people
        people = list(dict.fromkeys(e["payer"] for e in self.expenses))

        if len(people) < 2:
            messagebox.showwarning("Need More Members",
                                   "Add entries for at least 2 different members.")
            return

        total    = sum(e["amount"] for e in self.expenses)
        share    = round(total / len(people), 2)
        balances = calc_balances(people, self.expenses)
        txns     = smart_settle(balances)
        naive    = max(0, len(people) - 1)
        optimized= len(txns)

        self._wa_text = build_wa(txns, share, self.expenses)
        self._render_results(total, share, balances, txns, optimized, naive, people)
        self.copy_btn.configure(state="normal")
        self.tabs.set("📊  Results")

    def _copy_clipboard(self):
        if not self._wa_text:
            return
        try:
            if _CLIP:
                pyperclip.copy(self._wa_text)
            else:
                self.clipboard_clear()
                self.clipboard_append(self._wa_text)
            self.copy_btn.configure(text="✅  Copied to clipboard!")
            self.after(2500, lambda: self.copy_btn.configure(text="📋  Copy for WhatsApp"))
        except Exception as err:
            messagebox.showerror("Copy Failed", str(err))

    # ════════════════════════════════════════════
    #  REFRESH LIST
    # ════════════════════════════════════════════

    def _refresh_list(self):
        for w in self.list_scroll.winfo_children():
            w.destroy()

        if not self.expenses:
            ctk.CTkLabel(self.list_scroll,
                text="No entries yet.\nFill in the form above and click  ➕ Add Entry",
                font=FS, text_color=SUB, justify="center").pack(pady=40)
            self.summary_lbl.configure(
                text="Total: ₹0.00  |  Members: 0  |  Entries: 0")
            return

        # Color palette for member avatars
        avatar_colors = [ACCENT, GREEN, GOLD, RED, PURPLE, "#e67e22", "#1abc9c", "#e74c3c"]
        member_colors = {}
        members_seen  = []
        for e in self.expenses:
            if e["payer"] not in members_seen:
                members_seen.append(e["payer"])
                idx = len(members_seen) - 1
                member_colors[e["payer"]] = avatar_colors[idx % len(avatar_colors)]

        for i, e in enumerate(self.expenses):
            row = ctk.CTkFrame(self.list_scroll, fg_color=CARD2 if i % 2 == 0 else CARD,
                               corner_radius=8, height=48)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            # Avatar
            color = member_colors.get(e["payer"], ACCENT)
            av = ctk.CTkLabel(row, text=e["payer"][0].upper(),
                               width=32, height=32, font=FL,
                               text_color="white", fg_color=color,
                               corner_radius=16)
            av.pack(side="left", padx=(10, 8), pady=8)

            # Name
            ctk.CTkLabel(row, text=e["payer"], font=FL,
                         text_color=TEXT, width=130, anchor="w").pack(side="left", padx=(0, 8))

            # Amount
            ctk.CTkLabel(row, text=f"₹{e['amount']:.2f}", font=FL,
                         text_color=GREEN, width=90, anchor="w").pack(side="left", padx=(0, 8))

            # Remark
            remark_text = e.get("remark", "") or "—"
            ctk.CTkLabel(row, text=remark_text, font=FS,
                         text_color=SUB, anchor="w").pack(side="left", fill="x", expand=True, padx=(0, 8))

            # Delete button
            ctk.CTkButton(row, text="✕", width=30, height=28,
                          fg_color="transparent", hover_color=RED,
                          text_color=SUB, font=("Segoe UI", 11, "bold"),
                          command=lambda idx=i: self._remove_entry(idx)
                          ).pack(side="right", padx=8)

        # Update summary bar
        total   = sum(e["amount"] for e in self.expenses)
        members = len(set(e["payer"] for e in self.expenses))
        self.summary_lbl.configure(
            text=f"Total: ₹{total:.2f}  |  Members: {members}  |  Entries: {len(self.expenses)}")

    # ════════════════════════════════════════════
    #  RENDER RESULTS
    # ════════════════════════════════════════════

    def _show_placeholder(self):
        for w in self.res_scroll.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.res_scroll,
                     text="⚡  Add entries and hit  'Calculate Settlement'\nResults will appear here.",
                     font=("Segoe UI", 13), text_color=SUB, justify="center"
                     ).pack(pady=120)

    def _render_results(self, total, share, balances, txns, optimized, naive, people):
        for w in self.res_scroll.winfo_children():
            w.destroy()
        rb = self.res_scroll

        # ── 3 stat boxes ─────────────────────────
        stats_row = ctk.CTkFrame(rb, fg_color="transparent")
        stats_row.pack(fill="x", pady=(6, 14))
        stats_row.columnconfigure(0, weight=1)
        stats_row.columnconfigure(1, weight=1)
        stats_row.columnconfigure(2, weight=1)
        stats_row.columnconfigure(3, weight=1)

        for col, (label, value, color) in enumerate([
            ("Total Spent",  f"₹{total:.2f}",   GOLD),
            ("Equal Share",  f"₹{share:.2f}",   GREEN),
            ("Members",      str(len(people)),   ACCENT),
            ("Transactions", str(optimized),     RED),
        ]):
            box = ctk.CTkFrame(stats_row, fg_color=CARD2, corner_radius=12)
            box.grid(row=0, column=col, padx=4, sticky="ew")
            ctk.CTkLabel(box, text=value, font=FG, text_color=color).pack(pady=(12, 2))
            ctk.CTkLabel(box, text=label, font=FS, text_color=SUB).pack(pady=(0, 12))

        # ── Individual balances ───────────────────
        sec_lbl(rb, "👤  Individual Balances")

        for person, bal in balances.items():
            if   bal > 0.009:
                icon, clr, tag = "⬆", GREEN, f"+₹{bal:.2f}  (will receive)"
            elif bal < -0.009:
                icon, clr, tag = "⬇", RED,   f"-₹{abs(bal):.2f}  (needs to pay)"
            else:
                icon, clr, tag = "✓", SUB,   "Already settled"

            row = ctk.CTkFrame(rb, fg_color=CARD2, corner_radius=10, height=46)
            row.pack(fill="x", pady=3)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=f"{icon}  {person}", font=FB,
                         text_color=TEXT).pack(side="left", padx=14)
            ctk.CTkLabel(row, text=tag, font=FL,
                         text_color=clr).pack(side="right", padx=14)

        # ── Settlement plan ───────────────────────
        sec_lbl(rb, "💸  Settlement Plan")

        if not txns:
            ctk.CTkLabel(rb, text="✅  Everyone is already settled — no payments needed!",
                         font=FB, text_color=GREEN).pack(anchor="w", padx=10, pady=8)
        else:
            for t in txns:
                card = ctk.CTkFrame(rb, fg_color=CARD2, corner_radius=12)
                card.pack(fill="x", pady=4)

                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="x", padx=18, pady=14)
                inner.columnconfigure(0, weight=1)
                inner.columnconfigure(1, weight=0)
                inner.columnconfigure(2, weight=1)

                ctk.CTkLabel(inner, text=t["from"], font=FR,
                             text_color=RED).grid(row=0, column=0, sticky="w")

                mid = ctk.CTkFrame(inner, fg_color="transparent")
                mid.grid(row=0, column=1, padx=20)
                ctk.CTkLabel(mid, text="pays", font=FS,
                             text_color=SUB).pack()
                ctk.CTkLabel(mid, text=f"₹{t['amount']:.2f}", font=("Segoe UI", 16, "bold"),
                             text_color=GOLD).pack()
                ctk.CTkLabel(mid, text="to", font=FS,
                             text_color=SUB).pack()

                ctk.CTkLabel(inner, text=t["to"], font=FR,
                             text_color=GREEN).grid(row=0, column=2, sticky="e")

        # ── Expense breakdown ─────────────────────
        sec_lbl(rb, "🧾  Expense Breakdown")

        for e in self.expenses:
            row = ctk.CTkFrame(rb, fg_color=CARD2, corner_radius=10, height=44)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            ctk.CTkLabel(row, text=e["payer"], font=FL,
                         text_color=TEXT, width=120, anchor="w").pack(side="left", padx=14)
            ctk.CTkLabel(row, text=f"₹{e['amount']:.2f}", font=FL,
                         text_color=GREEN, width=90, anchor="w").pack(side="left")
            remark = e.get("remark", "") or "—"
            ctk.CTkLabel(row, text=remark, font=FS,
                         text_color=SUB, anchor="w").pack(side="left", fill="x",
                                                           expand=True, padx=(4, 14))

        # ══════════════════════════════════════════
        #  FINAL TRIP LEDGER  ✨ (new section)
        # ══════════════════════════════════════════
        sec_lbl(rb, "🏁  Final Trip Ledger  —  What everyone actually spent")

        # Build per-person data:
        #   paid_by_me    = total they physically paid upfront
        #   send_to       = list of {name, amount} they still owe
        #   receive_from  = list of {name, amount} coming back to them
        #   net_spent     = paid_by_me - total_received + total_sent  == share (always)

        paid_map = {p: 0.0 for p in people}
        for e in self.expenses:
            paid_map[e["payer"]] = paid_map.get(e["payer"], 0) + e["amount"]

        # Map who sends to whom from the settlement transactions
        sends    = {p: [] for p in people}   # sends[p] = [{to, amount}]
        receives = {p: [] for p in people}   # receives[p] = [{from_, amount}]
        for t in txns:
            sends[t["from"]].append({"to": t["to"], "amount": t["amount"]})
            receives[t["to"]].append({"from_": t["from"], "amount": t["amount"]})

        avatar_palette = [ACCENT, GREEN, GOLD, RED, PURPLE, "#e67e22", "#1abc9c", "#3498db"]
        av_map = {}
        for idx, p in enumerate(people):
            av_map[p] = avatar_palette[idx % len(avatar_palette)]

        for person in people:
            paid_up   = paid_map.get(person, 0.0)
            total_out = sum(s["amount"] for s in sends[person])
            total_in  = sum(r["amount"] for r in receives[person])
            net       = round(paid_up + total_out - total_in, 2)

            pcard = ctk.CTkFrame(rb, fg_color=CARD, corner_radius=14,
                                  border_width=1, border_color=BORDER)
            pcard.pack(fill="x", pady=5)

            # ── Card header ─────────────────────
            hdr = ctk.CTkFrame(pcard, fg_color=CARD2, corner_radius=10)
            hdr.pack(fill="x", padx=12, pady=(12, 6))

            # Avatar
            ctk.CTkLabel(hdr, text=person[0].upper(),
                          width=36, height=36, font=("Segoe UI", 14, "bold"),
                          text_color="white", fg_color=av_map[person],
                          corner_radius=18).pack(side="left", padx=(12, 10), pady=8)

            ctk.CTkLabel(hdr, text=person, font=FR,
                          text_color=TEXT).pack(side="left")

            # Net spent badge
            badge_frame = ctk.CTkFrame(hdr, fg_color=BG, corner_radius=8)
            badge_frame.pack(side="right", padx=12, pady=8)
            ctk.CTkLabel(badge_frame, text="Net Spent",
                          font=("Segoe UI", 9), text_color=SUB).pack(padx=10, pady=(4, 0))
            ctk.CTkLabel(badge_frame, text=f"₹{net:.2f}",
                          font=("Segoe UI", 14, "bold"), text_color=GOLD).pack(padx=10, pady=(0, 4))

            # ── Body rows ───────────────────────
            body_f = ctk.CTkFrame(pcard, fg_color="transparent")
            body_f.pack(fill="x", padx=18, pady=(0, 4))

            # Paid upfront
            _ledger_row(body_f, "💳  Paid upfront",
                         f"₹{paid_up:.2f}", GREEN)

            # Payments they need to send
            if sends[person]:
                for s in sends[person]:
                    _ledger_row(body_f,
                                 f"  ➡  Send to  {s['to']}",
                                 f"−₹{s['amount']:.2f}", RED)
            else:
                _ledger_row(body_f, "  ➡  Send to", "Nothing to send", SUB)

            # Payments they will receive
            if receives[person]:
                for r in receives[person]:
                    _ledger_row(body_f,
                                 f"  ⬅  Receive from  {r['from_']}",
                                 f"+₹{r['amount']:.2f}", GREEN)
            else:
                _ledger_row(body_f, "  ⬅  Receive from", "Nothing to receive", SUB)

            # Divider
            ctk.CTkFrame(pcard, fg_color=BORDER, height=1).pack(
                fill="x", padx=18, pady=(4, 6))

            # Final equal line
            eq_row = ctk.CTkFrame(pcard, fg_color="transparent")
            eq_row.pack(fill="x", padx=18, pady=(0, 12))
            ctk.CTkLabel(eq_row, text="✅  Final equal share",
                          font=FL, text_color=GREEN).pack(side="left")
            ctk.CTkLabel(eq_row, text=f"₹{share:.2f}",
                          font=("Segoe UI", 14, "bold"), text_color=GREEN
                          ).pack(side="right")

        # ── AI suggestion ─────────────────────────
        ai = ctk.CTkFrame(rb, fg_color=CARD2, corner_radius=12)
        ai.pack(fill="x", pady=(14, 6))
        ctk.CTkLabel(ai, text="💡  Smart Suggestion", font=FL,
                     text_color=GOLD).pack(anchor="w", padx=16, pady=(12, 4))
        saved = naive - optimized
        line1 = (f"Settled in {optimized} transaction{'s' if optimized != 1 else ''}"
                 f" instead of up to {naive}.")
        line2 = (f"Saved {saved} step{'s' if saved != 1 else ''}! 🎉"
                 if saved > 0 else "Already the optimal number of transactions!")
        ctk.CTkLabel(ai, text=line1, font=FB, text_color=TEXT,
                     wraplength=700).pack(anchor="w", padx=16)
        ctk.CTkLabel(ai, text=line2, font=FL,
                     text_color=GREEN if saved > 0 else SUB,
                     wraplength=700).pack(anchor="w", padx=16, pady=(2, 12))

        # ── WhatsApp preview ──────────────────────
        sec_lbl(rb, "📄  WhatsApp Preview  (tap Copy below)")
        preview = ctk.CTkFrame(rb, fg_color=CARD2, corner_radius=12)
        preview.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(preview, text=self._wa_text,
                     font=("Consolas", 11), text_color=TEXT,
                     justify="left", wraplength=720
                     ).pack(anchor="w", padx=16, pady=14)


# ── tiny helpers ─────────────────────────────────

def sec_lbl(parent, text):
    ctk.CTkLabel(parent, text=text, font=FL, text_color=SUB
                 ).pack(anchor="w", padx=4, pady=(12, 4))


def _ledger_row(parent, label, value, value_color):
    """One line inside a person's Final Trip Ledger card."""
    row = ctk.CTkFrame(parent, fg_color="transparent", height=28)
    row.pack(fill="x", pady=1)
    row.pack_propagate(False)
    ctk.CTkLabel(row, text=label, font=FB, text_color=SUB,
                  anchor="w").pack(side="left")
    ctk.CTkLabel(row, text=value, font=FL, text_color=value_color,
                  anchor="e").pack(side="right")


# ════════════════════════════════════════════════
if __name__ == "__main__":
    BillBuddyApp().mainloop()