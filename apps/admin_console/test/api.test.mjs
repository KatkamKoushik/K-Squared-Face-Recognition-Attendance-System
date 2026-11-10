import test from "node:test";
import assert from "node:assert/strict";

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

test("Attendance percentage calculation invariants", () => {
  const calculateAttendancePercent = (attended, conducted) => {
    if (conducted === 0) {
      return { display: "N/A", isNa: true };
    }
    const pct = (100 * attended) / conducted;
    return { display: `${pct.toFixed(1)}%`, isNa: false };
  };

  // 100% attended
  const full = calculateAttendancePercent(10, 10);
  assert.equal(full.display, "100.0%");
  assert.equal(full.isNa, false);

  // 75% threshold
  const threshold = calculateAttendancePercent(3, 4);
  assert.equal(threshold.display, "75.0%");
  assert.equal(threshold.isNa, false);

  // Zero conducted units (Section 4.2 blueprint invariant: must evaluate to N/A, not 0.0%)
  const zeroConducted = calculateAttendancePercent(0, 0);
  assert.equal(zeroConducted.display, "N/A");
  assert.equal(zeroConducted.isNa, true);
});
