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
      await ref.read(sessionProvider.notifier).commitFinalAttendance();
      setState(() => _isCommitting = false);
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
                        'Attendance Committed (FINALIZED)',
                        style: theme.textTheme.headlineMedium?.copyWith(
                          color: AppTheme.statusCommitted,
                          fontSize: 20,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        'Receipt ID: ${receipt.id}',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontFamily: 'monospace'),
                      ),
                      const SizedBox(height: 20),
                      const Divider(),
                      const SizedBox(height: 12),
                      _ReceiptRow(label: 'Conducted Units', value: '${receipt.totalConductedUnits} Units'),
                      _ReceiptRow(label: 'Total Present', value: '${receipt.totalPresentRecords} Students'),
                      _ReceiptRow(label: 'Total Absent', value: '${receipt.totalAbsentRecords} Students'),
                      _ReceiptRow(label: 'Committed Time', value: receipt.committedAt.toLocal().toString().substring(0, 19)),
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.all(10),
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
                      'Review attendance across each conducted unit (1 to $conductedUnits). Tap chips to toggle per-unit attendance.',
                      style: theme.textTheme.bodyMedium,
                    ),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),

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
                                candidate.proposalStatus?.name ?? 'unresolved',
                                style: const TextStyle(fontSize: 11, color: AppTheme.textMutedLight),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Row(
                            children: List.generate(conductedUnits, (unitIdx) {
                              final unitNum = unitIdx + 1;
                              final status = candidate.unitAttendance[unitNum] ?? AttendanceStatus.absentConfirmed;
                              final isPresent = status == AttendanceStatus.presentConfirmed;

                              return Padding(
                                padding: const EdgeInsets.only(right: 8.0),
                                child: FilterChip(
                                  label: Text('Unit $unitNum: ${isPresent ? 'Present' : 'Absent'}'),
                                  selected: isPresent,
                                  selectedColor: AppTheme.statusMatched.withValues(alpha: 0.2),
                                  checkmarkColor: AppTheme.statusMatched,
                                  labelStyle: TextStyle(
                                    color: isPresent ? AppTheme.statusMatched : AppTheme.textMutedLight,
                                    fontWeight: isPresent ? FontWeight.bold : FontWeight.normal,
                                    fontSize: 12,
                                  ),
                                  onSelected: (val) {
                                    ref.read(sessionProvider.notifier).updateStudentUnitAttendance(
                                          candidate.studentId,
                                          unitNum,
                                          val ? AttendanceStatus.presentConfirmed : AttendanceStatus.absentConfirmed,
                                        );
                                  },
                                ),
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
                    backgroundColor: AppTheme.statusCommitted,
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
