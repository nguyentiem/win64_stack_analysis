# Phân tích stack usage theo callgraph

Thư mục này có công cụ để tìm các đường gọi hàm có stack usage cao nhất:

1. Build **emulator** bằng GCC để sinh file `.su` (stack frame của từng hàm).
2. Chạy `callgraph_gui.py` để xuất quan hệ caller → callee thành JSON.
3. Chạy `stack_callgraph.py` để ghép hai nguồn dữ liệu và cộng stack trên mỗi đường gọi.

Mọi lệnh bên dưới được chạy từ thư mục gốc repository (`cellular/`).

## 1. Build emulator và sinh file `.su`

Preset `cmcell-local-stack` dùng MinGW-w64 GCC và bật `CMCELL_ENABLE_STACK_ANALYSIS`.
Tùy chọn này thêm các cờ GCC `-fstack-usage` và `-fcallgraph-info=su`.

```powershell
cmake -S emulator --preset cmcell-local-stack
cmake --build emulator/build/cmcell-stack -j 8
```

> Quan trọng: cần có `-S emulator`, vì file `CMakePresets.json` nằm trong thư mục
> `emulator/`, không phải ở root repository.

Xác nhận build đã sinh `.su`:

```powershell
Get-ChildItem emulator/build/cmcell-stack -Recurse -Filter *.su |
  Measure-Object
```

`Count` phải lớn hơn 0. Các file `.su` được tạo cạnh object file, ví dụ:
`emulator/build/cmcell-stack/CMakeFiles/cmcell.dir/.../cell_xxx.c.su`.

Nếu preset local chưa phù hợp với máy, cập nhật đường dẫn GCC/Ninja trong
`emulator/CMakeUserPresets.json`. Tính stack phụ thuộc compiler, ABI, optimization
và target. Số từ host emulator dùng để kiểm tra luồng công cụ; số cho firmware cuối
cùng cần được tạo bằng target toolchain tương ứng.

## 2. Xuất callgraph JSON

`callgraph_gui.py` phân tích C source bằng libclang và tạo file JSON gồm các cạnh gọi
hàm. Binding `libclang==18.1.1` (kèm `libclang.dll`) đã được đóng gói trong
`tools/stack_analysis/clang/`, nên không cần cài pip để chạy bản tool này.
Tool cũng dùng các header C tối thiểu trong `stub_headers/` khi parse; vì vậy không
phụ thuộc MSVC/Windows SDK của máy đang chạy và không đưa call chuẩn như
`printf`/`memcpy` vào danh sách callback chưa resolve.
Nếu đóng gói một bản khác không bao gồm thư mục `clang/`, cài binding một lần:

```powershell
python -m pip install libclang
```

Mở giao diện:

```powershell
python tools/stack_analysis/callgraph_gui.py
```

Trong giao diện:

1. Chọn các thư mục source `cellular`, `com`, và `modem`.
2. Nhấn **Chạy phân tích** và kiểm tra log không có lỗi quan trọng.
3. Nếu cần, thêm các cạnh callback/function-pointer bằng phần link thủ công.
4. Nhấn **Xuất JSON** và lưu, ví dụ:
   `emulator/build/cmcell-stack/callgraph.json`.

Mỗi cạnh JSON có dạng:

```json
{
  "caller": {"name": "caller_function", "file": ".../caller.c"},
  "callee": {"name": "callee_function", "file": ".../callee.c"},
  "type": "direct"
}
```

Hàm được nhận dạng bằng cả tên và file định nghĩa, tránh gộp nhầm các hàm `static`
trùng tên ở file khác nhau.

## 3. Tính stack usage lớn nhất theo đường gọi

Chạy với các `.su` của **cùng build** và JSON vừa xuất:

```powershell
python tools/stack_analysis/stack_callgraph.py `
  --su-dir emulator/build/cmcell-stack `
  --callgraph emulator/build/cmcell-stack/callgraph.json `
  --report emulator/build/cmcell-stack/stack_call_paths.md `
  --json emulator/build/cmcell-stack/stack_call_paths.json
```

