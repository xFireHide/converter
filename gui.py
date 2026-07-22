"""Interface gráfica do FireConverter (tkinter).

Conversão em lote de imagens, áudio, vídeo e PDF — espelha o estilo da GUI do
projeto Image-to-SVG: lista de arquivos, pasta de saída, formato, progresso e log.
"""
from __future__ import annotations

import os
import queue
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from converters import CONVERTERS


def _max_workers(n_files: int) -> int:
    cpu = os.cpu_count() or 4
    return max(1, min(n_files, 8, max(2, cpu // 2)))


class ConverterGui:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("FireConverter")
        self.root.minsize(560, 480)

        self.files: list[Path] = []
        self.output_dir: Path | None = None
        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._running = False
        # mapeia rótulo exibido no combobox -> valor de formato
        self._format_map: dict[str, str] = {}

        main = ttk.Frame(root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        # Tipo de conversão
        type_fr = ttk.Frame(main)
        type_fr.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(type_fr, text="Tipo:").pack(side=tk.LEFT)
        self.var_type = tk.StringVar(value=next(iter(CONVERTERS)))
        self.cmb_type = ttk.Combobox(
            type_fr,
            textvariable=self.var_type,
            values=list(CONVERTERS.keys()),
            state="readonly",
            width=12,
        )
        self.cmb_type.pack(side=tk.LEFT, padx=(6, 16))
        self.cmb_type.bind("<<ComboboxSelected>>", lambda _e: self._on_type_change())

        ttk.Label(type_fr, text="Converter para:").pack(side=tk.LEFT)
        self.var_format = tk.StringVar()
        self.cmb_format = ttk.Combobox(
            type_fr, textvariable=self.var_format, state="readonly", width=28
        )
        self.cmb_format.pack(side=tk.LEFT, padx=(6, 0))

        # Lista de arquivos
        ttk.Label(main, text="Arquivos (vários ao mesmo tempo)").pack(anchor=tk.W)
        list_fr = ttk.Frame(main)
        list_fr.pack(fill=tk.BOTH, expand=True, pady=(4, 8))
        scroll = ttk.Scrollbar(list_fr)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = tk.Listbox(
            list_fr, height=10, selectmode=tk.EXTENDED, yscrollcommand=scroll.set
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.listbox.yview)

        row_btns = ttk.Frame(main)
        row_btns.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(row_btns, text="Adicionar arquivos…", command=self._add_files).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(row_btns, text="Adicionar pasta…", command=self._add_folder).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(row_btns, text="Remover selecionados", command=self._remove_selected).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(row_btns, text="Limpar lista", command=self._clear_list).pack(side=tk.LEFT)

        # Saída
        out_fr = ttk.Frame(main)
        out_fr.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(out_fr, text="Pasta de saída:").pack(anchor=tk.W)
        out_row = ttk.Frame(out_fr)
        out_row.pack(fill=tk.X, pady=(2, 0))
        self.lbl_out = ttk.Label(out_row, text="(não definida)", foreground="#555")
        self.lbl_out.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(out_row, text="Escolher…", command=self._choose_output).pack(side=tk.RIGHT)

        self.btn_run = ttk.Button(main, text="Converter agora", command=self._start_batch)
        self.btn_run.pack(fill=tk.X, pady=(0, 8))

        self.progress = ttk.Progressbar(main, mode="determinate")
        self.progress.pack(fill=tk.X, pady=(0, 4))

        ttk.Label(main, text="Log").pack(anchor=tk.W)
        self.txt = scrolledtext.ScrolledText(main, height=8, wrap=tk.WORD, state=tk.DISABLED)
        self.txt.pack(fill=tk.BOTH, expand=True)

        self._on_type_change()
        self.root.after(120, self._poll_queue)

    # ---- conversor atual -------------------------------------------------
    @property
    def _module(self):
        return CONVERTERS[self.var_type.get()]

    def _on_type_change(self) -> None:
        labels: list[str] = []
        self._format_map.clear()
        for group, options in self._module.OUTPUT_FORMAT_GROUPS:
            for value, label in options:
                display = f"{label}  —  {group}"
                labels.append(display)
                self._format_map[display] = value
        self.cmb_format.configure(values=labels)
        if labels:
            self.cmb_format.current(0)

    # ---- log / lista -----------------------------------------------------
    def _log(self, line: str) -> None:
        self.txt.configure(state=tk.NORMAL)
        self.txt.insert(tk.END, line + "\n")
        self.txt.see(tk.END)
        self.txt.configure(state=tk.DISABLED)

    def _refresh_listbox(self) -> None:
        self.listbox.delete(0, tk.END)
        for p in self.files:
            self.listbox.insert(tk.END, str(p))

    def _add_unique(self, path: Path) -> None:
        path = path.resolve()
        if path not in self.files and path.is_file():
            self.files.append(path)

    def _add_files(self) -> None:
        exts = sorted(self._module.INPUT_EXTENSIONS)
        pattern = " ".join(f"*.{e}" for e in exts)
        paths = filedialog.askopenfilenames(
            title="Selecionar arquivos",
            filetypes=[(f"{self.var_type.get()}", pattern), ("Todos", "*.*")],
        )
        for p in paths:
            self._add_unique(Path(p))
        self._refresh_listbox()

    def _add_folder(self) -> None:
        d = filedialog.askdirectory(title="Pasta com arquivos")
        if not d:
            return
        exts = self._module.INPUT_EXTENSIONS
        for p in sorted(Path(d).rglob("*")):
            if p.is_file() and p.suffix.lower().lstrip(".") in exts:
                self._add_unique(p)
        self._refresh_listbox()

    def _remove_selected(self) -> None:
        for idx in reversed(list(self.listbox.curselection())):
            if 0 <= idx < len(self.files):
                del self.files[idx]
        self._refresh_listbox()

    def _clear_list(self) -> None:
        self.files.clear()
        self._refresh_listbox()

    def _choose_output(self) -> None:
        d = filedialog.askdirectory(title="Pasta de saída")
        if d:
            self.output_dir = Path(d).expanduser().resolve()
            self.lbl_out.config(text=str(self.output_dir), foreground="")

    # ---- conversão -------------------------------------------------------
    def _start_batch(self) -> None:
        if self._running:
            return
        if not self.files:
            messagebox.showinfo("Lista vazia", "Adicione pelo menos um arquivo.")
            return
        if not self.output_dir:
            messagebox.showinfo("Saída", "Escolha a pasta de saída.")
            return
        display = self.var_format.get()
        fmt = self._format_map.get(display)
        if not fmt:
            messagebox.showinfo("Formato", "Escolha o formato de saída.")
            return

        module = self._module
        exts = module.INPUT_EXTENSIONS
        files_copy = list(self.files)
        out_dir = self.output_dir

        self._running = True
        self.btn_run.configure(state=tk.DISABLED)
        self.progress.configure(maximum=len(files_copy), value=0)
        self.txt.configure(state=tk.NORMAL)
        self.txt.delete("1.0", tk.END)
        self.txt.configure(state=tk.DISABLED)

        def one(src: Path) -> tuple[Path, list[Path]]:
            if src.suffix.lower().lstrip(".") not in exts:
                raise ValueError(f"extensão não suportada para {module.NAME}")
            outputs = module.convert(src, fmt, out_dir)
            return src, outputs

        def worker() -> None:
            n = len(files_copy)
            workers = _max_workers(n)
            self._queue.put(("log", f"Iniciando: {n} arquivo(s), até {workers} em paralelo."))
            done = 0
            errors: list[str] = []
            with ThreadPoolExecutor(max_workers=workers) as ex:
                future_map = {ex.submit(one, s): s for s in files_copy}
                for fu in as_completed(future_map):
                    src = future_map[fu]
                    try:
                        _, outputs = fu.result()
                        names = ", ".join(o.name for o in outputs)
                        self._queue.put(("log", f"OK: {src.name} → {names}"))
                    except Exception as e:  # noqa: BLE001 — feedback na UI
                        errors.append(f"{src.name}: {e}")
                        self._queue.put(("log", f"ERRO: {src.name}: {e}"))
                    done += 1
                    self._queue.put(("prog", done))
            self._queue.put(("done", errors))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "log":
                    self._log(str(payload))
                elif kind == "prog":
                    self.progress["value"] = int(payload)
                elif kind == "done":
                    errs = payload
                    self._running = False
                    self.btn_run.configure(state=tk.NORMAL)
                    if errs:
                        messagebox.showwarning(
                            "Concluído com erros",
                            f"{len(errs)} falha(s). Veja o log para detalhes.",
                        )
                    else:
                        messagebox.showinfo("Concluído", "Todos os arquivos foram convertidos.")
        except queue.Empty:
            pass
        self.root.after(120, self._poll_queue)


def main() -> None:
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except tk.TclError:
        pass
    ConverterGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
