import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../data/kucet_faculty_directory.dart';
import '../../logic/auth_provider.dart';
import '../../logic/session_provider.dart';
import 'session_setup_screen.dart';
import 'student_enrollment_screen.dart';
import 'model_manager_screen.dart';
import 'class_pack_screen.dart';
import 'developer_student_manager_screen.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final offeringsAsync = ref.watch(assignedOfferingsProvider);
    final journal = ref.watch(offlineSyncJournalProvider);
    final auth = ref.watch(authProvider);
    final activeCoord = auth.email != null ? KucetFacultyDirectory.findByEmail(auth.email!) : null;
    final facultyDisplayName = activeCoord?.name ?? auth.email ?? 'Faculty Member';
    final facultyDisplayDesignation = activeCoord != null
        ? '${activeCoord.designation} & ${activeCoord.category}'
        : 'Faculty & Academic Instructor';
    final facultyDisplayDept = activeCoord != null
        ? (activeCoord.department.startsWith('Department')
            ? activeCoord.department
            : 'Department of ${activeCoord.department}')
        : (auth.role != null ? '${auth.role} Access' : 'Department Faculty');

    return Scaffold(
      appBar: AppBar(
        title: const Text('KUCET Faculty Portal'),
        actions: [
          IconButton(
            icon: const Icon(Icons.admin_panel_settings_rounded, color: AppTheme.accentGold),
            tooltip: 'Developer Database Control (koushikkatkam@gmail.com)',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => const DeveloperStudentManagerScreen(),
                ),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.person_add_alt_1_rounded),
            tooltip: 'Direct Student Enrollment',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => const StudentEnrollmentScreen(),
                ),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Offerings',
            onPressed: () => ref.refresh(assignedOfferingsProvider),
          ),
          IconButton(
            icon: const Icon(Icons.account_circle_outlined),
            tooltip: 'Faculty Profile',
            onPressed: () {
              final auth = ref.read(authProvider);
              showDialog(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text('Faculty Session'),
                  content: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        auth.email ?? 'Faculty Member',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Role: ${auth.role ?? "FACULTY"}',
                        style: TextStyle(color: Colors.grey.shade700, fontSize: 13),
                      ),
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: auth.isOfflineDemo ? Colors.amber.shade50 : Colors.green.shade50,
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(
                            color: auth.isOfflineDemo ? Colors.amber.shade300 : Colors.green.shade300,
                          ),
                        ),
                        child: Text(
                          auth.isOfflineDemo ? 'Offline Preview Session' : 'Authoritative Control Plane Active',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: auth.isOfflineDemo ? Colors.amber.shade900 : Colors.green.shade900,
                          ),
                        ),
                      ),
                    ],
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(ctx),
                      child: const Text('Close'),
                    ),
                    TextButton(
                      onPressed: () {
                        Navigator.pop(ctx);
                        ref.read(authProvider.notifier).logout();
                      },
                      style: TextButton.styleFrom(foregroundColor: AppTheme.errorRed),
                      child: const Text('Sign Out'),
                    ),
                  ],
                ),
              );
            },
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
                              facultyDisplayName,
                              style: theme.textTheme.titleLarge,
                            ),
                            const SizedBox(height: 2),
                            Text(
                              facultyDisplayDesignation,
                              style: theme.textTheme.bodyMedium?.copyWith(
                                color: AppTheme.primaryNavy,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              '$facultyDisplayDept\nKU College of Engineering & Technology (KUCET)',
                              style: theme.textTheme.bodyMedium,
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 16),

                // Developer Database Control Card (koushikkatkam@gmail.com)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppTheme.accentGold.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppTheme.accentGold.withValues(alpha: 0.4), width: 1.5),
                  ),
                  child: Row(
                    children: [
                      CircleAvatar(
                        radius: 24,
                        backgroundColor: AppTheme.primaryNavy,
                        child: const Icon(Icons.admin_panel_settings_rounded, color: AppTheme.accentGold, size: 26),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                const Text(
                                  'Developer Database Control',
                                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14.5, color: AppTheme.primaryNavy),
                                ),
                                const SizedBox(width: 6),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                                  decoration: BoxDecoration(
                                    color: AppTheme.primaryNavy,
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: const Text(
                                    'ROOT',
                                    style: TextStyle(color: AppTheme.accentGold, fontSize: 9, fontWeight: FontWeight.bold),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 3),
                            const Text(
                              'koushikkatkam@gmail.com • Rewrite details, replace photos in Cloudinary, purge biometrics, or delete records.',
                              style: TextStyle(fontSize: 11.5, color: AppTheme.textMainLight),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 8),
                      ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.primaryNavy,
                          foregroundColor: AppTheme.accentGold,
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        ),
                        icon: const Icon(Icons.tune_rounded, size: 16),
                        label: const Text('Manage', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const DeveloperStudentManagerScreen(),
                            ),
                          );
                        },
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 12),

                // Student Direct Enrollment Quick Action Card
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppTheme.surfaceLight,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppTheme.borderLight),
                  ),
                  child: Row(
                    children: [
                      CircleAvatar(
                        radius: 24,
                        backgroundColor: AppTheme.secondaryBlue.withValues(alpha: 0.1),
                        child: const Icon(Icons.person_add_rounded, color: AppTheme.secondaryBlue, size: 26),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Student Direct Enrollment',
                              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppTheme.textMainLight),
                            ),
                            const SizedBox(height: 2),
                            const Text(
                              'Capture & enroll directly to Cloudinary with Option 1, Option 3 & Fine-Tuned AI.',
                              style: TextStyle(fontSize: 12, color: AppTheme.textMutedLight),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 8),
                      ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.primaryNavy,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        ),
                        icon: const Icon(Icons.add, size: 16),
                        label: const Text('Enroll', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const StudentEnrollmentScreen(),
                            ),
                          );
                        },
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 12),

                // AI Model Manager & Class Packs Quick Row
                Row(
                  children: [
                    Expanded(
                      child: InkWell(
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const ModelManagerScreen(),
                            ),
                          );
                        },
                        borderRadius: BorderRadius.circular(12),
                        child: Container(
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: AppTheme.surfaceLight,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: AppTheme.borderLight),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  CircleAvatar(
                                    radius: 16,
                                    backgroundColor: AppTheme.primaryNavy.withValues(alpha: 0.1),
                                    child: const Icon(Icons.memory_rounded, color: AppTheme.primaryNavy, size: 18),
                                  ),
                                  const Spacer(),
                                  const Icon(Icons.arrow_forward_ios, size: 12, color: AppTheme.textMutedLight),
                                ],
                              ),
                              const SizedBox(height: 10),
                              const Text(
                                'AI Model Manager',
                                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                              ),
                              const SizedBox(height: 2),
                              const Text(
                                'Packs & Auto-Cascade',
                                style: TextStyle(fontSize: 11, color: AppTheme.textMutedLight),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: InkWell(
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const ClassPackScreen(),
                            ),
                          );
                        },
                        borderRadius: BorderRadius.circular(12),
                        child: Container(
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: AppTheme.surfaceLight,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: AppTheme.borderLight),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  CircleAvatar(
                                    radius: 16,
                                    backgroundColor: AppTheme.statusMatched.withValues(alpha: 0.1),
                                    child: const Icon(Icons.folder_shared_outlined, color: AppTheme.statusMatched, size: 18),
                                  ),
                                  const Spacer(),
                                  const Icon(Icons.arrow_forward_ios, size: 12, color: AppTheme.textMutedLight),
                                ],
                              ),
                              const SizedBox(height: 10),
                              const Text(
                                'Class Data Packs',
                                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                              ),
                              const SizedBox(height: 2),
                              const Text(
                                'Authorized Offline Rosters',
                                style: TextStyle(fontSize: 11, color: AppTheme.textMutedLight),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ],
                ),

                // Offline Sync Pending Banner
                if (journal.pendingCount > 0) ...[
                  const SizedBox(height: 16),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: Colors.amber.shade50,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: Colors.amber.shade300),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.cloud_off_rounded, color: Colors.amber.shade900, size: 24),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '${journal.pendingCount} Pending Offline Mutation(s)',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: Colors.amber.shade900,
                                  fontSize: 13,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                'Attendance draft waiting to synchronize with control plane.',
                                style: TextStyle(
                                  color: Colors.amber.shade800,
                                  fontSize: 11,
                                ),
                              ),
                            ],
                          ),
                        ),
                        TextButton(
                          onPressed: () async {
                            final count = await ref.read(sessionProvider.notifier).syncOfflineJournal();
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text(
                                    count > 0
                                        ? 'Synchronized $count mutation(s) with control plane.'
                                        : 'Server unreachable. Changes remain queued in journal.',
                                  ),
                                ),
                              );
                            }
                          },
                          child: const Text('Sync Now', style: TextStyle(fontWeight: FontWeight.bold)),
                        ),
                      ],
                    ),
                  ),
                ],

                const SizedBox(height: 28),

                // Section Title
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        'Assigned Subject Offerings',
                        style: theme.textTheme.headlineMedium?.copyWith(fontSize: 18),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppTheme.secondaryBlue.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        '${offeringsAsync.asData?.value.length ?? 0} Active',
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

                // Live Offerings List from Server
                offeringsAsync.when(
                  loading: () => const Center(
                    child: Padding(
                      padding: EdgeInsets.symmetric(vertical: 32.0),
                      child: Column(
                        children: [
                          CircularProgressIndicator(),
                          SizedBox(height: 12),
                          Text('Loading assigned subject offerings from server...'),
                        ],
                      ),
                    ),
                  ),
                  error: (err, stack) => Card(
                    color: AppTheme.errorRed.withValues(alpha: 0.05),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                      side: BorderSide(color: AppTheme.errorRed.withValues(alpha: 0.3)),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: const [
                              Icon(Icons.cloud_off, color: AppTheme.errorRed, size: 20),
                              SizedBox(width: 8),
                              Text(
                                'Unable to Load Live Offerings',
                                style: TextStyle(fontWeight: FontWeight.bold, color: AppTheme.errorRed),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Text(
                            err.toString().replaceFirst('Exception: ', ''),
                            style: const TextStyle(fontSize: 12, color: AppTheme.textMutedLight),
                          ),
                          const SizedBox(height: 12),
                          ElevatedButton.icon(
                            icon: const Icon(Icons.refresh, size: 16),
                            label: const Text('Retry Fetching Offerings'),
                            onPressed: () => ref.refresh(assignedOfferingsProvider),
                          ),
                        ],
                      ),
                    ),
                  ),
                  data: (offerings) {
                    if (offerings.isEmpty) {
                      return Card(
                        child: Padding(
                          padding: const EdgeInsets.all(24.0),
                          child: Column(
                            children: [
                              const Icon(Icons.school_outlined, size: 36, color: AppTheme.textMutedLight),
                              const SizedBox(height: 12),
                              const Text(
                                'No Assigned Offerings Found',
                                style: TextStyle(fontWeight: FontWeight.bold),
                              ),
                              const SizedBox(height: 4),
                              const Text(
                                'Verify faculty assignment on server or run demo seeder.',
                                style: TextStyle(fontSize: 12, color: AppTheme.textMutedLight),
                              ),
                              const SizedBox(height: 12),
                              OutlinedButton.icon(
                                icon: const Icon(Icons.refresh, size: 16),
                                label: const Text('Refresh'),
                                onPressed: () => ref.refresh(assignedOfferingsProvider),
                              ),
                            ],
                          ),
                        ),
                      );
                    }

                    return Column(
                      children: offerings.map((offering) {
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
                                  Wrap(
                                    alignment: WrapAlignment.spaceBetween,
                                    crossAxisAlignment: WrapCrossAlignment.center,
                                    spacing: 8,
                                    runSpacing: 10,
                                    children: [
                                      Row(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          const Icon(Icons.people_outline, size: 18, color: AppTheme.textMutedLight),
                                          const SizedBox(width: 6),
                                          Text(
                                            '${offering['enrolledCount'] ?? 42} Enrolled Students',
                                            style: theme.textTheme.bodyMedium,
                                          ),
                                        ],
                                      ),
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
                      }).toList(),
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

