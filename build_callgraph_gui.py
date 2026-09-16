##!/usr/bin/env python3

import glob
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional, Tuple

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import clang
import clang.cindex as ci


CLANG_PACKAGE_DIR = Path(clang.__file__).resolve().parent
LIBCLANG_DLL = CLANG_PACKAGE_DIR / "native" / "libclang.dll"

if not LIBCLANG_DLL.is_file():
    raise FileNotFoundError(
        f"Cannot find libclang.dll: {LIBCLANG_DLL}"
    )

ci.Config.set_library_file(str(LIBCLANG_DLL))

print(f"clang module : {clang.__file__}")
print(f"libclang DLL : {ci.Config.library_file}")


STUB_INCLUDE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "stub_headers",
)


STUB_INCLUDE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "stub_headers")


IGNORED_EXTERNAL_FUNCTIONS = {
    "memchr", "memcmp", "memcpy", "memmove", "memset",
    "strcat", "strchr", "strcmp", "strcpy", "strlen", "strncmp", "strncpy",
    "strstr", "strtol", "strtoul", "snprintf", "printf", "vprintf", "sscanf",
    "malloc", "calloc", "realloc", "free", "abort", "abs", "qsort",
    "__builtin_va_start", "__builtin_va_end",
}


FuncKey = Tuple[Optional[str], str]  


def is_function_pointer_type(t: ci.Type) -> bool:
    t = t.get_canonical()
    if t.kind == ci.TypeKind.POINTER:
        pointee = t.get_pointee().get_canonical()
        return pointee.kind in (ci.TypeKind.FUNCTIONPROTO, ci.TypeKind.FUNCTIONNOPROTO)
    return False


def linkage_is_internal(cursor: ci.Cursor) -> bool:
    try:
        return cursor.linkage == ci.LinkageKind.INTERNAL
    except Exception:
        return False


def function_identity(cursor: ci.Cursor) -> Tuple[FuncKey, str, Optional[str]]:

    def_cursor = cursor.get_definition() or cursor
    name = def_cursor.spelling
    loc = def_cursor.location
    file = loc.file.name if loc.file else None
    if file:
        file = os.path.abspath(file)
    if linkage_is_internal(def_cursor):
        return (file, name), name, file
    return (None, name), name, file


def strip_wrappers(cursor: ci.Cursor) -> ci.Cursor:
    while True:
        children = list(cursor.get_children())
        if cursor.kind == ci.CursorKind.PAREN_EXPR and len(children) == 1:
            cursor = children[0]
            continue
        if cursor.kind == ci.CursorKind.UNEXPOSED_EXPR and len(children) == 1:
            cursor = children[0]
            continue
        if cursor.kind == ci.CursorKind.UNARY_OPERATOR and len(children) == 1:
            toks = [t.spelling for t in cursor.get_tokens()]
            if toks and toks[0] == '&':
                cursor = children[0]
                continue
        break
    return cursor


def referenced_function_name(cursor: ci.Cursor, known_functions) -> Optional[FuncKey]:
    cursor = strip_wrappers(cursor)
    if cursor.kind == ci.CursorKind.DECL_REF_EXPR:
        ref = cursor.referenced
        if ref is not None:
            key, _, _ = function_identity(ref)
            if key in known_functions:
                return key
    return None


def symbol_key_for_lvalue(cursor: ci.Cursor) -> Optional[str]:
    cursor = strip_wrappers(cursor)
    if cursor.kind == ci.CursorKind.DECL_REF_EXPR:
        ref = cursor.referenced
        if ref is not None:
            if ref.kind == ci.CursorKind.PARM_DECL:
                owner = ref.semantic_parent
                if owner is not None:
                    owner_key, _, _ = function_identity(owner)
                    return f"param:{owner_key}:{ref.spelling}"
                return None
            return f"var:{ref.spelling}"
    if cursor.kind == ci.CursorKind.MEMBER_REF_EXPR:
        return f"field:{cursor.spelling}"
    if cursor.kind == ci.CursorKind.ARRAY_SUBSCRIPT_EXPR:
        children = list(cursor.get_children())
        if children:
            base_key = symbol_key_for_lvalue(children[0])
            if base_key:
                return base_key
    return None


