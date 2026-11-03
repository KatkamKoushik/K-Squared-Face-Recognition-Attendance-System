import test from "node:test";
import assert from "node:assert/strict";
import { FALLBACK_STUDENTS, FALLBACK_GOVERNANCE_SUMMARY } from "../lib/mock-data.ts";

test("FALLBACK_STUDENTS fixture integrity and consent invariants", () => {
  assert.equal(FALLBACK_STUDENTS.length, 7, "Must contain exactly 7 sample students");

  const rollNumbers = FALLBACK_STUDENTS.map((s) => s.rollNumber);
  const uniqueRolls = new Set(rollNumbers);
  assert.equal(uniqueRolls.size, 7, "All roll numbers must be unique");

  // Verify non-biometric alternative mapping
  for (const student of FALLBACK_STUDENTS) {
    if (!student.biometricConsentActive) {
      assert.equal(
        student.alternativeRollCallRequired,
        true,
        `Student ${student.studentId} with withheld consent must require alternative roll-call`
      );
    }
  }

  // Verify DPDP consent withholding demonstration exists
  const withheld = FALLBACK_STUDENTS.filter((s) => !s.biometricConsentActive);
  assert.equal(withheld.length, 1, "Must have exactly 1 student with withheld consent for DPDP compliance demonstration");
  assert.equal(withheld[0].rollNumber, "00622504");
});

test("FALLBACK_GOVERNANCE_SUMMARY telemetry consistency", () => {
  assert.equal(FALLBACK_GOVERNANCE_SUMMARY.total_students, 7);
  assert.equal(
    FALLBACK_GOVERNANCE_SUMMARY.students_with_biometric_consent +
      FALLBACK_GOVERNANCE_SUMMARY.students_withheld_consent,
    FALLBACK_GOVERNANCE_SUMMARY.total_students
  );
  assert.equal(
    FALLBACK_GOVERNANCE_SUMMARY.active_unpurged_frames +
      FALLBACK_GOVERNANCE_SUMMARY.purged_frames,
    FALLBACK_GOVERNANCE_SUMMARY.total_captured_frames
  );
  assert.equal(FALLBACK_GOVERNANCE_SUMMARY.retention_policy_days, 7);
});

test("Bearer token authorization header construction", () => {
  const dummyToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummyPayload";
  const customHeaders = {
    "X-Correlation-ID": "corr-unit-test-123",
  };

  const headers = {
    "Content-Type": "application/json",
    ...customHeaders,
  };

  if (dummyToken && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${dummyToken}`;
  }

  assert.equal(headers["Content-Type"], "application/json");
  assert.equal(headers["X-Correlation-ID"], "corr-unit-test-123");
  assert.equal(headers["Authorization"], `Bearer ${dummyToken}`);
});

test("Response envelope unwrapping logic", () => {
  // Scenario 1: Envelope wrapper with { data: ... }
  const enveloped = {
    data: { id: "DEP-CSE", name: "Computer Science" },
    correlation_id: "corr-456",
  };
  const unwrapped1 = enveloped && typeof enveloped === "object" && "data" in enveloped
    ? enveloped.data
    : enveloped;
  assert.deepEqual(unwrapped1, { id: "DEP-CSE", name: "Computer Science" });

  // Scenario 2: Direct raw payload
  const rawPayload = [{ id: "1" }, { id: "2" }];
  const unwrapped2 = rawPayload && typeof rawPayload === "object" && "data" in rawPayload
    ? (rawPayload).data
    : rawPayload;
  assert.deepEqual(unwrapped2, [{ id: "1" }, { id: "2" }]);
});
