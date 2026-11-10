# Accessibility Statement for FRS V7.1 K²

**Kakatiya University College of Engineering & Technology (KUCET)**  
*Classroom Photo Attendance Proposal System*

---

## 1. Our Commitment

Kakatiya University College of Engineering & Technology (KUCET) is committed to ensuring digital accessibility for all students, faculty members, and administrative staff, including individuals with disabilities. We continually improve the user experience for everyone and apply the relevant accessibility standards to our institutional applications.

This accessibility statement applies to the complete **FRS V7.1 K²** platform:
- **Teacher Mobile Application** (Flutter 3.27 / Dart 3.6+ for Android)
- **Admin Web Console** (Next.js 15.5 / React 19)
- **Technical Documentation & Public Interfaces**

---

## 2. Conformance Status & Standards

The **FRS V7.1 K²** platform is designed and tested to conform to the **Web Content Accessibility Guidelines (WCAG) 2.1 Level AA** standards.

### Core Architectural Accessibility Measures

1. **Semantic HTML & Landmark Structure:**
   - The web console utilizes semantic landmark elements (`<header>`, `<nav>`, `<aside>`, `<main>`) to facilitate screen reader orientation.
   - An accessible skip-to-content anchor link (`<a href="#main-content">Skip to main content</a>`) is rendered at the top of the DOM to allow keyboard users to bypass repetitive sidebar navigation directly.

2. **Color Contrast & Independence:**
   - Adheres to the Swiss Modernism 2.0 design palette with high-contrast text: Deep Institutional Navy (`#0F172A`) against Light Background (`#F8FAFC`), achieving contrast ratios $\ge 7:1$ (exceeding WCAG AA $\ge 4.5:1$).
   - Color is never used as the sole indicator of state. Biometric consent, attendance verification, and proposal status chips pair colors with distinct icons (e.g., checkmarks, warning triangles) and explicit textual descriptors.

3. **Keyboard Navigability & Focus Management:**
   - All interactive elements—including data tables, modal dialogs, date selectors, and buttons—are fully reachable and operable via keyboard alone (`Tab`, `Shift+Tab`, `Enter`, `Space`, `Escape`).
   - Highly visible focus rings (`focus:ring-2 focus:ring-institutional-blue`) ensure clear visual feedback for keyboard navigation.

4. **Mobile & Touch Accessibility (Flutter Client):**
   - All interactive touch targets adhere to Material Design accessibility guidelines with minimum bounds of $48 \times 48\text{ dp}$.
   - Full support for Android TalkBack screen reader, providing explicit `Semantics` labels for capture sweeps, thumbnail galleries, and review lists.
   - Dynamic system font scaling is supported up to 200% without horizontal layout breaks or text clipping.

5. **Inclusivity & Non-Biometric Alternative Workflows (DPDP Act):**
   - For students with disabilities, physical injuries, or withheld biometric consent, the platform provides seamless manual roll-call alternatives (`manual_attendance_screen.dart`). No student is ever penalized or automatically marked absent due to biometric non-participation.

---

## 3. Supported Assistive Technologies & Environments

The FRS V7.1 K² platform is engineered and verified for compatibility with:

| Client Tier | Supported Environments | Compatible Assistive Technologies |
| :--- | :--- | :--- |
| **Admin Web Console** | Google Chrome, Microsoft Edge, Mozilla Firefox, Apple Safari (current releases) | NVDA (Windows), JAWS (Windows), VoiceOver (macOS / iOS), Built-in Chrome Screen Reader |
| **Teacher Mobile App** | Android 10.0+ (API Level 29+) | Android TalkBack, Select to Speak, Switch Access, Voice Access |
| **Documentation & Wiki** | GitHub Web Interface, PDF exports | Built-in browser zoom, high-contrast display modes |

---

## 4. Automated Testing & Verification in CI/CD

Accessibility standards are continuously enforced through automated CI/CD pipelines:
- **Playwright Browser E2E:** Automated accessibility assertions verify skip-to-content links, viewport adaptability across mobile and desktop breakpoints, and DOM structure.
- **Static Analysis:** Dart analysis and TypeScript typecheck pipelines enforce semantic attributes and reject invalid accessibility properties.

---

## 5. Known Limitations & Alternative Solutions

While we strive for comprehensive accessibility, certain features present inherent constraints:
- **Camera Capture Sweep:** Capturing multi-photo classroom sweeps requires pointing the physical camera toward the classroom seating rows. For visually impaired faculty members, the app provides full access to the **Manual Roll-Call** workflow, enabling attendance recording via keyboard or TalkBack-driven student rosters without using the camera.

---

## 6. Feedback & Reporting Barriers

We welcome feedback on the accessibility of the FRS V7.1 K² platform. If you encounter accessibility barriers or have suggestions for improvement, please contact our engineering team:

- **Institutional Contact:** KUCET Academic Accessibility Office
- **Technical Maintainer:** Katkam Koushik
- **Email:** `koushikkatkam@gmail.com`
- **Postal Address:** Kakatiya University College of Engineering & Technology, KU Campus, Warangal, Telangana 506009, India
- **Repository Issues:** [Submit an Accessibility Issue](https://github.com/KatkamKoushik/K-Squared-Face-Recognition-Attendance-System/issues)

We aim to acknowledge feedback within **48 hours** and provide a resolution or workaround within **5 business days**.

---

*This statement was created on November 4, 2026, and is reviewed periodically alongside each institutional release.*
