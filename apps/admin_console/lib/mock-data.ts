/**
 * Institutional Mock & Fallback Fixtures for FRS Admin Console.
 * Used exclusively for local offline preview and deterministic verification.
 * Authoritative production runtime queries PostgreSQL control plane via lib/api.ts.
 */

export interface StudentConsentRow {
  studentId: string;
  rollNumber: string;
  fullName: string;
  biometricConsentActive: boolean;
  alternativeRollCallRequired: boolean;
}

export const FALLBACK_STUDENTS: StudentConsentRow[] = [
  {
    studentId: "STU-KUCET-00622501",
    rollNumber: "00622501",
    fullName: "Katkam Koushik",
    biometricConsentActive: true,
    alternativeRollCallRequired: false,
  },
  {
    studentId: "STU-KUCET-00622502",
    rollNumber: "00622502",
    fullName: "A. Sai Teja",
    biometricConsentActive: true,
    alternativeRollCallRequired: false,
  },
  {
    studentId: "STU-KUCET-00622503",
    rollNumber: "00622503",
    fullName: "B. Manasa Reddy",
    biometricConsentActive: true,
    alternativeRollCallRequired: false,
  },
  {
    studentId: "STU-KUCET-00622504",
    rollNumber: "00622504",
    fullName: "Ch. Rahul",
    biometricConsentActive: false,
    alternativeRollCallRequired: true,
  },
  {
    studentId: "STU-KUCET-00622505",
    rollNumber: "00622505",
    fullName: "D. Ananya",
    biometricConsentActive: true,
    alternativeRollCallRequired: false,
  },
  {
    studentId: "STU-KUCET-00622506",
    rollNumber: "00622506",
    fullName: "E. Srikanth",
    biometricConsentActive: true,
    alternativeRollCallRequired: false,
  },
  {
    studentId: "STU-KUCET-00622507",
    rollNumber: "00622507",
    fullName: "G. Akhil Kumar",
    biometricConsentActive: true,
    alternativeRollCallRequired: false,
  },
];

export const FALLBACK_GOVERNANCE_SUMMARY = {
  total_students: 7,
  students_with_biometric_consent: 6,
  students_withheld_consent: 1,
  consent_compliance_percentage: 85.7,
  total_captured_frames: 42,
  active_unpurged_frames: 18,
  purged_frames: 24,
  disk_usage_bytes: 8400000,
  disk_usage_mb: 8.01,
  retention_policy_days: 7,
};
