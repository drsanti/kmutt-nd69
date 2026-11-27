# Lesson 06 — Secure Edge AI: Protecting the Model and Firmware

> Week 08 · ES3C28P / ESP32-S3 · 11:35–11:45

[Lesson index](README.md) · [Previous: Lesson 05](05-firmware-inference.md) · [Next: Lesson 07](07-imu-gesture-alternative.md)

## Learning objectives

Identify what an attacker can do with physical access to an Edge AI device, and explain what ESP32-S3 secure boot and flash encryption protect — and what they do not.

## What is worth protecting?

| Asset | Threat | Example |
|---|---|---|
| Firmware integrity | Someone flashes modified firmware | A "keyword" device that streams audio to a server |
| Model and code confidentiality | Someone reads the flash with a USB cable | Your trained model copied into a competing product |
| Data | Recorded audio or user data in flash/SD | Voice clips extracted from a lost device |
| Decisions | Adversarial inputs | A sound pattern that triggers `off` |

**Host inference is a privacy trade-off too.** With the workshop firmware, the board streams raw microphone audio to any program that opens its USB port — that is exactly what `robotos-kws collect-board` and `robotos-kws live-board` use. Fine for a lab; in a product, raw sensor streams should be off by default, need an explicit command, and never leave the device unless the user agreed.

On the board, the model is just bytes in flash: `g_kws_model` sits in the app image. Without protection, reading the flash over USB with `esptool` (`read-flash`) copies it in seconds.

## Secure boot v2 — "only run firmware I signed"

```text
ROM bootloader ──verifies signature──► 2nd-stage bootloader ──verifies signature──► app
       ▲                                                                              
   public-key digest burned in eFuse (cannot be changed)
```

- You sign the bootloader and app with a private key on your PC (`espsecure.py`, or automatically by `idf.py build` when enabled).
- The chip stores a **digest of the public key** in eFuse and refuses to boot an image with a bad signature.
- Protects **integrity**: modified firmware will not run.
- Does **not** hide anything: the flash can still be read unless flash encryption is also on.

## Flash encryption — "flash contents are unreadable off-chip"

- The chip generates (or you provide) an AES key stored in eFuse, readable only by the hardware.
- Flash is encrypted with that key; the CPU decrypts it transparently on read through the cache.
- Protects **confidentiality**: a flash dump is ciphertext, so the model and code cannot be copied.
- In **release mode**, plaintext reflashing over serial is disabled.

## Turning them on (read first, then decide)

Both are enabled in `idf.py menuconfig` → *Security features*. See the ESP-IDF guides for [Secure Boot v2](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/security/secure-boot-v2.html) and [Flash Encryption](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/security/flash-encryption.html), and the [Security overview](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/security/security.html).

> [!CAUTION]
> These features **burn eFuses, which is permanent**. A lost signing key or a wrong setting can make a board impossible to update. **Do not enable them on course boards.** Practise with *Development mode* only on a spare board, and only with instructor approval.

## A short checklist for a shipped Edge AI device

1. Secure boot v2 + flash encryption (release mode) on production units.
2. Disable or protect JTAG and the USB download mode in production.
3. Sign over-the-air (OTA) updates, and do not accept a downgrade to vulnerable firmware.
4. Keep the signing key **off** the build server where possible (HSM or offline machine); never commit it to Git.
5. Do not store raw user audio on the device unless it is needed; if needed, encrypt it (NVS encryption, encrypted SD files).
6. Treat the model output as untrusted input for safety-critical actions: require confirmation or a second signal before something dangerous happens.

These tie into the 12 December onsite session on connecting securely to the cloud.

## Check your understanding

1. Secure boot is on, flash encryption is off. Can an attacker copy your model? Can they run modified firmware?
2. Why must the signing private key never be committed to your project repository?
3. Name one attack on an Edge AI system that neither secure boot nor flash encryption prevents.
4. The workshop firmware streams microphone audio over USB when asked. What would you change before shipping such a device?
