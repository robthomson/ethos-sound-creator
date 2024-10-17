#!/usr/bin/env python3
"""Ethos Sound Creator - GUI utility for generating TTS audio files."""

import codecs
import csv
import json
import os
import sys
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

# ── Paths ──────────────────────────────────────────────────────────────────

APPDATA = os.path.join(os.environ.get("APPDATA", str(Path.home())), "EthosSoundCreator")
SETTINGS_FILE = os.path.join(APPDATA, "settings.json")
SOUNDS_FILE = os.path.join(APPDATA, "sounds.json")

# ── Voice catalogue (sourced from rotorflight-lua-ethos-suite generate-all.bat) ──
#
# Each language maps to a list of (display_label, google_voice_code) pairs.
# Ordering matches the official sound packs.

LANGUAGE_VOICES: dict[str, list[tuple[str, str]]] = {
    "English": [
        ("US Female (Wavenet F)",  "en-US-Wavenet-F"),
        ("UK Female (Neural2 A)",  "en-GB-Neural2-A"),
    ],
    "French": [
        ("Female / Femme (Neural2 F)", "fr-FR-Neural2-F"),
        ("Male / Homme (Standard B)",  "fr-FR-Standard-B"),
    ],
    "German": [
        ("Female (Wavenet E)",     "de-DE-Wavenet-E"),
    ],
    "Spanish": [
        ("Female (Wavenet C)",     "es-ES-Wavenet-C"),
    ],
    "Italian": [
        ("Female (Wavenet B)",     "it-IT-Wavenet-B"),
    ],
    "Dutch": [
        ("Female (Standard A)",    "nl-NL-Standard-A"),
    ],
    "Portuguese (Brazil)": [
        ("Female (Wavenet A)",     "pt-BR-Wavenet-A"),
    ],
    "Norwegian": [
        ("Female (Standard E)",    "nb-NO-Standard-E"),
    ],
    "Czech": [
        ("Female (Wavenet A)",     "cs-CZ-Wavenet-A"),
    ],
    "Polish": [
        ("Female (Wavenet A)",     "cs-CZ-Wavenet-A"),
    ],
    "Chinese (Simplified)": [
        ("Female (Wavenet A)",     "cmn-CN-Wavenet-A"),
    ],
}

LANGUAGE_NAMES = list(LANGUAGE_VOICES.keys())


def _voice_labels_for(language: str) -> list[str]:
    return [label for label, _ in LANGUAGE_VOICES.get(language, [])]


def _voice_code(language: str, label: str) -> str:
    for lbl, code in LANGUAGE_VOICES.get(language, []):
        if lbl == label:
            return code
    return ""


def _language_for_code(voice_code: str) -> str:
    for lang, voices in LANGUAGE_VOICES.items():
        for _, code in voices:
            if code == voice_code:
                return lang
    return "English"


def _label_for_code(language: str, voice_code: str) -> str:
    for lbl, code in LANGUAGE_VOICES.get(language, []):
        if code == voice_code:
            return lbl
    voices = LANGUAGE_VOICES.get(language, [])
    return voices[0][0] if voices else ""

DEFAULT_SETTINGS: dict = {
    "api_key": "",
    "language": "English",
    "voice": "en-US-Wavenet-F",
    "speed": 1.0,
    "output_dir": str(Path.home() / "EthosSounds"),
}

# ── Persistence helpers ────────────────────────────────────────────────────


def _ensure_appdata() -> None:
    os.makedirs(APPDATA, exist_ok=True)


def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as fh:
                return {**DEFAULT_SETTINGS, **json.load(fh)}
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings_file(settings: dict) -> None:
    _ensure_appdata()
    with open(SETTINGS_FILE, "w") as fh:
        json.dump(settings, fh, indent=2)


def load_sounds() -> list:
    if os.path.exists(SOUNDS_FILE):
        try:
            with open(SOUNDS_FILE, "r") as fh:
                return json.load(fh)
        except Exception:
            pass
    return []


