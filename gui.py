import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import sys
import os
import csv
from main import run_procurement_intelligence
from emailer import send_bulk_emails
from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD


class PrintRedirector:
    """Redirects print() output to a Tkinter Text widget."""

    def __init__(self, text_widget, root):
        self.text_widget = text_widget
        self.root = root

    def write(self, text):
        self.root.after(0, self._append, text)

    def _append(self, text):
        self.text_widget.config(state="normal")
        self.text_widget.insert("end", text)
        self.text_widget.see("end")
        self.text_widget.config(state="disabled")

    def flush(self):
        pass


class SupplierFinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Supplier Discovery Tool")
        self.root.geometry("950x750")
        self.root.minsize(800, 650)
        self.csv_path = None
        self.selected_items = set()

        self._build_ui()

    def _build_ui(self):
        # --- Input Frame ---
        input_frame = ttk.LabelFrame(self.root, text="Search", padding=10)
        input_frame.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Label(input_frame, text="Material:").grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.material_var = tk.StringVar(value="PET Film")
        ttk.Entry(input_frame, textvariable=self.material_var, width=30).grid(row=0, column=1, padx=(0, 15))

        ttk.Label(input_frame, text="Country:").grid(row=0, column=2, padx=(0, 5), sticky="w")
        self.country_var = tk.StringVar(value="Vietnam")
        ttk.Entry(input_frame, textvariable=self.country_var, width=20).grid(row=0, column=3, padx=(0, 15))

        self.search_btn = ttk.Button(input_frame, text="Search", command=self._on_search)
        self.search_btn.grid(row=0, column=4, padx=(10, 0))

        # --- Log Frame ---
        log_frame = ttk.LabelFrame(self.root, text="Status Log", padding=5)
        log_frame.pack(fill="x", padx=10, pady=5)

        self.log_text = tk.Text(log_frame, height=8, state="disabled", wrap="word", font=("Consolas", 9))
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

        # --- Results Frame ---
        results_frame = ttk.LabelFrame(self.root, text="Results", padding=5)
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Selection buttons row
        sel_frame = ttk.Frame(results_frame)
        sel_frame.pack(fill="x", pady=(0, 5))
        ttk.Button(sel_frame, text="Select All", command=self._select_all).pack(side="left", padx=(0, 5))
        ttk.Button(sel_frame, text="Deselect All", command=self._deselect_all).pack(side="left")
        self.sel_count_label = ttk.Label(sel_frame, text="0 selected")
        self.sel_count_label.pack(side="right")

        # Treeview with checkbox column
        columns = ("check", "name", "website", "emails", "phones")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=10)
        self.tree.heading("check", text="")
        self.tree.heading("name", text="Supplier Name")
        self.tree.heading("website", text="Website")
        self.tree.heading("emails", text="Emails")
        self.tree.heading("phones", text="Phones")
        self.tree.column("check", width=30, stretch=False, anchor="center")
        self.tree.column("name", width=180)
        self.tree.column("website", width=220)
        self.tree.column("emails", width=240)
        self.tree.column("phones", width=160)

        # Click to toggle selection
        self.tree.bind("<ButtonRelease-1>", self._on_row_click)

        tree_scroll = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        # --- Bottom Frame ---
        bottom_frame = ttk.Frame(self.root, padding=5)
        bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.status_label = ttk.Label(bottom_frame, text="Ready")
        self.status_label.pack(side="left")

        self.email_btn = ttk.Button(bottom_frame, text="Email Selected", command=self._open_email_dialog, state="disabled")
        self.email_btn.pack(side="right", padx=(5, 0))

        self.open_csv_btn = ttk.Button(bottom_frame, text="Open CSV", command=self._open_csv, state="disabled")
        self.open_csv_btn.pack(side="right")

        ttk.Button(bottom_frame, text="Load CSV", command=self._load_csv_from_file).pack(side="right", padx=(0, 5))

    # --- Row selection ---

    def _on_row_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return

        values = self.tree.item(item, "values")
        emails = values[3] if len(values) > 3 else ""
        if not emails or emails == "Not Found":
            return  # can't select rows without emails

        if item in self.selected_items:
            self.selected_items.discard(item)
            self.tree.set(item, "check", "")
        else:
            self.selected_items.add(item)
            self.tree.set(item, "check", ">>")

        self._update_sel_count()

    def _select_all(self):
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            emails = values[3] if len(values) > 3 else ""
            if emails and emails != "Not Found":
                self.selected_items.add(item)
                self.tree.set(item, "check", ">>")
        self._update_sel_count()

    def _deselect_all(self):
        for item in self.selected_items:
            self.tree.set(item, "check", "")
        self.selected_items.clear()
        self._update_sel_count()

    def _update_sel_count(self):
        count = len(self.selected_items)
        self.sel_count_label.config(text=f"{count} selected")
        self.email_btn.config(state="normal" if count > 0 else "disabled")

    # --- Search ---

    def _on_search(self):
        material = self.material_var.get().strip()
        country = self.country_var.get().strip()
        if not material or not country:
            return

        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.selected_items.clear()
        self._update_sel_count()

        self.search_btn.config(state="disabled")
        self.open_csv_btn.config(state="disabled")
        self.email_btn.config(state="disabled")
        self.status_label.config(text="Searching...")
        self.csv_path = None

        thread = threading.Thread(target=self._run_search, args=(material, country), daemon=True)
        thread.start()

    def _run_search(self, material, country):
        old_stdout = sys.stdout
        sys.stdout = PrintRedirector(self.log_text, self.root)
        try:
            csv_path = run_procurement_intelligence(material, country)
            self.csv_path = csv_path
            self.root.after(0, self._on_search_done, csv_path)
        except Exception as e:
            self.root.after(0, self._on_search_error, str(e))
        finally:
            sys.stdout = old_stdout

    def _on_search_done(self, csv_path):
        self.search_btn.config(state="normal")
        if csv_path and os.path.exists(csv_path):
            self._load_csv(csv_path)
            self.open_csv_btn.config(state="normal")
            count = len(self.tree.get_children())
            self.status_label.config(text=f"Done — {count} suppliers found")
        else:
            self.status_label.config(text="Done — no results")

    def _on_search_error(self, error_msg):
        self.search_btn.config(state="normal")
        self.status_label.config(text=f"Error: {error_msg}")

    def _load_csv(self, csv_path):
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.tree.insert("", "end", values=(
                        "",
                        row.get("Supplier Name", ""),
                        row.get("Website", ""),
                        row.get("Emails", ""),
                        row.get("Phones", ""),
                    ))
        except Exception:
            pass

    def _load_csv_from_file(self):
        path = filedialog.askopenfilename(
            title="Select CSV",
            filetypes=[("CSV files", "*.csv")],
            initialdir=os.path.dirname(os.path.abspath(__file__)),
        )
        if not path:
            return
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.selected_items.clear()
        self._update_sel_count()
        self.csv_path = path
        self._load_csv(path)
        self.open_csv_btn.config(state="normal")
        count = len(self.tree.get_children())
        self.status_label.config(text=f"Loaded {count} suppliers from file")

    def _open_csv(self):
        if self.csv_path and os.path.exists(self.csv_path):
            os.startfile(self.csv_path)

    # --- Email Dialog ---

    def _open_email_dialog(self):
        if not self.selected_items:
            return

        dlg = tk.Toplevel(self.root)
        dlg.title("Compose Email")
        dlg.geometry("550x480")
        dlg.resizable(False, False)
        dlg.grab_set()

        pad = {"padx": 10, "pady": 3}

        # From
        ttk.Label(dlg, text="From (Gmail):").pack(anchor="w", **pad)
        from_var = tk.StringVar(value=GMAIL_ADDRESS)
        ttk.Entry(dlg, textvariable=from_var, width=50).pack(**pad)

        # App Password
        ttk.Label(dlg, text="App Password:").pack(anchor="w", **pad)
        pass_var = tk.StringVar(value=GMAIL_APP_PASSWORD)
        pass_entry = ttk.Entry(dlg, textvariable=pass_var, width=50, show="*")
        pass_entry.pack(**pad)

        # Subject
        ttk.Label(dlg, text="Subject:").pack(anchor="w", **pad)
        subj_var = tk.StringVar(value="Inquiry about {company_name} products")
        ttk.Entry(dlg, textvariable=subj_var, width=50).pack(**pad)

        # Body
        ttk.Label(dlg, text="Body ({company_name} will be replaced):").pack(anchor="w", **pad)
        body_text = tk.Text(dlg, height=10, wrap="word", font=("Segoe UI", 10))
        body_text.insert("1.0",
            "Dear {company_name},\n\n"
            "We are interested in your products and would like to discuss a potential partnership.\n\n"
            "Could you please share your product catalog and pricing?\n\n"
            "Best regards"
        )
        body_text.pack(fill="x", **pad)

        # Status
        send_status = ttk.Label(dlg, text=f"Will send to {len(self.selected_items)} recipients")
        send_status.pack(anchor="w", **pad)

        # Send button
        send_btn = ttk.Button(dlg, text="Send")

        def _do_send():
            sender = from_var.get().strip()
            password = pass_var.get().strip()
            subject = subj_var.get().strip()
            body = body_text.get("1.0", "end").strip()

            if not sender or not password or not subject or not body:
                messagebox.showwarning("Missing fields", "Please fill in all fields.", parent=dlg)
                return

            # Build recipient list from selected rows
            recipients = []
            for item in self.selected_items:
                values = self.tree.item(item, "values")
                name = values[1]
                emails_str = values[3]
                # Take first email if multiple
                first_email = emails_str.split(",")[0].strip()
                if first_email and first_email != "Not Found":
                    recipients.append({"email": first_email, "company_name": name})

            if not recipients:
                messagebox.showwarning("No emails", "No valid email addresses in selection.", parent=dlg)
                return

            send_btn.config(state="disabled")
            send_status.config(text="Sending...")

            def _send_thread():
                old_stdout = sys.stdout
                sys.stdout = PrintRedirector(self.log_text, self.root)
                try:
                    success, failures = send_bulk_emails(sender, password, recipients, subject, body)
                    msg = f"Done — {success} sent"
                    if failures:
                        msg += f", {len(failures)} failed"
                    self.root.after(0, send_status.config, {"text": msg})
                    self.root.after(0, send_btn.config, {"state": "normal"})
                except Exception as e:
                    self.root.after(0, send_status.config, {"text": f"Error: {e}"})
                    self.root.after(0, send_btn.config, {"state": "normal"})
                finally:
                    sys.stdout = old_stdout

            threading.Thread(target=_send_thread, daemon=True).start()

        send_btn.config(command=_do_send)
        send_btn.pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = SupplierFinderApp(root)
    root.mainloop()
