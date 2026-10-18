# Parameter & lifecycle — node มีชีวิตไม่ใช่แค่ "รันตลอด"

![alt text](images/05-parameters-and-lifecycle.png)

ในโลก PLC: โปรแกรมมีสถานะ — STOP/RUN — และ tag คือค่าที่ปรับได้
โลก node-based มีสองแนวคิดที่เทียบกันได้: **parameter** (ค่าปรับ
ของ node) และ **lifecycle** (สถานะชีวิตของ node)

## Parameter — ค่าปรับได้ที่มีเจ้าของชัด

ต่างจาก tag ที่ลอยอยู่กลางระบบ:

- **parameter เป็นของ node ตัวนั้น** — ไม่มี "ตารางกลาง" — แต่ละ
  node เป็นเจ้าของ parameter ของตัวเอง
- ปรับได้ **ขณะ runtime** — ไม่ต้องหยุด/compile ใหม่ — เหมือน tune
  PID สด ๆ แต่ผ่าน interface ที่เป็นระบบ
- มีชนิดและขอบเขตชัดเจน — setpoint, threshold, mode, rate — อ่าน/
  เขียนผ่าน service-like call
- **รู้ว่าใครเปลี่ยน** — การตั้งค่าผ่าน interface ของ node เอง
  ไม่ใช่เขียนทับ address ดิบ

จากมุม automation: เหมือน faceplate ของ function block — แต่
เข้าถึงได้ผ่านเครือข่ายโดยไม่ต้องรู้ว่า node รันอยู่ที่ไหน

```python
# pseudo-API — แนวคิดเชิงออกแบบ ไม่ใช่ API จริง
node.declare_parameter("max_speed", 1.5)      # ค่าเริ่มต้น
speed = node.get_parameter("max_speed")        # อ่าน
node.set_parameter("max_speed", 2.0)           # ปรับ runtime
```

## ทำไม parameter ต่างจาก topic

ความสับสนเริ่มต้นที่เจอบ่อย:

- **topic** = ข้อมูลไหลต่อเนื่อง (ค่า sensor, state) — เปลี่ยนตลอด
  ไม่มีใคร "เป็นเจ้าของค่า"
- **parameter** = การตั้งค่าของ node — เปลี่ยนเมื่อมีคนตั้งใจเปลี่ยน
  node เป็นเจ้าของ คงอยู่จนกว่าจะเปลี่ยน

เทียบง่าย ๆ: topic เหมือน process variable ที่ไหลผ่าน /
parameter เหมือน setpoint/config ใน controller — หนึ่งคือสัญญาณ
อีกหนึ่งคือการตั้งค่า

## Lifecycle — node ไม่ใช่ "เปิดแล้วรันเลย"

โลก PLC: โปรแกรมมีสอง state หลัก (STOP/RUN) — โลก node ละเอียด
กว่าเพราะระบบใหญ่ต้อง bring-up อย่างเป็นระบบ:

```
┌──────────────┐                  ┌──────────┐                 ┌────────┐
│ unconfigured │ ── configure ──► │ inactive │ ── activate ──► │ active │
└───────┬──────┘                  └─────┬────┘                 └────┬───┘
        ▲ cleanup                       │                           │
        └───────────────────────────────┘                           │
        ▲ shutdown / error                                          │
        └───────────────────────────────────────────────────────────┘
```

- **unconfigured** — node ถูกสร้างแต่ยังไม่ตั้งค่า (รอ parameter/
  การเชื่อมต่อ)
- **inactive** — ตั้งค่าแล้ว แต่ยังไม่ทำงาน (พร้อมแต่ยังไม่รัน)
- **active** — ทำงานจริง — publish/subscribe/act ตามปกติ
- **shutdown/error** — ทางออกที่เป็นระบบ — ปิด connection คืน
  resource อย่างสุภาพ

## ทำไมต้องมี lifecycle แยก

ระบบที่มี node หลายสิบตัวกระจายอยู่ ไม่สามารถ "เปิดพร้อมกันหมด"
ได้:

- **ลำดับการ bring-up สำคัญ** — sensor node ต้องขึ้นก่อน control
  node; safety node ก่อนทุกอย่าง — lifecycle ให้ orchestrator คุม
  ลำดับได้
- **configure ≠ activate** — ตั้งค่าก่อน ค่อยให้ทำงาน — เหมือน
  download program ก่อน แล้วค่อย RUN
- **shutdown อย่างสุภาพ** — node ปิดตัวด้วยวิธีที่ถูก (คืนทรัพย์
  แจ้งผู้อื่น) ไม่ใช่ตายเงียบ ๆ
- **recovery มีจุดให้กลับ** — error → cleanup → unconfigured →
  configure ใหม่ — ไม่ต้อง kill ทั้งระบบ

จากมุม automation: lifecycle คือ PLC program states ที่ละเอียด
กว่าและกระจายไปทุก node — แต่ละตัวมี state machine ของตัวเองที่
ระบบคุมร่วมกันได้

## เชื่อมกับส่วนอื่น

- parameter ปรับผ่าน service-like call — เครื่องมือเดียวกับบท 04
- lifecycle state ของ node ปรากฏใน graph/inspector (บท 07) —
  เห็นว่าใคร active ใครยัง configure อยู่
- twin รู้สถานะ node จริงผ่าน lifecycle events — twin แสดง "เครื่อง
  กำลัง boot" ต่างจาก "กำลังรัน"
- ในระบบใหญ่ node มี "ผู้จัดการ" (supervisor pattern) ที่ดู lifecycle
  ทั้งระบบ — คล้าย master ที่คุม sequence ของ cell

## Checklist

| คำถาม | ควรตอบได้ |
|---|---|
| parameter ต่างจาก topic | parameter = การตั้งค่าของ node (เปลี่ยนเมื่อตั้งใจ) / topic = stream ข้อมูล (ไหลต่อเนื่อง) |
| ปรับ parameter ตอนรันได้ไหม | ได้ — ผ่าน node interface ไม่ต้องหยุด/compile |
| lifecycle มีกี่สถานะ | unconfigured → inactive → active (+shutdown/error) |
| ทำไม configure แยกจาก activate | ตั้งค่าก่อนให้ทำงาน — เหมือน download ก่อน RUN |
| lifecycle ช่วยอะไรระบบใหญ่ | bring-up ตามลำดับ, shutdown อย่างสุภาพ, recovery มีจุดกลับ |
| ใครคุม lifecycle | supervisor/orchestrator — คล้าย master คุม sequence cell |
