import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../data/models/domain_contracts.dart';
import '../../logic/session_provider.dart';
import 'commit_receipt_screen.dart';

class ManualAttendanceScreen extends ConsumerStatefulWidget {
  const ManualAttendanceScreen({super.key});

  @override
  ConsumerState<ManualAttendanceScreen> createState() => _ManualAttendanceScreenState();
}

class _ManualAttendanceScreenState extends ConsumerState<ManualAttendanceScreen> {
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final sessionState = ref.watch(sessionProvider);
    final candidates = sessionState.candidates;
    final conductedUnits = sessionState.conductedUnitsCount;

    final filteredCandidates = candidates.where((c) {
      if (_searchQuery.isEmpty) return true;
      final q = _searchQuery.toLowerCase();
      return c.fullName.toLowerCase().contains(q) || c.rollNumber.toLowerCase().contains(q);
    }).toList();

    int presentCount = 0;
    int absentCount = 0;
    for (final c in candidates) {
      final isPresent = c.unitAttendance.values.any((s) => s == AttendanceStatus.presentConfirmed);
      if (isPresent) {
        presentCount++;
      } else {
        absentCount++;
      }
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Manual Roll-Call Attendance'),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert),
            onSelected: (val) {
              if (val == 'all_present') {
                for (final c in candidates) {
                  ref.read(sessionProvider.notifier).resolveCandidateState(
                        c.studentId,
                        AttendanceStatus.presentConfirmed,
                      );
                }
              } else if (val == 'all_absent') {
                for (final c in candidates) {
                  ref.read(sessionProvider.notifier).resolveCandidateState(
                        c.studentId,
                        AttendanceStatus.absentConfirmed,
                      );
                }
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'all_present',
                child: Row(
                  children: [
                    Icon(Icons.check_circle_outline, color: AppTheme.statusMatched, size: 20),
                    SizedBox(width: 8),
                    Text('Mark All Present'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'all_absent',
                child: Row(
                  children: [
                    Icon(Icons.highlight_off, color: AppTheme.statusError, size: 20),
                    SizedBox(width: 8),
                    Text('Mark All Absent'),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Status bar
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              color: AppTheme.surfaceLight,
              child: Row(
                children: [
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: AppTheme.statusMatched.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: AppTheme.statusMatched.withValues(alpha: 0.3)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Present', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.statusMatched)),
                          Text('$presentCount', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.statusMatched)),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: AppTheme.statusError.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: AppTheme.statusError.withValues(alpha: 0.3)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Absent', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.statusError)),
                          Text('$absentCount', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.statusError)),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: AppTheme.primaryNavy.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: AppTheme.primaryNavy.withValues(alpha: 0.2)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Units', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.primaryNavy)),
                          Text('$conductedUnits Conducted', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.primaryNavy)),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),

            // Search Bar
            Padding(
              padding: const EdgeInsets.all(12),
              child: TextField(
                controller: _searchController,
                decoration: InputDecoration(
                  hintText: 'Search by Roll No or Student Name...',
                  prefixIcon: const Icon(Icons.search, size: 20),
                  suffixIcon: _searchQuery.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear, size: 18),
                          onPressed: () {
                            _searchController.clear();
                            setState(() => _searchQuery = '');
                          },
                        )
                      : null,
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                ),
                onChanged: (val) {
                  setState(() => _searchQuery = val);
                },
              ),
            ),

            // Candidate List
            Expanded(
              child: filteredCandidates.isEmpty
                  ? const Center(child: Text('No students found matching query.'))
                  : ListView.separated(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      itemCount: filteredCandidates.length,
                      separatorBuilder: (context, index) => const SizedBox(height: 10),
                      itemBuilder: (context, index) {
                        final candidate = filteredCandidates[index];
                        final isPresent = candidate.unitAttendance.values.any((s) => s == AttendanceStatus.presentConfirmed);

                        return Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(
                              color: isPresent
                                  ? AppTheme.statusMatched.withValues(alpha: 0.4)
                                  : AppTheme.borderLight,
                            ),
                          ),
                          child: Row(
                            children: [
                              CircleAvatar(
                                radius: 18,
                                backgroundColor: isPresent
                                    ? AppTheme.statusMatched.withValues(alpha: 0.15)
                                    : AppTheme.surfaceVariantLight,
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
                                    Text(
                                      candidate.fullName,
                                      style: theme.textTheme.titleMedium?.copyWith(fontSize: 14),
                                    ),
                                    Text(
                                      candidate.rollNumber,
                                      style: theme.textTheme.bodyMedium?.copyWith(
                                        fontFamily: 'monospace',
                                        fontSize: 12,
                                      ),
                                    ),
                                  ],
                                ),
                              ),

                              // Quick Present / Absent Toggle Buttons
                              Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  IconButton(
                                    icon: Icon(
                                      isPresent ? Icons.check_circle : Icons.check_circle_outline,
                                      color: isPresent ? AppTheme.statusMatched : AppTheme.textMutedLight,
                                      size: 28,
                                    ),
                                    tooltip: 'Mark Present',
                                    onPressed: () {
                                      ref.read(sessionProvider.notifier).resolveCandidateState(
                                            candidate.studentId,
                                            AttendanceStatus.presentConfirmed,
                                          );
                                    },
                                  ),
                                  IconButton(
                                    icon: Icon(
                                      !isPresent ? Icons.cancel : Icons.cancel_outlined,
                                      color: !isPresent ? AppTheme.statusError : AppTheme.textMutedLight,
                                      size: 28,
                                    ),
                                    tooltip: 'Mark Absent',
                                    onPressed: () {
                                      ref.read(sessionProvider.notifier).resolveCandidateState(
                                            candidate.studentId,
                                            AttendanceStatus.absentConfirmed,
                                          );
                                    },
                                  ),
                                ],
                              ),
                            ],
                          ),
                        );
                      },
                    ),
            ),

            // Bottom Confirmation Bar
            Container(
              padding: const EdgeInsets.all(16),
              decoration: const BoxDecoration(
                color: AppTheme.surfaceLight,
                border: Border(top: BorderSide(color: AppTheme.borderLight)),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      child: const Text('Back to Proposal'),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton.icon(
                      icon: const Icon(Icons.arrow_forward),
                      label: const Text('Proceed to Commit'),
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
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
