#!/usr/bin/env python3
"""
callgraph_gui.py
----------------
Giao dien desktop (Tkinter) cho tool bo sung canh caller->callee bi call
graph tinh bo sot do goi qua con tro ham (callback / ops-table / vtable).

Tinh nang UI:
  - Chon NHIEU thu muc chua source can phan tich (khong gioi han so luong).
  - Chon them file le (ngoai cac thu muc da chon).
  - Nut "Chay phan tich": parse TOAN BO file .c trong cac thu muc + file le
    CUNG LUC trong 1 lan (dung 1 index libclang) -> dam bao truong hop ham
    dinh nghia trong thu muc A nhung duoc GAN/TRUYEN nhu con tro trong 1
    file o thu muc B van duoc resolve dung, vi buoc "gom known_functions"
    chay tren toan bo tap file truoc khi buoc "gom points-to/call site"
    chay tren tung file - thu tu nay khong phu thuoc file nam thu muc nao.
  - Link thu cong: chon/nhap 1 ham CHA (caller), nhap danh sach ham CON
    (callee) cach nhau boi dau ',' -> tao nhieu canh caller->callee_i.
    Dung cho cac truong hop AST/points-to khong the thay (vi du: dang ky
    callback qua macro la, qua IPC/message queue, qua bang lookup dong...).
    Neu ten ham bi trung (static cung ten o nhieu file), nhap dang
    "ten_ham@duong_dan_file" (chi can 1 doan CUOI duong dan la du, khong
    can go het duong dan tuyet doi) de chi ro ham o file nao.
  - Xuat JSON: moi canh gom {caller: {name, file}, callee: {name, file},
    type}. "file" la duong dan file NOI HAM DO DUOC DINH NGHIA (khong phai
    noi no duoc goi), lay tu FUNCTION_DECL definition thuc su trong AST.
    Neu 1 ten ham (thuong la link thu cong) khong khop ham nao da parse,
    file se la null - UI se canh bao truong hop nay o log.

DINH DANH HAM (quan trong - tranh gop nham cac ham static trung ten):
  Ham C khong-static (external linkage) ve nguyen tac chi co 1 dinh nghia
  duy nhat trong toan chuong trinh, nen dung TEN lam dinh danh la du.
  Nhung ham "static" (internal linkage) chi co pham vi trong 1 file/TU -
  2 file khac nhau hoan toan co the co 2 ham static TRUNG TEN nhung la
  2 THUC THE KHAC NHAU (vd 2 ham "handler" static rieng trong uart.c va
  spi.c). Neu chi dung ten lam key (nhu ban dau) thi 2 ham nay se bi GOP
  LAM MOT trong known_functions/direct_edges/points_to -> callgraph sai.
  De sua, moi ham duoc gan 1 "identity key":
    - Ham static : (duong_dan_file_dinh_nghia, ten_ham)
    - Ham khac   : (None, ten_ham)
  Viec static hay khong duoc xac dinh qua cursor.linkage (thong tin ngu
  nghia tu clang, xem ham linkage_is_internal) chu KHONG doan qua token
  'static' trong text - cach nay dung ke ca khi tu khoa bi che boi macro
  hoac dat khong theo thu tu thong thuong. Dung tuple (file, ten) thay vi
  noi chuoi "file__ten" de khoi phai lo ky tu '_' trong ten ham/duong dan
  gay nham lan khi can tach nguoc lai - ten hien thi va file duoc luu rieng
  trong known_functions[key] = {"name":.., "file":..}.

Chay: python3 callgraph_gui.py
Yeu cau: libclang 18.1.1 da duoc dong goi trong thu muc ./clang.
         (tkinter thuong co san trong python3; neu thieu: apt-get install
          python3-tk)
         Luu y: can ban libclang python binding co ho tro thuoc tinh
         Cursor.linkage (cac ban tuong doi gan day deu co).
"""

import glob
import json
import os
from collections import defaultdict
from typing import Optional, Tuple

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import clang.cindex as ci


# Header C toi thieu, chi dung de libclang hieu source CMCELL.  Khong dung
# Windows SDK/MSVC de tool cho ket qua phu thuoc vao may dang chay va khong
# keo cac ham thu vien chuan vao callgraph.
STUB_INCLUDE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "stub_headers")

