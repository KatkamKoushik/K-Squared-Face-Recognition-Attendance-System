import 'package:flutter/material.dart';
import '../../core/storage/class_pack.dart';
import '../../core/storage/class_pack_manager.dart';
import '../../core/theme/app_theme.dart';

class ClassPackScreen extends StatefulWidget {
  const ClassPackScreen({super.key});

  @override
  State<ClassPackScreen> createState() => _ClassPackScreenState();
}

class _ClassPackScreenState extends State<ClassPackScreen> {
  final ClassPackManager _manager = ClassPackManager();
  String? _downloadingPackId;
  double _downloadProgress = 0.0;

  @override
  void initState() {
    super.initState();
    _manager.addListener(_onChanged);
  }

  @override
  void dispose() {
    _manager.removeListener(_onChanged);
    super.dispose();
  }

  void _onChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _handleDownload(ClassDataPack pack) async {
    setState(() {
      _downloadingPackId = pack.id;
      _downloadProgress = 0.0;
    });

    await _manager.downloadClassPack(
      pack.id,
      onProgress: (p) {
        if (mounted) setState(() => _downloadProgress = p);
      },
    );

    if (mounted) {
      setState(() {
        _downloadingPackId = null;
        _downloadProgress = 0.0;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Class pack "${pack.title}" downloaded for offline attendance.'),
          backgroundColor: AppTheme.statusMatched,
        ),
      );
    }
  }

  Future<void> _handleRemove(ClassDataPack pack) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Remove Offline Class Pack'),
        content: Text(
          'Remove cached biometric templates for "${pack.title}"? You will need internet to download it again.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.errorRed, foregroundColor: Colors.white),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Remove'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await _manager.removeClassPack(pack.id);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Class pack "${pack.title}" removed from offline storage.'),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Class Database Packs', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            Text(
              'Authorized Offline Student Biometrics',
              style: TextStyle(fontSize: 11, color: Colors.white70),
            ),
          ],
        ),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            // Informational Overview Banner
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.primaryNavy.withValues(alpha: 0.05),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.primaryNavy.withValues(alpha: 0.2)),
              ),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 22,
                    backgroundColor: AppTheme.primaryNavy,
                    child: const Icon(Icons.cloud_download_outlined, color: Colors.white, size: 24),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Authorized Class Packs',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppTheme.primaryNavy),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          'Download approved student rosters and face embeddings to conduct attendance without laptop or internet. Secured with 14-day lease encryption.',
                          style: theme.textTheme.bodySmall?.copyWith(color: AppTheme.textMutedLight, height: 1.3),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            Row(
              children: [
                Text(
                  'Assigned Class Databases',
                  style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.secondaryBlue.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${_manager.downloadedCount} Ready Offline',
                    style: const TextStyle(
                      color: AppTheme.secondaryBlue,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Class Pack Cards
            ..._manager.packs.map((pack) {
              final isDownloading = _downloadingPackId == pack.id;

              return Container(
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: AppTheme.surfaceLight,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: pack.isDownloaded ? AppTheme.statusMatched : AppTheme.borderLight,
                    width: pack.isDownloaded ? 1.5 : 1.0,
                  ),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  pack.title,
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  pack.subtitle,
                                  style: const TextStyle(fontSize: 13, color: AppTheme.textMutedLight),
                                ),
                              ],
                            ),
                          ),
                          if (pack.isDownloaded)
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: AppTheme.statusMatched.withValues(alpha: 0.12),
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(color: AppTheme.statusMatched),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: const [
                                  Icon(Icons.check_circle_rounded, size: 14, color: AppTheme.statusMatched),
                                  SizedBox(width: 4),
                                  Text(
                                    'OFFLINE READY',
                                    style: TextStyle(
                                      fontSize: 10,
                                      fontWeight: FontWeight.bold,
                                      color: AppTheme.statusMatched,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          const Icon(Icons.people_outline, size: 16, color: AppTheme.textMutedLight),
                          const SizedBox(width: 4),
                          Text(
                            '${pack.enrolledStudentCount} Students (${pack.embeddingsCount} Templates)',
                            style: const TextStyle(fontSize: 12, color: AppTheme.textMutedLight),
                          ),
                          const SizedBox(width: 14),
                          const Icon(Icons.folder_outlined, size: 16, color: AppTheme.textMutedLight),
                          const SizedBox(width: 4),
                          Text(
                            pack.formattedSize,
                            style: const TextStyle(fontSize: 12, color: AppTheme.textMutedLight),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      const Divider(height: 1),
                      const SizedBox(height: 12),

                      if (isDownloading) ...[
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text(
                                  'Downloading roster & embeddings...',
                                  style: TextStyle(fontSize: 12, color: AppTheme.primaryNavy),
                                ),
                                Text(
                                  '${(_downloadProgress * 100).toInt()}%',
                                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                                ),
                              ],
                            ),
                            const SizedBox(height: 6),
                            LinearProgressIndicator(
                              value: _downloadProgress,
                              backgroundColor: Colors.grey.shade200,
                              color: AppTheme.primaryNavy,
                            ),
                            const SizedBox(height: 8),
                          ],
                        ),
                      ],

                      Row(
                        children: [
                          if (!pack.isDownloaded && !isDownloading)
                            ElevatedButton.icon(
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppTheme.primaryNavy,
                                foregroundColor: Colors.white,
                              ),
                              icon: const Icon(Icons.download_rounded, size: 16),
                              label: const Text('Download Class Pack'),
                              onPressed: () => _handleDownload(pack),
                            ),
                          if (pack.isDownloaded) ...[
                            Text(
                              'Valid for 13 more days (Lease Active)',
                              style: TextStyle(fontSize: 11, color: Colors.green.shade800, fontWeight: FontWeight.w500),
                            ),
                            const Spacer(),
                            OutlinedButton.icon(
                              style: OutlinedButton.styleFrom(
                                foregroundColor: AppTheme.errorRed,
                                side: const BorderSide(color: AppTheme.errorRed),
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              ),
                              icon: const Icon(Icons.delete_outline_rounded, size: 14),
                              label: const Text('Remove', style: TextStyle(fontSize: 12)),
                              onPressed: () => _handleRemove(pack),
                            ),
                          ],
                        ],
                      ),
                    ],
                  ),
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}
