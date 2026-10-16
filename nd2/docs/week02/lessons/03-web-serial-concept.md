# Web Serial — ช่องทางแบบสายในเชิงหลักการ

## Serial port คืออะไรในเชิงแนวคิด

ลืม hardware ก่อน — **serial port คือท่อ byte สองทิศ** ระหว่างสอง
เครื่อง:

- data ไหลเป็นลำดับ byte ต่อเนื่อง — ไม่มี "ข้อความ" ไม่มี
  "packet" ในตัวมันเอง
- ทิศละเส้นทางแยกกัน — ส่งและรับพร้อมกันได้ (full duplex)
- สองฝั่งต้องตกลงความเร็วกันไว้ (baud rate) — ผิดความเร็ว = byte
  เพี้ยนหมด
- ไม่มีใครรู้ว่าอีกฝั่งคืออะไร — เป็นแค่ท่อ ความหมายมาจาก
  "ภาษาที่ตกลงกัน" ข้างบน

นี่คือ channel ดั้งเดิมที่สุดของ embedded — อยู่มาก่อน USB ก่อน
เครือข่าย — แต่ยังครองตำแหน่ง "ทางคุยที่เรียบง่ายที่สุด" จนถึงวันนี้

## Web Serial เปิดท่อนี้ให้เว็บ

API ตัวนี้ทำให้เว็บเพจเปิด serial port ของเครื่องผู้ใช้ได้ — สิ่งที่
เคยเป็นได้แค่ native app (putty, tera term, Arduino monitor)

แผนที่แนวคิด:

```
web page ── Web Serial API ── serial port ── device
           (browser-owned)    (OS-owned)    (hardware)
```

เว็บไม่ได้แตะ port ตรง ๆ — browser เป็นคนเปิดและคุม permission
เว็บได้แค่ "ขอ" แล้วใช้ stream ที่ได้มา

## Lifecycle ที่ต้องเข้าใจ

### 1. Request — user เลือกเองเสมอ

- เว็บเรียกได้เฉพาะตอน user เพิ่ง interact (กดปุ่ม) — เข้ากฎ
  gesture จากบทก่อน
- browser แสดง **port picker** ของตัวเอง — user เห็น list เครื่อง
  ที่เสียบอยู่ เลือกให้เว็บตัวเดียว
- เว็บ list port ทั้งหมดเองไม่ได้ — privacy by design
- เลือกครั้งเดียวจำได้ (remembered grant) — ครั้งถัดไปเปิดได้เลย
  โดยไม่ต้องเลือกใหม่ (จนกว่าจะถูก revoke)

### 2. Open — ตกลงความเร็วแล้วได้ท่อ

- `open()` ระบุ baud rate — สองฝั่งต้องตรงกัน
- ได้ **ReadableStream + WritableStream** — สองทิศแยกชัด
- port เปิดได้ **ครั้งละผู้ใช้เดียว** — app/tab อื่นเปิดซ้ำไม่ได้
  (claim) — ถ้า serial monitor ตัวอื่นเปิดอยู่ เว็บเราจะเปิดไม่ได้

### 3. Converse — data เป็น chunk ไม่ใช่ message

สำคัญที่สุดในบทนี้:

- stream ส่ง **chunk ของ byte** — ไม่ใช่ข้อความสมบูรณ์
- chunk ที่ได้อาจตัดกลางข้อความ หรือรวมหลายข้อความ — **stream ไม่มี
  boundary** ให้ฟรี
- การหา "ข้อความหนึ่งจบตรงไหน" คือหน้าที่ของ layer บน — นี่คือจุดที่
  "protocol" เข้ามา

### 4. Close — ปล่อยท่ออย่างสุภาพ

- ต้องปิด reader/writer ก่อนปิด port — **lock** ค้าง = close ไม่ได้
- ปิด = release claim → app อื่นใช้ได้
- tab ปิด = เชื่อมหายเอง — app ต้องออกแบบให้ reconnect ได้เสมอ

## "Protocol คือภาษาที่ตกลงกัน" — แนวคิดเดียวที่ต้องได้

เพราะท่อมีแต่ byte — การสนทนาต้องมีภาษาร่วม นั่นคือ protocol:

| คำถามที่ protocol ตอบ | ตัวอย่างแนวคิด |
|---|---|
| ข้อความเริ่ม/จบตรงไหน | framing — รู้ขอบเขตของแต่ละ message |
| ข้อความนี้คือชนิดอะไร | type — telemetry, command, event, ack |
| byte เพี้ยนตรวจยังไง | error check — รู้ว่า data เสียหรือไม่ |
| คำสั่งสำเร็จไหม | ack/response — มารยาทการสนทนา |

**สำหรับ board ตัวนี้**: device คุยด้วย framed binary protocol ที่
ออกแบบมาให้ทน noise/สูญหายได้ — รายละเอียดภาษานั้นอยู่ฝั่ง
library/SDK ที่จะให้ภายหลัง ผู้เรียนไม่ต้องรู้ format — แค่เข้าใจว่า
**ท่อเป็น byte ล้วน ภาษาคือสิ่งที่ตกลงกันไว้**

## Pitfall ที่เว็บเพจ hardware เจอจริง

| อาการ | สาเหตุเชิงแนวคิด |
|---|---|
| เปิด port ไม่ได้ | app/tab อื่น claim อยู่ — port มีเจ้าของเดียว |
| เชื่อมแล้วนิ่ง | baud ไม่ตรงกับฝั่ง device |
| อ่านได้บางส่วนแล้วหาย | tab ถูกซ่อน/refresh — connection ตายเอง |
| close ไม่ได้ | reader lock ค้าง — ต้อง release ก่อน |
| ครั้งแรกเลือกแล้วครั้งหน้าไม่ขึ้น picker | remembered grant — ปกติ เช็ค site settings |
| data อ่านแล้วขาดกลาง | stream ไม่มี message boundary — ต้อง reassemble |

แกนของทุกอาการคือข้อเดียว: **การเชื่อมต่อเป็นของเปราะและมีเจ้าของ
เดียว** — app ที่ดีถูกออกแบบรอบความจริงข้อนี้

## เชื่อมกับลูปใหญ่ของ week

serial channel นี้คือวิธีที่ "decide/act" ฝั่งเว็บไปถึง "sense/act"
ฝั่ง device:

- telemetry ไหลเข้า readable stream → app แสดงผล/เก็บ/ตัดสินใจ
- command ไหลออก writable stream → device เปลี่ยนพฤติกรรม
- ลูปปิดเมื่อสองฝั่งคุยภาษาเดียวกัน — ซึ่งคือสิ่งที่ library/SDK
  จะจัดการให้

## Checklist

| คำถาม | ควรตอบได้ |
|---|---|
| serial port คืออะไร | ท่อ byte สองทิศ — ไม่มี message ในตัว |
| เว็บเลือก port เองได้ไหม | ไม่ — user เลือกผ่าน picker ของ browser |
| ทำไมต้องมี protocol | stream ไม่มี boundary — ต้องตกลงภาษากัน |
| port เปิดพร้อมกันได้กี่ตัว | หนึ่ง — claim เดียวต่อ port |
| ครั้งแรกต้องทำอะไร | user gesture → picker → open ด้วย baud ตรง |
| close ก่อนออก | release reader/writer ก่อน ไม่งั้น lock ค้าง |