# Cac symbol thu vien duoc khai bao trong stub_headers. Chung khong phai la
# canh noi bo va khong can hien trong danh sach callback chua resolve.
IGNORED_EXTERNAL_FUNCTIONS = {
    "memchr", "memcmp", "memcpy", "memmove", "memset",
    "strcat", "strchr", "strcmp", "strcpy", "strlen", "strncmp", "strncpy",
    "strstr", "strtol", "strtoul", "snprintf", "printf", "vprintf", "sscanf",
    "malloc", "calloc", "realloc", "free", "abort", "abs", "qsort",
    "__builtin_va_start", "__builtin_va_end",
}


# ---------------------------------------------------------------------------
# Neu libclang.so khong tu tim duoc, set duong dan cu the tai day, vi du:
# ci.Config.set_library_file('/usr/lib/llvm-18/lib/libclang.so.1')
# ---------------------------------------------------------------------------


# =============================================================================
# ENGINE: phan tich AST + points-to (giong ban CLI truoc, co bo sung tracking
# duong dan file dinh nghia cho tung ham, dinh danh ham theo linkage de
# khong gop nham cac ham static trung ten o file khac nhau, va them
# "manual_edges").
# =============================================================================

FuncKey = Tuple[Optional[str], str]  # (duong_dan_file neu la static else None, ten_ham)


def is_function_pointer_type(t: ci.Type) -> bool:
    t = t.get_canonical()
    if t.kind == ci.TypeKind.POINTER:
        pointee = t.get_pointee().get_canonical()
        return pointee.kind in (ci.TypeKind.FUNCTIONPROTO, ci.TypeKind.FUNCTIONNOPROTO)
    return False


def linkage_is_internal(cursor: ci.Cursor) -> bool:
    """True neu cursor la 1 khai bao co internal linkage (tuc duoc khai bao
    voi 'static' o pham vi file). Dung cursor.linkage (ngu nghia tu clang)
    thay vi doan token 'static' trong source vi token co the bi che boi
    macro hoac thu tu qualifier khac thuong."""
    try:
        return cursor.linkage == ci.LinkageKind.INTERNAL
    except Exception:
        return False