def save_sounds_file(sounds: list) -> None:
    _ensure_appdata()
    with open(SOUNDS_FILE, "w") as fh:
        json.dump(sounds, fh, indent=2)


# ── Audio helper ───────────────────────────────────────────────────────────


def trim_trailing_silence(audio, threshold: float = 0.001):
    """Remove trailing silence (mirrors sox reverse-silence-reverse pattern)."""
    import numpy as np

    if audio.ndim > 1:
        audio = audio[:, 0]
    mask = np.abs(audio) > threshold
    if not mask.any():
        return audio
    last = len(mask) - mask[::-1].argmax() - 1
    return audio[: last + 1]


# ── Add / Edit dialog ──────────────────────────────────────────────────────


class SoundDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str = "Add Sound", sound: dict | None = None):
        super().__init__(parent)
        self.title(title)
        self.geometry("560x200")
        self.resizable(False, False)
        self.grab_set()
        self.lift()
        self.focus_force()
        self.result: dict | None = None

        p = dict(padx=14, pady=9)

        ctk.CTkLabel(self, text="Output filename:", anchor="e", width=140).grid(
            row=0, column=0, sticky="e", **p
        )
        self._fn = tk.StringVar(value=sound["filename"] if sound else "")
        fn_entry = ctk.CTkEntry(
            self,
            textvariable=self._fn,
            width=350,
            placeholder_text="e.g. armed.wav  or  audio/alerts/armed.wav",
        )
        fn_entry.grid(row=0, column=1, sticky="ew", **p)

        ctk.CTkLabel(self, text="Text to speak:", anchor="e", width=140).grid(
            row=1, column=0, sticky="e", **p
        )
        self._tx = tk.StringVar(value=sound["text"] if sound else "")
        ctk.CTkEntry(
            self, textvariable=self._tx, width=350, placeholder_text="e.g. Armed!"
        ).grid(row=1, column=1, sticky="ew", **p)

        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.grid(row=2, column=0, columnspan=2, pady=12)
        ctk.CTkButton(bf, text="OK", width=110, command=self._ok).pack(
            side="left", padx=6
        )
        ctk.CTkButton(
            bf,
            text="Cancel",
            width=110,
            fg_color="#444",
            hover_color="#555",
            command=self.destroy,
        ).pack(side="left", padx=6)

        self.columnconfigure(1, weight=1)
        self.bind("<Return>", lambda _: self._ok())
        self.bind("<Escape>", lambda _: self.destroy())
        fn_entry.focus()

    def _ok(self) -> None:
        fn = self._fn.get().strip().replace("\\", "/").lstrip("/")
        tx = self._tx.get().strip()
        if not fn or not tx:
            messagebox.showerror("Missing fields", "Both fields are required.", parent=self)
            return
        self.result = {"filename": fn, "text": tx}
        self.destroy()


# ── Generation worker thread ───────────────────────────────────────────────