Kết quả:

- `stack_call_paths.md`: top 20 đường gọi hữu hạn có tổng static stack cao nhất,
  từng hàm trên đường đi và stack frame của nó.
- `stack_call_paths.json`: dữ liệu máy đọc được, gồm toàn bộ function stack, các
  đường gọi, hàm dynamic/unknown và node không ghép được.

Mặc định script dùng cạnh `direct` và các cạnh `indirect` đã resolve từ function
pointer. Cạnh `manual` vẫn bị bỏ qua vì đó là assertion do người dùng thêm; chỉ
bật chúng sau khi đã kiểm tra:

```powershell
python tools/stack_analysis/stack_callgraph.py `
  --su-dir emulator/build/cmcell-stack `
  --callgraph emulator/build/cmcell-stack/callgraph.json `
  --include-manual `
  --report emulator/build/cmcell-stack/stack_call_paths_all_edges.md
```

Callgraph có nhiều callback có thể tạo số lượng simple path rất lớn. Script
dừng an toàn sau 250.000 trạng thái (`--max-expanded-paths`); khi đó report
ghi rõ **Partial result** và giá trị lớn nhất chưa chắc là global maximum.
Tăng giới hạn khi cần, ví dụ `--max-expanded-paths 1000000`.

Để chỉ kiểm tra một task entry cụ thể, ví dụ `cell_task`, thêm:

```powershell
  --entry cell_task
```

Callgraph mức function không giữ quan hệ giữa từng call-site của một wrapper
chung (ví dụ `execute_command`) và callback argument tương ứng. Vì vậy kết quả
có `indirect` là upper bound: cần đối chiếu call-site trong source trước khi
coi một đường callback là luồng runtime xác định.

Các tùy chọn hữu ích:

```powershell
# Lấy 50 đường thay vì 20, giới hạn mỗi đường tối đa 200 hàm.
python tools/stack_analysis/stack_callgraph.py `
  --su-dir emulator/build/cmcell-stack `
  --callgraph emulator/build/cmcell-stack/callgraph.json `
  --top 50 --max-depth 200 `
  --report emulator/build/cmcell-stack/stack_call_paths.md

# Bao gồm emulator và third-party; mặc định chỉ dùng cellular/, com/, modem/.
python tools/stack_analysis/stack_callgraph.py `
  --su-dir emulator/build/cmcell-stack `
  --callgraph emulator/build/cmcell-stack/callgraph.json `
  --all-sources `
  --report emulator/build/cmcell-stack/stack_call_paths_all_sources.md
```

## Đọc và giới hạn kết quả

Tổng stack trong báo cáo là tổng các **static GCC stack frame** trên đường caller →
callee. Script không giả định stack bằng 0 trong các trường hợp sau:

- `.su` có `dynamic`, `dynamic,bounded` hoặc byte value không xác định: hàm được liệt
  kê là `dynamic/unknown` và không được cộng vào một worst-case giả.
- Hàm có trong callgraph nhưng không có `.su`: được liệt kê là `Callgraph nodes without
  stack usage`; kiểm tra lại source directory hoặc build directory.
- Vòng đệ quy: được liệt kê tại `Recursive cycles`. Không thể có tổng stack hữu hạn nếu
  chưa biết giới hạn depth đệ quy của hệ thống.

Với phân tích worst-case hoàn chỉnh, cần xử lý riêng các hàm dynamic và đặt recursion
depth thực tế theo thiết kế firmware.

## Chỉ xuất inventory stack từng hàm

Nếu chỉ cần danh sách stack frame, không cần callgraph, dùng:

```powershell
python tools/stack_analysis/analyze_callgraph.py `
  --su-dir emulator/build/cmcell-stack `
  --report emulator/build/cmcell-stack/stack_functions.md `
  --json emulator/build/cmcell-stack/stack_functions.json `
  --csv emulator/build/cmcell-stack/stack_functions.csv
```
