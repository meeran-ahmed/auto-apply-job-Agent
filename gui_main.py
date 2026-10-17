import os
import sys
import threading
import subprocess
import webbrowser
from pathlib import Path
import yaml
import customtkinter as ctk
from tkinter import filedialog, messagebox


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class OmniSwarmGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Auto Job: Autonomous Multi-Platform Application Agent")
        self.geometry("980x720")
        self.minsize(860, 600)

        # Paths
        self.base_dir = Path(__file__).parent.resolve()
        self.data_dir = self.base_dir / "data_folder"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.config_path = self.data_dir / "config.yaml"
        self.resume_yaml_path = self.data_dir / "plain_text_resume.yaml"
        self.secrets_path = self.data_dir / "secrets.yaml"
        self.resume_pdf_path = self.data_dir / "resume.pdf"
        self.report_md_path = self.data_dir / "output" / "APPLICATIONS_REPORT.md"
        self.success_json_path = self.data_dir / "output" / "success.json"

        self.current_process = None
        self.is_running = False

        self._build_ui()
        self._load_saved_data()

    def _build_ui(self):
        # Grid config
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar navigation
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        logo_title = ctk.CTkLabel(
            self.sidebar,
            text="⚡ Auto Job",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        logo_title.grid(row=0, column=0, padx=20, pady=(24, 6))

        logo_sub = ctk.CTkLabel(
            self.sidebar,
            text="Job Application Agent\nby Meeran Ahmed",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        logo_sub.grid(row=1, column=0, padx=20, pady=(0, 24))

        self.btn_nav_dashboard = ctk.CTkButton(
            self.sidebar, text="⚡ Run & Dashboard",
            command=lambda: self._select_tab("dashboard"),
            height=38, font=ctk.CTkFont(size=14, weight="bold")
        )
        self.btn_nav_dashboard.grid(row=2, column=0, padx=16, pady=8, sticky="ew")

        self.btn_nav_profile = ctk.CTkButton(
            self.sidebar, text="👤 Candidate Profile",
            command=lambda: self._select_tab("profile"),
            height=38, font=ctk.CTkFont(size=14), fg_color="transparent", border_width=1
        )
        self.btn_nav_profile.grid(row=3, column=0, padx=16, pady=8, sticky="ew")

        self.btn_nav_keys = ctk.CTkButton(
            self.sidebar, text="🔑 Free Gemini API Key",
            command=lambda: self._select_tab("keys"),
            height=38, font=ctk.CTkFont(size=14), fg_color="transparent", border_width=1
        )
        self.btn_nav_keys.grid(row=4, column=0, padx=16, pady=8, sticky="ew")

        # Bottom sidebar info
        lbl_info = ctk.CTkLabel(
            self.sidebar,
            text="100% Free & Open Source\nRuns Locally on Your Device",
            font=ctk.CTkFont(size=11), text_color="gray60"
        )
        lbl_info.grid(row=6, column=0, padx=16, pady=16)

        # Main Container
        self.main_container = ctk.CTkFrame(self, corner_radius=12)
        self.main_container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # Tabs Frames
        self.tab_dashboard = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.tab_profile = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.tab_keys = ctk.CTkFrame(self.main_container, fg_color="transparent")

        self._build_dashboard_tab()
        self._build_profile_tab()
        self._build_keys_tab()

        self._select_tab("dashboard")

    def _select_tab(self, name: str):
        self.tab_dashboard.grid_forget()
        self.tab_profile.grid_forget()
        self.tab_keys.grid_forget()

        # Reset nav buttons
        for btn, tab_name in [
            (self.btn_nav_dashboard, "dashboard"),
            (self.btn_nav_profile, "profile"),
            (self.btn_nav_keys, "keys")
        ]:
            if tab_name == name:
                btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], font=ctk.CTkFont(weight="bold"))
            else:
                btn.configure(fg_color="transparent", font=ctk.CTkFont(weight="normal"))

        if name == "dashboard":
            self.tab_dashboard.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        elif name == "profile":
            self.tab_profile.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        elif name == "keys":
            self.tab_keys.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)

    def _build_dashboard_tab(self):
        self.tab_dashboard.grid_columnconfigure(0, weight=1)
        self.tab_dashboard.grid_rowconfigure(3, weight=1)

        # Header card
        header_frame = ctk.CTkFrame(self.tab_dashboard, corner_radius=8)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 14))

        lbl_head = ctk.CTkLabel(
            header_frame,
            text="🚀 Swarm Control Center",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl_head.pack(anchor="w", padx=16, pady=(12, 4))

        lbl_desc = ctk.CTkLabel(
            header_frame,
            text="Autonomous browser agents scout tech positions, auto-populate your resume, and submit ATS applications.",
            font=ctk.CTkFont(size=12), text_color="gray70"
        )
        lbl_desc.pack(anchor="w", padx=16, pady=(0, 12))

        # Mode Selection
        mode_frame = ctk.CTkFrame(self.tab_dashboard)
        mode_frame.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        mode_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(mode_frame, text="Application Source:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=16, pady=12, sticky="w"
        )

        self.mode_var = ctk.StringVar(value="universal")
        self.opt_mode = ctk.CTkOptionMenu(
            mode_frame,
            values=["universal", "swarm", "excel", "outreach"],
            variable=self.mode_var,
            command=self._on_mode_change
        )
        self.opt_mode.grid(row=0, column=1, padx=12, pady=12, sticky="w")

        # Portal Selection (for Universal Mode)
        self.lbl_portal = ctk.CTkLabel(mode_frame, text="Target Portal:", font=ctk.CTkFont(weight="bold"))
        self.lbl_portal.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="w")

        self.portal_var = ctk.StringVar(value="all")
        self.opt_portal = ctk.CTkOptionMenu(
            mode_frame,
            values=["all", "linkedin", "naukri", "indeed", "cutshort", "internshala", "wellfound"],
            variable=self.portal_var
        )
        self.opt_portal.grid(row=1, column=1, padx=12, pady=(0, 12), sticky="w")

        # Chrome Live Debugging Session Control
        self.chrome_status_frame = ctk.CTkFrame(mode_frame, fg_color="transparent")
        self.chrome_status_frame.grid(row=2, column=0, columnspan=3, padx=16, pady=(0, 12), sticky="ew")

        self.btn_launch_chrome = ctk.CTkButton(
            self.chrome_status_frame,
            text="🌐 Launch Debug Chrome (Port 9222)",
            fg_color="#3B8ED0", hover_color="#1F6AA5",
            width=260, height=32,
            command=self._launch_chrome_debugging
        )
        self.btn_launch_chrome.pack(side="left", padx=(0, 12))

        self.lbl_chrome_status = ctk.CTkLabel(
            self.chrome_status_frame,
            text="Checking port 9222...",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        self.lbl_chrome_status.pack(side="left")

        # Custom File Picker (for Excel mode)
        self.lbl_file = ctk.CTkLabel(mode_frame, text="Spreadsheet File:")
        self.entry_file = ctk.CTkEntry(mode_frame, placeholder_text="Select jobs.xlsx or jobs.csv...")
        self.btn_browse = ctk.CTkButton(mode_frame, text="Browse...", width=90, command=self._browse_file)

        # Limit
        ctk.CTkLabel(mode_frame, text="Batch Limit:").grid(row=3, column=0, padx=16, pady=(0, 12), sticky="w")
        self.entry_limit = ctk.CTkEntry(mode_frame, width=90)
        self.entry_limit.insert(0, "10")
        self.entry_limit.grid(row=3, column=1, padx=12, pady=(0, 12), sticky="w")

        # Initial mode check & Chrome probe
        self.after(500, self._check_chrome_status)

        # Action Buttons & Progress
        act_frame = ctk.CTkFrame(self.tab_dashboard, fg_color="transparent")
        act_frame.grid(row=2, column=0, sticky="ew", pady=(0, 12))

        self.btn_start = ctk.CTkButton(
            act_frame, text="▶ START AUTONOMOUS SWARM",
            fg_color="#2EA043", hover_color="#238636",
            height=44, font=ctk.CTkFont(size=15, weight="bold"),
            command=self._start_swarm
        )
        self.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_stop = ctk.CTkButton(
            act_frame, text="⏹ STOP",
            fg_color="#DA3633", hover_color="#B62324",
            height=44, width=110, font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled", command=self._stop_swarm
        )
        self.btn_stop.pack(side="right")

        # Live Console Output Box
        console_frame = ctk.CTkFrame(self.tab_dashboard)
        console_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        console_frame.grid_columnconfigure(0, weight=1)
        console_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            console_frame, text="📋 Live Execution Log:", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, padx=12, pady=(8, 4), sticky="w")

        self.txt_console = ctk.CTkTextbox(console_frame, font=ctk.CTkFont(family="Consolas", size=11))
        self.txt_console.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="nsew")

        # Bottom reports row
        bottom_row = ctk.CTkFrame(self.tab_dashboard, fg_color="transparent")
        bottom_row.grid(row=4, column=0, sticky="ew")

        btn_view_report = ctk.CTkButton(
            bottom_row, text="📄 Open Applications Report",
            command=self._open_report, height=32
        )
        btn_view_report.pack(side="left", padx=(0, 8))

        btn_view_outreach = ctk.CTkButton(
            bottom_row, text="🤝 Open Referral Matrix",
            command=self._open_outreach_report, height=32, fg_color="#1F6AA5"
        )
        btn_view_outreach.pack(side="left", padx=(0, 8))

        btn_view_json = ctk.CTkButton(
            bottom_row, text="💾 Open Ledger (JSON)",
            command=self._open_json, height=32, fg_color="gray30"
        )
        btn_view_json.pack(side="left")

    def _build_profile_tab(self):
        self.tab_profile.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(
            self.tab_profile, text="Candidate Profile & Assets",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl.pack(anchor="w", pady=(0, 14))

        # Resume Upload Card
        res_card = ctk.CTkFrame(self.tab_profile)
        res_card.pack(fill="x", pady=(0, 14), padx=4)

        ctk.CTkLabel(res_card, text="PDF Resume:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        
        row_res = ctk.CTkFrame(res_card, fg_color="transparent")
        row_res.pack(fill="x", padx=16, pady=(0, 12))
        
        self.lbl_resume_status = ctk.CTkLabel(row_res, text="No resume uploaded yet", text_color="gray70")
        self.lbl_resume_status.pack(side="left")

        btn_upload_res = ctk.CTkButton(row_res, text="Upload Resume PDF...", command=self._upload_resume_pdf, width=160)
        btn_upload_res.pack(side="right")

        # Contact Details Card
        info_card = ctk.CTkFrame(self.tab_profile)
        info_card.pack(fill="x", pady=(0, 14), padx=4)
        info_card.grid_columnconfigure(1, weight=1)

        fields = [
            ("First Name:", "entry_fname"),
            ("Last Name / Surname:", "entry_lname"),
            ("Email Address:", "entry_email"),
            ("Phone Number (with + prefix):", "entry_phone"),
            ("City & Country:", "entry_city"),
            ("Portfolio Website URL:", "entry_portfolio"),
            ("LinkedIn Profile URL:", "entry_linkedin"),
            ("GitHub Profile URL:", "entry_github")
        ]

        for idx, (label_text, attr_name) in enumerate(fields):
            ctk.CTkLabel(info_card, text=label_text).grid(row=idx, column=0, padx=16, pady=6, sticky="w")
            entry = ctk.CTkEntry(info_card)
            entry.grid(row=idx, column=1, padx=16, pady=6, sticky="ew")
            setattr(self, attr_name, entry)

        btn_save_profile = ctk.CTkButton(
            self.tab_profile, text="💾 Save Candidate Profile",
            height=40, font=ctk.CTkFont(size=14, weight="bold"),
            command=self._save_profile
        )
        btn_save_profile.pack(fill="x", padx=4, pady=8)

    def _build_keys_tab(self):
        self.tab_keys.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(
            self.tab_keys, text="🔑 Google Gemini 1.5 Flash API Key",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl.pack(anchor="w", pady=(0, 8))

        lbl_sub = ctk.CTkLabel(
            self.tab_keys,
            text="Used to answer employer screening questions and match resume skills in milliseconds.\n100% Free with zero credit card required.",
            font=ctk.CTkFont(size=13), text_color="gray70", justify="left"
        )
        lbl_sub.pack(anchor="w", pady=(0, 16))

        card = ctk.CTkFrame(self.tab_keys)
        card.pack(fill="x", padx=4, pady=(0, 14))

        ctk.CTkLabel(card, text="Gemini API Key:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=16, pady=(16, 4))
        
        self.entry_key = ctk.CTkEntry(card, show="*", placeholder_text="AIzaSy...")
        self.entry_key.pack(fill="x", padx=16, pady=(0, 12))

        btn_show = ctk.CTkButton(
            card, text="Toggle Show/Hide", width=120, height=28, fg_color="gray30",
            command=self._toggle_key_visibility
        )
        btn_show.pack(anchor="w", padx=16, pady=(0, 16))

        btn_get_free = ctk.CTkButton(
            self.tab_keys, text="🌐 Get 100% Free Gemini Key from Google AI Studio ↗",
            fg_color="#1F6AA5", height=38, command=lambda: webbrowser.open("https://aistudio.google.com/app/apikey")
        )
        btn_get_free.pack(fill="x", padx=4, pady=(0, 12))

        btn_save_key = ctk.CTkButton(
            self.tab_keys, text="💾 Save API Key",
            height=40, font=ctk.CTkFont(size=14, weight="bold"),
            command=self._save_api_key
        )
        btn_save_key.pack(fill="x", padx=4, pady=8)

    def _toggle_key_visibility(self):
        if self.entry_key.cget("show") == "*":
            self.entry_key.configure(show="")
        else:
            self.entry_key.configure(show="*")

    def _on_mode_change(self, choice: str):
        if choice == "universal":
            self.lbl_portal.grid()
            self.opt_portal.grid()
            self.chrome_status_frame.grid()
            self.lbl_file.grid_remove()
            self.entry_file.grid_remove()
            self.btn_browse.grid_remove()
            self._check_chrome_status()
        elif choice == "excel":
            self.lbl_portal.grid_remove()
            self.opt_portal.grid_remove()
            self.chrome_status_frame.grid_remove()
            self.lbl_file.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="w")
            self.entry_file.grid(row=2, column=1, padx=12, pady=(0, 12), sticky="ew")
            self.btn_browse.grid(row=2, column=2, padx=(0, 16), pady=(0, 12))
        else:
            self.lbl_portal.grid_remove()
            self.opt_portal.grid_remove()
            self.chrome_status_frame.grid_remove()
            self.lbl_file.grid_remove()
            self.entry_file.grid_remove()
            self.btn_browse.grid_remove()

    def _check_chrome_status(self):
        def probe():
            import requests
            try:
                resp = requests.get("http://127.0.0.1:9222/json/version", timeout=1.5)
                if resp.status_code == 200:
                    self.after(0, lambda: self.lbl_chrome_status.configure(
                        text="🟢 Connected: Chrome Live Session (meeranahmed17@gmail.com)",
                        text_color="#2EA043"
                    ))
                    return
            except Exception:
                pass
            self.after(0, lambda: self.lbl_chrome_status.configure(
                text="⚪ Chrome not running on port 9222 (Click button to launch)",
                text_color="gray70"
            ))
        threading.Thread(target=probe, daemon=True).start()

    def _launch_chrome_debugging(self):
        bat_file = self.base_dir / "start_chrome_debugging.bat"
        if bat_file.exists():
            subprocess.Popen([str(bat_file)], shell=True)
            self._log_console("🌐 Started Chrome with debugging port 9222...")
            self.after(2000, self._check_chrome_status)
        else:
            messagebox.showerror("Error", "start_chrome_debugging.bat not found!")

    def _browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Job Spreadsheet",
            filetypes=[("Excel & CSV files", "*.xlsx *.xls *.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.entry_file.delete(0, "end")
            self.entry_file.insert(0, file_path)

    def _upload_resume_pdf(self):
        file_path = filedialog.askopenfilename(
            title="Select Resume PDF",
            filetypes=[("PDF files", "*.pdf")]
        )
        if file_path:
            import shutil
            shutil.copyfile(file_path, str(self.resume_pdf_path))
            size_kb = round(os.path.getsize(self.resume_pdf_path) / 1024, 1)
            self.lbl_resume_status.configure(
                text=f"✅ Resume Active: {Path(file_path).name} ({size_kb} KB)",
                text_color="#2EA043"
            )
            messagebox.showinfo("Success", "Resume PDF updated successfully!")

    def _load_saved_data(self):
        # 1. Resume status
        if self.resume_pdf_path.exists():
            size_kb = round(os.path.getsize(self.resume_pdf_path) / 1024, 1)
            self.lbl_resume_status.configure(
                text=f"✅ Resume Active: resume.pdf ({size_kb} KB)",
                text_color="#2EA043"
            )

        # 2. Plain text resume
        if self.resume_yaml_path.exists():
            try:
                with open(self.resume_yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                pi = data.get("personal_information", {})
                self.entry_fname.insert(0, pi.get("name", ""))
                self.entry_lname.insert(0, pi.get("surname", ""))
                self.entry_email.insert(0, pi.get("email", ""))
                self.entry_phone.insert(0, f"{pi.get('phone_prefix', '')} {pi.get('phone', '')}".strip())
                self.entry_city.insert(0, f"{pi.get('city', '')}, {pi.get('country', '')}".strip(" ,"))
                self.entry_portfolio.insert(0, "https://meeran-portfolio.antideploy.app")
                self.entry_linkedin.insert(0, pi.get("linkedin", ""))
                self.entry_github.insert(0, pi.get("github", ""))
            except Exception:
                pass

        # 3. Secrets
        if self.secrets_path.exists():
            try:
                with open(self.secrets_path, "r", encoding="utf-8") as f:
                    sec = yaml.safe_load(f) or {}
                key = sec.get("llm_api_key", "")
                if key:
                    self.entry_key.insert(0, key)
            except Exception:
                pass

        # 4. Default excel file
        default_excel = self.data_dir / "jobs.xlsx"
        if default_excel.exists():
            self.entry_file.insert(0, str(default_excel))

    def _save_profile(self):
        try:
            profile = {
                "personal_information": {
                    "name": self.entry_fname.get().strip(),
                    "surname": self.entry_lname.get().strip(),
                    "email": self.entry_email.get().strip(),
                    "phone": self.entry_phone.get().replace("+91", "").strip(),
                    "phone_prefix": "+91" if "+91" in self.entry_phone.get() else "",
                    "city": self.entry_city.get().split(",")[0].strip(),
                    "country": "India",
                    "portfolio": self.entry_portfolio.get().strip(),
                    "linkedin": self.entry_linkedin.get().strip(),
                    "github": self.entry_github.get().strip()
                }
            }
            with open(self.resume_yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(profile, f, indent=2)
            messagebox.showinfo("Success", "Candidate profile saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save profile: {e}")

    def _save_api_key(self):
        key = self.entry_key.get().strip()
        if not key:
            messagebox.showwarning("Warning", "Please enter a valid Gemini API key.")
            return
        try:
            with open(self.secrets_path, "w", encoding="utf-8") as f:
                yaml.dump({"llm_api_key": key}, f)
            messagebox.showinfo("Success", "Gemini API key saved securely!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save API key: {e}")

    def _log_console(self, text: str):
        self.txt_console.insert("end", text + "\n")
        self.txt_console.see("end")

    def _start_swarm(self):
        if self.is_running:
            return

        mode = self.mode_var.get()
        limit = self.entry_limit.get().strip() or "50"
        file_arg = self.entry_file.get().strip()

        cmd = [sys.executable, str(self.base_dir / "swarm_main.py"), "--mode", mode, "--limit", limit]
        if mode == "universal":
            portal = self.portal_var.get().strip()
            cmd.extend(["--portal", portal])
        elif mode == "excel" and file_arg:
            cmd.extend(["--file", file_arg])

        self.is_running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.txt_console.delete("1.0", "end")
        self._log_console(f"🚀 Initializing OmniSwarm ({mode.upper()} mode, limit: {limit})...")

        def run_thread():
            try:
                self.current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=str(self.base_dir)
                )

                for line in iter(self.current_process.stdout.readline, ""):
                    if not self.is_running:
                        break
                    if line:
                        self.after(0, self._log_console, line.strip())

                self.current_process.stdout.close()
                self.current_process.wait()
            except Exception as e:
                self.after(0, self._log_console, f"❌ Process error: {e}")
            finally:
                self.after(0, self._on_finish)

        threading.Thread(target=run_thread, daemon=True).start()

    def _stop_swarm(self):
        if self.current_process and self.is_running:
            self._log_console("⏹ Stopping process...")
            self.current_process.terminate()
            self.is_running = False

    def _on_finish(self):
        self.is_running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self._log_console("✨ Run complete! Executive report updated.")

    def _open_report(self):
        if self.report_md_path.exists():
            webbrowser.open(str(self.report_md_path))
        else:
            messagebox.showinfo("Info", "No report generated yet. Run the swarm first!")

    def _open_outreach_report(self):
        outreach_path = self.output_dir / "REFERRAL_OUTREACH.md"
        if outreach_path.exists():
            webbrowser.open(str(outreach_path))
        else:
            messagebox.showinfo("Info", "No referral outreach matrix generated yet. Select 'outreach' mode and click start!")

    def _open_json(self):
        if self.success_json_path.exists():
            webbrowser.open(str(self.success_json_path))
        else:
            messagebox.showinfo("Info", "No JSON ledger found yet.")


if __name__ == "__main__":
    app = OmniSwarmGUI()
    app.mainloop()
