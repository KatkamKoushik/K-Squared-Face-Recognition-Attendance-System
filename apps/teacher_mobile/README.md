# K² FRS — Teacher Mobile Application

The faculty classroom-sweep attendance application built with **Flutter 3.27**, **Dart 3.13**, and **Riverpod 3.0**.

---

## Capabilities & Architecture

* **Swiss Modernism Theme:** High-contrast, institutional visual language strictly adhering to accessibility guidelines (always pairing semantic colors with explicit text and icons).
* **Multi-Photo Sweep Ingress:** Captures multiple wide-angle classroom photos, computes `SHA-256` content checksums on-device, and streams multipart payloads.
* **Proposal Review & Triage:** Presents inferred evidence candidates with confidence scores and sighting counts. Allows instructors to resolve lookalike conflicts, mark excused absences, or confirm presence across 1 to 4 conducted units.
* **Offline Resilience:** Functions cleanly in intermittent campus Wi-Fi environments, persisting active state and falling back gracefully to verifiable deterministic models when the control plane is unreachable.
* **Atomic Commit Receipts:** Finalizes attendance with cryptographic replay protection, displaying immutable transaction hashes (`receipt_hash`).

---

## Local Development & Testing

```bash
# Install dependencies
flutter pub get

# Static analysis
flutter analyze

# Run unit and widget test suite
flutter test

# Launch on connected Android device / emulator
flutter run
```
