import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../data/mock/mock_teacher_data.dart';
import '../../logic/session_provider.dart';
import 'session_setup_screen.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final offeringsAsync = ref.watch(assignedOfferingsProvider);
    final offerings = offeringsAsync.asData?.value ?? MockTeacherData.sampleOfferings;

    return Scaffold(
      appBar: AppBar(
        title: const Text('FRS Attendance — Faculty Portal'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Offerings',
            onPressed: () => ref.refresh(assignedOfferingsProvider),
          ),
          IconButton(
            icon: const Icon(Icons.account_circle_outlined),
            tooltip: 'Faculty Profile',
            onPressed: () {},
          ),
        ],
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async => ref.refresh(assignedOfferingsProvider),
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Faculty Header Banner
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: AppTheme.surfaceLight,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppTheme.borderLight),
                  ),
                  child: Row(
                    children: [
                      CircleAvatar(
                        radius: 28,
                        backgroundColor: AppTheme.primaryNavy.withValues(alpha: 0.1),
                        child: const Icon(Icons.school, size: 32, color: AppTheme.primaryNavy),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              MockTeacherData.facultyName,
                              style: theme.textTheme.titleLarge,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Department of Computer Science & Engineering\nKUCET Campus',
                              style: theme.textTheme.bodyMedium,
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 28),

                // Section Title
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Assigned Subject Offerings',
                      style: theme.textTheme.headlineMedium?.copyWith(fontSize: 20),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppTheme.secondaryBlue.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        '${offerings.length} Active',
                        style: const TextStyle(
                          color: AppTheme.secondaryBlue,
                          fontWeight: FontWeight.w600,
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'Select an assigned offering or authorized joint group to initiate attendance.',
                  style: theme.textTheme.bodyMedium,
                ),

                const SizedBox(height: 16),

                // Offerings List
                ...offerings.map((offering) {
                  final isJoint = offering['isJointClass'] as bool? ?? false;
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 16.0),
                    child: Card(
                      child: Padding(
                        padding: const EdgeInsets.all(18.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: AppTheme.primaryNavy.withValues(alpha: 0.08),
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: Text(
                                    offering['subjectCode'] as String? ?? 'SUB',
                                    style: const TextStyle(
                                      fontWeight: FontWeight.bold,
                                      fontSize: 12,
                                      color: AppTheme.primaryNavy,
                                    ),
                                  ),
                                ),
                                const Spacer(),
                                if (isJoint)
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: AppTheme.accentGold.withValues(alpha: 0.15),
                                      borderRadius: BorderRadius.circular(6),
                                    ),
                                    child: const Text(
                                      'Approved Joint Union',
                                      style: TextStyle(
                                        fontWeight: FontWeight.bold,
                                        fontSize: 11,
                                        color: AppTheme.accentGold,
                                      ),
                                    ),
                                  ),
                              ],
                            ),
                            const SizedBox(height: 10),
                            Text(
                              offering['subjectName'] as String? ?? 'Subject Offering',
                              style: theme.textTheme.titleLarge?.copyWith(fontSize: 17),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              offering['cohort'] as String? ?? 'Active Cohort',
                              style: theme.textTheme.bodyMedium?.copyWith(color: AppTheme.textMutedLight),
                            ),
                            const SizedBox(height: 16),
                            const Divider(height: 1),
                            const SizedBox(height: 14),
                            Row(
                              children: [
                                const Icon(Icons.people_outline, size: 18, color: AppTheme.textMutedLight),
                                const SizedBox(width: 6),
                                Text(
                                  '${offering['enrolledCount'] ?? 42} Enrolled Students',
                                  style: theme.textTheme.bodyMedium,
                                ),
                                const Spacer(),
                                ElevatedButton.icon(
                                  icon: const Icon(Icons.camera_alt_outlined, size: 18),
                                  label: const Text('Start Session'),
                                  onPressed: () {
                                    ref.read(sessionProvider.notifier).selectOffering(offering);
                                    Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                        builder: (_) => const SessionSetupScreen(),
                                      ),
                                    );
                                  },
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                  );
                }),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