def function_identity(cursor: ci.Cursor) -> Tuple[FuncKey, str, Optional[str]]:
    """Tra ve (key, ten_ham, duong_dan_file) dinh danh DUY NHAT cho 1 ham,
    dung cho ca 2 truong hop goi:
      - cursor la 1 FUNCTION_DECL definition (tu collect_functions)
      - cursor la 1 'referenced' cursor lay tu 1 DECL_REF_EXPR tai call site
        (co the chi la 1 khai bao/prototype, chua chac da la definition)
    Dung get_definition() de quy ve dung cursor DINH NGHIA thuc su (phong
    truong hop ham duoc forward-declare truoc, dinh nghia sau trong cung
    file) - nho vay file/ten lay duoc luon la noi ham THUC SU duoc dinh
    nghia, dung nhat quan giua pass thu thap dinh nghia va pass phan giai
    call site.
    """
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
    """Bo qua PAREN_EXPR / UNARY_OPERATOR(&) / UNEXPOSED_EXPR (implicit cast,
    function-to-pointer decay...) de lay bieu thuc loi ben trong."""
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
    """Neu bieu thuc tham chieu toi 1 ham DA BIET (co trong known_functions),
    tra ve KEY dinh danh cua ham do (khong phai raw spelling nua) - de 2 ham
    static trung ten o 2 file khac nhau khong bi coi la "cung 1 ham"."""
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
                # Tham so hinh thuc (formal parameter) cua 1 ham, vi du
                # "at_parser_handler_t at_parser_handler" trong
                # at_command_request(). Neu chi dung key "var:<ten_tham_so>"
                # thi 2 ham khac nhau co tham so trung ten se bi GOP CHUNG
                # 1 key -> sai. Nen gan key theo CA ham chua tham so do
                # (ref.semantic_parent). QUAN TRONG: dung IDENTITY KEY cua
                # ham chu (function_identity), khong dung rieng spelling -
                # neu chi dung spelling thi 2 ham STATIC TRUNG TEN o 2 file
                # khac nhau (vd 2 ham "handler" static trong uart.c va
                # spi.c) se lai bi gop chung param key nhu cu, tai hien
                # dung bug ma tool nay dang sua o cho khac.
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
        self.functions_by_name = defaultdict(set)  # ten_ham (raw) -> {key, ...}
                                              # (>1 key nghia la ten bi trung -
                                              # thuong la cac ham static trung
                                              # ten o file khac nhau)
        self.func_params = {}                # key -> [param_name, ...] (theo dung thu tu khai bao)
        self.points_to = defaultdict(set)    # symbol_key -> {func_key, ...} (gan CU THE, da biet ro ham nao)
        self.aliases = defaultdict(set)      # symbol_key -> {symbol_key2, ...}: "key co the tro toi bat ky
                                              # gia tri nao ma key2 dang tro toi" (chua biet cu the la ham
                                              # nao ngay tai diem nay - vd 1 tham so duoc "chuyen tiep"
                                              # nguyen ven qua nhieu tang ham ma khong bi goi truc tiep
                                              # o tang do). Duoc "giai" (transitive) trong _resolve_targets().
        self.direct_edges = set()            # (caller_key, callee_key)
        self.indirect_sites = []             # (caller_key, symbol_key, "file:line")
        self.manual_edges = set()            # (caller_key, callee_key)
        self.diagnostics = []                # log lines (parse errors...)

    # -- pass 1: gom toan bo dinh nghia ham, TREN TOAN BO TU truoc --------
    def collect_functions(self, cursor: ci.Cursor):
        if cursor.kind == ci.CursorKind.FUNCTION_DECL and cursor.is_definition():
            key, name, path = function_identity(cursor)
            existing = self.known_functions.get(key)
            # Voi ham static, key da bao gom ca file nen 2 ham static trung
            # ten o 2 file khac nhau se KHONG con trung key -> nhanh nay chi
            # con bat truong hop that su bat thuong: 2 ham EXTERNAL (khong
            # static) trung ten dinh nghia o 2 file khac nhau (vi pham quy
            # tac 1 dinh nghia duy nhat cua C/linker).
            if existing is not None and existing["file"] != path:
                self.diagnostics.append(
                    f"[canh bao] ham '{name}' (non-static) dinh nghia o nhieu noi: "
                    f"{existing['file']} va {path}"
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

    # -- pass 2: gom points-to facts + call site --------------------------
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
                    # 1 con tro ham co the duoc "chuyen tiep" lam doi so cho
                    # 1 loi goi khac ma KHONG bi goi truc tiep tai day - vi
                    # du at_command_request(..., at_parser_service_domain_get)
                    # (truyen thang ten ham), hoac wrapper_send(..., handler)
                    # (chuyen tiep nguyen ven 1 tham so tu ham dang chua no).
                    # Gan/alias vao THAM SO HINH THUC tuong ung o ham duoc
                    # goi (direct), dung vi tri (idx) theo self.func_params.
                    # _resolve_targets() se "giai" xuyen qua nhieu tang nhu
                    # vay de tim ra tap ham cu the o dau chuoi.
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

    # -- gan "key" toi 1 ham cu the (neu bieu thuc la ten ham da biet), neu
    #    khong thi coi bieu thuc la 1 vi tri KHAC (var/field/tham so) va ghi
    #    lai quan he "alias" de _resolve_targets() giai xuyen tang sau nay --
    def _bind_or_alias(self, key: str, expr: ci.Cursor):
        fkey = referenced_function_name(expr, self.known_functions)
        if fkey:
            self.points_to[key].add(fkey)
            return
        other_key = symbol_key_for_lvalue(expr)
        if other_key and other_key != key:
            self.aliases[key].add(other_key)

    # -- "giai" 1 key ra tap ham cu the: gom ca gia tri gan truc tiep
    #    (points_to) lan gia tri ke thua tu cac key khac qua nhieu tang
    #    chuyen tiep (aliases), phong ngua vong lap bang _seen --
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

    # -- chay parse tren 1 tap file (co the tu nhieu thu muc khac nhau) --
    def parse(self, files, extra_args):
        self.__init__()  # reset toan bo state cho 1 lan chay moi
        index = ci.Index.create()
        tus = []
        for p in files:
            tu = index.parse(p, args=extra_args)
            for d in tu.diagnostics:
                if d.severity >= ci.Diagnostic.Error:
                    self.diagnostics.append(f"[clang] {p}: {d.spelling}")
            tus.append(tu)
        # QUAN TRONG: pass 1 chay tren TOAN BO cac TU truoc, roi moi pass 2.
        # Nho vay 1 ham dinh nghia trong file/thu muc A van duoc nhan dien
        # dung khi no duoc gan lam con tro trong file/thu muc B, bat ke thu
        # tu duyet file nao truoc.
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
        """True neu key la mot ham thu vien trong stub, khong phai callback."""
        return key.startswith("var:") and key[4:] in IGNORED_EXTERNAL_FUNCTIONS

    # -- phan giai 1 chuoi nguoi dung nhap (link thu cong) thanh 1 func key.
    #    Ho tro dang "ten_ham@doan_duoi_duong_dan_file" de chi ro ham nao
    #    khi ten bi trung (thuong la cac ham static cung ten o file khac
    #    nhau). Tra ve (key_hoac_None, dong_canh_bao_hoac_None). --
    def resolve_function_ref(self, text: str):
        text = text.strip()
        name, _, file_hint = text.partition("@")
        name = name.strip()
        file_hint = file_hint.strip().replace("\\", "/")
        candidates = self.functions_by_name.get(name, set())
        if not candidates:
            return None, f"'{text}' khong khop ham nao trong ket qua phan tich - file se la null trong JSON."
        if file_hint:
            matched = [k for k in candidates if k[0] and k[0].replace("\\", "/").endswith(file_hint)]
            if len(matched) == 1:
                return matched[0], None
            if not matched:
                return None, f"'{text}': khong tim thay ham '{name}' o file khop voi '@{file_hint}'."
            return None, f"'{text}': '@{file_hint}' van khop {len(matched)} ham '{name}' - hay ghi ro hon (vd them thu muc cha)."
        if len(candidates) > 1:
            chosen = sorted(candidates, key=lambda k: k[0] or "")[0]
            files = ", ".join(sorted((k[0] or "?") for k in candidates))
            return chosen, (
                f"[luu y] '{name}' la ten bi trung o nhieu ham static ({files}). "
                f"Da tam chon '{chosen[0]}'. Neu khong dung y, nhap '{name}@duong_dan_file' de chi ro."
            )
        return next(iter(candidates)), None

    def add_manual_link(self, caller_text: str, callees_csv: str):
        """Tra ve list[(callee_text_goc, caller_key, callee_key)] de GUI
        hien thi dung ten/file (callee_key co the la None neu khong khop
        ham nao - GUI se hien caller/callee dang raw text trong truong hop
        do)."""
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
    """Du an C thuong tach header/source thanh nhieu thu muc con (inc/, src/,
    drivers/xxx/inc/...). #include "foo.h" chi tu tim trong thu muc CUNG CAP
    file .c dang include no + cac thu muc truyen qua -I. Neu chi -I dung thu
    muc goc anh chon (vi du "cellular") ma header nam sau o "cellular/inc",
    clang se bao 'file not found'. Ham nay quet DE QUY tat ca thu muc con
    cua moi folder da chon va tra ve -I cho TUNG thu muc, de header o bat ky
    cap do nao cung duoc tim thay, khong can anh phai tro dung vao "inc/"."""
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
        self._diag_cursor = 0     # so dong diagnostics da in ra log
        self.manual_tree_keys = {}  # item_id -> (caller_key, callee_key)

        self._build_widgets()

    # ------------------------------------------------------------------ UI
    def _build_widgets(self):
        pad = {"padx": 8, "pady": 6}

        # --- Khu chon nguon: 2 cot (folders | files) ---
        source_frame = ttk.Frame(self.root)
        source_frame.pack(fill="x", **pad)

        folder_box = ttk.LabelFrame(source_frame, text="Thu muc source (co the chon nhieu)")
        folder_box.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.folder_list = tk.Listbox(folder_box, height=6, selectmode="extended")
        self.folder_list.pack(fill="both", expand=True, padx=4, pady=4)
        fbtns = ttk.Frame(folder_box)
        fbtns.pack(fill="x", padx=4, pady=(0, 4))
        ttk.Button(fbtns, text="+ Them thu muc", command=self.add_folder).pack(side="left")
        ttk.Button(fbtns, text="- Xoa da chon", command=self.remove_selected_folders).pack(side="left", padx=4)

        file_box = ttk.LabelFrame(source_frame, text="File le (bo sung ngoai thu muc tren)")
        file_box.pack(side="left", fill="both", expand=True, padx=(4, 0))
        self.file_list = tk.Listbox(file_box, height=6, selectmode="extended")
        self.file_list.pack(fill="both", expand=True, padx=4, pady=4)
        filebtns = ttk.Frame(file_box)
        filebtns.pack(fill="x", padx=4, pady=(0, 4))
        ttk.Button(filebtns, text="+ Them file", command=self.add_files).pack(side="left")
        ttk.Button(filebtns, text="- Xoa da chon", command=self.remove_selected_files).pack(side="left", padx=4)

        # --- Extra clang args + Run ---
        run_frame = ttk.Frame(self.root)
        run_frame.pack(fill="x", **pad)
        ttk.Label(run_frame, text="Extra clang args (vd: -DSTM32H523xx -Iextra/inc):").pack(side="left")
        self.extra_args_var = tk.StringVar()
        ttk.Entry(run_frame, textvariable=self.extra_args_var).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(run_frame, text="Chay phan tich", command=self.run_analysis).pack(side="left")

        # --- Log ---
        log_box = ttk.LabelFrame(self.root, text="Ket qua / log")
        log_box.pack(fill="both", expand=True, **pad)
        self.log_text = tk.Text(log_box, height=10, wrap="word", state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=4, pady=4)

        # --- Manual link ---
        manual_box = ttk.LabelFrame(
            self.root,
            text="Link thu cong (caller -> callee1, callee2, ... | dung 'ten@file' neu ten bi trung)",
        )
        manual_box.pack(fill="both", expand=True, **pad)

        manual_input = ttk.Frame(manual_box)
        manual_input.pack(fill="x", padx=4, pady=4)
        ttk.Label(manual_input, text="Caller:").pack(side="left")
        self.caller_var = tk.StringVar()
        self.caller_combo = ttk.Combobox(manual_input, textvariable=self.caller_var, width=32)
        self.caller_combo.pack(side="left", padx=(4, 12))
        ttk.Label(manual_input, text="Callees (cach nhau boi ','):").pack(side="left")
        self.callees_var = tk.StringVar()
        ttk.Entry(manual_input, textvariable=self.callees_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(manual_input, text="+ Them link", command=self.add_manual_link).pack(side="left", padx=4)

        columns = ("caller", "callee", "caller_file", "callee_file")
        self.manual_tree = ttk.Treeview(manual_box, columns=columns, show="headings", height=6)
        for col, label, width in (
            ("caller", "Caller", 140),
            ("callee", "Callee", 140),
            ("caller_file", "File cua caller", 300),
            ("callee_file", "File cua callee", 300),
        ):
            self.manual_tree.heading(col, text=label)
            self.manual_tree.column(col, width=width, anchor="w")
        self.manual_tree.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        ttk.Button(manual_box, text="- Xoa link da chon", command=self.remove_selected_manual_link).pack(
            anchor="w", padx=4, pady=(0, 4)
        )

        # --- Export ---
        export_frame = ttk.Frame(self.root)
        export_frame.pack(fill="x", **pad)
        ttk.Button(export_frame, text="Xuat JSON", command=self.export_json).pack(side="right")

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
        """In ra log moi dong diagnostics phat sinh tu lan flush truoc den
        gio (dung khi them link thu cong, de nguoi dung thay ngay canh bao
        'ten bi trung' / 'khong khop ham nao' ma khong bi in lai tu dau)."""
        for line in self.engine.diagnostics[self._diag_cursor:]:
            self.log(line)
        self._diag_cursor = len(self.engine.diagnostics)

    # ------------------------------------------------------------ actions
    def add_folder(self):
        path = filedialog.askdirectory(title="Chon thu muc source")
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
            title="Chon file source",
            filetypes=[("C source/header", "*.c *.h"), ("Tat ca file", "*.*")],
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
            messagebox.showwarning("Thieu nguon", "Hay chon it nhat 1 thu muc hoac 1 file .c truoc khi chay.")
            return

        # -nostdinc bat libclang dung bo header stub di kem tool thay vi tu
        # dong tim MSVC/Windows SDK cua tung may.  Cac -I cua project van
        # duoc them ben duoi nhu cu.
        extra_args = ["-nostdinc", "-I" + STUB_INCLUDE_DIR]
        extra_args += self.extra_args_var.get().split()
        include_dirs = discover_include_dirs(self.folders)
        # cac thu muc chua file duoc chon rieng le cung can duoc -I, phong khi
        # header cua no nam ngoai moi thu muc da chon
        include_dirs += [os.path.dirname(f) for f in self.files]
        extra_args += ["-I" + d for d in sorted(set(include_dirs))]

        self.clear_log()
        self.log(f"Dang phan tich {len(all_files)} file...")
        self.log(f"Da tu dong them -I cho {len(set(include_dirs))} thu muc (bao gom moi thu muc con).")
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
        self.log(f"Ham da biet                 : {len(self.engine.known_functions)}")
        self.log(f"Diem gan con tro (key)      : {len(self.engine.points_to)}")
        self.log(f"Canh truc tiep              : {len(self.engine.direct_edges)}")
        self.log(f"Canh gian tiep resolve duoc : {len(ind_edges)}")
        self.log(f"Call site KHONG resolve duoc (con tro tu ngoai / chua tung thay gan): {len(relevant_unresolved)}")
        if ignored_external:
            self.log(f"Bo qua {ignored_external} call thu vien chuan (printf/memcpy/...)")
        for caller, key, loc in relevant_unresolved[:50]:
            self.log(f"  - {loc}: trong {caller[1]}() goi qua '{key}' -> khong ro target")

        # canh bao cac ten ham bi trung (thuong la static cung ten o nhieu
        # file) - de nguoi dung biet can dung dang 'ten@file' khi nhap link
        # thu cong cho cac ten nay
        ambiguous = {name: keys for name, keys in self.engine.functions_by_name.items() if len(keys) > 1}
        if ambiguous:
            self.log(f"\n[luu y] {len(ambiguous)} ten ham bi trung o nhieu file (thuong la ham static):")
            for name, keys in sorted(ambiguous.items()):
                files = ", ".join(sorted((k[0] or "?") for k in keys))
                self.log(f"  - {name}: {files}")
            self.log("  Khi them link thu cong cho cac ten nay, dung dang 'ten@duong_dan_file' de chi ro.")

        # cap nhat danh sach goi y cho combobox Caller: ten don gian neu
        # khong bi trung, hoac "ten@file" cho tung ung vien neu bi trung
        display_values = []
        for name, keys in sorted(self.engine.functions_by_name.items()):
            if len(keys) == 1:
                display_values.append(name)
            else:
                for k in sorted(keys, key=lambda kk: kk[0] or ""):
                    display_values.append(f"{name}@{k[0]}")
        self.caller_combo["values"] = display_values
        self.log("\nHoan tat. Co the them link thu cong ben duoi hoac Xuat JSON ngay.")

    def add_manual_link(self):
        caller = self.caller_var.get().strip()
        callees_csv = self.callees_var.get().strip()
        if not caller or not callees_csv:
            messagebox.showwarning("Thieu du lieu", "Nhap ten ham Caller va it nhat 1 Callee.")
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
            messagebox.showwarning("Chua co du lieu", "Hay 'Chay phan tich' va/hoac them link thu cong truoc.")
            return
        path = filedialog.asksaveasfilename(
            title="Luu ket qua JSON",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(edges, f, ensure_ascii=False, indent=2)
        self.log(f"\nDa xuat {len(edges)} canh -> {path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = CallGraphApp(root)
    root.mainloop()
