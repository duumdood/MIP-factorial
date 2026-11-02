# Factorial & nCk บน MIPS Simulator (Computer Architecture — Software Track)

ต่อยอดจาก **python MIPS simulator V7.1 ของอาจารย์** แล้วเขียนโปรแกรม MIPS assembly
คำนวณ **factorial** และ **nCk** โดย**ไม่ใช้คำสั่งคูณหรือหาร**

## เรื่องที่โปรเจคนี้เล่า
```
factorial.asm (มีฟังก์ชัน mul ที่เขียนเอง)  →  13! OVERFLOW (เกิน 32 bit)  →  nck.asm แบบสามเหลี่ยมปาสคาล (บวกอย่างเดียว) ถึง n = 26
```

## โครงสร้าง
```
sim/                    simulator (ต่อยอดจาก V7.1) — จุดที่เปลี่ยนติดป้าย ★ [เพิ่มใหม่] / ★ [แก้ไข]
  main.py               จุดเริ่มต้น + ตัวเลือก command line
  cpu.py                CPU: register, fetch-execute, คำสั่งทั้งหมด, ตรวจ overflow, trace/step
  isa.py                แปลภาษา assembly: label (2-pass), ชื่อ register, machine code
  memory.py             memory แบบ byte + อ่าน/เขียน word (4 byte)
  tui.py                ★ หน้าจอเต็มแบบ Z80Sim ใน DOSBox (--tui)
  gui.py                ★ โปรแกรมหน้าต่าง (GUI) แบบ QtSpim — เขียนโค้ด/รัน/ดู register ในที่เดียว
  icon.ico, icon.png    ไอคอนของโปรแกรม
MIPS Simulator.pyw      ★ ดับเบิลคลิกเพื่อเปิด GUI
create_shortcut.bat     ★ สร้างไอคอนบน Desktop
build_exe.bat           ★ สร้าง MIPS Simulator.exe
  instructions.txt      โปรแกรมเริ่มต้นของอาจารย์ (บวก 10..1)
programs/
  factorial.asm         ★ โจทย์หลัก: n! ด้วยฟังก์ชัน mul (บวกซ้ำ) + JAL/JR + stack
  nck.asm               ★ ต่อยอด: nCk ด้วยสามเหลี่ยมปาสคาลใน memory
examples/               โปรแกรมตัวอย่างของอาจารย์ (ใช้ตรวจว่า simulator ยังเข้ากันได้)
tests/test_all.py       เทสต์อัตโนมัติ
```

## วิธีใช้
ต้องมี **Python 3.10 ขึ้นไป** (โค้ดและคอมเมนต์ในไฟล์เป็นภาษาอังกฤษ) เปิด Command Prompt แล้ว:
```
cd sim
python main.py ../programs/factorial.asm          แล้วพิมพ์ 5  → 120
python main.py ../programs/nck.asm                แล้วพิมพ์ 26 13 → 10400600
python main.py                                    รัน instructions.txt ของอาจารย์
```

| ตัวเลือก | ความหมาย |
|---|---|
| `--tui` | **หน้าจอเต็มแบบ Z80Sim/DOSBox** (T = ทีละคำสั่ง, G = รันจนจบ, M = เลือก address ของ memory, ↑↓ = เลื่อน memory, R = เริ่มใหม่, Q = ออก) — บน Windows ต้องรัน `pip install windows-curses` ครั้งแรกก่อน และหน้าต่างต้องกว้างอย่างน้อย 90×24 |
| `-t` | trace: แสดงทุกคำสั่งที่รัน + register ที่เปลี่ยน พร้อม**เลขบรรทัดในไฟล์ .asm** เช่น `line  40 [0000000C] JAL 0x30 \| $ra: ...` |
| `-s` | step: รันทีละคำสั่ง (Enter = ถัดไป, r = register, m = memory, g = รันจนจบ, q = ออก) |
| `-v` | แสดงแบบเดิมของอาจารย์ (register + memory ทุกคำสั่ง) |
| `-q` | แสดงเฉพาะผลลัพธ์ (สำหรับตรวจอัตโนมัติ) |
| `--mem 0x4000` | แสดง memory ที่ address นี้ตอนจบ (ดู array ของ nck) |
| `--int` | แสดง register เป็นเลขฐานสิบ |
| `--gui` | **เปิดไฟล์นั้นในโปรแกรมหน้าต่าง (GUI)** แล้วกด Step / Run และปรับ Speed ในหน้าต่าง (`python main.py --gui` เฉย ๆ = เปิดหน้าต่างเปล่า) |

### เปิดแบบดับเบิลคลิก (Windows)
- **`MIPS Simulator.pyw`** ดับเบิลคลิกเปิดได้เลย (ต้องมี Python 3.10+)
- **`create_shortcut.bat`** ดับเบิลคลิกครั้งเดียว ได้ไอคอน "MIPS Simulator" บน Desktop
- **`build_exe.bat`** ดับเบิลคลิกครั้งเดียว ได้ `MIPS Simulator.exe` ที่เปิดได้แม้เครื่องไม่มี Python (ใช้อินเทอร์เน็ตครั้งแรก ประมาณ 1 นาที) วาง .exe ไว้คู่กับโฟลเดอร์ `programs` และ `examples`

