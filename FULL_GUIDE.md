# FULL GUIDE — โปรเจค Factorial & nCk บน MIPS Simulator

> คู่มือนี้เขียนให้คนที่ **ไม่เคยเห็นโปรเจคนี้มาก่อน** อ่านแล้วรัน แก้ และทำงานต่อได้เอง
> อ่านจากบนลงล่างได้เลย ถ้ารีบ ให้อ่าน **ส่วนที่ 3 → 5 → 6** ก่อน (ติดตั้ง, รันครั้งแรก, คำสั่งทั้งหมด)

---

## สารบัญ

0. [อ่านคู่มือนี้ยังไง](#0-อ่านคู่มือนี้ยังไง)
1. [โปรเจคนี้คืออะไร](#1-โปรเจคนี้คืออะไร)
2. [ความรู้พื้นฐานที่ต้องรู้ก่อน](#2-ความรู้พื้นฐานที่ต้องรู้ก่อน)
3. [เตรียมเครื่อง (ติดตั้ง Python)](#3-เตรียมเครื่อง-ติดตั้ง-python)
4. [โครงสร้างโฟลเดอร์ ทีละไฟล์](#4-โครงสร้างโฟลเดอร์-ทีละไฟล์)
5. [รันครั้งแรก ทีละขั้น](#5-รันครั้งแรก-ทีละขั้น)
6. [คำสั่ง command line ทุกตัว และสิ่งที่จะเห็น](#6-คำสั่ง-command-line-ทุกตัว-และสิ่งที่จะเห็น)
7. [ข้อความ error ทั้งหมด และวิธีแก้](#7-ข้อความ-error-ทั้งหมด-และวิธีแก้)
8. [โปรแกรมหน้าต่าง (GUI) ทุกปุ่ม](#8-โปรแกรมหน้าต่าง-gui-ทุกปุ่ม)
9. [หน้าจอเต็มแบบ DOSBox (TUI)](#9-หน้าจอเต็มแบบ-dosbox-tui)
10. [เปิดแบบดับเบิลคลิก / ไอคอน / .exe](#10-เปิดแบบดับเบิลคลิก--ไอคอน--exe)
11. [อธิบาย factorial.asm ทีละบรรทัด](#11-อธิบาย-factorialasm-ทีละบรรทัด)
12. [อธิบาย nck.asm](#12-อธิบาย-nckasm)
13. [ภาษา assembly ที่ simulator นี้รับ](#13-ภาษา-assembly-ที่-simulator-นี้รับ)
14. [ข้างใน simulator ทำงานยังไง](#14-ข้างใน-simulator-ทำงานยังไง)
15. [เทสต์อัตโนมัติ](#15-เทสต์อัตโนมัติ)
16. [ถ้าจะทำงานต่อ ต้องทำยังไง](#16-ถ้าจะทำงานต่อ-ต้องทำยังไง)
17. [ข้อจำกัดที่รู้อยู่แล้ว](#17-ข้อจำกัดที่รู้อยู่แล้ว)
18. [แนวทางการ present](#18-แนวทางการ-present)
19. [คำถามที่พบบ่อย / แก้ปัญหา](#19-คำถามที่พบบ่อย--แก้ปัญหา)
20. [โฟลเดอร์ backup](#20-โฟลเดอร์-backup)

---

## 0. อ่านคู่มือนี้ยังไง

- กล่องแบบนี้ คือ **สิ่งที่ต้องพิมพ์** ใน Command Prompt (กด Enter ท้ายบรรทัด)
  ```
  python main.py
  ```
- กล่องที่ขึ้นต้นด้วย "ผลที่ได้" คือ **สิ่งที่จะเห็นบนจอ** (ตัวเลขจริงจากการรัน)
- `G:\Work\year3\com arc\factorial_project` คือที่เก็บโปรเจคในเครื่องเจ้าของ ถ้าเครื่องคุณเก็บที่อื่น ให้เปลี่ยน path เป็นของตัวเอง
- โค้ดและคอมเมนต์ในไฟล์ทั้งหมดเป็น**ภาษาอังกฤษ** (ตามที่ตกลงกัน) ยกเว้น `README.md` กับไฟล์นี้ที่เป็นภาษาไทย
- จุดที่กลุ่มเราเพิ่มหรือแก้จากโค้ดอาจารย์ มีป้ายในคอมเมนต์ว่า `★ [NEW]` (เพิ่มใหม่) หรือ `★ [MODIFIED]` (แก้ของเดิม พร้อมเหตุผล) ถ้าไม่มีป้าย = โค้ดเดิมของอาจารย์

---

## 1. โปรเจคนี้คืออะไร

### 1.1 โจทย์
วิชา **Computer Architecture (com arc)** — term project สายซอฟต์แวร์ อาจารย์ให้เลือกระหว่าง hardware / software / วิดีโอ กลุ่มเราเลือก **software** ตามที่อาจารย์โพสต์ (13 ก.ย.):

> "ทำโปรแกรมคำนวณ factorial และ python simulator ที่รันเอาผลลัพธ์ออกมาได้ … ให้สร้างฟังก์ชันคูณเองในกรณีที่ไม่มีคำสั่งคูณ"

แปลเป็นงานที่ต้องทำ:
1. **simulator** = โปรแกรม Python ที่ "แกล้งเป็น CPU MIPS" อ่านโปรแกรม assembly แล้วรันทีละคำสั่ง
   — เราไม่ได้เขียนจากศูนย์ แต่ **ต่อยอดจาก python MIPS simulator V7.1 ของอาจารย์**
2. **โปรแกรม factorial** เขียนเป็นภาษา **MIPS assembly** (ไม่ใช่ Python) แล้วให้ simulator รัน
3. simulator **ไม่มีคำสั่งคูณ (MUL)** → ต้องเขียน **ฟังก์ชันคูณเอง** ด้วยการบวกซ้ำ ๆ

ต่อมา (13 ต.ค.) อาจารย์โพสต์ `nCkbound.py` ให้คำนวณ **nCk ถึง n ≤ 26** เราจึงทำ `nck.asm` เพิ่ม

### 1.2 เรื่องที่โปรเจคนี้เล่า (สำคัญ ใช้ตอน present)
```
factorial.asm  (เขียนฟังก์ชัน mul เองด้วยการบวกซ้ำ)
     │
     ▼
ลอง n = 13  →  13! = 6,227,020,800  เกินที่ register 32 bit เก็บได้  →  simulator เตือน OVERFLOW
     │
     ▼
ถ้าจะทำ nCk ด้วยสูตร n! / (k!(n-k)!) ใช้ไม่ได้ เพราะ factorial ล้นตั้งแต่ 13!
     │
     ▼
nck.asm  "เปลี่ยนวิธี" ไปใช้สามเหลี่ยมปาสคาล (บวกอย่างเดียว ตัวเลขไม่โตเกินคำตอบ)  →  ได้ถึง n = 26 ตามที่อาจารย์ต้องการ
```
**ข้อควรระวังเวลาพูด:** nck.asm **ไม่ได้เรียกใช้** โค้ดของ factorial.asm เป็นโปรแกรมแยกที่ "เปลี่ยนวิธีคิด" เพราะวิธี factorial ใช้ไม่ได้ อย่าพูดว่า "ต่อยอดจาก factorial"

### 1.3 ผลงานที่มีตอนนี้
| ผลงาน | ไฟล์ | สถานะ |
|---|---|---|
| simulator ที่รันจาก command line | `sim/main.py` + `cpu.py` `isa.py` `memory.py` | ✅ |
| factorial ด้วย mul ที่เขียนเอง | `programs/factorial.asm` | ✅ ถูกถึง 12! |
| nCk แบบสามเหลี่ยมปาสคาล | `programs/nck.asm` | ✅ ถึง n = 26 (ใช้ได้ถึง 33) |
| ตรวจ overflow | ใน `cpu.py` | ✅ |
| trace / step | `-t` `-s` | ✅ |
| หน้าจอเต็มแบบ DOSBox | `sim/tui.py` (`--tui`) | ✅ |
| โปรแกรมหน้าต่าง (GUI) ธีมสีเข้ม | `sim/gui.py` (`--gui`) | ✅ |
| ไอคอน / .exe | `MIPS Simulator.pyw`, `create_shortcut.bat`, `build_exe.bat` | ✅ |
| เทสต์อัตโนมัติ | `tests/test_all.py` | ✅ 11 เทสต์ผ่าน |

### 1.4 ข้อห้ามของกลุ่ม
- มีโปรเจคของเพื่อนอีกกลุ่มที่เคยเอามาดู **ห้ามลอกโค้ดเด็ดขาด** ใช้ได้แค่เป็นแนวคิด
- simulator ที่ ChatGPT เคยทำ (`mips_sim`) ถูกลบทิ้งแล้ว ไม่ได้ใช้

---

## 2. ความรู้พื้นฐานที่ต้องรู้ก่อน

ถ้ารู้แล้วข้ามได้ ส่วนนี้อธิบายแบบง่ายที่สุด

### 2.1 CPU ทำงานยังไง
CPU ทำแค่ 3 อย่างวนไปเรื่อย ๆ เรียกว่า **fetch → decode → execute**
1. **fetch** หยิบคำสั่งถัดไปจาก memory (ดูจาก **PC** = Program Counter = "ตอนนี้อยู่คำสั่งที่เท่าไหร่")
2. **decode** แยกว่าคำสั่งนี้คืออะไร ใช้ register ตัวไหน
3. **execute** ทำจริง เช่น บวกเลขแล้วเก็บผล แล้ว PC ขยับไปคำสั่งถัดไป (หรือกระโดดถ้าเป็นคำสั่ง jump/branch)

### 2.2 register
ช่องเก็บตัวเลขในตัว CPU มี **32 ช่อง** แต่ละช่องเก็บได้ **32 bit** (ตัวเลขช่วง −2,147,483,648 ถึง 2,147,483,647)
มีชื่อเล่นตามหน้าที่:

| ชื่อ | เลข | ใช้ทำอะไร |
|---|---|---|
| `$zero` | 0 | เป็น 0 เสมอ เขียนทับไม่ได้ |
| `$v0` `$v1` | 2–3 | ค่าที่ฟังก์ชันส่งกลับ / เลข service ของ SYSCALL |
| `$a0`–`$a3` | 4–7 | ค่าที่ส่งเข้าฟังก์ชัน (argument) |
| `$t0`–`$t9` | 8–15, 24–25 | ตัวแปรชั่วคราว ฟังก์ชันที่ถูกเรียกเขียนทับได้ |
| `$s0`–`$s7` | 16–23 | ตัวแปรที่ต้อง "คืนค่าเดิม" ถ้าฟังก์ชันจะใช้ ต้องเก็บค่าเก่าลง stack ก่อน |
| `$sp` | 29 | stack pointer ชี้ยอด stack (เริ่มที่ `0x8000`) |
| `$ra` | 31 | return address — `JAL` เขียนให้อัตโนมัติ, `JR $ra` ใช้กลับ |

### 2.3 memory
ตู้เก็บของขนาดใหญ่ ช่องละ **1 byte** แต่ละช่องมีเลขที่อยู่ (address)
ตัวเลข 1 ตัว (word) ใช้ **4 byte = 4 ช่องติดกัน** เรียงแบบ **big-endian** (byte ที่มีค่ามากสุดอยู่ address ต่ำสุด เหมือนเขียนเลขจากซ้ายไปขวา)
```
เก็บเลข 10 (= 0x0000000A) ที่ address 0x4004
address:  4004  4005  4006  4007
ค่า:       00    00    00    0A
```

### 2.4 เลขฐาน 16 (hex)
คอมพิวเตอร์ชอบแสดงเลขเป็นฐาน 16 ใช้ 0–9 และ A–F (A=10 … F=15) เขียนนำหน้าด้วย `0x`
`0x0A` = 10, `0x2D` = 45, `0x78` = 120, `0x4000` = 16384, `0x8000` = 32768
ใน GUI กดปุ่ม **DEC** ได้ถ้าไม่อยากแปลงเอง

### 2.5 assembly → machine code
- **assembly** = คำสั่งที่คนอ่านออก เช่น `ADD $s2, $s1, $zero`
- **machine code** = ตัวเลข 32 bit ที่ CPU อ่านจริง เช่น `02209020`
- โปรแกรมที่แปลงจากอันบนเป็นอันล่าง = **assembler** (อยู่ใน `isa.py`)

ตัวอย่างแปลงคำสั่ง R-type ด้วยมือ (`ADD $s2, $s1, $zero`):
```
opcode  rs($s1=17)  rt($zero=0)  rd($s2=18)  shamt  funct(ADD)
000000    10001       00000        10010     00000   100000
→ 0000 0010 0010 0000 1001 0000 0010 0000  =  0x02209020
```
ตรงกับเฉลยแบบฝึกหัด A01 ของอาจารย์ (V7.1 เดิมให้ `00000000` ซึ่งผิด เราแก้แล้ว)

### 2.6 stack และการเรียกฟังก์ชัน
- `JAL label` = กระโดดไปฟังก์ชัน และจำที่กลับไว้ใน `$ra`
- `JR $ra` = กลับไปที่ที่จำไว้
- ถ้าฟังก์ชัน A เรียกฟังก์ชัน B อีกที `$ra` ของ A จะถูกเขียนทับ → A ต้อง **เก็บ `$ra` ลง stack ก่อน** แล้วค่อยเอาคืนก่อน `JR`
- stack อยู่ใน memory เริ่มที่ `0x8000` แล้ว **โตลงล่าง** (จองที่ = ลบ `$sp`, คืนที่ = บวก `$sp`)

### 2.7 SYSCALL
คำสั่งพิเศษให้โปรแกรมคุยกับโลกภายนอก ใส่เลข service ใน `$v0` แล้วสั่ง `SYSCALL`

| `$v0` | ทำอะไร | ใช้ register ไหน |
|---|---|---|
| 1 | พิมพ์ตัวเลข | ตัวเลขอยู่ใน `$a0` |
| 5 | รับตัวเลขจากคีย์บอร์ด | ผลเก็บใน `$v0` |
| 10 | จบโปรแกรม | – |
| 11 | พิมพ์ตัวอักษร 1 ตัว | รหัส ASCII ใน `$a0` (10 = ขึ้นบรรทัดใหม่) |

### 2.8 overflow
ถ้าผลบวกเกินช่วงที่ 32 bit เก็บได้ ตัวเลขจะ "วนกลับ" เป็นค่าผิด (เหมือนมาตรวัดรถที่เกิน 999999 แล้วกลับเป็น 0)
MIPS จริงจะหยุดโปรแกรม (exception) แต่ simulator ของเรา **เตือนแล้วรันต่อ** เพื่อให้เห็นว่าผลผิดไปยังไง

---

## 3. เตรียมเครื่อง (ติดตั้ง Python)

### 3.1 ต้องมี Python 3.10 ขึ้นไป
เปิด Command Prompt (กด `Win + R` พิมพ์ `cmd` กด Enter) แล้วพิมพ์
```
python --version
```
ผลที่ได้ (ตัวอย่าง):
```
Python 3.12.4
```
- ถ้าเลขตั้งแต่ **3.10** ขึ้นไป → ใช้ได้
- ถ้าขึ้น `'python' is not recognized ...` หรือเปิด Microsoft Store → ยังไม่ได้ติดตั้ง
  1. โหลดจาก https://www.python.org/downloads/
  2. ตอนติดตั้ง **ติ๊ก "Add python.exe to PATH"** (สำคัญมาก)
  3. ปิด-เปิด Command Prompt ใหม่ แล้วลอง `python --version` อีกครั้ง
- ถ้าต่ำกว่า 3.10 → `isa.py` ใช้คำสั่ง `match` ที่มีตั้งแต่ 3.10 จะ error ทันที ให้ติดตั้งใหม่

### 3.2 ของที่ไม่ต้องติดตั้ง
- **GUI** ใช้ Tkinter ที่มากับ Python อยู่แล้ว
- command line ปกติไม่ต้องลงอะไรเพิ่ม

### 3.3 ของที่ต้องติดตั้งเฉพาะบางโหมด
| ใช้อะไร | ต้องพิมพ์ครั้งเดียว |
|---|---|
| หน้าจอเต็ม `--tui` บน Windows | `pip install windows-curses` |
| เทสต์ด้วย pytest (ไม่บังคับ) | `pip install pytest` |
| สร้าง .exe | ไม่ต้องพิมพ์เอง `build_exe.bat` ติดตั้ง PyInstaller ให้ (ต้องมีเน็ตครั้งแรก) |

---

## 4. โครงสร้างโฟลเดอร์ ทีละไฟล์

```
factorial_project/
├─ README.md                 สรุปโปรเจค (ไทย) — อ่านเร็ว ๆ
├─ FULL_GUIDE.md             ไฟล์นี้ — อ่านละเอียด
├─ MIPS Simulator.pyw        ดับเบิลคลิกเปิด GUI (ไม่มีหน้าต่างดำ)
├─ create_shortcut.bat       ดับเบิลคลิกครั้งเดียว → ไอคอนบน Desktop
├─ build_exe.bat             ดับเบิลคลิกครั้งเดียว → MIPS Simulator.exe
├─ .gitignore                บอก git ว่าไม่ต้องเก็บไฟล์ขยะ (__pycache__, build)
│
├─ sim/                      ★ ตัว simulator ทั้งหมดอยู่ที่นี่ — ต้อง cd เข้ามาก่อนรันเสมอ
│  ├─ main.py                จุดเริ่มต้น: อ่านคำสั่ง command line แล้วสั่งงานส่วนอื่น
│  ├─ cpu.py                 CPU: register 32 ตัว, PC, fetch-decode-execute, SYSCALL, overflow, trace, step
│  ├─ isa.py                 assembler: แยกคำสั่ง, label 2-pass, ชื่อ register, แปลงเป็น machine code
│  ├─ memory.py              memory แบบ byte + อ่าน/เขียนทีละ word (4 byte)
│  ├─ tui.py                 หน้าจอเต็มแบบ Z80Sim ใน DOSBox (--tui)
│  ├─ gui.py                 โปรแกรมหน้าต่าง (--gui)
│  ├─ instructions.txt       โปรแกรมเริ่มต้นของอาจารย์ (บวก 10+9+…+1) รันเมื่อไม่ระบุไฟล์
│  ├─ icon.ico, icon.png     ไอคอนของโปรแกรม
│  └─ __pycache__/           Python สร้างเอง ลบได้ ไม่ต้องสนใจ
│
├─ programs/                 ★ โปรแกรม assembly ที่เราเขียน
│  ├─ factorial.asm          n! ด้วย mul ที่เขียนเอง
│  └─ nck.asm                nCk ด้วยสามเหลี่ยมปาสคาล
│
├─ examples/                 โปรแกรมตัวอย่าง (ใช้เช็คว่าแก้ simulator แล้วของเดิมยังรันได้)
│  ├─ teacher_sum_10_to_1.txt          ของอาจารย์ (เหมือน instructions.txt)
│  ├─ teacher_instruction_test.txt     ของอาจารย์ ทดสอบคำสั่งหลายแบบ
│  └─ fibonacci.asm                    (ถ้ามี) ตัวอย่างที่เขียนเพิ่มเอง
│
├─ tests/
│  └─ test_all.py            เทสต์อัตโนมัติ 11 ชุด
│
└─ backup_before_.../        ไฟล์สำรองก่อนแก้แต่ละครั้ง (ดูส่วนที่ 20)
```

**กฎสำคัญ:** คำสั่ง `python main.py ...` ต้องรัน **ในโฟลเดอร์ `sim`** เพราะ path ของโปรแกรมเขียนแบบ `../programs/...` (`..` = ถอยออกไป 1 โฟลเดอร์)

---

## 5. รันครั้งแรก ทีละขั้น

### ขั้นที่ 1 — เปิด Command Prompt แล้วเข้าโฟลเดอร์ sim
```
G:
cd "G:\Work\year3\com arc\factorial_project\sim"
```
- บรรทัดแรก `G:` = สลับไปไดรฟ์ G (ถ้าโปรเจคอยู่ไดรฟ์ C ไม่ต้องพิมพ์)
- ต้องมี **เครื่องหมายคำพูด** ครอบ path เพราะ `com arc` มีช่องว่าง
- **ทางลัด:** เปิดโฟลเดอร์ `sim` ใน File Explorer → คลิกที่ช่อง address ด้านบน → พิมพ์ `cmd` → Enter จะได้ Command Prompt ที่อยู่ในโฟลเดอร์นั้นเลย

เช็คว่าอยู่ถูกที่: บรรทัดรอพิมพ์ต้องลงท้ายด้วย `\sim>`
```
G:\Work\year3\com arc\factorial_project\sim>
```

### ขั้นที่ 2 — รันโปรแกรมของอาจารย์ (ไม่ต้องใส่ input)
```
python main.py
```
ผลที่ได้ (ส่วนท้าย):
```
Last STATE
Registers:
 0- 4   00000000   00000000   00000000   00000037   00000000
...
Executed 33 instructions
```
`$3` (ช่องที่ 4 ของแถวแรก) = `0x37` = **55** = 10+9+…+1 ✅ แปลว่า simulator ทำงาน

### ขั้นที่ 3 — รัน factorial
```
python main.py ../programs/factorial.asm
```
จะเห็นตาราง machine code ยาว ๆ แล้วหยุดรอ:
```
================================================================================
Running program ../programs/factorial.asm
================================================================================
>>> The program is waiting for input #1 (SYSCALL 5): type a number and press Enter:
```
พิมพ์ `5` แล้ว Enter
```
120
Last STATE
...
Executed 101 instructions
```
`120` คือ 5! ✅

### ขั้นที่ 4 — รัน nCk
```
python main.py ../programs/nck.asm
```
มันจะถาม **2 ครั้ง** (`input #1` = n, `input #2` = k) หรือพิมพ์ทีเดียว `26 13` ก็ได้
```
10400600
```
26C13 = 10,400,600 ✅

### ขั้นที่ 5 — เปิดหน้าต่าง GUI
```
python main.py ../programs/factorial.asm --gui
```
หน้าต่างสีเข้มจะเปิดพร้อมโค้ด กด **Run (F5)** แล้วใส่ 5 ในหน้าต่างที่เด้งขึ้นมา (รายละเอียดในส่วนที่ 8)

---

## 6. คำสั่ง command line ทุกตัว และสิ่งที่จะเห็น

รูปแบบทั่วไป:
```
python main.py [ไฟล์โปรแกรม] [ตัวเลือก...]
```
- ไม่ใส่ไฟล์ = รัน `instructions.txt`
- ใส่ตัวเลือกหลายตัวพร้อมกันได้ เช่น `-t --int --mem 0x4000`
- ดูรายการตัวเลือกทั้งหมด: `python main.py -h`

### 6.1 ไม่ใส่ตัวเลือก (โหมดปกติ)
```
python main.py ../programs/factorial.asm
```
สิ่งที่เห็นตามลำดับ:
1. **ตาราง machine code** — ทุกคำสั่งในไฟล์ 1 บรรทัด
   ```
   00000000 None .ORG 0
   00000000 34020005 ORI $v0 $zero 5
   0000000c 0c00000c JAL 0x30
   ↑address ↑machine code ↑คำสั่ง (label ถูกแปลงเป็นตัวเลขแล้ว)
   ```
   `.ORG` ขึ้น `None` เพราะเป็นคำสั่งบอก assembler (ตั้งจุดเริ่ม) ไม่ใช่คำสั่งจริงของ CPU
2. เส้น `=====` + `Running program ...`
3. ข้อความถาม input (ถ้าโปรแกรมใช้ SYSCALL 5)
4. **ผลลัพธ์** ที่โปรแกรมพิมพ์ด้วย SYSCALL 1/11
5. **Last STATE** — register ทั้ง 32 ตัว (ฐาน 16, แถวละ 5 ตัว, `0- 4` = register 0 ถึง 4)
6. **Memory** — 100 byte แรก (ส่วนใหญ่คือ machine code ของโปรแกรมเอง)
7. `Executed N instructions` — จำนวนคำสั่งที่รันจริง (+ คำเตือนถ้ามี overflow)

### 6.2 `-q` (quiet) — แสดงแค่ผลลัพธ์
```
python main.py ../programs/factorial.asm -q
```
```
>>> The program is waiting for input #1 (SYSCALL 5): type a number and press Enter: 5
120
```
- ไม่มีตาราง ไม่มี Last STATE — มีแค่สิ่งที่โปรแกรม assembly พิมพ์เอง
- **ใช้สำหรับตรวจอัตโนมัติ (autolab)**
- ข้อความ `>>> ... waiting for input` จะขึ้น **เฉพาะตอนคนพิมพ์เองที่คีย์บอร์ด** ถ้าป้อน input จากไฟล์ จะไม่ขึ้น:
  ```
  echo 5 | python main.py ../programs/factorial.asm -q
  ```
  ผลที่ได้ มีบรรทัดเดียว:
  ```
  120
  ```
  (ข้อความถามถูกส่งไปทาง stderr จึงไม่ปนกับผลลัพธ์ที่ autolab เทียบ)
- ถ้ามี error จะได้ **exit code 1** (ระบบตรวจรู้ว่าล้มเหลว)

### 6.3 `-t` (trace) — ดูทุกคำสั่งที่รัน
```
python main.py ../programs/factorial.asm -t
```
หลัง `Running program` จะได้ 1 บรรทัดต่อ 1 คำสั่งที่รันจริง:
```
line  36 [00000000] ORI $v0 $zero 5            | $v0: 00000000 -> 00000005
line  38 [00000008] ADD $a0 $v0 $zero          | $a0: 00000000 -> 00000003
line  40 [0000000C] JAL 0x30                   | $ra: 00000000 -> 00000010
line  68 [00000030] ADDI $sp $sp -16           | $sp: 00008000 -> 00007FF0
line  69 [00000034] SW $ra 12($sp)             |
```
| ส่วน | ความหมาย |
|---|---|
| `line  40` | บรรทัดที่ 40 ในไฟล์ `.asm` — เปิดไฟล์เทียบได้ |
| `[0000000C]` | address ของคำสั่ง |
| `JAL 0x30` | คำสั่ง (label ถูกแปลงเป็นตัวเลขแล้ว) |
| `$ra: 00000000 -> 00000010` | register ที่เปลี่ยน: ค่าเก่า → ค่าใหม่ (ว่าง = ไม่มี register เปลี่ยน เช่น SW เขียน memory) |

- ตารางบน (machine code) เรียงตาม **ไฟล์** ส่วน trace เรียงตาม **ลำดับที่รันจริง** จะเห็นการกระโดดและวน loop
- โปรแกรมยาว trace ก็ยาว (factorial 5 = 101 บรรทัด, 12 = หลายพัน) ดูในหน้าต่าง GUI สะดวกกว่า

### 6.4 `-s` (step) — รันทีละคำสั่ง กด Enter ไปเรื่อย ๆ
```
python main.py -s
```
แต่ละคำสั่งจะหยุดรอ:
```
line   2 [00000000] ORI $2 $0 10               | $v0: 00000000 -> 0000000A
  [Enter]=next  r=registers  m=memory  g=run to end  q=quit >
```
| กด | ผล |
|---|---|
| Enter | รันคำสั่งถัดไป |
| `r` แล้ว Enter | แสดง register ทั้ง 32 ตัว พร้อมชื่อ |
| `m` แล้ว Enter | แสดง memory บริเวณ stack (ที่ `$sp` ชี้) |
| `m 0x4000` แล้ว Enter | แสดง memory ที่ address นั้น |
| `g` แล้ว Enter | รันที่เหลือจนจบ |
| `q` แล้ว Enter | หยุดโปรแกรม |
| Ctrl+C | ออกแบบไม่ error |

เหมือนคำสั่ง T ใน Z80Sim ของวิชา Microprocessor Lab

### 6.5 `-v` (verbose) — แบบเดิมของอาจารย์
```
python main.py -v
```
หลัง **ทุกคำสั่ง** จะพิมพ์ `Executed: ...` + register ทั้งหมด + memory → ยาวมาก ใช้กับโปรแกรมสั้นเท่านั้น (ไว้แสดงว่าเรายังเก็บพฤติกรรมเดิมของอาจารย์ไว้)

### 6.6 `--mem ADDR` — ดู memory ตำแหน่งที่ต้องการตอนจบ
```
python main.py ../programs/nck.asm --mem 0x4000
```
ใส่ `10` และ `4` → ท้ายผลลัพธ์จะมี:
```
Memory at 0x4000:
Memory:
    4000: 00 00 00 01 00 00 00 0a 00 00 00 2d 00 00 00 78
    4010: 00 00 00 d2 00 00 00 00 00 00 00 00 00 00 00 00
```
อ่านทีละ 4 byte: `1, 10, 45, 120, 210` = แถวที่ 10 ของสามเหลี่ยมปาสคาล (10C0 ถึง 10C4) และ 10C4 = 210 คือคำตอบ
**ทำไม 0x4000?** เพราะ `nck.asm` เลือกเก็บ array ไว้ที่นั่นเอง (ดูส่วนที่ 12) — ถ้าใส่ address อื่นจะไปดูที่อื่น

### 6.7 `--int` — register เป็นเลขฐานสิบ
```
python main.py ../programs/factorial.asm --int
```
Last STATE จะแสดงเลขฐานสิบ (มีลบได้) แทน hex

### 6.8 `--gui` — เปิดในโปรแกรมหน้าต่าง
```
python main.py ../programs/factorial.asm --gui
python main.py --gui                          ← หน้าต่างเปล่า
```
- หน้าต่างเปิดพร้อมโหลดและ assemble ไฟล์ให้แล้ว
- ความเร็ว / Step / Run / HEX-DEC ปรับในหน้าต่าง
- Command Prompt จะรอจนกว่าจะปิดหน้าต่าง
- ถ้าชื่อไฟล์ผิด: `*** ERROR: file not found: ...` และไม่เปิดหน้าต่าง

### 6.9 `--tui` — หน้าจอเต็มแบบ DOSBox
```
python main.py ../programs/factorial.asm --tui
```
ดูส่วนที่ 9

### 6.10 `--max-steps N` — กัน loop ไม่รู้จบ
ค่าเริ่มต้น 1,000,000 คำสั่ง ถ้าเกินจะหยุดพร้อม error
```
python main.py myprog.asm --max-steps 5000
```

### 6.11 ตารางสรุป
| คำสั่ง | ใช้เมื่อ |
|---|---|
| `python main.py` | เช็คว่า simulator ยังทำงาน (ต้องได้ $3 = 0x37) |
| `python main.py FILE` | รันปกติ ดูผล + สถานะสุดท้าย |
| `python main.py FILE -q` | ตรวจคำตอบ / autolab |
| `python main.py FILE -t` | ดูว่าแต่ละคำสั่งทำอะไร (debug, present) |
| `python main.py FILE -s` | ไล่ทีละคำสั่งด้วยมือ |
| `python main.py FILE -v` | แบบเดิมของอาจารย์ |
| `python main.py FILE --mem 0x4000` | ดู array ใน memory |
| `python main.py FILE --int` | register ฐานสิบ |
| `python main.py FILE --gui` | เปิดหน้าต่าง |
| `python main.py FILE --tui` | หน้าจอเต็มแบบ DOSBox |

---

## 7. ข้อความ error ทั้งหมด และวิธีแก้

ทุก error ขึ้นต้นด้วย `*** ERROR:` และโปรแกรมจบด้วย exit code 1

| ข้อความ | สาเหตุ | แก้ |
|---|---|---|
| `[Errno 2] No such file or directory: 'xxx'` | หาไฟล์ไม่เจอ | เช็คว่าอยู่ในโฟลเดอร์ `sim` และพิมพ์ path ถูก (`../programs/...`) |
| `file not found: xxx` | เหมือนข้างบน แต่มาจาก `--gui` | เหมือนข้างบน |
| `invalid instruction 'FOO $t0': unknown instruction 'FOO'` | คำสั่งที่ไม่รู้จัก / สะกดผิด | ดูรายการคำสั่งในส่วนที่ 13 (ใน GUI จะบอกเลขบรรทัดและไฮไลต์แดงให้ด้วย) |
| `invalid instruction 'ADD $t10 ...': unknown register '$t10'` | ชื่อ register ผิด | ใช้ `$t0`–`$t9`, `$s0`–`$s7` ฯลฯ |
| `line 12: invalid label name '...'` | ชื่อ label มีอักขระแปลก | ใช้ตัวอักษร ตัวเลข `_` และห้ามขึ้นต้นด้วยตัวเลข |
| `line 12: duplicate label 'loop'` | ตั้งชื่อ label ซ้ำ | เปลี่ยนชื่อ |
| `line 31: .ORG must come before all instructions and labels` | `.ORG` ไม่ได้อยู่บนสุด | ย้าย `.ORG` ขึ้นเป็นคำสั่งแรก |
| `no instructions found in the program` | ไฟล์ว่าง / มีแต่คอมเมนต์ | ใส่คำสั่ง |
| `input must be an integer` | ใส่ input ที่ไม่ใช่ตัวเลข (เช่น `abc`) | ใส่จำนวนเต็ม (`12`, `-3`, `0x1F` ได้) |
| `no input (SYSCALL 5 needs a number)` | โปรแกรมรอ input แต่ไม่มีให้ (เช่น ป้อนจากไฟล์ว่าง) | ป้อน input ให้ครบ |
| `more than 1,000,000 instructions executed (possible infinite loop)` | loop ไม่รู้จบ | เช็คเงื่อนไข branch หรือเพิ่ม `--max-steps` |
| `unknown SYSCALL service N` | `$v0` ไม่ใช่ 1/5/10/11 ตอนเรียก SYSCALL | ตั้ง `$v0` ให้ถูกก่อน SYSCALL |
| `The --tui mode needs the curses module...` | ยังไม่ได้ลง windows-curses | `pip install windows-curses` |

**คำเตือน (ไม่ใช่ error โปรแกรมรันต่อ):**
```
*** OVERFLOW at 00000098  ADD $v0 $v0 $a0
    correct value = 2,395,008,000  but a 32-bit register can only hold = -1,899,959,296
...
Executed 533 instructions   WARNING: 1 overflow(s), the result may be wrong
```
อ่านว่า: คำสั่งที่ address 0x98 (`ADD` ใน `mul`) ควรได้ 2,395,008,000 แต่ register เก็บได้แค่ −1,899,959,296 → ผลสุดท้าย (1932053504) **ผิด** — นี่คือสิ่งที่เราตั้งใจโชว์ตอนรัน 13!
(ถ้า overflow หลายครั้ง จะแสดงรายละเอียดแค่ 3 ครั้งแรก)

---

## 8. โปรแกรมหน้าต่าง (GUI) ทุกปุ่ม

### 8.1 เปิดยังไง (เลือกวิธีไหนก็ได้)
| วิธี | ทำยังไง |
|---|---|
| จาก main.py | `python main.py ../programs/factorial.asm --gui` |
| เรียก gui.py ตรง | `python gui.py` หรือ `python gui.py ../programs/factorial.asm` |
| ดับเบิลคลิก | `MIPS Simulator.pyw` ในโฟลเดอร์หลัก |
| ไอคอน Desktop | หลังรัน `create_shortcut.bat` |
| .exe | `MIPS Simulator.exe` หลังรัน `build_exe.bat` |

### 8.2 หน้าตา
```
┌─ แถบเครื่องมือ ──────────────────────────────────────────────────────────────┐
│ Open  Save  Examples▾ │ Assemble  Step(F10)  Run(F5)  Reset │ Speed ━━●━ 6/10 │ Numbers [HEX][DEC] │
├───────────────────────────────────────┬──────────────────────────────────────┤
│  Editor (โค้ด + เลขบรรทัด)              │  Registers (32 ตัว, ตัวที่เปลี่ยน=เขียว) │
│  ● ← breakpoint (คลิกเลขบรรทัด)         │                                      │
│  ▓▓ บรรทัดที่จะรันถัดไป (ฟ้า)            │  Memory  address [0x4000] ☑Follow $sp │
├───────────────────────────────────────┴──────────────────────────────────────┤
│ [Console] [Trace] [Machine code]                                              │
├───────────────────────────────────────────────────────────────────────────────┤
│ สถานะ                                    PC = ...  steps = ...  ready/running │
└───────────────────────────────────────────────────────────────────────────────┘
```
ลากเส้นแบ่งระหว่างส่วนต่าง ๆ เพื่อขยาย/ย่อได้

### 8.3 แถบเครื่องมือ
| ปุ่ม | ทำอะไร |
|---|---|
| **Open** (Ctrl+O) | เปิดไฟล์ `.asm` / `.s` / `.txt` แล้ว assemble ให้ทันที |
| **Save** (Ctrl+S) | บันทึกโค้ดใน editor (ถ้ายังไม่มีชื่อไฟล์จะถามที่เก็บ) |
| **Examples ▾** | เลือกโปรแกรมใน `programs/*.asm` และ `examples/*.txt` (ไฟล์ `.asm` ใน examples ต้องเปิดผ่าน Open) |
| **Assemble** | แปลโค้ดใน editor ใหม่ และเริ่ม CPU ใหม่ (register กลับเป็น 0) |
| **Step (F10)** | รัน 1 คำสั่ง |
| **Run (F5)** | รันต่อเนื่องตามความเร็ว — ระหว่างรัน ปุ่มเปลี่ยนเป็น **Pause (F5)** กดอีกทีเพื่อหยุดชั่วคราว |
| **Reset** | เริ่มโปรแกรมใหม่ตั้งแต่ต้น (เหมือน Assemble) |
| **Speed** | 1 = ช้าสุด (1 วินาที/คำสั่ง) … 9 = เร็ว … **max** = เร็วสุด (รันทีละ 5,000 คำสั่งแล้วค่อยวาดจอ) |
| **Numbers HEX / DEC** | เปลี่ยนตัวเลข **ทั้งหน้าจอพร้อมกัน**: register, memory, trace (address ยังเป็น hex เสมอ) |

ถ้าแก้โค้ดใน editor แล้วกด Step/Run เลย โปรแกรมจะ assemble ใหม่ให้อัตโนมัติ

### 8.4 Editor
- พิมพ์/แก้โค้ดได้สด ๆ คอมเมนต์ (`# ...`) เป็นสีเทา
- **แถบฟ้า** = คำสั่งที่จะรัน **ถัดไป**
- **แถบแดง** = บรรทัดที่ assemble ไม่ผ่าน (ข้อความ error อยู่ใน Console)
- **คลิกเลขบรรทัด** = ตั้ง/ลบ **breakpoint** (จุดแดง) — ตอนกด Run จะหยุดก่อนรันบรรทัดนั้น
  - คลิกบรรทัดว่าง/คอมเมนต์/label เปล่า → จุดจะย้ายไปคำสั่งถัดไปให้เอง

### 8.5 Registers
- 32 ตัว แสดง `$ชื่อ (เลข)  ค่า`
- **สีเขียว** = เพิ่งเปลี่ยนจากคำสั่งล่าสุด
- โหมด DEC แสดงแบบมีเครื่องหมาย (เช่น `$sp` หลัง `ADDI $sp,$sp,-16` = 32752)

### 8.6 Memory
- แสดง 15 แถว แถวละ 8 byte
- **Follow $sp** (ติ๊กไว้ตั้งแต่เปิด) = เลื่อนตาม stack อัตโนมัติ แถวที่ `$sp` ชี้มีป้าย `◄ $sp` สีเขียว — เหมาะกับ factorial
- **ดู address อื่น** (เช่น array ของ nck): เอาติ๊ก Follow $sp ออก → พิมพ์ `0x4000` ในช่อง address → Enter
- โหมด **HEX**: `address: byte ทั้ง 8 ตัว   word(hex) 2 ตัว`
- โหมด **DEC**: `address: word(ฐานสิบ) 2 ตัว   byte ทั้ง 8 ตัว` — ตัวเลขฐานสิบอยู่ด้านหน้า เห็นได้แม้ช่องแคบ
  ```
  00004000:           1          10   00 00 00 01  00 00 00 0A
  00004008:          45         120   00 00 00 2D  00 00 00 78
  ```

### 8.7 แท็บด้านล่าง
| แท็บ | มีอะไร |
|---|---|
| **Console** | ข้อความระบบ (เทา), input ที่เราใส่ `input #1: 10` (ฟ้า), **ผลลัพธ์ของโปรแกรม** (ขาว), overflow (ส้ม), error (แดง), สรุปตอนจบ |
| **Trace** | เหมือน `-t` (มี `line NN`) ตามปุ่ม HEX/DEC — ปุ่ม **Open in large window** เปิดหน้าต่างใหญ่ที่อัปเดตสด (ติ๊ก Follow newest line = เลื่อนตามบรรทัดล่าสุด), ปุ่ม **Clear** ล้าง |
| **Machine code** | ตาราง Address / Code / Line / Label / Instruction |

ใน Console: บรรทัด `input #...` = สิ่งที่**เรา**พิมพ์, ตัวเลขที่ไม่มีอะไรนำหน้า = สิ่งที่**โปรแกรม MIPS** พิมพ์เองด้วย SYSCALL (simulator ไม่เติมคำว่า "Result" ให้ เพราะต้องแสดงตามที่โปรแกรม assembly พิมพ์จริงเท่านั้น)

### 8.8 หน้าต่างถาม input
เมื่อโปรแกรมถึง SYSCALL 5 จะมีหน้าต่างเด้งกลางจอ:
```
The program asks for a number  (input #1)
SYSCALL 5 at line 44. Type an integer (several can be separated by spaces).
[                    ]
                               [OK] [Stop program]
```
- พิมพ์ตัวเลขแล้ว Enter / OK
- ใส่หลายตัวคั่นด้วยเว้นวรรคได้ (เช่น `10 4` ให้ nck ทีเดียว)
- ใส่ไม่ใช่ตัวเลข → ขึ้นแดงใต้ช่อง ไม่ปิดหน้าต่าง
- **Stop program** / Esc → หยุดชั่วคราว กด Step/Run เพื่อให้ถามใหม่

### 8.9 สีที่ใช้ (ธีมกลางคืน)
| ส่วน | สี |
|---|---|
| พื้นหลัง | `#0D1117` กรมท่าเกือบดำ |
| แผงโค้ด/register/memory | `#161B22` |
| ตัวอักษร | `#E6EDF3` ขาวนวล |
| ตัวรอง / คอมเมนต์ / เลขบรรทัด | `#8B949E` เทา |
| บรรทัดที่จะรันถัดไป / input | ฟ้า `#58A6FF` |
| register ที่เปลี่ยน | เขียว `#3FB950` |
| overflow | ส้ม `#F0B040` |
| error / breakpoint | แดง `#F85149` |

แก้สีได้ที่ค่าคงที่ด้านบนของ `gui.py` (`BG`, `PANEL`, `FG`, ...) และฟังก์ชัน `apply_theme()`

### 8.10 ตัวอย่างใช้งาน: ดูสามเหลี่ยมปาสคาลถูกสร้าง
1. `python main.py ../programs/nck.asm --gui`
2. เอาติ๊ก **Follow $sp** ออก → พิมพ์ `0x4000` ช่อง address → Enter
3. กด **DEC**
4. ตั้ง Speed ประมาณ 6
5. กด **Run** → ใส่ `10 4` → OK
6. ดู memory ด้านขวา: ตัวเลข 1, 10, 45, 120, 210 ค่อย ๆ ถูกเขียน, Console ขึ้น `210`

---

## 9. หน้าจอเต็มแบบ DOSBox (TUI)

```
pip install windows-curses          ← ครั้งแรกครั้งเดียว (Windows)
python main.py ../programs/factorial.asm --tui
```
- หน้าต่าง Command Prompt ต้องกว้างอย่างน้อย **90 × 24** ตัวอักษร (ขยายหน้าต่างก่อนรัน)
- แบ่งจอเป็น: Registers / Program (ลูกศร ► ชี้คำสั่งถัดไป) / Memory / Output / Message

| ปุ่ม | ทำอะไร |
|---|---|
| `T` / Enter / Space | รัน 1 คำสั่ง |
| `G` | รันจนจบ |
| `M` | เลือก address ของ memory (ว่าง = ตาม `$sp`) |
| ↑ ↓ | เลื่อน memory |
| `R` | เริ่มใหม่ |
| `Q` | ออก |

ทำไว้ให้หน้าตาคล้าย Z80Sim ใน DOSBox ที่ใช้ในวิชา Microprocessor Lab

---

## 10. เปิดแบบดับเบิลคลิก / ไอคอน / .exe

### 10.1 `MIPS Simulator.pyw`
ดับเบิลคลิกได้เลย (ต้องมี Python 3.10+) เปิด GUI โดยไม่มีหน้าต่างดำ ถ้า Python เก่าเกินจะขึ้นกล่องเตือน

### 10.2 `create_shortcut.bat`
ดับเบิลคลิกครั้งเดียว → ได้ไอคอน **MIPS Simulator** บน Desktop
- ถ้าขึ้น `Could not find Python` → ติดตั้ง Python และติ๊ก Add to PATH
- **ย้ายโฟลเดอร์โปรเจค** แล้วต้องรันใหม่ (ไอคอนจำ path เดิม)
- แก้โค้ด **ไม่ต้อง**รันใหม่ ไอคอนเปิดไฟล์ล่าสุดเสมอ

### 10.3 `build_exe.bat` → `MIPS Simulator.exe`
ดับเบิลคลิกครั้งเดียว ใช้เวลาประมาณ 1 นาที (ต้องมีเน็ตครั้งแรกเพื่อลง PyInstaller) ได้ `.exe` ในโฟลเดอร์หลัก
- **เปิดได้แม้เครื่องไม่มี Python** → ให้อาจารย์ลองเองได้
- **.exe คือ GUI อย่างเดียว** ใช้ `-q` `-t` ไม่ได้ — การตรวจแบบ command line ยังใช้ `python main.py`
- ลากไฟล์ `.asm` ไปวางบนไอคอน .exe → เปิดพร้อมไฟล์นั้น
- วาง .exe ไว้คู่กับโฟลเดอร์ `programs` และ `examples` (ไม่งั้นเมนู Examples ว่าง)
- เปิดครั้งแรกช้า 2–5 วินาที (แตกไฟล์ตัวเอง)
- Windows อาจขึ้น "Windows protected your PC" เพราะไม่มีลายเซ็น → More info → Run anyway
- **แก้โค้ดแล้วต้อง build ใหม่** (.exe เก็บโค้ดตอน build ไว้)

---

## 11. อธิบาย factorial.asm ทีละบรรทัด

ไฟล์: `programs/factorial.asm` (มีคอมเมนต์ภาษาอังกฤษทุกบรรทัดในไฟล์)

### 11.1 แนวคิด
แปลมาจาก `factorial_no_mul_1.py` ของอาจารย์:
```python
fac = 1
for i in range(2, n+1):
    fac = mul(fac, i)          # mul = บวก fac ซ้ำ i ครั้ง
```
มี 3 ส่วน: **main** → เรียก **factorial** → factorial เรียก **mul** หลายครั้ง

### 11.2 main
```asm
.ORG 0
main:
    ORI   $v0, $zero, 5      # $v0 = 5  (service: อ่านตัวเลข)
    SYSCALL                  # $v0 = n ที่ผู้ใช้พิมพ์
    ADD   $a0, $v0, $zero    # ส่ง n เข้าฟังก์ชันผ่าน $a0
    JAL   factorial          # เรียก factorial(n), $ra = ที่อยู่บรรทัดถัดไป
    ADD   $a0, $v0, $zero    # ผลอยู่ใน $v0 → ย้ายไป $a0 เพื่อพิมพ์
    ORI   $v0, $zero, 1      # service 1 = พิมพ์ตัวเลข
    SYSCALL
    ORI   $a0, $zero, 10     # 10 = ASCII ขึ้นบรรทัดใหม่
    ORI   $v0, $zero, 11     # service 11 = พิมพ์ตัวอักษร
    SYSCALL
    ORI   $v0, $zero, 10     # service 10 = จบโปรแกรม
    SYSCALL
```
- ไม่มีคำสั่ง `LI` (load immediate) → ใช้ `ORI $x, $zero, ค่า` แทน (0 OR ค่า = ค่า)
- ไม่มีคำสั่ง `MOVE` → ใช้ `ADD $x, $y, $zero` แทน

### 11.3 factorial(n) — ต้องใช้ stack
```asm
factorial:
    ADDI  $sp, $sp, -16      # จอง stack 4 ช่อง × 4 byte
    SW    $ra, 12($sp)       # เก็บ $ra (เพราะ JAL mul จะเขียนทับ)
    SW    $s0, 8($sp)        # เก็บ $s0-$s2 ค่าเก่า (กฎ: ใช้ $s ต้องคืนค่าเดิม)
    SW    $s1, 4($sp)
    SW    $s2, 0($sp)

    ADD   $s0, $a0, $zero    # $s0 = n
    ORI   $s1, $zero, 1      # $s1 = fac = 1
    ORI   $s2, $zero, 2      # $s2 = i = 2
fact_loop:
    SLT   $t0, $s0, $s2      # $t0 = 1 ถ้า n < i
    BNE   $t0, $zero, fact_done   # ถ้าใช่ → ออกจาก loop
    ADD   $a0, $s1, $zero    # arg1 = fac
    ADD   $a1, $s2, $zero    # arg2 = i
    JAL   mul                # $v0 = fac × i
    ADD   $s1, $v0, $zero    # fac = ผลคูณ
    ADDI  $s2, $s2, 1        # i++
    J     fact_loop
fact_done:
    ADD   $v0, $s1, $zero    # คืน fac ใน $v0
    LW    $s2, 0($sp)        # คืนค่าเดิมของ $s2 $s1 $s0 $ra
    LW    $s1, 4($sp)
    LW    $s0, 8($sp)
    LW    $ra, 12($sp)
    ADDI  $sp, $sp, 16       # คืนพื้นที่ stack
    JR    $ra                # กลับ main
```
หน้าตา stack หลังจอง (address จริงตอนรัน):
```
0x7FFC  ($sp+12) : $ra เก่า   = 0x10
0x7FF8  ($sp+8)  : $s0 เก่า
0x7FF4  ($sp+4)  : $s1 เก่า
0x7FF0  ($sp+0)  : $s2 เก่า   ← $sp ชี้ตรงนี้
```
ใน GUI ติ๊ก Follow $sp ไว้ จะเห็น 4 ช่องนี้ถูกเขียนตอน SW

### 11.4 mul(a, b) — "ฟังก์ชันคูณที่เขียนเอง"
```asm
mul:
    ADD   $v0, $zero, $zero  # result = 0
    ADD   $t0, $a1, $zero    # count = b
mul_loop:
    BEQ   $t0, $zero, mul_done   # count = 0 → เสร็จ
    ADD   $v0, $v0, $a0      # result += a   ← overflow เกิดตรงนี้ (address 0x98)
    ADDI  $t0, $t0, -1       # count--
    J     mul_loop
mul_done:
    JR    $ra
```
ตัวอย่าง: 6 × 4 = 6 + 6 + 6 + 6 = 24
เป็น **leaf function** (ไม่เรียกใครต่อ) และใช้แค่ `$t` → ไม่ต้องใช้ stack

### 11.5 ผลที่คาดไว้
| n | ผล | หมายเหตุ |
|---|---|---|
| 0, 1 | 1 | loop ไม่ทำงานเลย |
| 5 | 120 | 101 คำสั่ง |
| 10 | 3628800 | |
| 12 | 479001600 | ค่าสุดท้ายที่ถูก |
| 13 | 1932053504 + คำเตือน OVERFLOW | ผิด (ที่ถูกคือ 6,227,020,800) |

### 11.6 label กลายเป็นตัวเลขยังไง
ดูตาราง machine code: `BNE $t0 $zero 6` (address 0x54) → กระโดดไป `fact_done` ที่ 0x70
offset = (0x70 − 0x58) ÷ 4 = **6** (นับจากคำสั่งถัดไป หน่วยเป็นคำสั่ง)
`JAL 0x30` → machine code `0c00000c` (opcode JAL = 000011, target = 0x30 ÷ 4 = 0xC)

---

## 12. อธิบาย nck.asm

ไฟล์: `programs/nck.asm`

### 12.1 ทำไมไม่ใช้สูตร n! / (k!(n−k)!)
13! ล้น 32 bit แล้ว แต่อาจารย์ต้องการถึง n = 26 → ต้องใช้วิธีที่ตัวเลขระหว่างทางไม่โต

### 12.2 สามเหลี่ยมปาสคาล
แต่ละช่อง = ผลบวก 2 ช่องข้างบน `C(i, j) = C(i−1, j−1) + C(i−1, j)`
```
        1            ← แถว 0
       1 1           ← แถว 1
      1 2 1          ← แถว 2
     1 3 3 1         ← แถว 3
    1 4 6 4 1        ← แถว 4   เช่น 4C2 = 6
```
ใช้ **การบวกอย่างเดียว** ตัวเลขระหว่างทางไม่เกินคำตอบ → ไม่ล้นจนถึง n = 33

Python ที่เทียบเท่า:
```python
row = [1] + [0] * k
for i in range(1, n+1):
    for j in range(min(i, k), 0, -1):    # ขวา → ซ้าย
        row[j] = row[j] + row[j-1]
return row[k]
```
**ทำไมต้องขวาไปซ้าย:** ถ้าไปซ้ายไปขวา `row[j-1]` จะถูกเปลี่ยนเป็นค่าแถวใหม่ก่อนที่ `row[j]` จะใช้

### 12.3 array อยู่ที่ 0x4000
```
row[j] อยู่ที่ address 0x4000 + 4 × j
```
แผนผัง memory:
```
0x0000 – 0x00DC   ตัวโปรแกรม (machine code)
     … ว่าง …
0x4000 ↓          array ของ nck   ← เลือกตรงนี้เพราะไกลจากทั้งสองฝั่ง
     … ว่าง …
0x8000 ↑          stack ($sp เริ่มที่นี่แล้วโตลง)
```

### 12.4 โครงโปรแกรม
- **main**: อ่าน n (`$s0`), อ่าน k (`$a1`), เรียก `JAL nck`, พิมพ์ผล, จบ
- **nck**:
  1. ถ้า k < 0 หรือ n < k → คืน 0 (`nck_zero`)
  2. `$t9 = 0x4000` (ROW_BASE)
  3. `init_loop`: row[0] = 1, row[1..k] = 0
  4. `row_loop` (i = 1..n) → `col_loop` (j = min(i,k) ลงไปถึง 1):
     ```asm
     SLL   $t3, $t2, 2        # j × 4 (เลื่อนซ้าย 2 bit = คูณ 4)
     ADD   $t3, $t3, $t9      # address ของ row[j]
     LW    $t5, 0($t3)        # row[j]
     LW    $t6, -4($t3)       # row[j-1]  (ช่องก่อนหน้า ต่ำกว่า 4 byte)
     ADD   $t5, $t5, $t6      # ← การคำนวณเดียวของทั้งอัลกอริทึม
     SW    $t5, 0($t3)
     ```
  5. คืน row[k] ใน `$v0`
- nck เป็น leaf function ใช้แค่ `$t` → ไม่ต้องใช้ stack
- ใช้ `SLL ... 2` แทนการคูณ 4 → ยังไม่ใช้คำสั่งคูณตามโจทย์

### 12.5 ผลที่คาดไว้
| input | ผล |
|---|---|
| `5 2` | 10 |
| `10 4` | 210 |
| `10 5` | 252 |
| `26 13` | 10400600 (ค่ากลางที่ใหญ่สุดของแถว 26) |
| `5 7` | 0 (k > n) |

เทสต์ตรวจครบทั้ง **378 คู่** ของ n ≤ 26

---

## 13. ภาษา assembly ที่ simulator นี้รับ

### 13.1 รูปแบบบรรทัด
```asm
label:   OPCODE  operand1, operand2, operand3   # comment
```
- ตัวพิมพ์ใหญ่/เล็กของคำสั่งไม่สำคัญ
- **คอมมา** ใส่หรือไม่ใส่ก็ได้ (`ADD $t0, $t1, $t2` = `ADD $t0 $t1 $t2`)
- **คอมเมนต์** หลัง `#` ถูกตัดทิ้ง
- **label** ชื่อขึ้นต้นด้วยตัวอักษร/`_` ตามด้วย `:` อยู่บรรทัดเดียวกับคำสั่งหรือบรรทัดเดี่ยวก็ได้
- **`.ORG addr`** ต้องอยู่บนสุด (ก่อนคำสั่งและ label ทั้งหมด) ตั้ง address เริ่มต้น ถ้าไม่ใส่เริ่มที่ 0

### 13.2 เขียน register ได้หลายแบบ
`$t0` = `$8` = `R8` = `$T0` (ทั้งหมดคือ register 8)

### 13.3 เขียนตัวเลขได้หลายแบบ
`10`, `-3`, `0x4000`, `-0x10`, `0b1010`

### 13.4 คำสั่งที่รันได้
| กลุ่ม | คำสั่ง | ตัวอย่าง |
|---|---|---|
| บวก/ลบ | `ADD ADDU SUB SUBU ADDI ADDIU` | `ADDI $sp, $sp, -16` |
| ตรรกะ | `AND OR NOR ANDI ORI` | `ORI $v0, $zero, 5` |
| shift | `SLL SRL` | `SLL $t3, $t2, 2` |
| เปรียบเทียบ | `SLT SLTU SLTI SLTIU` | `SLT $t0, $s0, $s2` |
| ค่าคงที่ | `LUI` | `LUI $t1, 0xFFFF` |
| memory | `LW SW` (4 byte) | `LW $t5, 0($t3)` |
| branch | `BEQ BNE` (ใช้ label ได้) | `BNE $t0, $zero, done` |
| jump | `J JAL JR` | `JAL mul` / `JR $ra` |
| ระบบ | `SYSCALL` (1/5/10/11) `HALT` | |

- **overflow ถูกตรวจ** ใน `ADD ADDI SUB` (แบบ signed) ส่วน `ADDU ADDIU SUBU` ไม่ตรวจ (ตามนิยาม MIPS)
- `HALT` ไม่ใช่คำสั่ง MIPS จริง (มาจาก V7.1 ของอาจารย์) ไม่มี machine code
- **ไม่มีและห้ามใช้ตามโจทย์:** `MUL MULT DIV` → ต้องเขียนเองด้วยการบวก
- มีใน assembler แต่ยังรันไม่ได้: `LBU LHU SB SH LL SC` (จะขึ้น error ชัดเจน)

### 13.5 ตัวอย่างโปรแกรมเล็ก ๆ (ลองพิมพ์ใน GUI)
```asm
# print 1 to 5
.ORG 0
    ORI  $t0, $zero, 1        # i = 1
    ORI  $t1, $zero, 6        # stop when i == 6
loop:
    ADD  $a0, $t0, $zero
    ORI  $v0, $zero, 1        # print i
    SYSCALL
    ORI  $a0, $zero, 32       # space
    ORI  $v0, $zero, 11
    SYSCALL
    ADDI $t0, $t0, 1
    BNE  $t0, $t1, loop
    ORI  $v0, $zero, 10
    SYSCALL
```
ผล: `1 2 3 4 5` (ทดสอบแล้ว)

---

## 14. ข้างใน simulator ทำงานยังไง

### 14.1 เส้นทางเมื่อพิมพ์ `python main.py FILE -t`
```
main.py
 ├─ parse_args()              อ่านตัวเลือก (-t, -q, --gui, ...)
 ├─ ถ้า --gui → gui.main(FILE) แล้วจบ
 ├─ ถ้า --tui → tui.run_tui(...) แล้วจบ
 ├─ load_instructions(FILE)   อ่านไฟล์เป็นรายการบรรทัด
 ├─ Memory()                  memory ว่าง
 ├─ CPU(lines, memory)        ← assemble ตรงนี้
 │    ├─ source_line_numbers()  จำว่าคำสั่งแต่ละตัวมาจากบรรทัดไหน (ใช้ใน trace)
 │    ├─ preprocess()           assembler 2-pass: ตัดคอมเมนต์/คอมมา, หา label, แทน label ด้วยตัวเลข
 │    ├─ Instruction(line)      decode → decode2 → decode3 (แปลงเป็น machine code)
 │    └─ เขียน machine code ลง memory + พิมพ์ตาราง
 ├─ cpu.run(trace=True)       วน fetch → execute → validate → PC+1
 └─ พิมพ์ Last STATE / --mem / จำนวนคำสั่ง
```

### 14.2 แต่ละไฟล์
**`isa.py`** (assembler)
- `cmdDict` ตารางคำสั่ง: ชื่อ, ชนิด (R/I/J), opcode, funct
- `REG_NAMES` ชื่อ register 32 ตัว, `reg2int()` แปลงชื่อเป็นเลข, `imm2int()` แปลงตัวเลขหลายรูปแบบ
- `preprocess()` **assembler 2 รอบ** — รอบ 1 หา label ทั้งหมด (เพราะ label ข้างล่างยังไม่รู้ address จนอ่านจบ), รอบ 2 แทน label: BEQ/BNE = offset สัมพัทธ์, J/JAL = address จริง
- `source_line_numbers()` บอกเลขบรรทัดในไฟล์ของแต่ละคำสั่ง (กฎเดียวกับ preprocess)
- `class Instruction` ของอาจารย์: `decode()` แยกคำ, `decode2()` เตรียมค่า, `decode3()` สร้าง machine code

**`cpu.py`**
- `PC` เก็บเป็น "address ÷ 4" (แบบ V7.1) และใช้ `BASE_PC` จัดการ `.ORG`
- `execute()` ทำงานตาม opcode (if/elif ยาว)
- `u32() s32() sext16()` ช่วยให้ทุกค่าอยู่ใน 32 bit ถูกต้อง
- `check_overflow()` เทียบผลจริง (Python ไม่มีขีดจำกัด) กับช่วง 32 bit
- `step_once()` รัน 1 คำสั่ง (ใช้โดย GUI และ TUI), `current_index()`, `address_of()`
- `print_trace()` (`-t`), `step_prompt()` (`-s`)
- SYSCALL 5 อ่านด้วย `input_func` (GUI ส่งฟังก์ชันหน้าต่างเด้งมาแทน, เทสต์ส่งฟังก์ชันปลอม)

**`memory.py`**
- เก็บใน dict `{address: byte}` (ที่ไม่เคยเขียน = 0) → ใช้ address ไหนก็ได้
- `read_word()/write_word()` อ่าน/เขียน 4 byte big-endian

**`gui.py`** ใช้ CPU ตัวเดียวกัน แต่เรียก `step_once()` ผ่าน timer `after()` ของ Tkinter เพื่อให้หน้าต่างไม่ค้าง

**`tui.py`** ใช้ `curses` วาดหน้าจอข้อความ

### 14.3 สิ่งที่แก้จาก V7.1 ของอาจารย์ (บั๊กที่เจอ)
1. machine code R-type (เช่น ADD) ได้ `00000000` → แก้แล้ว ตรงเฉลย A01
2. BEQ/BNE วาง rs/rt สลับกับ MIPS จริง
3. SW/LW เขียนค่าทั้งก้อนลง address เดียว → เป็น 4 byte
4. `validate()` พังเมื่อค่าเกิน 32 bit
5. `SLTI` เขียนทับ register ต้นทาง
6. ไฟล์ไม่มี `.ORG` → error (`textpos` ไม่ได้ตั้งค่า)
7. คำสั่งที่ไม่รองรับถูกข้ามเงียบ ๆ → ตอนนี้แจ้ง error

ที่เพิ่ม: label, ชื่อ register, คำสั่งใหม่ (SUB SUBU ADDU AND OR NOR SLT SLTU ANDI SLL SRL JAL JR SYSCALL), stack, overflow, โหมด -t -s -q --mem --int --tui --gui, เลขบรรทัดใน trace, เทสต์

---

## 15. เทสต์อัตโนมัติ

รันที่ **โฟลเดอร์หลัก** (ไม่ใช่ `sim`):
```
cd "G:\Work\year3\com arc\factorial_project"
python -m unittest discover -s tests -v
```
ผลที่ได้ ท้ายสุด:
```
Ran 11 tests in ...s
OK
```
| เทสต์ | ตรวจอะไร |
|---|---|
| `test_all_values_0_to_12` | factorial 0..12 ถูกทุกค่า ไม่มี overflow |
| `test_13_overflows` | 13! ต้องมีคำเตือน overflow |
| `test_all_pairs_up_to_26` | nCk ทุกคู่ n ≤ 26 (378 คู่) ตรงกับ `math.comb` |
| `test_k_out_of_range_gives_zero` | k < 0 หรือ k > n ได้ 0 |
| `test_sum_10_to_1` | โปรแกรมของอาจารย์ได้ 55 |
| `test_instruction_test` | ไฟล์ทดสอบคำสั่งของอาจารย์ได้ค่าตามที่ควร |
| `test_encoding` | machine code 13 คำสั่งตรงเฉลย A01 |
| `test_labels_and_register_names` | label และชื่อ register ใช้ได้ |
| `test_zero_register_stays_zero` | `$zero` เป็น 0 เสมอ |
| `test_signed_compare` | SLT/SLTU เปรียบเทียบมีเครื่องหมายถูก |
| `test_errors_are_clear` | error บอกเลขบรรทัดชัดเจน |

**แก้โค้ดอะไรก็ตาม รันเทสต์ก่อนส่งงานทุกครั้ง** ถ้าขึ้น `FAILED` แปลว่าไปทำของเดิมพัง

---

## 16. ถ้าจะทำงานต่อ ต้องทำยังไง

### 16.1 กฎของโปรเจค
1. **โค้ดและคอมเมนต์เป็นภาษาอังกฤษ** (ยกเว้น README.md / FULL_GUIDE.md)
2. ส่วนที่เพิ่มติดป้าย `★ [NEW]` ส่วนที่แก้ของอาจารย์ติด `★ [MODIFIED]` พร้อมเหตุผล
3. **สำรองไฟล์ก่อนแก้** (copy ไว้ในโฟลเดอร์ `backup_before_...`)
4. รันเทสต์หลังแก้
5. **ห้ามลอกโค้ดกลุ่มอื่น**

### 16.2 เขียนโปรแกรม assembly ใหม่
1. สร้างไฟล์ `programs/ชื่อ.asm` (ใน GUI: พิมพ์แล้ว Save)
2. ขึ้นต้นด้วย `.ORG 0` และคอมเมนต์อธิบาย
3. ใช้ `ORI` แทน `LI`, `ADD x,y,$zero` แทน `MOVE`
4. จบด้วย `ORI $v0,$zero,10` + `SYSCALL`
5. รัน `python main.py ../programs/ชื่อ.asm -t` ดูว่าทำงานตามคิด
6. ถ้าเรียกฟังก์ชันซ้อน → เก็บ `$ra` ลง stack (ดู factorial)

### 16.3 เพิ่มคำสั่ง MIPS ใหม่ (ตัวอย่าง: `XOR`)
1. `isa.py` → เพิ่มใน `cmdDict`: `cmdDict['XOR'] = ('XOR', 'R', '000000', '100110')  # ★ [NEW]`
2. `cpu.py` → ใน `execute()` เพิ่ม
   ```python
   elif opcode == "XOR":            # ★ [NEW]
       rd,rs,rt = ops[0], ops[1], ops[2]
       self.set_reg(rd, R[rs] ^ R[rt])
   ```
   (ลอกรูปแบบจากคำสั่ง `OR` ที่อยู่ข้าง ๆ)
3. `tests/test_all.py` → เพิ่มเทสต์ machine code และผลลัพธ์
4. รันเทสต์

### 16.4 เพิ่ม SYSCALL ใหม่ (ตัวอย่าง: 4 = พิมพ์ข้อความ)
อยู่ใน `cpu.py` ส่วน `elif opcode == "SYSCALL":` เพิ่ม `elif service == 4:` (ต้องมีวิธีใส่ข้อความใน memory ด้วย เช่น `.asciiz` ซึ่งยังไม่มี — เป็นงานใหญ่)
**ระวัง:** ถ้าให้โปรแกรมพิมพ์คำอย่าง "Result:" ผลของ `-q` จะเปลี่ยน อาจทำให้การตรวจอัตโนมัติไม่ผ่าน

### 16.5 แก้ GUI
- สีทั้งหมด: ค่าคงที่ด้านบน `gui.py` + `apply_theme()`
- ปุ่มบนแถบ: `build_toolbar()`
- register/memory: `refresh_registers()` / `refresh_memory()`
- trace: `run_one()` (เก็บข้อมูล) + `format_trace()` (จัดรูปแบบ)
- หน้าต่าง input: `open_input_dialog()`
- แก้แล้วถ้าใช้ .exe ต้องรัน `build_exe.bat` ใหม่

### 16.6 อัปขึ้น GitHub (เจ้าของโปรเจคจะทำเอง)
```
cd "G:\Work\year3\com arc\factorial_project"
git init
git add .
git commit -m "MIPS simulator: factorial and nCk"
git branch -M main
git remote add origin https://github.com/<ชื่อ>/<repo>.git
git push -u origin main
```
`.gitignore` กันไฟล์ขยะไว้แล้ว (โฟลเดอร์ `backup_before_...` ถ้าไม่อยากอัป ให้เพิ่มชื่อลงใน `.gitignore`)

---

## 17. ข้อจำกัดที่รู้อยู่แล้ว

- factorial ถูกถึง **12!** (13! เกิน 32 bit — ข้อจำกัดของ register ไม่ใช่บั๊ก)
- nck ใช้ได้ถึง **n = 33** (เทสต์ครบถึง 26)
- `mul` รับ b ติดลบไม่ได้ และช้าเมื่อ b ใหญ่ (บวกซ้ำ b ครั้ง)
- ยังไม่รองรับ `LBU LHU SB SH LL SC`, SYSCALL 4 (string), `.data` / `.asciiz`
- ไม่จำลอง branch delay slot, pipeline, exception จริงของ MIPS (overflow แค่เตือน)
- `HALT` ไม่ใช่ MIPS จริง
- ส่วนที่เป็น Windows (`.bat`, `.exe`, GUI บน Windows) ทดสอบบนเครื่องจริงน้อย ควรลองก่อน present

---

## 18. แนวทางการ present

ประมาณ 10 นาที:
1. **โจทย์** (1 นาที) — factorial บน simulator ที่ไม่มีคำสั่งคูณ → เขียน mul เอง
2. **simulator** (2 นาที) — ต่อยอด V7.1 ของอาจารย์: label, แก้ machine code R-type (โชว์ว่าตรงเฉลย A01), stack/JAL/JR, SYSCALL, overflow
3. **factorial.asm** (2 นาที) — main → factorial → mul, stack frame
4. **Demo** (3 นาที)
   - `python main.py ../programs/factorial.asm -q` ใส่ 5 → `120` (แบบที่ autolab ตรวจ)
   - `-t` แล้วชี้ `line 40 ... JAL` เทียบกับไฟล์
   - `--gui` → Run ช้า ๆ ให้เห็น `$sp` ลดลงและ stack ถูกเขียน
   - ใส่ 13 → คำเตือน OVERFLOW (ส้ม)
5. **nCk** (1 นาที) — factorial ล้นตั้งแต่ 13! → **เปลี่ยนวิธี** เป็นสามเหลี่ยมปาสคาล → GUI ดู memory 0x4000 แบบ DEC
6. **สรุป + ข้อจำกัด** (1 นาที) — และบอกว่าอาจารย์ลองเองได้จาก `MIPS Simulator.exe` โดยไม่ต้องลง Python

เตรียมก่อนขึ้น: เปิด Command Prompt ที่ `cd` เข้า `sim` แล้ว, เปิดไฟล์ factorial.asm ไว้เทียบ, ลอง .exe บนเครื่องที่จะใช้จริง

ประโยคที่ใช้ได้:
> "ตัว simulator คือ `main.py` ที่รันจาก command line ตามโจทย์ ส่วน GUI เป็นตัวเสริมให้เห็นข้างใน เปิดด้วย `--gui` ทั้งสองแบบใช้ CPU ตัวเดียวกัน"

---

## 19. คำถามที่พบบ่อย / แก้ปัญหา

**Q: พิมพ์ `python main.py` แล้วขึ้น `can't open file ... main.py`**
A: ยังไม่ได้อยู่ในโฟลเดอร์ `sim` → `cd` เข้าไปก่อน (ส่วนที่ 5)

**Q: โปรแกรมค้าง ไม่ขึ้นอะไร**
A: น่าจะรอ input อยู่ ดูบรรทัด `>>> The program is waiting for input #1` แล้วพิมพ์ตัวเลข + Enter

**Q: nck ถามสองครั้ง ใส่อะไร**
A: ครั้งที่ 1 = n, ครั้งที่ 2 = k (หรือพิมพ์ `26 13` ทีเดียว)

**Q: ทำไมใน GUI ไม่ต้องใส่ `--mem 0x4000`**
A: ช่อง Memory ใน GUI เปิดค้างตลอด แค่เอาติ๊ก Follow $sp ออกแล้วพิมพ์ `0x4000` ในช่อง address

**Q: register ใน GUI อ่านยาก**
A: กดปุ่ม **DEC** บนแถบเครื่องมือ

**Q: ตัวเลขใน trace เก่าเปลี่ยนตอนกด HEX/DEC ไหม**
A: เปลี่ยนทั้งหมด (GUI เก็บข้อมูลดิบไว้แล้ววาดใหม่)

**Q: แก้โค้ดใน editor แล้วกด Run ไม่เห็นเปลี่ยน**
A: GUI assemble ใหม่ให้อัตโนมัติเมื่อโค้ดเปลี่ยน ถ้ายังไม่เปลี่ยน กด **Assemble** เอง ถ้ามีแถบแดง = มี error ดูใน Console

**Q: breakpoint ไม่หยุด**
A: breakpoint ทำงานตอน **Run** เท่านั้น (Step หยุดทุกคำสั่งอยู่แล้ว) และจะไม่หยุดที่บรรทัดที่กำลังเริ่มรัน

**Q: `--tui` ขึ้น error เรื่อง curses / หน้าจอเพี้ยน**
A: `pip install windows-curses` และขยายหน้าต่างให้ใหญ่กว่า 90×24

**Q: แก้โค้ดแล้ว .exe ยังเหมือนเดิม**
A: ต้องรัน `build_exe.bat` ใหม่

**Q: ไอคอน Desktop เปิดไม่ขึ้นหลังย้ายโฟลเดอร์**
A: รัน `create_shortcut.bat` ใหม่

**Q: ผลของ `-q` มีข้อความถามปนอยู่ autolab จะผิดไหม**
A: ไม่ผิด ข้อความถามไปทาง stderr และขึ้นเฉพาะตอนพิมพ์ที่คีย์บอร์ด ถ้าป้อน input จากไฟล์จะไม่มี

**Q: อยากเห็นว่าแต่ละบรรทัดใน trace มาจากไหนในไฟล์**
A: ดูตัวเลข `line NN` ด้านหน้า แล้วเปิดไฟล์ไปบรรทัดนั้น (ใน GUI ดูแท็บ Machine code คอลัมน์ Line ก็ได้)

---

## 20. โฟลเดอร์ backup

ก่อนแก้แต่ละครั้งมีการสำรองไฟล์ไว้ในโฟลเดอร์หลัก แต่ละโฟลเดอร์มี `HOW_TO_RESTORE.txt` บอกวิธีคืน

| โฟลเดอร์ | เป็นเวอร์ชันก่อน |
|---|---|
| `backup_before_command_line` | แท็บ Command line ใน GUI (ทดลองแล้วถอดออก) |
| `backup_before_gui_flag` | เพิ่ม `--gui` และเลขบรรทัดใน trace |
| `backup_before_dark_theme` | ปุ่ม HEX/DEC คุมทุกส่วน, `input #N`, ธีมสีเข้ม, ไฟล์นี้ |

วิธีคืน: copy ไฟล์ในโฟลเดอร์ backup ไปทับไฟล์ที่ตำแหน่งเดียวกันในโปรเจค
ถ้างานเสถียรแล้วและอัป GitHub แล้ว ลบโฟลเดอร์ backup ทิ้งได้ (git เก็บประวัติให้แทน)
