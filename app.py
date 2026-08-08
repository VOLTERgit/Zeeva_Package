"""
Zeeva Clinic - Hair Transplant Package Generator
--------------------------------------------------
A desktop tool for clinic staff to enter patient details, tick which
services are included in a package, adjust any price on the fly, and
generate a branded PDF package quote that matches the Zeeva design.

Run with:  python app.py
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from pdf_generator import generate_pdf
from patient_log import log_patient_to_excel


def resource_path(relative_path):
    """Get absolute path to a bundled resource, works for dev and for PyInstaller .exe"""
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


def app_dir():
    """
    Folder where the running .exe (or script, in dev) actually lives — used for
    writable data like the patient Excel log. This is DIFFERENT from
    resource_path()/_MEIPASS, which is a temporary extraction folder for the
    bundled .exe and gets wiped after the app closes, so it can't be used to
    persist anything.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.dirname(__file__))


class LineItem:
    """
    Represents one row in the 'Package Includes' table.

    kind:
        "flat"          -> a single price, no quantity (e.g. Post-Operative Care)
        "unit"          -> quantity x rate (e.g. Grafts)
        "session_flat"  -> a session/qty count shown as text, but staff types the
                            TOTAL price directly (for bundle/discount pricing, e.g.
                            "6 sessions" but a flat discounted total instead of qty x rate)
        "medicine"      -> two editable amounts (e.g. Post-op + Long-term) summed into one row
        "info"          -> checkbox + free-text detail, no price at all (e.g. Follow-Up
                            Consultation, Procedure Day)
    """

    def __init__(self, parent, row, name, kind, on_change,
                 default_qty=None, default_rate=0, unit_label="",
                 detail_template="", default_detail_text="",
                 default_amount2=0, amount2_label="", default_included=True):
        self.name = name
        self.kind = kind
        self.unit_label = unit_label
        self.detail_template = detail_template
        self.on_change = on_change

        self.include_var = tk.BooleanVar(value=default_included)
        self.qty_var = tk.StringVar(value=str(default_qty) if default_qty is not None else "")
        self.rate_var = tk.StringVar(value=str(default_rate))
        self.rate2_var = tk.StringVar(value=str(default_amount2))
        self.detail_var = tk.StringVar(value=default_detail_text)

        # --- checkbox ---
        self.chk = ttk.Checkbutton(parent, variable=self.include_var, command=self._changed)
        self.chk.grid(row=row, column=0, padx=(6, 4), pady=4)

        # --- service name ---
        ttk.Label(parent, text=name, width=22, anchor="w").grid(
            row=row, column=1, sticky="w", padx=4, pady=4
        )

        if kind == "unit":
            qty_entry = ttk.Entry(parent, textvariable=self.qty_var, width=7, justify="center")
            qty_entry.grid(row=row, column=2, padx=4, pady=4)
            self.qty_var.trace_add("write", lambda *a: self._changed())
            ttk.Label(parent, text=unit_label, width=8, anchor="w").grid(
                row=row, column=3, sticky="w", padx=(0, 4)
            )
            rate_entry = ttk.Entry(parent, textvariable=self.rate_var, width=10, justify="center")
            rate_entry.grid(row=row, column=4, padx=4, pady=4)
            self.rate_var.trace_add("write", lambda *a: self._changed())
            ttk.Label(parent, text="Rs / unit", width=9, anchor="w",
                      foreground="#777").grid(row=row, column=5, sticky="w")

        elif kind == "session_flat":
            qty_entry = ttk.Entry(parent, textvariable=self.qty_var, width=7, justify="center")
            qty_entry.grid(row=row, column=2, padx=4, pady=4)
            self.qty_var.trace_add("write", lambda *a: self._changed())
            ttk.Label(parent, text=unit_label, width=8, anchor="w").grid(
                row=row, column=3, sticky="w", padx=(0, 4)
            )
            rate_entry = ttk.Entry(parent, textvariable=self.rate_var, width=10, justify="center")
            rate_entry.grid(row=row, column=4, padx=4, pady=4)
            self.rate_var.trace_add("write", lambda *a: self._changed())
            ttk.Label(parent, text="Rs total (editable)", width=15, anchor="w",
                      foreground="#777").grid(row=row, column=5, sticky="w")

        elif kind == "medicine":
            ttk.Label(parent, text="-", width=8, anchor="center").grid(row=row, column=2)
            rate_entry = ttk.Entry(parent, textvariable=self.rate_var, width=9, justify="center")
            rate_entry.grid(row=row, column=3, padx=2, pady=4)
            self.rate_var.trace_add("write", lambda *a: self._changed())
            ttk.Label(parent, text="+", width=1, anchor="center").grid(row=row, column=4)
            rate2_entry = ttk.Entry(parent, textvariable=self.rate2_var, width=9, justify="center")
            rate2_entry.grid(row=row, column=5, padx=2, pady=4)
            self.rate2_var.trace_add("write", lambda *a: self._changed())

        elif kind == "info":
            ttk.Label(parent, text="-", width=8, anchor="center").grid(row=row, column=2)
            detail_entry = ttk.Entry(parent, textvariable=self.detail_var, width=24)
            detail_entry.grid(row=row, column=3, columnspan=3, sticky="w", padx=4, pady=4)

        else:  # "flat"
            ttk.Label(parent, text="-", width=8, anchor="center").grid(row=row, column=2)
            ttk.Label(parent, text="", width=8).grid(row=row, column=3)
            rate_entry = ttk.Entry(parent, textvariable=self.rate_var, width=10, justify="center")
            rate_entry.grid(row=row, column=4, padx=4, pady=4)
            self.rate_var.trace_add("write", lambda *a: self._changed())
            ttk.Label(parent, text="Rs (flat)", width=9, anchor="w",
                      foreground="#777").grid(row=row, column=5, sticky="w")

        # --- computed amount ---
        self.amount_label = ttk.Label(parent, text="", width=13, anchor="e",
                                       font=("Segoe UI", 10, "bold"))
        self.amount_label.grid(row=row, column=6, padx=(10, 6), pady=4, sticky="e")

        self._update_amount()

    def _changed(self):
        self._update_amount()
        if self.on_change:
            self.on_change()

    def _safe_float(self, s, default=0.0):
        try:
            return float(s)
        except (ValueError, TypeError):
            return default

    def amount(self):
        if not self.include_var.get():
            return 0.0
        if self.kind == "unit":
            return self._safe_float(self.qty_var.get()) * self._safe_float(self.rate_var.get())
        if self.kind == "session_flat":
            return self._safe_float(self.rate_var.get())
        if self.kind == "medicine":
            return self._safe_float(self.rate_var.get()) + self._safe_float(self.rate2_var.get())
        if self.kind == "info":
            return 0.0
        return self._safe_float(self.rate_var.get())  # flat

    def _update_amount(self):
        if self.kind == "info":
            self.amount_label.config(text="")
        else:
            self.amount_label.config(text=f"Rs {self.amount():,.0f}")

    def detail_text(self):
        """Text shown in the 'Details' column of the PDF table."""
        if self.kind == "unit":
            qty = self.qty_var.get().strip() or "0"
            return self.detail_template.format(qty=qty)
        if self.kind == "session_flat":
            qty = self.qty_var.get().strip() or "0"
            return self.detail_template.format(qty=qty)
        if self.kind == "info":
            return self.detail_var.get().strip()
        return self.detail_template

    def to_dict(self):
        return {
            "name": self.name,
            "included": self.include_var.get(),
            "amount": self.amount(),
            "detail": self.detail_text(),
        }