### โปรแกรมหน้าต่าง (GUI)
```
cd sim
python gui.py                              เปิดหน้าต่างเปล่า
python gui.py ../programs/factorial.asm    เปิดพร้อมไฟล์
python main.py ../programs/factorial.asm --gui   เหมือนบรรทัดบน แต่สั่งจาก main.py
```
ไม่ต้องติดตั้งอะไรเพิ่ม (ใช้ Tkinter ที่มากับ Python) ในหน้าต่างมี:
- **Open / Save / Examples** เปิด-บันทึกไฟล์ `.asm` หรือเลือกโปรแกรมตัวอย่าง (ให้อาจารย์เปิดไฟล์ที่ต้องการตรวจได้)
- **Editor** เขียนโค้ดสด ๆ มีเลขบรรทัด ไฮไลต์บรรทัดที่จะรันถัดไป ชี้บรรทัดที่เขียนผิด **คลิกเลขบรรทัดเพื่อตั้ง breakpoint**
- **Assemble / Step (F10) / Run–Pause (F5) / Reset** และแถบ **Speed** (1 = ช้า เห็นทีละคำสั่ง, max = เร็วสุด)
- **Registers** ครบ 32 ตัว ตัวที่เพิ่งเปลี่ยนเป็นสีเขียว · **Memory** ใส่ address หรือติดตาม `$sp`
- ปุ่ม **Numbers: HEX / DEC** บนแถบเครื่องมือ เปลี่ยนตัวเลขทั้งหน้าจอพร้อมกัน (register, memory เป็น word ฐานสิบ, trace)
- ธีมสีเข้ม (night mode): บรรทัดที่จะรันถัดไป = ฟ้า, register ที่เปลี่ยน = เขียว, overflow = ส้ม, error/breakpoint = แดง
- เมื่อโปรแกรมขอ input (SYSCALL 5) จะมี**หน้าต่างเด้งขึ้นมา**ให้พิมพ์ตัวเลข (กด Stop program เพื่อหยุด) ค่าที่ใส่จะขึ้นใน Console เป็น `input #1: 10`
- แท็บ **Console** (ผลลัพธ์ + คำเตือน) · **Trace** (มีเลขบรรทัดเหมือน `-t`) · **Machine code**

GUI ใช้ simulator ตัวเดียวกับ command line (cpu.py/isa.py/memory.py ชุดเดียวกัน) — command line ยังใช้ตรวจงานได้เหมือนเดิม

รันเทสต์ (ที่โฟลเดอร์หลัก): `python -m unittest discover -s tests -v`

## สิ่งที่เพิ่ม/แก้จาก V7.1
**เพิ่มใหม่**
- คำสั่งที่รันได้เพิ่ม: `SUB SUBU ADDU AND OR NOR SLT SLTU ANDI SLL SRL JAL JR SYSCALL`
- เรียกฟังก์ชันได้ด้วย `JAL` / `JR $ra` และมี stack (`$sp` เริ่มที่ `0x8000`)
- `SYSCALL`: 1 = พิมพ์ตัวเลข, 5 = รับตัวเลข, 10 = จบ, 11 = พิมพ์ตัวอักษร
- assembler 2-pass: เขียน `loop:` แทนการนับ offset, ใช้ `$t0 $sp $ra`, ใส่คอมเมนต์ `#` และคอมมาได้
- เตือน **OVERFLOW** ของ ADD/ADDI/SUB พร้อมบอก address และค่าที่ถูกต้อง
- โหมด trace / step / หน้าจอเต็ม `--tui` / โปรแกรมหน้าต่าง `gui.py`, เทสต์อัตโนมัติ

**แก้บั๊ก**
- machine code ของ R-type (เช่น ADD) เดิมได้ `00000000` → ตอนนี้ถูกต้อง (ตรวจกับเฉลยแบบฝึกหัด A01)
- BEQ/BNE วาง rs/rt ให้ตรงกับ MIPS จริง
- `SW`/`LW` อ่าน-เขียน 4 byte (เดิมเขียนทั้งค่าลง address เดียว)
- `validate()` พังเมื่อค่าเกิน 32 bit (`int()` ไม่ระบุฐาน 16) → register เป็น 32 bit เสมอ
- `SLTI` เขียนทับค่า register ต้นทางโดยไม่ตั้งใจ
- ไฟล์ที่ไม่มี `.ORG` ทำให้ error, address ของคำสั่งหลัง `HALT` แสดงผิด
- คำสั่งที่ยังไม่รองรับ เดิมถูกข้ามเงียบ ๆ → ตอนนี้แจ้ง error

## ข้อจำกัด
- factorial ถูกต้องถึง n = 12 (13! เกิน 32 bit — เป็นข้อจำกัดของ register ไม่ใช่บั๊ก)
- nck ใช้ได้ถึง n = 33 (ทดสอบครบถึง n = 26)
- ยังไม่รองรับ `LBU LHU SB SH LL SC` และไม่จำลอง branch delay slot / exception จริงของ MIPS
- `HALT` ไม่ใช่คำสั่งของ MIPS จริง (มาจากต้นฉบับ) จึงไม่มี machine code
