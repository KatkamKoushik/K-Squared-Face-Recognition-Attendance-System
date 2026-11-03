import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../logic/session_provider.dart';
import 'capture_gallery_screen.dart';

class SessionSetupScreen extends ConsumerWidget {
  const SessionSetupScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final sessionState = ref.watch(sessionProvider);
    final offering = sessionState.selectedOffering;

    if (offering == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Session Setup')),
        body: const Center(child: Text('No offering selected.')),
      );
    }

    final conductedUnits = sessionState.conductedUnitsCount;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Confirm Session Context'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Context Card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(18.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.school_outlined, size: 20, color: AppTheme.primaryNavy),
                          const SizedBox(width: 8),
                          Text(
                            'Academic Context',
                            style: theme.textTheme.labelLarge?.copyWith(color: AppTheme.primaryNavy),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Text(
                        (offering['subjectName'] ?? offering['name'] ?? 'Classroom Session') as String,
                        style: theme.textTheme.titleLarge,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${offering['subjectCode'] ?? offering['code'] ?? 'OFFERING'} • ${offering['cohort'] ?? offering['section'] ?? 'Primary Section'}',
                        style: theme.textTheme.bodyMedium,
                      ),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 8,
                        runSpacing: 6,
                        children: [
                          _ContextPill(label: 'Term: ${offering['term'] ?? 'Current Term'}'),
                          _ContextPill(label: '${offering['enrolledCount'] ?? 66} Roster Size'),
                        ],
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 24),

              // Unit Selector Section
              Text(
                'Instructional Units Conducted',
                style: theme.textTheme.headlineMedium?.copyWith(fontSize: 20),
              ),
              const SizedBox(height: 8),
              Text(
                'Attendance is recorded per student per conducted unit. Select how many instructional periods were conducted during this classroom session.',
                style: theme.textTheme.bodyMedium,
              ),

              const SizedBox(height: 16),

              // 1 to 4 Units Selection
              Row(
                children: [1, 2, 3, 4].map((unitCount) {
                  final isSelected = conductedUnits == unitCount;
                  return Expanded(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 4.0),
                      child: InkWell(
                        onTap: () {
                          ref.read(sessionProvider.notifier).setConductedUnits(unitCount);
                        },
                        borderRadius: BorderRadius.circular(10),
                        child: Container(
                          height: 72,
                          decoration: BoxDecoration(
                            color: isSelected ? AppTheme.primaryNavy : AppTheme.surfaceLight,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(
                              color: isSelected ? AppTheme.primaryNavy : AppTheme.borderLight,
                              width: isSelected ? 2 : 1,
                            ),
                          ),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(
                                '$unitCount',
                                style: TextStyle(
                                  fontSize: 22,
                                  fontWeight: FontWeight.bold,
                                  color: isSelected ? Colors.white : AppTheme.textMainLight,
                                ),
                              ),
                              Text(
                                unitCount == 1 ? 'Unit' : 'Units',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w500,
                                  color: isSelected ? Colors.white70 : AppTheme.textMutedLight,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),

              const SizedBox(height: 20),

              // Invariant Information Alert
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppTheme.secondaryBlue.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppTheme.secondaryBlue.withValues(alpha: 0.3)),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.info_outline, size: 20, color: AppTheme.secondaryBlue),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Each student present will be credited with $conductedUnits out of $conductedUnits eligible units upon faculty commit.',
                        style: const TextStyle(
                          fontSize: 13,
                          color: AppTheme.primaryNavy,
                          height: 1.4,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 40),

              // Action button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  icon: const Icon(Icons.photo_camera_rounded),
                  label: Text('Proceed to Camera ($conductedUnits ${conductedUnits == 1 ? 'Unit' : 'Units'})'),
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => const CaptureGalleryScreen(),
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ContextPill extends StatelessWidget {
  final String label;

  const _ContextPill({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: AppTheme.surfaceVariantLight,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        label,
        style: const TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w500,
          color: AppTheme.textMutedLight,
        ),
      ),
    );
  }
}