class ZeevaApp:
    TEAL = "#1CA39C"
    DARK = "#0B2E36"

    def __init__(self, root):
        self.root = root
        root.title("Zeeva Clinic - Hair Transplant Package Generator")
        root.geometry("920x820")
        root.configure(bg="#F4F6F6")

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"),
                         foreground=self.DARK, background="#F4F6F6")
        style.configure("Sub.TLabel", font=("Segoe UI", 10), foreground="#555",
                         background="#F4F6F6")
        style.configure("Section.TLabel", font=("Segoe UI", 12, "bold"),
                         foreground="#fff", background=self.DARK)
        style.configure("TFrame", background="#F4F6F6")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("TCheckbutton", background="#ffffff")
        style.configure("TLabel", background="#ffffff")

        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        header = ttk.Frame(self.root, padding=(16, 14, 16, 6))
        header.pack(fill="x")
        ttk.Label(header, text="Zeeva Clinic - Package Generator",
                  style="Header.TLabel").pack(anchor="w")
        ttk.Label(header, text="Fill patient details, tick the services included, "
                               "adjust prices if needed, then generate the PDF.",
                  style="Sub.TLabel").pack(anchor="w")

        # ---------------- Patient details card ----------------
        patient_card = tk.Frame(self.root, bg="white", bd=0, highlightthickness=1,
                                 highlightbackground="#ddd")
        patient_card.pack(fill="x", padx=16, pady=(8, 10))

        tk.Label(patient_card, text="PATIENT DETAILS", bg=self.DARK, fg="white",
                  font=("Segoe UI", 10, "bold"), anchor="w", padx=10, pady=6).pack(fill="x")

        form = tk.Frame(patient_card, bg="white", padx=12, pady=10)
        form.pack(fill="x")

        self.name_var = tk.StringVar()
        self.age_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.country_var = tk.StringVar(value="India")
        self.quotation_id_var = tk.StringVar(value=self._new_quotation_id())

        self._labeled_entry(form, "Patient Name", self.name_var, 0, 0)
        self._labeled_entry(form, "Age", self.age_var, 0, 2, width=8)
        self._labeled_entry(form, "Phone Number", self.phone_var, 1, 0)
        self._labeled_entry(form, "Country", self.country_var, 1, 2)
        self._labeled_entry(form, "Quotation ID (auto, editable)", self.quotation_id_var, 2, 0)

        # ---------------- Package items card ----------------
        items_card = tk.Frame(self.root, bg="white", bd=0, highlightthickness=1,
                               highlightbackground="#ddd")
        items_card.pack(fill="both", expand=False, padx=16, pady=(0, 10))

        tk.Label(items_card, text="PACKAGE INCLUDES  (uncheck to remove from PDF)",
                  bg=self.DARK, fg="white", font=("Segoe UI", 10, "bold"),
                  anchor="w", padx=10, pady=6).pack(fill="x")

        table = tk.Frame(items_card, bg="white", padx=12, pady=10)
        table.pack(fill="x")

        headers = ["Incl.", "Service", "Qty", "", "Rate / Price", "", "Amount"]
        for c, h in enumerate(headers):
            tk.Label(table, text=h, bg="white", fg="#777",
                     font=("Segoe UI", 9, "bold")).grid(row=0, column=c, padx=4, sticky="w")

        self.items = []
        r = 1
        self.items.append(LineItem(
            table, r, "Pre-Operative Blood Tests", "flat", self._recalc,
            default_rate=3500, detail_template="Included")); r += 1
        self.graft_item = LineItem(
            table, r, "Hair Transplant Surgery", "unit", self._recalc,
            default_qty=4000, default_rate=60, unit_label="grafts",
            detail_template="{qty} Scalp Grafts \u2022 ")
        self.items.append(self.graft_item); r += 1

        # --- Technique for the Hair Transplant Surgery row above: DHT or FUE ---
        # Mutually exclusive (radio buttons) - only one can be selected.
        self.technique_var = tk.StringVar(value="DHT")
        tech_frame = tk.Frame(table, bg="white")
        tech_frame.grid(row=r, column=1, columnspan=5, sticky="w", padx=4, pady=(0, 6))
        tk.Label(tech_frame, text="Technique:", bg="white", fg="#555",
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 8))
        ttk.Radiobutton(tech_frame, text="DHT", variable=self.technique_var,
                         value="DHT", command=self._recalc).pack(side="left", padx=(0, 14))
        ttk.Radiobutton(tech_frame, text="FUE", variable=self.technique_var,
                         value="FUE", command=self._recalc).pack(side="left")
        r += 1

        # --- Beard Grafts (separate from the scalp grafts above) ---
        # Off by default since not every patient wants a beard transplant;
        # rate defaults to Rs 70/graft but staff can edit it per patient.
        self.beard_item = LineItem(
            table, r, "Beard Transplant Surgery", "unit", self._recalc,
            default_qty=0, default_rate=70, unit_label="grafts",
            detail_template="{qty} Beard Grafts", default_included=False)
        self.items.append(self.beard_item); r += 1

        self.items.append(LineItem(
            table, r, "PRP Therapy Sessions", "session_flat", self._recalc,
            default_qty=6, default_rate=22500, unit_label="sessions",
            detail_template="{qty} Sessions Included")); r += 1
        self.items.append(LineItem(
            table, r, "Post-Operative Care", "flat", self._recalc,
            default_rate=2000, detail_template="Post-Op Immediate Medication Included")); r += 1
        self.items.append(LineItem(
            table, r, "Medicine", "medicine", self._recalc,
            default_rate=0, default_amount2=0,
            detail_template="Post-Op (1 Week) & Long-Term (1 Year) Medication Included")); r += 1
        self.items.append(LineItem(
            table, r, "Anesthesia", "flat", self._recalc,
            default_rate=20000, detail_template="Included")); r += 1
        self.items.append(LineItem(
            table, r, "Doctor-Led Surgery", "info", self._recalc,
            default_detail_text="Included - no technicians at any stage")); r += 1
        self.items.append(LineItem(
            table, r, "Lunch + Beverages", "info", self._recalc,
            default_detail_text="Included on surgery day")); r += 1
        self.items.append(LineItem(
            table, r, "Head Wash & Dressing", "info", self._recalc,
            default_detail_text="Included")); r += 1
        self.items.append(LineItem(
            table, r, "Follow-Up Consultation", "info", self._recalc,
            default_detail_text="1 Year Follow-Up Consultation with Medical Team Included")); r += 1
        self.items.append(LineItem(
            table, r, "Procedure Day", "info", self._recalc,
            default_detail_text="One-Day Procedure")); r += 1

        self.advance_item = LineItem(
            table, r, "Advance Payment (Date Booking)", "flat", self._recalc,
            default_rate=10000,
            detail_template="Non-refundable. Advance to confirm your slot",
        )
        self.items.append(self.advance_item); r += 1

        # --- Payment Mode for the Advance Payment row above ---
        # Mutually exclusive (radio buttons) - only one can be selected.
        self.payment_mode_var = tk.StringVar(value="Online")
        pay_frame = tk.Frame(table, bg="white")
        pay_frame.grid(row=r, column=1, columnspan=5, sticky="w", padx=4, pady=(0, 6))
        tk.Label(pay_frame, text="Payment Mode:", bg="white", fg="#555",
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 8))
        for mode in ("Online", "Cash", "Card", "Net Banking"):
            ttk.Radiobutton(pay_frame, text=mode, variable=self.payment_mode_var,
                             value=mode, command=self._recalc).pack(side="left", padx=(0, 10))
        r += 1

        hint = tk.Label(table, text="Medicine row: first box = Post-op amount, second box = Long-term amount (added together).\n"
                                     "Advance Payment row: shown as its own line in the PDF, but NOT added into the total below.",
                         bg="white", fg="#999", font=("Segoe UI", 8, "italic"), anchor="w", justify="left")
        hint.grid(row=r, column=0, columnspan=7, sticky="w", padx=4, pady=(6, 0))

        # ---------------- Totals ----------------
        totals_frame = tk.Frame(self.root, bg="#F4F6F6", padx=16)
        totals_frame.pack(fill="x", pady=(0, 8))

        self.gst_var = tk.BooleanVar(value=True)
        gst_chk = ttk.Checkbutton(totals_frame, text="Add GST (5%) to total",
                                   variable=self.gst_var, command=self._recalc)
        gst_chk.pack(side="left")

        self.total_label = tk.Label(totals_frame, text="Total: Rs 0", bg="#F4F6F6",
                                     fg=self.DARK, font=("Segoe UI", 14, "bold"))
        self.total_label.pack(side="right")

        # ---------------- Generate button ----------------
        btn_frame = tk.Frame(self.root, bg="#F4F6F6", padx=16, pady=6)
        btn_frame.pack(fill="x")

        generate_btn = tk.Button(
            btn_frame, text="Generate PDF Package", bg=self.TEAL, fg="white",
            font=("Segoe UI", 11, "bold"), relief="flat", padx=16, pady=10,
            activebackground="#178e88", cursor="hand2", command=self._generate
        )
        generate_btn.pack(side="right")

        self.status_label = tk.Label(btn_frame, text="", bg="#F4F6F6", fg="#666")
        self.status_label.pack(side="left")

        self._recalc()

    def _new_quotation_id(self):
        """ZC-YYMMDD-XXX, e.g. ZC-260807-482. Staff can overwrite this in
        the field if they use a different internal numbering scheme."""
        import random
        return f"ZC-{datetime.now().strftime('%y%m%d')}-{random.randint(100, 999)}"

    def _labeled_entry(self, parent, label, var, row, col, width=24):
        tk.Label(parent, text=label, bg="white", fg="#555",
                 font=("Segoe UI", 9)).grid(row=row * 2, column=col, sticky="w", padx=6, pady=(4, 0))
        entry = ttk.Entry(parent, textvariable=var, width=width)
        entry.grid(row=row * 2 + 1, column=col, sticky="w", padx=6, pady=(0, 8))
        return entry

    # -------------------------------------------------------------- logic
    def _subtotal(self):
        # Advance Payment is a separate booking deposit, not part of the
        # package price - shown as its own line in the PDF, but excluded
        # from the total.
        return sum(item.amount() for item in self.items if item is not self.advance_item)

    def _grand_total(self):
        """
        GST (5%) applies ONLY to the Hair Transplant Surgery (grafts) amount -
        e.g. 4000 grafts = Rs 2,40,000 + 5% GST. Every other line item
        (blood tests, PRP, medicine, anesthesia, advance payment, etc.) is
        added at its plain amount, with no GST on top.
        """
        subtotal = self._subtotal()
        graft_amount = self.graft_item.amount()
        if self.gst_var.get():
            return (subtotal - graft_amount) + graft_amount * 1.05
        return subtotal

    def _gst_amount(self):
        """The actual GST rupees added on top of the subtotal (0 if the GST
        checkbox is off) - passed to the PDF so it can show a clear
        breakdown instead of just a '5% applies' note."""
        if not self.gst_var.get():
            return 0.0
        return self.graft_item.amount() * 0.05

    def _recalc(self):
        total = self._grand_total()
        self.total_label.config(text=f"Total: Rs {total:,.0f}")

    def _generate(self):
        name = self.name_var.get().strip()
        age = self.age_var.get().strip()
        phone = self.phone_var.get().strip()
        country = self.country_var.get().strip()
        quotation_id = self.quotation_id_var.get().strip()

        if not name:
            messagebox.showwarning("Missing info", "Please enter the patient's name.")
            return

        # Basic phone sanity check (non-blocking - staff can proceed anyway,
        # e.g. for international numbers with unusual lengths) + auto country
        # code prefix for India so it doesn't have to be typed every time.
        digits_only = "".join(ch for ch in phone if ch.isdigit())
        if country.lower() == "india" and phone and not phone.startswith("+"):
            if len(digits_only) == 10:
                phone = f"+91 {digits_only}"
            self.phone_var.set(phone)
        if phone and len(digits_only) < 7:
            proceed = messagebox.askyesno(
                "Check phone number",
                f'"{phone}" looks too short to be a valid phone number.\n\n'
                f"Continue anyway?"
            )
            if not proceed:
                return

        included_items = [item.to_dict() for item in self.items if item.include_var.get()]
        if not included_items:
            messagebox.showwarning("Nothing selected",
                                    "Please tick at least one service to include.")
            return

        # Append the chosen technique (DHT or FUE) after the grafts detail text,
        # e.g. "4000 Scalp Grafts • DHT Technique" - only if that row is included.
        technique = self.technique_var.get()
        if self.graft_item.include_var.get():
            for d in included_items:
                if d["name"] == self.graft_item.name:
                    d["detail"] = f'{d["detail"]}{technique} Technique'

        # Advance Payment row: shows the amount + fixed booking phrase in the
        # PDF's Details column (this row has no separate amount column in
        # the PDF, and its amount is deliberately excluded from the total -
        # see _subtotal()).
        payment_mode = self.payment_mode_var.get()
        if self.advance_item.include_var.get():
            for d in included_items:
                if d["name"] == self.advance_item.name:
                    amt = self.advance_item.amount()
                    d["detail"] = (
                        f"Rs {amt:,.0f} For Booking Your Hair Transplant "
                        f"(Non-refundable, Payment Mode: {payment_mode})"
                    )

        total = self._grand_total()

        default_filename = f"Zeeva_Package_{name.replace(' ', '_') or 'Patient'}.pdf"
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=default_filename,
            filetypes=[("PDF files", "*.pdf")],
            title="Save Package PDF"
        )
        if not save_path:
            return

        patient = {
            "name": name,
            "age": age,
            "phone": phone,
            "country": country,
            "quotation_id": quotation_id,
            "date": datetime.now().strftime("%d %b %Y"),
        }

        try:
            generate_pdf(
                save_path,
                patient=patient,
                items=included_items,
                total=total,
                gst_applied=self.gst_var.get(),
                gst_amount=self._gst_amount(),
                assets_dir=resource_path("assets"),
            )
        except Exception as e:
            messagebox.showerror("Error generating PDF", str(e))
            return

        # Log this patient/package to the Excel sheet (auto-created next to the
        # app if it doesn't exist yet, one new row per PDF generated). A failure
        # here should never lose the PDF that was already saved, so it's a
        # separate try/except that just warns instead of blocking.
        try:
            log_patient_to_excel(
                log_path=os.path.join(app_dir(), "Zeeva_Patients_Log.xlsx"),
                patient=patient,
                items_included=included_items,
                technique=technique,
                total=total,
                gst_applied=self.gst_var.get(),
                pdf_filename=os.path.basename(save_path),
            )
        except Exception as e:
            messagebox.showwarning(
                "PDF saved, but Excel log failed",
                f"The PDF was generated successfully, but this patient could not "
                f"be added to Zeeva_Patients_Log.xlsx:\n\n{e}\n\n"
                f"(Make sure that Excel file isn't currently open on this computer, "
                f"then try generating again.)"
            )

        self.status_label.config(text=f"Saved: {os.path.basename(save_path)}")
        if messagebox.askyesno("Done", "PDF generated successfully.\nOpen it now?"):
            self._open_file(save_path)

    def _open_file(self, path):
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # noqa
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception:
            pass


def main():
    root = tk.Tk()
    ZeevaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
