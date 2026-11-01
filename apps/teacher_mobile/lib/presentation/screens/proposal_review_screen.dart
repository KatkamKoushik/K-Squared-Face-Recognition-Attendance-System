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
              child: ListView.separated(
                padding: const EdgeInsets.all(16),
                itemCount: candidates.length,
                separatorBuilder: (context, index) => const SizedBox(height: 12),
                itemBuilder: (context, index) {
                  final candidate = candidates[index];
                  final isPresent = candidate.unitAttendance.values.any((s) => s == AttendanceStatus.presentConfirmed);

                  return Card(
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

                          if (candidate.uncertaintyReason != null) ...[
                            const SizedBox(height: 10),
                            Container(
                              padding: const EdgeInsets.all(10),
                              decoration: BoxDecoration(
                                color: AppTheme.backgroundLight,
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(color: AppTheme.borderLight),
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Icon(Icons.info_outline, size: 16, color: AppTheme.textMutedLight),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      candidate.uncertaintyReason!,
                                      style: const TextStyle(fontSize: 12, color: AppTheme.textMutedLight),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],

                          const SizedBox(height: 14),
                          const Divider(height: 1),
                          const SizedBox(height: 10),

                          // Quick Action Row
                          Row(
                            children: [
                              if (candidate.highestSimilarityScore != null)
                                Text(
                                  'Similarity: ${(candidate.highestSimilarityScore! * 100).toInt()}%',
                                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
                                ),
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
                  );
                },
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
