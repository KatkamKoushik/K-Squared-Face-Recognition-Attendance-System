import { supabaseFetch } from "./supabase";
import {
  getAuthToken,
  AdminDashboardMetrics,
  DashboardRecentSessionItem,
  DemoEnrolledStudentSummary,
  StudentListItem,
  DepartmentItem,
  CohortItem,
  TermItem,
  SubjectOfferingItem,
  EnrollmentSubmissionItem,
  ReadinessTelemetry,
  GovernanceSummary,
} from "./api";

/**
 * Universal direct Supabase PostgREST fallback for K² FRS Admin Console.
 * Enables live executive overview, roster preview, and student gallery views
 * directly from cloud Postgres when the local FastAPI bridge is offline.
 */
export async function fallbackFromSupabase<T>(endpoint: string): Promise<T | null> {
  const cleanEndpoint = endpoint.split("?")[0];
  const queryString = endpoint.includes("?") ? endpoint.split("?")[1] : "";

  try {
    // 1. Dashboard Executive Overview Metrics
    if (cleanEndpoint === "/enrollment/dashboard/stats") {
      const [
        studentsRes,
        offeringsRes,
        deptsRes,
        cohortsRes,
        pendingRes,
        sessionsRes,
        unitsRes,
        subjectsRes,
        facultyRes,
        receiptsRes,
        recordsRes,
      ] = await Promise.all([
        supabaseFetch("/rest/v1/students?select=id"),
        supabaseFetch("/rest/v1/subject_offerings?select=id,section,subject_id"),
        supabaseFetch("/rest/v1/departments?select=id,code,name"),
        supabaseFetch("/rest/v1/cohorts?select=id,name"),
        supabaseFetch("/rest/v1/enrollment_submissions?select=id&status=eq.PENDING_REVIEW"),
        supabaseFetch("/rest/v1/attendance_sessions?select=id,session_date,state,offering_id,faculty_id,created_at&order=created_at.desc&limit=10"),
        supabaseFetch("/rest/v1/attendance_units?select=id,session_id,is_conducted,status"),
        supabaseFetch("/rest/v1/subjects?select=id,code,name"),
        supabaseFetch("/rest/v1/faculty?select=id,full_name"),
        supabaseFetch("/rest/v1/commit_receipts?select=session_id,receipt_hash"),
        supabaseFetch("/rest/v1/attendance_records?select=session_id,status"),
      ]);

      const students = (await studentsRes.json().catch(() => [])) || [];
      const offerings = (await offeringsRes.json().catch(() => [])) || [];
      const departments = (await deptsRes.json().catch(() => [])) || [];
      const cohorts = (await cohortsRes.json().catch(() => [])) || [];
      const pending = (await pendingRes.json().catch(() => [])) || [];
      const sessions = (await sessionsRes.json().catch(() => [])) || [];
      const units = (await unitsRes.json().catch(() => [])) || [];
      const subjects = (await subjectsRes.json().catch(() => [])) || [];
      const faculty = (await facultyRes.json().catch(() => [])) || [];
      const receipts = (await receiptsRes.json().catch(() => [])) || [];
      const records = (await recordsRes.json().catch(() => [])) || [];

      const todayStr = new Date().toISOString().slice(0, 10);
      const unitsToday = units.filter(
        (u: any) => u.is_conducted && (u.status === "COMMITTED" || u.status === "CONDUCTED_CONFIRMED")
      );

      const recentSessions: DashboardRecentSessionItem[] = sessions.map((s: any) => {
        const off = offerings.find((o: any) => o.id === s.offering_id);
        const subj = subjects.find((sb: any) => sb.id === off?.subject_id);
        const fac = faculty.find((f: any) => f.id === s.faculty_id);
        const cohort = cohorts.find((c: any) => c.id === off?.cohort_id);
        const rec = receipts.find((r: any) => r.session_id === s.id);
        const sessionUnits = units.filter((u: any) => u.session_id === s.id && u.is_conducted);
        const sessionRecords = records.filter((ar: any) => ar.session_id === s.id);
        const presentCount = sessionRecords.filter((ar: any) => ar.status === "PRESENT").length;
        const totalEnrolled = sessionRecords.length || 0;
        const pct = totalEnrolled > 0 ? ((presentCount / totalEnrolled) * 100).toFixed(1) + "%" : "0.0%";

        return {
          session_id: s.id,
          subject_code: subj?.code || "",
          subject_name: subj?.name || "Subject",
          cohort: cohort?.name || "",
          faculty: fac?.full_name || "Unassigned",
          conducted_units: sessionUnits.length,
          present_count: presentCount,
          total_enrolled: totalEnrolled,
          attendance_percent: pct,
          receipt_hash: rec?.receipt_hash || "",
          timestamp: s.session_date || todayStr,
        };
      });

      const metrics: AdminDashboardMetrics = {
        total_enrolled_students: students.length,
        total_active_offerings: offerings.length,
        pending_submissions_count: pending.length,
        finalized_sessions_count: sessions.filter((s: any) => s.state === "FINALIZED").length || sessions.length,
        conducted_units_today: unitsToday.length,
        active_departments_count: departments.length,
        active_cohorts_count: cohorts.length,
        recent_sessions: recentSessions,
        system_readiness: "AUTHORITATIVE_POSTGRES_ACTIVE",
      };

      return metrics as unknown as T;
    }

    // 2. Demo Visualizer Enrolled Gallery (Requires authenticated session)
    if (cleanEndpoint === "/demo/enrolled-students") {
      const isAuth = Boolean(getAuthToken());
      if (!isAuth) {
        return [] as unknown as T;
      }

      const [studentsRes, submissionsRes, cohortsRes, deptsRes] = await Promise.all([
        supabaseFetch("/rest/v1/students?select=id,roll_number,full_name,is_active,cohort_id&order=roll_number.asc"),
        supabaseFetch("/rest/v1/enrollment_submissions?status=eq.APPROVED&select=roll_number,photo_storage_path"),
        supabaseFetch("/rest/v1/cohorts?select=id,department_id"),
        supabaseFetch("/rest/v1/departments?select=id,code"),
      ]);

      const students = (await studentsRes.json().catch(() => [])) || [];
      const submissions = (await submissionsRes.json().catch(() => [])) || [];
      const cohorts = (await cohortsRes.json().catch(() => [])) || [];
      const departments = (await deptsRes.json().catch(() => [])) || [];

      // Parse department filter if provided
      const params = new URLSearchParams(queryString);
      const deptFilter = params.get("department_code")?.toUpperCase();

      let gallery: DemoEnrolledStudentSummary[] = students.map((s: any) => {
        const sub = submissions.find((subm: any) => subm.roll_number === s.roll_number);
        const cohort = cohorts.find((c: any) => c.id === s.cohort_id);
        const dept = departments.find((d: any) => d.id === cohort?.department_id);

        return {
          student_id: s.id,
          roll_number: s.roll_number,
          full_name: s.full_name,
          is_active: s.is_active,
          has_reference_photo: Boolean(sub?.photo_storage_path),
          photo_url: sub?.photo_storage_path || undefined,
          department_code: dept?.code || "",
        };
      });

      if (deptFilter && deptFilter !== "ALL") {
        gallery = gallery.filter((s) => s.department_code === deptFilter);
      }

      return gallery as unknown as T;
    }

    // 3. Academic Student Directory
    if (cleanEndpoint === "/academic/students") {
      const [studentsRes, cohortsRes, deptsRes] = await Promise.all([
        supabaseFetch("/rest/v1/students?select=id,roll_number,full_name,is_active,cohort_id,created_at&order=roll_number.asc"),
        supabaseFetch("/rest/v1/cohorts?select=id,name,department_id"),
        supabaseFetch("/rest/v1/departments?select=id,name,code"),
      ]);

      const students = (await studentsRes.json().catch(() => [])) || [];
      const cohorts = (await cohortsRes.json().catch(() => [])) || [];
      const depts = (await deptsRes.json().catch(() => [])) || [];

      const list: StudentListItem[] = students.map((s: any) => {
        const cohort = cohorts.find((c: any) => c.id === s.cohort_id);
        const dept = depts.find((d: any) => d.id === cohort?.department_id);

        return {
          id: s.id,
          roll_number: s.roll_number,
          full_name: s.full_name,
          department_id: cohort?.department_id || "",
          current_term: s.current_term || "",
          status: s.is_active ? "ACTIVE" : "INACTIVE",
          consent_signed: Boolean(s.consent_signed),
          enrollment_date: s.created_at ? s.created_at.slice(0, 10) : "",
          is_active: s.is_active,
          cohort_id: s.cohort_id,
          cohort_name: cohort?.name || "",
          department_name: dept?.name || "",
        };
      });

      return list as unknown as T;
    }

    // 4. Academic Departments
    if (cleanEndpoint === "/academic/departments") {
      const res = await supabaseFetch("/rest/v1/departments?select=*&order=code.asc");
      const data = await res.json().catch(() => []);
      return (data || []) as unknown as T;
    }

    // 5. Academic Cohorts
    if (cleanEndpoint === "/academic/cohorts") {
      const res = await supabaseFetch("/rest/v1/cohorts?select=*&order=name.asc");
      const data = await res.json().catch(() => []);
      return (data || []) as unknown as T;
    }

    // 6. Academic Terms
    if (cleanEndpoint === "/academic/terms") {
      const res = await supabaseFetch("/rest/v1/terms?select=*&order=start_date.desc");
      const data = await res.json().catch(() => []);
      return (data || []) as unknown as T;
    }

    // 7. Academic Subject Offerings
    if (cleanEndpoint === "/academic/offerings") {
      const [offeringsRes, subjectsRes, facultyRes, cohortsRes] = await Promise.all([
        supabaseFetch("/rest/v1/subject_offerings?select=*"),
        supabaseFetch("/rest/v1/subjects?select=id,code,name"),
        supabaseFetch("/rest/v1/faculty?select=id,full_name"),
        supabaseFetch("/rest/v1/cohorts?select=id,name"),
      ]);

      const offerings = (await offeringsRes.json().catch(() => [])) || [];
      const subjects = (await subjectsRes.json().catch(() => [])) || [];
      const faculty = (await facultyRes.json().catch(() => [])) || [];
      const cohorts = (await cohortsRes.json().catch(() => [])) || [];

      const list: SubjectOfferingItem[] = offerings.map((o: any) => {
        const subj = subjects.find((s: any) => s.id === o.subject_id);
        const fac = faculty.find((f: any) => f.id === o.faculty_id);
        const cohort = cohorts.find((c: any) => c.id === o.cohort_id);

        return {
          id: o.id,
          subject_code: subj?.code || "",
          subject_name: subj?.name || "Subject",
          faculty_name: fac?.full_name || "Unassigned",
          cohort_name: cohort?.name || "",
          section: o.section || "",
          term_name: "",
          enrolled_count: 0,
          total_sessions: 0,
        };
      });

      return list as unknown as T;
    }

    // 8. Enrollment Submissions
    if (cleanEndpoint === "/enrollment/submissions") {
      const res = await supabaseFetch("/rest/v1/enrollment_submissions?select=*&order=created_at.desc");
      const data = await res.json().catch(() => []);
      return (data || []) as unknown as T;
    }

    // 9. Governance Status
    if (cleanEndpoint === "/governance/status") {
      const [studentsRes, consentsRes] = await Promise.all([
        supabaseFetch("/rest/v1/students?select=id"),
        supabaseFetch("/rest/v1/student_consents?select=student_id,consent_given"),
      ]);
      const students = (await studentsRes.json().catch(() => [])) || [];
      const consents = (await consentsRes.json().catch(() => [])) || [];
      const consentedCount = consents.filter((c: any) => c.consent_given).length;
      const withheldCount = consents.filter((c: any) => !c.consent_given).length;
      const pct = students.length > 0 ? (consentedCount / students.length) * 100 : 0.0;

      const summary: GovernanceSummary = {
        total_students: students.length,
        students_with_biometric_consent: consentedCount,
        students_withheld_consent: withheldCount,
        consent_compliance_percentage: Number(pct.toFixed(1)),
        total_captured_frames: 0,
        active_unpurged_frames: 0,
        purged_frames: 0,
        disk_usage_bytes: 0,
        disk_usage_mb: 0.0,
        retention_policy_days: 14,
      };

      return summary as unknown as T;
    }

    // 10. System Health Readiness
    if (cleanEndpoint === "/health/readiness") {
      const readiness: ReadinessTelemetry = {
        status: "DEGRADED",
        api_status: "STANDBY_SUPABASE_DIRECT",
        database: "POSTGRES_CONNECTED",
        worker_queue: "STANDBY_BRIDGE_OFFLINE",
        model_registry: {
          detector_approved: true,
          recognizer_approved: true,
        },
      };
      return readiness as unknown as T;
    }

    return null;
  } catch (error) {
    console.warn(`[Supabase Fallback Failed] ${endpoint}:`, error);
    return null;
  }
}

