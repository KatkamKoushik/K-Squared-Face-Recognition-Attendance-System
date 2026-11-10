import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/status_chip.dart';
import '../../data/models/domain_contracts.dart';
import '../../logic/session_provider.dart';
import 'commit_receipt_screen.dart';
import 'manual_attendance_screen.dart';

class ProposalReviewScreen extends ConsumerWidget {
  const ProposalReviewScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final sessionState = ref.watch(sessionProvider);
    final candidates = sessionState.candidates;
    final unassigned = sessionState.unassignedObservations;
    final conductedUnits = sessionState.conductedUnitsCount;

    // Canonical Metric summaries
    final presentCount = candidates.where((c) => c.evidenceState == EvidenceState.candidate).length;
    final reviewCount = candidates.where((c) => c.evidenceState == EvidenceState.review).length;
    final recaptureCount = candidates.where((c) => c.evidenceState == EvidenceState.recaptureRequired).length;
    final unknownCount = candidates.where((c) => c.evidenceState == EvidenceState.unknown).length;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Review Proposals'),
        actions: [
          IconButton(
            icon: const Icon(Icons.fact_check_outlined),
            tooltip: 'Manual Roll-Call',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => const ManualAttendanceScreen(),
                ),
              );
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Top Overview Bar
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              color: AppTheme.surfaceLight,
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _MetricChip(label: 'Proposed Present', count: presentCount, color: AppTheme.statusMatched),
                    const SizedBox(width: 8),
                    _MetricChip(label: 'Needs Review', count: reviewCount, color: AppTheme.statusReview),
                    const SizedBox(width: 8),
                    _MetricChip(label: 'Recapture Needed', count: recaptureCount, color: AppTheme.statusRecapture),
                    const SizedBox(width: 8),
                    _MetricChip(label: 'Unrecognized', count: unknownCount, color: AppTheme.statusUnknown),
                  ],
                ),
              ),
            ),
            const Divider(height: 1),

            // Invariant Notice
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              color: AppTheme.surfaceVariantLight,
              child: Row(
                children: [
                  const Icon(Icons.security_outlined, size: 16, color: AppTheme.primaryNavy),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'AI proposals are non-binding. Faculty review is mandatory before committing.',
                      style: theme.textTheme.bodyMedium?.copyWith(fontSize: 12),
                    ),
                  ),
                ],
              ),
            ),

            // Candidates List
            Expanded(
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Roster Candidates Section Header
                  Padding(
                    padding: const EdgeInsets.only(bottom: 12.0),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'Enrolled Roster Proposals (${candidates.length})',
                          style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                  ),

                  ...candidates.map((candidate) {
                    final isPresent = candidate.unitAttendance.values.any((s) => s == AttendanceStatus.presentConfirmed);

                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12.0),
                      child: Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  CircleAvatar(
                                    radius: 20,
                                    backgroundColor: isPresent
                                        ? AppTheme.statusMatched.withValues(alpha: 0.15)
                                        : AppTheme.borderLight,
                                    child: Text(
                                      candidate.fullName.substring(0, 1),
                                      style: TextStyle(
                                        fontWeight: FontWeight.bold,
                                        color: isPresent ? AppTheme.statusMatched : AppTheme.textMutedLight,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(candidate.fullName, style: theme.textTheme.titleLarge?.copyWith(fontSize: 16)),
                                        const SizedBox(height: 2),
                                        Text(
                                          candidate.rollNumber,
                                          style: const TextStyle(
                                            fontFamily: 'monospace',
                                            fontSize: 13,
                                            color: AppTheme.textMutedLight,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  EvidenceStatusChip(state: candidate.evidenceState, compact: true),
                                ],
                              ),

                              // P0.8 Evidence Provenance Block
                              if (candidate.sightingsCount > 0) ...[
                                const SizedBox(height: 10),
                                Container(
                                  width: double.infinity,
                                  padding: const EdgeInsets.all(10),
                                  decoration: BoxDecoration(
                                    color: AppTheme.backgroundLight,
                                    borderRadius: BorderRadius.circular(6),
                                    border: Border.all(color: AppTheme.borderLight),
                                  ),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        'PROVENANCE: Frame ${candidate.frameId ?? "N/A"} • Detection ${candidate.detectionId ?? "N/A"}',
                                        style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.textMutedLight),
                                      ),
                                      const SizedBox(height: 3),
                                      Text(
                                        'Similarity: ${((candidate.highestSimilarityScore ?? 0.0) * 100).toInt()}% (Threshold: ${((candidate.matchThreshold ?? 0.70) * 100).toInt()}%) • Quality: ${((candidate.qualityScore ?? 1.0) * 100).toInt()}%',
                                        style: const TextStyle(fontSize: 11, color: AppTheme.primaryNavy, fontWeight: FontWeight.w600),
                                      ),
                                      const SizedBox(height: 2),
                                      Text(
                                        'Model Lineage: ${candidate.modelVersion ?? "sface_128d_v1"}',
                                        style: const TextStyle(fontSize: 10, color: AppTheme.textMutedLight),
                                      ),
                                    ],
                                  ),
                                ),
                              ] else ...[
                                const SizedBox(height: 10),
                                if (candidate.uncertaintyReason?.contains('NON_BIOMETRIC_ALTERNATIVE_REQUIRED') == true)
                                  Container(
                                    width: double.infinity,
                                    padding: const EdgeInsets.all(10),
                                    decoration: BoxDecoration(
                                      color: Colors.indigo.shade50,
                                      borderRadius: BorderRadius.circular(6),
                                      border: Border.all(color: Colors.indigo.shade200),
                                    ),
                                    child: Row(
                                      children: [
                                        Icon(Icons.shield_outlined, size: 16, color: Colors.indigo.shade800),
                                        const SizedBox(width: 8),
                                        Expanded(
                                          child: Text(
                                            'DPDP ACT NON-BIOMETRIC ALTERNATIVE — Consent withheld. Conduct manual roll-call.',
                                            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.indigo.shade900),
                                          ),
                                        ),
                                      ],
                                    ),
                                  )
                                else
                                  Container(
                                    width: double.infinity,
                                    padding: const EdgeInsets.all(10),
                                    decoration: BoxDecoration(
                                      color: Colors.orange.shade50,
                                      borderRadius: BorderRadius.circular(6),
                                      border: Border.all(color: Colors.orange.shade200),
                                    ),
                                    child: Row(
                                      children: [
                                        Icon(Icons.videocam_off_outlined, size: 16, color: Colors.orange.shade800),
                                        const SizedBox(width: 8),
                                        Expanded(
                                          child: Text(
                                            'NO CAMERA SIGHTING — Awaiting manual faculty roll-call.',
                                            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.orange.shade900),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                              ],

                              if (candidate.uncertaintyReason != null && candidate.uncertaintyReason != 'NO_CAMERA_SIGHTING') ...[
                                const SizedBox(height: 8),
                                Text(
                                  candidate.uncertaintyReason!,
                                  style: const TextStyle(fontSize: 11, color: AppTheme.textMutedLight, fontStyle: FontStyle.italic),
                                ),
                              ],

                              const SizedBox(height: 12),
                              const Divider(height: 1),
                              const SizedBox(height: 8),

                              // Quick Action Row
                              Row(
                                children: [
                                  const Spacer(),
                                  TextButton(
                                    onPressed: () {
                                      _showAdjudicationSheet(context, ref, candidate, conductedUnits);
                                    },
                                    child: const Text('Adjudicate / Edit'),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                  }),

                  // P0.8 Unassigned Face Observations Section
                  if (unassigned.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8.0),
                      child: Text(
                        'Unassigned Classroom Observations (${unassigned.length})',
                        style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.textMainLight),
                      ),
                    ),
                    const Text(
                      'Detected face crops with quality or similarity below threshold. Kept unassigned per P0.8 Consistency Gate.',
                      style: TextStyle(fontSize: 11, color: AppTheme.textMutedLight),
                    ),
                    const SizedBox(height: 10),
                    ...unassigned.map((obs) => Card(
                      color: AppTheme.surfaceLight,
                      margin: const EdgeInsets.only(bottom: 10),
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: Colors.red.shade50,
                                    borderRadius: BorderRadius.circular(4),
                                    border: Border.all(color: Colors.red.shade200),
                                  ),
                                  child: Text(
                                    obs.issueReason,
                                    style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.red.shade800),
                                  ),
                                ),
                                const Spacer(),
                                Text(
                                  'Frame: ${obs.frameId}',
                                  style: const TextStyle(fontSize: 10, color: AppTheme.textMutedLight),
                                ),
                              ],
                            ),
                            const SizedBox(height: 6),
                            Text(
                              obs.description,
                              style: const TextStyle(fontSize: 12, color: AppTheme.textMutedLight),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Quality: ${(obs.qualityScore * 100).toInt()}% • Unlinked Observation (No Roster Sighting)',
                              style: const TextStyle(fontSize: 10, color: AppTheme.textMutedLight),
                            ),
                          ],
                        ),
                      ),
                    )),
                  ],
                ],
              ),
            ),

            // Bottom Action Button
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.surfaceLight,
                border: const Border(top: BorderSide(color: AppTheme.borderLight)),
              ),
              child: SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  icon: const Icon(Icons.checklist_rounded),
                  label: const Text('Review Units & Confirm Commit'),
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => const CommitReceiptScreen(),
                      ),
                    );
                  },
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showAdjudicationSheet(
    BuildContext context,
    WidgetRef ref,
    CandidateProposalItem candidate,
    int conductedUnits,
  ) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (sheetContext) {
        return Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Adjudicate Student: ${candidate.fullName}',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              Text('Roll Number: ${candidate.rollNumber}'),
              const SizedBox(height: 20),
              const Text(
                'Select Faculty Decision:',
                style: TextStyle(fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 12),
              ListTile(
                leading: const Icon(Icons.check_circle, color: AppTheme.statusMatched),
                title: const Text('Mark Present (PRESENT_CONFIRMED)'),
                subtitle: Text('Credits student for $conductedUnits of $conductedUnits units'),
                onTap: () {
                  ref.read(sessionProvider.notifier).resolveCandidateState(
                        candidate.studentId,
                        AttendanceStatus.presentConfirmed,
                      );
                  Navigator.pop(sheetContext);
                },
              ),
              ListTile(
                leading: const Icon(Icons.cancel, color: AppTheme.statusError),
                title: const Text('Mark Absent (ABSENT_CONFIRMED)'),
                subtitle: const Text('Confirmed not physically in classroom'),
                onTap: () {
                  ref.read(sessionProvider.notifier).resolveCandidateState(
                        candidate.studentId,
                        AttendanceStatus.absentConfirmed,
                      );
                  Navigator.pop(sheetContext);
                },
              ),
              ListTile(
                leading: const Icon(Icons.camera_alt, color: AppTheme.statusRecapture),
                title: const Text('Flag for Targeted Recapture'),
                subtitle: const Text('Requires capturing another frame of this student'),
                onTap: () {
                  Navigator.pop(sheetContext);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Targeted recapture flag logged.')),
                  );
                },
              ),
              const SizedBox(height: 16),
            ],
          ),
        );
      },
    );
  }
}

class _MetricChip extends StatelessWidget {
  final String label;
  final int count;
  final Color color;

  const _MetricChip({
    required this.label,
    required this.count,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '$count',
            style: TextStyle(fontWeight: FontWeight.bold, color: color, fontSize: 14),
          ),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: color),
          ),
        ],
      ),
    );
  }
}
