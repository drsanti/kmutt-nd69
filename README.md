# KMUTT ND69

![Course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![Tracks](https://img.shields.io/badge/tracks-3-2e8b57?style=flat-square)
![Status](https://img.shields.io/badge/status-active-brightgreen?style=flat-square)
![Language](https://img.shields.io/badge/lang-TH%20%2B%20EN-orange?style=flat-square)

![alt text](images/cover.png)

> เอกสารประกอบการเรียนการสอน — จาก hardware จริง สู่ software ที่เข้าใจโลกกายภาพ

คอร์สนี้สอนให้คนทำงานสายต่าง ๆ **เข้าถึงและควบคุมฮาร์ดแวร์จริง** —
เพราะในยุคที่ AI เขียน code ได้แล้ว ความแตกต่างอยู่ที่การเข้าใจ
พารามิเตอร์จริงของโลกและสร้าง action จริง ไม่ใช่แค่สร้างข้อมูล

---

## 📚 Table of Contents

- [Learning Tracks](#-learning-tracks)
- [ND01 — Embedded & Hardware](#nd01--embedded--hardware)
- [ND02 — Application Developers](#nd02--application-developers)
- [ND03 — Automation & Robotics](#nd03--automation--robotics)
- [How to Read](#-how-to-read)

---

## 🎯 Learning Tracks

| Track | Audience | Focus |
|---|---|---|
| 🔧 **ND01** | Electronics / embedded systems | ESP32-S3 board, firmware, FreeRTOS |
| 🌐 **ND02** | Application / full-stack developers | Web Serial, Web Bluetooth, TS apps |
| 🏭 **ND03** | Automation / PLC / machinery engineers | ROS-style middleware, digital twin |

---

## ND01 — Embedded & Hardware

> เข้าใจฮาร์ดแวร์จริงของบอร์ด ES3C28P (ESP32-S3R8) ตั้งแต่ชิปถึง firmware

| Week | Topic | Content |
|---|---|---|
| 01 | [Introduction](nd1/docs/week01/) | course kickoff + presentation |
| 02 | [ES3C28P Hardware](nd1/docs/week02/lessons/) | **15 lessons** — chip, memory, ESP-IDF, USB/serial, display, touch, audio, WS2812, MicroSD, GPIO, embedded C/FreeRTOS |

## ND02 — Application Developers

> เข้าถึง hardware จาก browser — ไม่ต้องเขียน firmware เอง

| Week | Topic | Content |
|---|---|---|
| 01 | [Introduction](nd2/docs/week01/) | course kickoff + presentation |
| 02 | [Browser Hardware APIs](nd2/docs/week02/lessons/) | **11 lessons** — Web Serial/BLE/WiFi, pub-sub thinking, app anatomy, TypeScript+Vite toolchain |

## ND03 — Automation & Robotics

> จาก PLC/DCS สู่ ROS-era — middleware + digital twin

| Week | Topic | Content |
|---|---|---|
| 01 | [Introduction](nd3/docs/week01/) | course kickoff + presentation |
| 02 | [ROS Thinking & Digital Twin](nd3/docs/week02/lessons/) | **11 lessons** — node/topic/schema, service/action, TF, record/replay, QoS, twin — เตรียม hands-on |

---

##  How to Read

> [!TIP]
> **แต่ละบทอ่านอิสระได้** — lesson มีหมายเลขนำหน้า (`01-`, `02-`, …)
> แนะนำอ่านตามลำดับเพราะ concept ต่อกัน แต่แต่ละไฟล์ self-contained

> [!NOTE]
> **ภาษา** — เนื้อหาเป็นภาษาไทย คำศัพท์เทคนิคใช้ภาษาอังกฤษตรง ๆ
> (node, topic, firmware) เพื่อให้ตรงกับเอกสารจริงของอุตสาหกรรม

> [!IMPORTANT]
> **Slide images** — ภาพประกอบแต่ละบทอยู่ใน `lessons/images/`
> เป็นภาพ 16:9 infographic ที่ generate จาก prompt เฉพาะบท

---

<p align="center">
  <sub>course materials · KMUTT ND69</sub>
</p>