class GeneratorThread(threading.Thread):
    def __init__(self, settings, sounds, skip_existing, cb_progress, cb_log, cb_done):
        super().__init__(daemon=True)
        self.settings = settings
        self.sounds = sounds
        self.skip_existing = skip_existing
        self.cb_progress = cb_progress
        self.cb_log = cb_log
        self.cb_done = cb_done
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        try:
            import soundfile as sf  # noqa: F401
        except ImportError:
            self.cb_log("ERROR: 'soundfile' not installed.")
            self.cb_log("  Run:  pip install soundfile numpy")
            self.cb_done(False)
            return

        try:
            from google.api_core.client_options import ClientOptions
            from google.cloud import texttospeech
        except ImportError:
            self.cb_log("ERROR: 'google-cloud-texttospeech' not installed.")
            self.cb_log("  Run:  pip install google-cloud-texttospeech")
            self.cb_done(False)
            return

        import soundfile as sf

        api_key = self.settings.get("api_key", "").strip()
        if not api_key:
            self.cb_log("ERROR: No API key configured — set it in Settings.")
            self.cb_done(False)
            return

        voice_code = self.settings["voice"]
        speed = float(self.settings["speed"])
        output_dir = self.settings["output_dir"]

        try:
            client = texttospeech.TextToSpeechClient(
                client_options=ClientOptions(api_key=api_key)
            )
            voice_params = texttospeech.VoiceSelectionParams(
                language_code="-".join(voice_code.split("-")[:2]),
                name=voice_code,
            )
            audio_cfg = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                speaking_rate=speed,
            )
        except Exception as exc:
            self.cb_log(f"ERROR setting up TTS client: {exc}")
            self.cb_done(False)
            return

        total = len(self.sounds)
        done = errors = skipped = 0

        for i, sound in enumerate(self.sounds):
            if self._stop.is_set():
                self.cb_log("Stopped by user.")
                break

            fn = sound["filename"].replace("\\", "/").lstrip("/")
            text = sound["text"]
            out_path = os.path.join(output_dir, fn)

            if self.skip_existing and os.path.exists(out_path):
                self.cb_log(f"  skip    {fn}")
                skipped += 1
                self.cb_progress(i + 1, total)
                continue

            self.cb_log(f'  gen     {fn}  ←  "{text}"')
            try:
                parent_dir = os.path.dirname(out_path)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)

                response = client.synthesize_speech(
                    input=texttospeech.SynthesisInput(text=text),
                    voice=voice_params,
                    audio_config=audio_cfg,
                )

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(response.audio_content)
                    tmp_path = tmp.name

                audio_data, _ = sf.read(tmp_path, dtype="float32")
                os.unlink(tmp_path)
                audio_data = trim_trailing_silence(audio_data)
                sf.write(out_path, audio_data, 16000, subtype="ALAW")

                self.cb_log(f"  done    {fn}")
                done += 1

            except Exception as exc:
                self.cb_log(f"  ERROR   {fn}: {exc}")
                errors += 1

            self.cb_progress(i + 1, total)

        parts = [f"{done} generated"]
        if skipped:
            parts.append(f"{skipped} skipped")
        if errors:
            parts.append(f"{errors} errors")
        self.cb_log("\nFinished: " + ", ".join(parts))
        self.cb_done(True)


