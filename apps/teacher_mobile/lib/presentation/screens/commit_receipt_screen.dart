import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../data/models/domain_contracts.dart';
import '../../logic/session_provider.dart';

class CommitReceiptScreen extends ConsumerStatefulWidget {
  const CommitReceiptScreen({super.key});

  @override
  ConsumerState<CommitReceiptScreen> createState() => _CommitReceiptScreenState();
}

class _CommitReceiptScreenState extends ConsumerState<CommitReceiptScreen> {
  bool _isCommitting = false;

  Future<void> _handleCommit() async {
    final sessionState = ref.read(sessionProvider);
    final conductedUnits = sessionState.conductedUnitsCount;
    final unadjudicatedCount = sessionState.candidates.where((c) {
      for (int i = 1; i <= conductedUnits; i++) {
        if (c.unitAttendance[i] == null) return true;
      }
      return false;
    }).length;

    if (unadjudicatedCount > 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Cannot commit: $unadjudicatedCount student(s) have unadjudicated units. '
            'Please adjudicate each or click "Mark All Absent".',
          ),
          backgroundColor: Colors.redAccent,
          duration: const Duration(seconds: 4),
        ),
      );
      return;
    }

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        title: const Text('Commit Final Attendance?'),
        content: const Text(
          'This action will permanently commit attendance records to the PostgreSQL ledger. '
          'An immutable audit event and cryptographic receipt will be generated.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogCtx, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(dialogCtx, true),
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.statusCommitted),
            child: const Text('Confirm & Commit'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      setState(() => _isCommitting = true);
      final receipt = await ref.read(sessionProvider.notifier).commitFinalAttendance();
      setState(() => _isCommitting = false);

      if (receipt == null && mounted) {
        final err = ref.read(sessionProvider).errorMessage ?? 'Commit rejected or server unreachable.';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(err),
            backgroundColor: Colors.redAccent,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    }
  }

  Future<void> _confirmMarkAllUnadjudicatedAsAbsent(BuildContext context, int count) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Confirm Faculty Adjudication'),
        content: Text(
          'Explicitly record ABSENT_CONFIRMED for all $count unadjudicated student(s) across all conducted units? '
          'This is an explicit, audited faculty decision.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.statusError),
            child: const Text('Confirm Absent'),
          ),
        ],
      ),
    );
    if (confirmed == true) {
      ref.read(sessionProvider.notifier).markAllUnadjudicatedAsAbsent();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final sessionState = ref.watch(sessionProvider);
    final receipt = sessionState.receipt;
    final candidates = sessionState.candidates;
    final conductedUnits = sessionState.conductedUnitsCount;

    // If finalized, render durable receipt view
    if (receipt != null) {
      return Scaffold(
        appBar: AppBar(
          title: const Text('Commit Receipt'),
          automaticallyImplyLeading: false,
        ),
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              children: [
                const Spacer(),
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: AppTheme.surfaceLight,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppTheme.statusCommitted, width: 2),
                    boxShadow: [
                      BoxShadow(
                        color: AppTheme.statusCommitted.withValues(alpha: 0.1),
                        blurRadius: 16,
                        offset: const Offset(0, 6),
                      ),
                    ],
                  ),
                  child: Column(
                    children: [
                      const CircleAvatar(
                        radius: 32,
                        backgroundColor: AppTheme.statusCommitted,
                        child: Icon(Icons.shield_outlined, color: Colors.white, size: 36),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'ATTENDANCE COMMITTED',
                        style: theme.textTheme.titleMedium?.copyWith(
                          color: AppTheme.statusCommitted,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.2,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Session: ${receipt.sessionId}',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                      const Divider(height: 32),
                      _ReceiptRow(label: 'Conducted Units', value: '${receipt.totalConductedUnits} Units'),
                      _ReceiptRow(label: 'Total Present', value: '${receipt.totalPresentRecords} Records'),
                      _ReceiptRow(label: 'Total Absent', value: '${receipt.totalAbsentRecords} Records'),
                      _ReceiptRow(label: 'Committed At', value: receipt.committedAt.toLocal().toString().split('.')[0]),
                      const SizedBox(height: 16),
                      Container(
                        padding: const EdgeInsets.all(12),
                        width: double.infinity,
                        decoration: BoxDecoration(
                          color: AppTheme.surfaceVariantLight,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'TRANSACTION HASH (ACID)',
                              style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.textMutedLight),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              receipt.receiptHash,
                              style: const TextStyle(fontSize: 11, fontFamily: 'monospace'),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const Spacer(),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () {
                      ref.read(sessionProvider.notifier).resetSession();
                      Navigator.of(context).popUntil((route) => route.isFirst);
                    },
                    child: const Text('Return to Home Dashboard'),
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

    final unadjudicatedCount = candidates.where((c) {
      for (int i = 1; i <= conductedUnits; i++) {
        if (c.unitAttendance[i] == null) return true;
      }
      return false;
    }).length;

    // Pre-commit unit-by-unit review
    return Scaffold(
      appBar: AppBar(
        title: const Text('Unit-by-Unit Review'),
      ),
      body: SafeArea(
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              color: AppTheme.surfaceLight,
              child: Row(
                children: [
                  const Icon(Icons.info_outline, color: AppTheme.secondaryBlue, size: 20),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Review attendance across each conducted unit (1 to $conductedUnits). '
                      'Every student must have an explicit decision.',
                      style: theme.textTheme.bodyMedium,
                    ),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),

            // Adjudication warning banner if any unconfirmed students
            if (unadjudicatedCount > 0)
              Container(
                margin: const EdgeInsets.all(12),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.amber.shade50,
                  border: Border.all(color: Colors.amber.shade300),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Icon(Icons.warning_amber_rounded, color: Colors.amber.shade800),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '$unadjudicatedCount student(s) have unconfirmed units. Adjudicate each or mark all unadjudicated as absent.',
                        style: TextStyle(fontSize: 12, color: Colors.amber.shade900),
                      ),
                    ),
                    TextButton(
                      onPressed: () => _confirmMarkAllUnadjudicatedAsAbsent(context, unadjudicatedCount),
                      child: const Text('Mark All Absent', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                    ),
                  ],
                ),
              ),

            Expanded(
              child: ListView.separated(
                padding: const EdgeInsets.all(16),
                itemCount: candidates.length,
                separatorBuilder: (context, index) => const SizedBox(height: 12),
                itemBuilder: (context, index) {
                  final candidate = candidates[index];

                  return Card(
                    child: Padding(
                      padding: const EdgeInsets.all(14.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(candidate.fullName, style: const TextStyle(fontWeight: FontWeight.bold)),
                                    Text(
                                      candidate.rollNumber,
                                      style: const TextStyle(fontSize: 12, color: AppTheme.textMutedLight),
                                    ),
                                  ],
                                ),
                              ),
                              Text(
                                candidate.proposalStatus?.name ?? 'Unresolved Sighting',
                                style: const TextStyle(fontSize: 11, color: AppTheme.textMutedLight),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Wrap(
                            spacing: 8.0,
                            runSpacing: 6.0,
                            children: List.generate(conductedUnits, (unitIdx) {
                              final unitNum = unitIdx + 1;
                              final status = candidate.unitAttendance[unitNum];
                              final isPresent = status == AttendanceStatus.presentConfirmed;
                              final isAbsent = status == AttendanceStatus.absentConfirmed;
                              final isUndecided = status == null;

                              String labelText = 'Unit $unitNum: Undecided';
                              Color chipColor = Colors.orange.shade700;
                              if (isPresent) {
                                labelText = 'Unit $unitNum: Present';
                                chipColor = AppTheme.statusMatched;
                              } else if (isAbsent) {
                                labelText = 'Unit $unitNum: Absent';
                                chipColor = AppTheme.statusError;
                              }

                              return FilterChip(
                                label: Text(labelText),
                                selected: isPresent,
                                selectedColor: AppTheme.statusMatched.withValues(alpha: 0.2),
                                checkmarkColor: AppTheme.statusMatched,
                                side: BorderSide(
                                  color: isUndecided ? Colors.orange.shade300 : chipColor.withValues(alpha: 0.5),
                                ),
                                labelStyle: TextStyle(
                                  color: chipColor,
                                  fontWeight: isUndecided ? FontWeight.normal : FontWeight.bold,
                                  fontSize: 12,
                                ),
                                onSelected: (val) {
                                  ref.read(sessionProvider.notifier).updateStudentUnitAttendance(
                                        candidate.studentId,
                                        unitNum,
                                        val ? AttendanceStatus.presentConfirmed : AttendanceStatus.absentConfirmed,
                                      );
                                },
                              );
                            }),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),

            if (sessionState.errorMessage != null)
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.amber.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.amber.shade200),
                ),
                child: Row(
                  children: [
                    Icon(Icons.warning_amber_rounded, size: 16, color: Colors.amber.shade800),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        sessionState.errorMessage!,
                        style: TextStyle(fontSize: 11, color: Colors.amber.shade900, fontWeight: FontWeight.w500),
                      ),
                    ),
                    TextButton(
                      onPressed: () async {
                        setState(() => _isCommitting = true);
                        final synced = await ref.read(sessionProvider.notifier).syncOfflineJournal();
                        setState(() => _isCommitting = false);
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(
                                synced > 0
                                    ? 'Synchronized with control plane. Receipt issued.'
                                    : 'Server still unreachable. Change remains safely in offline journal.',
                              ),
                            ),
                          );
                        }
                      },
                      child: const Text('Retry Sync', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
              ),

            Container(
              padding: const EdgeInsets.all(16),
              decoration: const BoxDecoration(
                color: AppTheme.surfaceLight,
                border: Border(top: BorderSide(color: AppTheme.borderLight)),
              ),
              child: SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  icon: _isCommitting
                      ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : const Icon(Icons.verified_user_rounded),
                  label: Text(_isCommitting ? 'Committing to Ledger...' : 'Commit Final Attendance ($conductedUnits Units)'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: unadjudicatedCount > 0 ? Colors.grey : AppTheme.statusCommitted,
                  ),
                  onPressed: _isCommitting ? null : _handleCommit,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ReceiptRow extends StatelessWidget {
  final String label;
  final String value;

  const _ReceiptRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: AppTheme.textMutedLight, fontSize: 13)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
        ],
      ),
    );
  }
}