class CallGraphEngine:
    def __init__(self):
        self.known_functions = {}            # key -> {"name":, "file":}
        self.functions_by_name = defaultdict(set)  # func (raw) -> {key, ...}

        self.func_params = {}                # key -> [param_name, ...]
        self.points_to = defaultdict(set)    # symbol_key -> {func_key, ...}
        self.aliases = defaultdict(set)      # symbol_key -> {symbol_key2, ...}:
        self.direct_edges = set()            # (caller_key, callee_key)
        self.indirect_sites = []             # (caller_key, symbol_key, "file:line")
        self.manual_edges = set()            # (caller_key, callee_key)
        self.diagnostics = []                # log lines (parse errors...)

    def collect_functions(self, cursor: ci.Cursor):
        if cursor.kind == ci.CursorKind.FUNCTION_DECL and cursor.is_definition():
            key, name, path = function_identity(cursor)
            existing = self.known_functions.get(key)
            if existing is not None and existing["file"] != path:
                self.diagnostics.append(
                    f"[warning] the function '{name}' (non-static) is defined in multiple places: "
                    f"{existing['file']} and {path}"
                )
            else:
                self.known_functions.setdefault(key, {"name": name, "file": path})
                self.func_params.setdefault(
                    key,
                    [p.spelling for p in cursor.get_children()
                     if p.kind == ci.CursorKind.PARM_DECL],
                )
            self.functions_by_name[name].add(key)
        for c in cursor.get_children():
            self.collect_functions(c)

    def walk(self, cursor: ci.Cursor, enclosing_func: Optional[FuncKey]):
        if cursor.kind == ci.CursorKind.FUNCTION_DECL and cursor.is_definition():
            enclosing_func, _, _ = function_identity(cursor)

        if cursor.kind == ci.CursorKind.BINARY_OPERATOR:
            children = list(cursor.get_children())
            toks = [t.spelling for t in cursor.get_tokens()]
            if len(children) == 2 and '=' in toks:
                lhs, rhs = children
                key = symbol_key_for_lvalue(lhs)
                if key:
                    self._bind_or_alias(key, rhs)

        if cursor.kind == ci.CursorKind.VAR_DECL and is_function_pointer_type(cursor.type):
            children = list(cursor.get_children())
            if children:
                self._bind_or_alias(f"var:{cursor.spelling}", children[-1])

        if cursor.kind == ci.CursorKind.INIT_LIST_EXPR:
            record_fields = self._fields_for_init_list(cursor)
            for idx, elem in enumerate(cursor.get_children()):
                field, expr = self._designated_field_and_expr(elem)
                if field is None and idx < len(record_fields):
                    field, expr = record_fields[idx], elem
                if field is None:
                    continue
                self._bind_or_alias(f"field:{field}", expr)

        if cursor.kind == ci.CursorKind.CALL_EXPR:
            children = list(cursor.get_children())
            if children and enclosing_func:
                callee_expr = children[0]
                direct = referenced_function_name(callee_expr, self.known_functions)
                if direct:
                    self.direct_edges.add((enclosing_func, direct))
                    param_names = self.func_params.get(direct, [])
                    for idx, arg in enumerate(children[1:]):
                        if idx < len(param_names):
                            key = f"param:{direct}:{param_names[idx]}"
                            self._bind_or_alias(key, arg)
                else:
                    key = symbol_key_for_lvalue(callee_expr)
                    if key:
                        loc = cursor.location
                        self.indirect_sites.append(
                            (enclosing_func, key, f"{loc.file}:{loc.line}")
                        )

        for c in cursor.get_children():
            self.walk(c, enclosing_func)

    def _bind_or_alias(self, key: str, expr: ci.Cursor):
        fkey = referenced_function_name(expr, self.known_functions)
        if fkey:
            self.points_to[key].add(fkey)
            return
        other_key = symbol_key_for_lvalue(expr)
        if other_key and other_key != key:
            self.aliases[key].add(other_key)

    def _resolve_targets(self, key: str, _seen=None):
        if _seen is None:
            _seen = set()
        if key in _seen:
            return set()
        _seen.add(key)
        targets = set(self.points_to.get(key, ()))
        for other_key in self.aliases.get(key, ()):
            targets |= self._resolve_targets(other_key, _seen)
        return targets

    @staticmethod
    def _designated_field_and_expr(elem: ci.Cursor):
        children = list(elem.get_children())
        if elem.kind == ci.CursorKind.UNEXPOSED_EXPR and len(children) == 2:
            first, second = children
            if first.kind == ci.CursorKind.MEMBER_REF:
                return first.spelling, second
        if len(children) == 2 and children[0].kind == ci.CursorKind.MEMBER_REF:
            return children[0].spelling, children[1]
        return None, None

    @staticmethod
    def _fields_for_init_list(init_list_cursor: ci.Cursor):
        t = init_list_cursor.type.get_canonical()
        decl = t.get_declaration()
        return [f.spelling for f in decl.get_children()
                if f.kind == ci.CursorKind.FIELD_DECL]

  
    def parse(self, files, extra_args):
        self.__init__()  
        index = ci.Index.create()
        tus = []
        for p in files:
            tu = index.parse(p, args=extra_args)
            for d in tu.diagnostics:
                if d.severity >= ci.Diagnostic.Error:
                    self.diagnostics.append(f"[clang] {p}: {d.spelling}")
            tus.append(tu)
    
        for tu in tus:
            self.collect_functions(tu.cursor)
        for tu in tus:
            self.walk(tu.cursor, None)

    def resolved_indirect_edges(self):
        edges = set()
        unresolved = []
        for caller, key, loc in self.indirect_sites:
            targets = self._resolve_targets(key)
            if targets:
                for t in targets:
                    edges.add((caller, t))
            else:
                unresolved.append((caller, key, loc))
        return edges, unresolved

    @staticmethod
    def is_ignored_external_call(key: str) -> bool:
        return key.startswith("var:") and key[4:] in IGNORED_EXTERNAL_FUNCTIONS

    def resolve_function_ref(self, text: str):
        text = text.strip()
        name, _, file_hint = text.partition("@")
        name = name.strip()
        file_hint = file_hint.strip().replace("\\", "/")
        candidates = self.functions_by_name.get(name, set())
        if not candidates:
            return None, f"'{text}' not match any function in the analysis results - the file will be null in JSON."
        if file_hint:
            matched = [k for k in candidates if k[0] and k[0].replace("\\", "/").endswith(file_hint)]
            if len(matched) == 1:
                return matched[0], None
            if not matched:
                return None, f"'{text}': not found function '{name}' in file matching '@{file_hint}'."
            return None, f"'{text}': '@{file_hint}' still matches {len(matched)} functions '{name}' - please specify more precisely (e.g., include parent directory)."
        if len(candidates) > 1:
            chosen = sorted(candidates, key=lambda k: k[0] or "")[0]
            files = ", ".join(sorted((k[0] or "?") for k in candidates))
            return chosen, (
                f"[note] '{name}' is a name duplicated in many static functions ({files}). "
                f"Temporarily chose '{chosen[0]}'. If not what you want, enter '{name}@file_path' to specify."
            )
        return next(iter(candidates)), None

    def add_manual_link(self, caller_text: str, callees_csv: str):
        caller_key, warn = self.resolve_function_ref(caller_text)
        if warn:
            self.diagnostics.append(warn)
        results = []
        for callee_text in [c.strip() for c in callees_csv.split(",") if c.strip()]:
            callee_key, warn2 = self.resolve_function_ref(callee_text)
            if warn2:
                self.diagnostics.append(warn2)
            eff_caller = caller_key if caller_key is not None else (None, caller_text)
            eff_callee = callee_key if callee_key is not None else (None, callee_text)
            self.manual_edges.add((eff_caller, eff_callee))
            results.append((callee_text, eff_caller, eff_callee))
        return results

    def remove_manual_link(self, caller_key, callee_key):
        self.manual_edges.discard((caller_key, callee_key))

    def all_edges(self):
        def info(key):
            return self.known_functions.get(key, {"name": (key[1] if isinstance(key, tuple) else str(key)),
                                                    "file": (key[0] if isinstance(key, tuple) else None)})

        def make(caller_key, callee_key, edge_type):
            c, ce = info(caller_key), info(callee_key)
            return {
                "caller": {"name": c["name"], "file": c["file"]},
                "callee": {"name": ce["name"], "file": ce["file"]},
                "type": edge_type,
            }
        edges = [make(c, ce, "direct") for c, ce in self.direct_edges]
        ind_edges, _ = self.resolved_indirect_edges()
        edges += [make(c, ce, "indirect") for c, ce in ind_edges]
        edges += [make(c, ce, "manual") for c, ce in self.manual_edges]
        return edges