# ── Main application ───────────────────────────────────────────────────────


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Ethos Sound Creator")
        self.geometry("960x720")
        self.minsize(720, 520)

        self._settings = load_settings()
        self._sounds = load_sounds()
        self._gen_thread: GeneratorThread | None = None

        self._build_ui()
        self._populate_settings()
        self._refresh_tree()

    # ── UI construction ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=(12, 0))
        for name in ("Settings", "Sound List", "Generate"):
            self.tabs.add(name)
        self._build_settings_tab(self.tabs.tab("Settings"))
        self._build_list_tab(self.tabs.tab("Sound List"))
        self._build_gen_tab(self.tabs.tab("Generate"))
        self._build_footer()

    # ── Footer ────────────────────────────────────────────────────────────

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, height=32, fg_color="#1a1a1a", corner_radius=0)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        ctk.CTkButton(
            footer, text="Help & Documentation",
            width=160, height=22, font=("Segoe UI", 11),
            fg_color="transparent", hover_color="#2a2a2a", text_color="#888",
            command=self._open_repo,
        ).pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            footer, text="Setup Guide",
            width=100, height=22, font=("Segoe UI", 11),
            fg_color="transparent", hover_color="#2a2a2a", text_color="#888",
            command=self._open_setup_guide,
        ).pack(side="left")

        ctk.CTkLabel(
            footer, text="github.com/robthomson/ethos-sound-creator",
            font=("Segoe UI", 10), text_color="#444",
        ).pack(side="right", padx=12)

    def _open_repo(self) -> None:
        import webbrowser
        webbrowser.open("https://github.com/robthomson/ethos-sound-creator/")

    # ── Settings tab ──────────────────────────────────────────────────────

    def _build_settings_tab(self, parent) -> None:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=36, pady=28)
        frame.columnconfigure(1, weight=1)

        def label(row, text):
            ctk.CTkLabel(frame, text=text, anchor="e", width=160).grid(
                row=row, column=0, sticky="e", padx=(0, 14), pady=11
            )

        # API key
        label(0, "Google API Key:")
        self._api_var = tk.StringVar()
        self._api_entry = ctk.CTkEntry(frame, textvariable=self._api_var, show="●", width=360)
        self._api_entry.grid(row=0, column=1, sticky="ew", pady=11)
        key_btns = ctk.CTkFrame(frame, fg_color="transparent")
        key_btns.grid(row=0, column=2, padx=(10, 0))
        self._show_btn = ctk.CTkButton(
            key_btns, text="Show", width=72, command=self._toggle_key_vis
        )
        self._show_btn.pack(side="left", padx=2)
        ctk.CTkButton(key_btns, text="Test", width=72, command=self._test_key).pack(
            side="left", padx=2
        )
        ctk.CTkButton(
            key_btns, text="? Guide", width=72, fg_color="#444", hover_color="#555",
            command=self._open_setup_guide,
        ).pack(side="left", padx=2)

        # Language
        label(1, "Language:")
        self._lang_cb = ctk.CTkComboBox(
            frame, values=LANGUAGE_NAMES, width=360, command=self._on_language_change
        )
        self._lang_cb.grid(row=1, column=1, sticky="ew", pady=11)

        # Voice (populated dynamically when language changes)
        label(2, "Voice:")
        self._voice_cb = ctk.CTkComboBox(frame, values=[], width=360)
        self._voice_cb.grid(row=2, column=1, sticky="ew", pady=11)

        # Speed
        label(3, "Speaking speed:")
        speed_row = ctk.CTkFrame(frame, fg_color="transparent")
        speed_row.grid(row=3, column=1, sticky="ew", pady=11)
        ctk.CTkLabel(speed_row, text="0.5×", text_color="#888").pack(side="left")
        self._speed_sl = ctk.CTkSlider(
            speed_row, from_=0.5, to=2.0, number_of_steps=30, command=self._on_speed
        )
        self._speed_sl.pack(side="left", fill="x", expand=True, padx=6)
        ctk.CTkLabel(speed_row, text="2.0×", text_color="#888").pack(side="left")
        self._speed_lbl = ctk.CTkLabel(speed_row, text="1.0×", width=52, anchor="w")
        self._speed_lbl.pack(side="left", padx=(8, 0))

        # Output dir
        label(4, "Output directory:")
        self._outdir_var = tk.StringVar()
        ctk.CTkEntry(frame, textvariable=self._outdir_var, width=360).grid(
            row=4, column=1, sticky="ew", pady=11
        )
        ctk.CTkButton(frame, text="Browse…", width=82, command=self._browse_out).grid(
            row=4, column=2, padx=(10, 0)
        )

        ctk.CTkButton(frame, text="Save Settings", width=140, command=self._save_settings).grid(
            row=5, column=1, sticky="e", pady=(24, 0)
        )

    def _on_language_change(self, language: str = "") -> None:
        lang = self._lang_cb.get()
        labels = _voice_labels_for(lang)
        self._voice_cb.configure(values=labels)
        if labels:
            self._voice_cb.set(labels[0])

    def _toggle_key_vis(self) -> None:
        if self._api_entry.cget("show"):
            self._api_entry.configure(show="")
            self._show_btn.configure(text="Hide")
        else:
            self._api_entry.configure(show="●")
            self._show_btn.configure(text="Show")

    def _on_speed(self, v) -> None:
        self._speed_lbl.configure(text=f"{v:.1f}×")

    def _browse_out(self) -> None:
        d = filedialog.askdirectory(title="Select output directory")
        if d:
            self._outdir_var.set(d)

    def _populate_settings(self) -> None:
        s = self._settings
        self._api_var.set(s.get("api_key", ""))

        voice = s.get("voice", DEFAULT_SETTINGS["voice"])
        language = s.get("language") or _language_for_code(voice)
        self._lang_cb.set(language)
        labels = _voice_labels_for(language)
        self._voice_cb.configure(values=labels)
        self._voice_cb.set(_label_for_code(language, voice))

        speed = float(s.get("speed", 1.0))
        self._speed_sl.set(speed)
        self._speed_lbl.configure(text=f"{speed:.1f}×")
        self._outdir_var.set(s.get("output_dir", DEFAULT_SETTINGS["output_dir"]))

    def _settings_from_ui(self) -> dict:
        language = self._lang_cb.get()
        voice = _voice_code(language, self._voice_cb.get())
        return {
            "api_key": self._api_var.get().strip(),
            "language": language,
            "voice": voice,
            "speed": round(self._speed_sl.get(), 2),
            "output_dir": self._outdir_var.get().strip(),
        }

    def _save_settings(self) -> None:
        self._settings.update(self._settings_from_ui())
        save_settings_file(self._settings)
        messagebox.showinfo("Saved", "Settings saved.", parent=self)

    def _open_setup_guide(self) -> None:
        import webbrowser
        guide = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SETUP_GOOGLE_KEY.md")
        if os.path.exists(guide):
            webbrowser.open(f"file:///{guide.replace(os.sep, '/')}")
        else:
            webbrowser.open(
                "https://github.com/robthomson/ethos-sound-creator/blob/main/SETUP_GOOGLE_KEY.md"
            )

    def _test_key(self) -> None:
        api_key = self._api_var.get().strip()
        if not api_key:
            messagebox.showwarning("No key", "Enter an API key first.", parent=self)
            return

        def _run():
            try:
                from google.api_core.client_options import ClientOptions
                from google.cloud import texttospeech

                client = texttospeech.TextToSpeechClient(
                    client_options=ClientOptions(api_key=api_key)
                )
                client.list_voices(language_code="en-US")
                self.after(0, lambda: messagebox.showinfo("Valid", "API key is valid.", parent=self))
            except Exception as exc:
                err = str(exc)
                self.after(
                    0,
                    lambda: messagebox.showerror("Failed", f"API key test failed:\n\n{err}", parent=self),
                )

        threading.Thread(target=_run, daemon=True).start()

    # ── Sound list tab ─────────────────────────────────────────────────────

    def _build_list_tab(self, parent) -> None:
        tb = ctk.CTkFrame(parent, fg_color="transparent")
        tb.pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkButton(tb, text="+ Add", width=80, command=self._add).pack(side="left", padx=2)
        ctk.CTkButton(tb, text="Edit", width=80, command=self._edit).pack(side="left", padx=2)
        ctk.CTkButton(tb, text="Delete", width=80, fg_color="#7a2a2a", hover_color="#963535",
                      command=self._delete).pack(side="left", padx=2)

        ctk.CTkFrame(tb, width=1, height=24, fg_color="#555").pack(side="left", padx=10)

        ctk.CTkButton(tb, text="Import CSV", width=102, command=self._import_csv).pack(
            side="left", padx=2
        )
        ctk.CTkButton(tb, text="Import JSON", width=102, command=self._import_json).pack(
            side="left", padx=2
        )
        ctk.CTkButton(tb, text="Export CSV", width=102, command=self._export_csv).pack(
            side="left", padx=2
        )
        ctk.CTkButton(tb, text="Clear All", width=90, fg_color="#444", hover_color="#555",
                      command=self._clear_all).pack(side="right", padx=2)

        tree_wrap = ctk.CTkFrame(parent)
        tree_wrap.pack(fill="both", expand=True, padx=10, pady=4)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "ESC.Treeview",
            background="#1e1e1e",
            foreground="#d4d4d4",
            rowheight=26,
            fieldbackground="#1e1e1e",
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "ESC.Treeview.Heading",
            background="#252525",
            foreground="#999",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "ESC.Treeview",
            background=[("selected", "#264f78")],
            foreground=[("selected", "white")],
        )

        self._tree = ttk.Treeview(
            tree_wrap,
            style="ESC.Treeview",
            columns=("filename", "text"),
            show="headings",
            selectmode="browse",
        )
        self._tree.heading("filename", text="Output Filename")
        self._tree.heading("text", text="Text to Speak")
        self._tree.column("filename", width=290, minwidth=100, stretch=False)
        self._tree.column("text", width=520, minwidth=150)

        vsb = ttk.Scrollbar(tree_wrap, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._tree.bind("<Double-1>", lambda _: self._edit())
        self._tree.bind("<Delete>", lambda _: self._delete())

        self._status_lbl = ctk.CTkLabel(
            parent, text="0 entries", anchor="w", text_color="#777", font=("Segoe UI", 11)
        )
        self._status_lbl.pack(fill="x", padx=14, pady=(2, 6))

    def _refresh_tree(self) -> None:
        self._tree.delete(*self._tree.get_children())
        for s in self._sounds:
            self._tree.insert("", "end", values=(s["filename"], s["text"]))
        n = len(self._sounds)
        self._status_lbl.configure(text=f"{n} entr{'y' if n == 1 else 'ies'}")

    def _add(self) -> None:
        dlg = SoundDialog(self, title="Add Sound")
        self.wait_window(dlg)
        if dlg.result:
            self._sounds.append(dlg.result)
            save_sounds_file(self._sounds)
            self._refresh_tree()
            last = self._tree.get_children()[-1]
            self._tree.selection_set(last)
            self._tree.see(last)

    def _edit(self) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        idx = self._tree.index(sel[0])
        dlg = SoundDialog(self, title="Edit Sound", sound=self._sounds[idx])
        self.wait_window(dlg)
        if dlg.result:
            self._sounds[idx] = dlg.result
            save_sounds_file(self._sounds)
            self._refresh_tree()
            children = self._tree.get_children()
            if idx < len(children):
                self._tree.selection_set(children[idx])

    def _delete(self) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        idx = self._tree.index(sel[0])
        fn = self._sounds[idx]["filename"]
        if messagebox.askyesno("Delete", f"Remove '{fn}'?", parent=self):
            del self._sounds[idx]
            save_sounds_file(self._sounds)
            self._refresh_tree()

    def _clear_all(self) -> None:
        if not self._sounds:
            return
        if messagebox.askyesno("Clear All", f"Remove all {len(self._sounds)} entries?", parent=self):
            self._sounds.clear()
            save_sounds_file(self._sounds)
            self._refresh_tree()

    def _import_csv(self) -> None:
        path = filedialog.askopenfilename(
            title="Import CSV", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            count = 0
            with codecs.open(path, "r", "utf-8") as fh:
                reader = csv.reader(fh)
                next(reader, None)  # skip header row
                for row in reader:
                    if len(row) >= 2 and row[0].strip() and row[1].strip():
                        fn = row[0].strip().replace("\\", "/").lstrip("/")
                        self._sounds.append({"filename": fn, "text": row[1].strip()})
                        count += 1
            save_sounds_file(self._sounds)
            self._refresh_tree()
            messagebox.showinfo("Imported", f"Added {count} entries.", parent=self)
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc), parent=self)

    def _import_json(self) -> None:
        """Import from rotorflight-lua-ethos-suite JSON language files.

        Format: [{file, english, translation, needs_translation}, ...]
        Uses 'translation' as text; falls back to 'english' when translation is null.
        """
        path = filedialog.askopenfilename(
            title="Import JSON sound file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, list):
                raise ValueError("Expected a JSON array at the top level.")

            count = skipped = 0
            for entry in data:
                fn = (entry.get("file") or "").strip()
                text = (entry.get("translation") or entry.get("english") or "").strip()
                if not fn or not text:
                    skipped += 1
                    continue
                fn = fn.replace("\\", "/").lstrip("/")
                self._sounds.append({"filename": fn, "text": text})
                count += 1

            save_sounds_file(self._sounds)
            self._refresh_tree()
            msg = f"Imported {count} entries."
            if skipped:
                msg += f"\n({skipped} skipped — missing file or text)"
            messagebox.showinfo("JSON Import", msg, parent=self)
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc), parent=self)

    def _export_csv(self) -> None:
        if not self._sounds:
            messagebox.showwarning("Empty", "No entries to export.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            title="Export CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["filename", "text"])
                for s in self._sounds:
                    w.writerow([s["filename"], s["text"]])
            messagebox.showinfo("Exported", f"Saved {len(self._sounds)} entries.", parent=self)
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc), parent=self)

    # ── Generate tab ───────────────────────────────────────────────────────

    def _build_gen_tab(self, parent) -> None:
        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(14, 8))

        opts = ctk.CTkFrame(top)
        opts.pack(side="left", padx=(0, 18))
        ctk.CTkLabel(opts, text="Options", font=("Segoe UI", 12, "bold")).pack(
            anchor="w", padx=12, pady=(10, 4)
        )
        self._skip_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(opts, text="Skip files that already exist", variable=self._skip_var).pack(
            anchor="w", padx=12, pady=(0, 10)
        )

        btns = ctk.CTkFrame(top, fg_color="transparent")
        btns.pack(side="left")
        self._gen_btn = ctk.CTkButton(
            btns,
            text="▶  Generate All",
            width=160,
            font=("Segoe UI", 13),
            command=self._start_gen,
        )
        self._gen_btn.pack(pady=4)
        self._stop_btn = ctk.CTkButton(
            btns,
            text="■  Stop",
            width=160,
            fg_color="#7a2a2a",
            hover_color="#963535",
            state="disabled",
            command=self._stop_gen,
        )
        self._stop_btn.pack(pady=4)

        pf = ctk.CTkFrame(parent, fg_color="transparent")
        pf.pack(fill="x", padx=16, pady=4)
        self._prog = ctk.CTkProgressBar(pf)
        self._prog.set(0)
        self._prog.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._prog_lbl = ctk.CTkLabel(
            pf, text="0 / 0", width=80, anchor="e", font=("Segoe UI", 11)
        )
        self._prog_lbl.pack(side="right")

        self._log = ctk.CTkTextbox(parent, state="disabled", font=("Consolas", 11), wrap="none")
        self._log.pack(fill="both", expand=True, padx=16, pady=(4, 14))

    def _log_append(self, msg: str) -> None:
        self._log.configure(state="normal")
        self._log.insert("end", msg + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _start_gen(self) -> None:
        if not self._sounds:
            messagebox.showwarning(
                "No entries", "Add sounds in the Sound List tab first.", parent=self
            )
            self.tabs.set("Sound List")
            return

        self._settings.update(self._settings_from_ui())
        if not self._settings.get("api_key"):
            messagebox.showwarning(
                "No API Key", "Enter your Google API key in Settings first.", parent=self
            )
            self.tabs.set("Settings")
            return

        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")
        total = len(self._sounds)
        self._prog.set(0)
        self._prog_lbl.configure(text=f"0 / {total}")
        self._log_append(
            f"Starting: {total} file(s)  |  voice: {self._settings['voice']}"
            f"  |  speed: {self._settings['speed']}×"
        )
        self._log_append(f"Output → {self._settings['output_dir']}\n")

        self._gen_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")

        self._gen_thread = GeneratorThread(
            settings=dict(self._settings),
            sounds=list(self._sounds),
            skip_existing=self._skip_var.get(),
            cb_progress=lambda d, t: self.after(0, self._update_prog, d, t),
            cb_log=lambda m: self.after(0, self._log_append, m),
            cb_done=lambda _: self.after(0, self._gen_done),
        )
        self._gen_thread.start()

    def _stop_gen(self) -> None:
        if self._gen_thread:
            self._gen_thread.stop()
        self._stop_btn.configure(state="disabled")

    def _update_prog(self, done: int, total: int) -> None:
        self._prog.set(done / total if total else 0)
        self._prog_lbl.configure(text=f"{done} / {total}")

    def _gen_done(self) -> None:
        self._gen_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()