def collect_source_files(folders, extra_files):
    files = set()
    for folder in folders:
        files.update(glob.glob(os.path.join(folder, "**", "*.c"), recursive=True))
    files.update(extra_files)
    return sorted(files)


_SKIP_DIR_NAMES = {".git", ".svn", "build", "cmake-build-debug", "cmake-build-release",
                   "__pycache__", "node_modules"}


def discover_include_dirs(folders):
    include_dirs = []
    for folder in folders:
        for root, dirs, _files in os.walk(folder):
            dirs[:] = [d for d in dirs if d not in _SKIP_DIR_NAMES and not d.startswith(".")]
            include_dirs.append(root)
    return include_dirs


# =============================================================================
# GUI
# =============================================================================

class CallGraphApp:
    def __init__(self, root):
        self.root = root
        root.title("Call Graph (function-pointer aware) builder")
        root.geometry("980x760")

        self.engine = CallGraphEngine()
        self.folders = []   # list[str]
        self.files = []     # list[str]
        self._diag_cursor = 0     
        self.manual_tree_keys = {}  # item_id -> (caller_key, callee_key)

        self._build_widgets()

    # ------------------------------------------------------------------ UI
    def _build_widgets(self):
        pad = {"padx": 8, "pady": 6}

        source_frame = ttk.Frame(self.root)
        source_frame.pack(fill="x", **pad)

        folder_box = ttk.LabelFrame(source_frame, text="the source (can select multiple)")
        folder_box.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.folder_list = tk.Listbox(folder_box, height=6, selectmode="extended")
        self.folder_list.pack(fill="both", expand=True, padx=4, pady=4)
        fbtns = ttk.Frame(folder_box)
        fbtns.pack(fill="x", padx=4, pady=(0, 4))
        ttk.Button(fbtns, text="+ Add folder", command=self.add_folder).pack(side="left")
        ttk.Button(fbtns, text="- Remove selected", command=self.remove_selected_folders).pack(side="left", padx=4)

        file_box = ttk.LabelFrame(source_frame, text="Individual files (in addition to the above folders)")
        file_box.pack(side="left", fill="both", expand=True, padx=(4, 0))
        self.file_list = tk.Listbox(file_box, height=6, selectmode="extended")
        self.file_list.pack(fill="both", expand=True, padx=4, pady=4)
        filebtns = ttk.Frame(file_box)
        filebtns.pack(fill="x", padx=4, pady=(0, 4))
        ttk.Button(filebtns, text="+ Add file", command=self.add_files).pack(side="left")
        ttk.Button(filebtns, text="- Remove selected", command=self.remove_selected_files).pack(side="left", padx=4)

        # --- Extra clang args + Run ---
        run_frame = ttk.Frame(self.root)
        run_frame.pack(fill="x", **pad)
        ttk.Label(run_frame, text="Extra clang args (vd: -DSTM32H523xx -Iextra/inc):").pack(side="left")
        self.extra_args_var = tk.StringVar()
        ttk.Entry(run_frame, textvariable=self.extra_args_var).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(run_frame, text="Run analysis", command=self.run_analysis).pack(side="left")

        # --- Log ---
        log_box = ttk.LabelFrame(self.root, text="Results / log")
        log_box.pack(fill="both", expand=True, **pad)
        self.log_text = tk.Text(log_box, height=10, wrap="word", state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=4, pady=4)

        # --- Manual link ---
        manual_box = ttk.LabelFrame(
            self.root,
            text="Manual link (caller -> callee1, callee2, ... | use 'name@file' if name is duplicated)",
        )
        manual_box.pack(fill="both", expand=True, **pad)

        manual_input = ttk.Frame(manual_box)
        manual_input.pack(fill="x", padx=4, pady=4)
        ttk.Label(manual_input, text="Caller:").pack(side="left")
        self.caller_var = tk.StringVar()
        self.caller_combo = ttk.Combobox(manual_input, textvariable=self.caller_var, width=32)
        self.caller_combo.pack(side="left", padx=(4, 12))
        ttk.Label(manual_input, text="Callees (separated by ','):").pack(side="left")
        self.callees_var = tk.StringVar()
        ttk.Entry(manual_input, textvariable=self.callees_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(manual_input, text="+ Add link", command=self.add_manual_link).pack(side="left", padx=4)

        columns = ("caller", "callee", "caller_file", "callee_file")
        self.manual_tree = ttk.Treeview(manual_box, columns=columns, show="headings", height=6)
        for col, label, width in (
            ("caller", "Caller", 140),
            ("callee", "Callee", 140),
            ("caller_file", "Caller file", 300),
            ("callee_file", "Callee file", 300),
        ):
            self.manual_tree.heading(col, text=label)
            self.manual_tree.column(col, width=width, anchor="w")
        self.manual_tree.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        ttk.Button(manual_box, text="- Remove selected link", command=self.remove_selected_manual_link).pack(
            anchor="w", padx=4, pady=(0, 4)
        )

        # --- Export ---
        export_frame = ttk.Frame(self.root)
        export_frame.pack(fill="x", **pad)
        ttk.Button(export_frame, text="Export JSON", command=self.export_json).pack(side="right")

    # ------------------------------------------------------------ helpers
    def log(self, msg: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.configure(state="disabled")
        self.log_text.see("end")

    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _flush_new_diagnostics(self):
        for line in self.engine.diagnostics[self._diag_cursor:]:
            self.log(line)
        self._diag_cursor = len(self.engine.diagnostics)

    # ------------------------------------------------------------ actions
    def add_folder(self):
        path = filedialog.askdirectory(title="Select source folder")
        if path and path not in self.folders:
            self.folders.append(path)
            self.folder_list.insert("end", path)

    def remove_selected_folders(self):
        for idx in reversed(self.folder_list.curselection()):
            path = self.folder_list.get(idx)
            self.folder_list.delete(idx)
            if path in self.folders:
                self.folders.remove(path)

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select source file",
            filetypes=[("C source/header", "*.c *.h"), ("All files", "*.*")],
        )
        for p in paths:
            if p and p not in self.files:
                self.files.append(p)
                self.file_list.insert("end", p)

    def remove_selected_files(self):
        for idx in reversed(self.file_list.curselection()):
            path = self.file_list.get(idx)
            self.file_list.delete(idx)
            if path in self.files:
                self.files.remove(path)

    def run_analysis(self):
        all_files = collect_source_files(self.folders, self.files)
        if not all_files:
            messagebox.showwarning("Missing source", "Please select at least one folder or one .c file before running.")
            return


        extra_args = ["-nostdinc", "-I" + STUB_INCLUDE_DIR]
        extra_args += self.extra_args_var.get().split()
        include_dirs = discover_include_dirs(self.folders)
        include_dirs += [os.path.dirname(f) for f in self.files]
        extra_args += ["-I" + d for d in sorted(set(include_dirs))]

        self.clear_log()
        self.log(f"Analyzing {len(all_files)} files...")
        self.log(f"Automatically added -I for {len(set(include_dirs))} directories (including all subdirectories).")
        self.root.update_idletasks()

        self.engine.parse(all_files, extra_args)
        self._diag_cursor = 0
        self._flush_new_diagnostics()

        ind_edges, unresolved = self.engine.resolved_indirect_edges()
        relevant_unresolved = [
            site for site in unresolved
            if not self.engine.is_ignored_external_call(site[1])
        ]
        ignored_external = len(unresolved) - len(relevant_unresolved)
        self.log(f"Known functions            : {len(self.engine.known_functions)}")
        self.log(f"Points-to (key)            : {len(self.engine.points_to)}")
        self.log(f"Direct edges               : {len(self.engine.direct_edges)}")
        self.log(f"Resolved indirect edges    : {len(ind_edges)}")
        self.log(f"Unresolved call sites (external pointer / not yet assigned): {len(relevant_unresolved)}")
        if ignored_external:
            self.log(f"Ignored {ignored_external} standard library calls (printf/memcpy/...)")
        for caller, key, loc in relevant_unresolved[:50]:
            self.log(f"  - {loc}: in {caller[1]}() calls '{key}' -> unknown target")


        ambiguous = {name: keys for name, keys in self.engine.functions_by_name.items() if len(keys) > 1}
        if ambiguous:
            self.log(f"\n[Note] {len(ambiguous)} function names are duplicated in multiple files (usually static functions):")
            for name, keys in sorted(ambiguous.items()):
                files = ", ".join(sorted((k[0] or "?") for k in keys))
                self.log(f"  - {name}: {files}")
            self.log("  When manually adding links for these names, use the format 'name@file_path' to specify.")

        # update suggestions for the Caller combobox: simple name if
        # not duplicated, or "name@file" for each candidate if duplicated
        display_values = []
        for name, keys in sorted(self.engine.functions_by_name.items()):
            if len(keys) == 1:
                display_values.append(name)
            else:
                for k in sorted(keys, key=lambda kk: kk[0] or ""):
                    display_values.append(f"{name}@{k[0]}")
        self.caller_combo["values"] = display_values
        self.log("\nDone. You can now manually add links below or export to JSON.")

    def add_manual_link(self):
        caller = self.caller_var.get().strip()
        callees_csv = self.callees_var.get().strip()
        if not caller or not callees_csv:
            messagebox.showwarning("Missing data", "Enter the Caller function name and at least one Callee.")
            return
        results = self.engine.add_manual_link(caller, callees_csv)
        self._flush_new_diagnostics()
        for callee_text, caller_key, callee_key in results:
            caller_info = self.engine.known_functions.get(caller_key, {"name": caller, "file": None})
            callee_info = self.engine.known_functions.get(callee_key, {"name": callee_text, "file": None})
            item = self.manual_tree.insert(
                "", "end",
                values=(caller_info["name"], callee_info["name"],
                        caller_info["file"] or "", callee_info["file"] or ""),
            )
            self.manual_tree_keys[item] = (caller_key, callee_key)
        self.callees_var.set("")

    def remove_selected_manual_link(self):
        for item in self.manual_tree.selection():
            keys = self.manual_tree_keys.pop(item, None)
            if keys is not None:
                self.engine.remove_manual_link(*keys)
            self.manual_tree.delete(item)

    def export_json(self):
        edges = self.engine.all_edges()
        if not edges:
            messagebox.showwarning("No data", "Please 'Run analysis' and/or add manual links first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save JSON results",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(edges, f, ensure_ascii=False, indent=2)
        self.log(f"\nExported {len(edges)} edges -> {path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = CallGraphApp(root)
    root.mainloop()
