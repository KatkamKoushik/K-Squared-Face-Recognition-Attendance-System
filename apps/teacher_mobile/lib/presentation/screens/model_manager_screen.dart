import 'package:flutter/material.dart';
import '../../core/ai/model_pack.dart';
import '../../core/ai/model_pack_manager.dart';
import '../../core/theme/app_theme.dart';

class ModelManagerScreen extends StatefulWidget {
  const ModelManagerScreen({super.key});

  @override
  State<ModelManagerScreen> createState() => _ModelManagerScreenState();
}

class _ModelManagerScreenState extends State<ModelManagerScreen> {
  final ModelPackManager _manager = ModelPackManager();
  String? _downloadingPackId;
  double _downloadProgress = 0.0;

  @override
  void initState() {
    super.initState();
    _manager.addListener(_onManagerChanged);
  }

  @override
  void dispose() {
    _manager.removeListener(_onManagerChanged);
    super.dispose();
  }

  void _onManagerChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _handleDownload(ModelPack pack) async {
    setState(() {
      _downloadingPackId = pack.id;
      _downloadProgress = 0.0;
    });

    await _manager.installPack(
      pack.id,
      onProgress: (p) {
        if (mounted) {
          setState(() => _downloadProgress = p);
        }
      },
    );

    if (mounted) {
      setState(() {
        _downloadingPackId = null;
        _downloadProgress = 0.0;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Model pack "${pack.shortName}" installed successfully.'),
          backgroundColor: AppTheme.statusMatched,
        ),
      );
    }
  }

  Future<void> _handleSelect(ModelPack pack) async {
    try {
      await _manager.setActivePack(pack.id);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Active recognition pipeline switched to: ${pack.shortName}'),
            backgroundColor: AppTheme.primaryNavy,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e.toString().replaceFirst('Exception: ', '')),
            backgroundColor: AppTheme.errorRed,
          ),
        );
      }
    }
  }

  Future<void> _handleDelete(ModelPack pack) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete Model Pack'),
        content: Text(
          'Remove "${pack.name}" from local device storage? You can re-download it anytime.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.errorRed, foregroundColor: Colors.white),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        await _manager.uninstallPack(pack.id);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Model pack "${pack.shortName}" removed from device.'),
            ),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(e.toString().replaceFirst('Exception: ', '')),
              backgroundColor: AppTheme.errorRed,
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final activePack = _manager.activePack;

    return Scaffold(
      appBar: AppBar(
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('AI Model Manager', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            Text(
              'Downloadable Vision Inference Packs',
              style: TextStyle(fontSize: 11, color: Colors.white70),
            ),
          ],
        ),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            // Active Pipeline Summary Card
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: AppTheme.primaryNavy,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: const Text(
                          'ACTIVE PIPELINE',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 0.8,
                          ),
                        ),
                      ),
                      const Spacer(),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppTheme.statusMatched,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          activePack.badge,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    activePack.name,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 17,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Embedding Dimension: ${activePack.dimension}-D | Target Threshold: ${activePack.defaultThreshold.toStringAsFixed(3)}',
                    style: const TextStyle(color: Colors.white70, fontSize: 12),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Namespace: ${activePack.embeddingNamespace}',
                    style: const TextStyle(color: Colors.white60, fontSize: 11, fontFamily: 'monospace'),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 18),

            // Intelligent Auto-Cascading Switch
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.surfaceLight,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.borderLight),
              ),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 20,
                    backgroundColor: AppTheme.accentGold.withValues(alpha: 0.15),
                    child: const Icon(Icons.auto_awesome, color: AppTheme.accentGold, size: 20),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Intelligent Auto Mode',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          'Option 1 runs first for broad speed. Ambiguous or distant faces automatically escalate to Option 3 for high-precision resolution.',
                          style: theme.textTheme.bodySmall?.copyWith(color: AppTheme.textMutedLight, height: 1.3),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  Switch(
                    value: _manager.isAutoModeEnabled,
                    activeThumbColor: AppTheme.primaryNavy,
                    onChanged: (val) => _manager.toggleAutoMode(val),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 24),

            Row(
              children: [
                Text(
                  'Available Model Packs',
                  style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                ),
                const Spacer(),
                Text(
                  '${_manager.packs.where((p) => p.isInstalled).length} / ${_manager.packs.length} Installed',
                  style: const TextStyle(fontSize: 12, color: AppTheme.textMutedLight, fontWeight: FontWeight.w600),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Model Pack Cards
            ..._manager.packs.map((pack) {
              final isDownloading = _downloadingPackId == pack.id;
              final isCurrent = pack.isActive;

              return Container(
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: AppTheme.surfaceLight,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: isCurrent ? AppTheme.primaryNavy : AppTheme.borderLight,
                    width: isCurrent ? 1.5 : 1.0,
                  ),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                      decoration: BoxDecoration(
                                        color: AppTheme.primaryNavy.withValues(alpha: 0.08),
                                        borderRadius: BorderRadius.circular(6),
                                      ),
                                      child: Text(
                                        pack.badge,
                                        style: const TextStyle(
                                          fontSize: 11,
                                          fontWeight: FontWeight.bold,
                                          color: AppTheme.primaryNavy,
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 8),
                                    Text(
                                      pack.formattedSize,
                                      style: const TextStyle(
                                        fontSize: 12,
                                        color: AppTheme.textMutedLight,
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  pack.name,
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                                ),
                              ],
                            ),
                          ),
                          if (isCurrent)
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: AppTheme.statusMatched.withValues(alpha: 0.12),
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(color: AppTheme.statusMatched),
                              ),
                              child: const Text(
                                'ACTIVE',
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.bold,
                                  color: AppTheme.statusMatched,
                                ),
                              ),
                            ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        pack.description,
                        style: const TextStyle(fontSize: 12, color: AppTheme.textMutedLight, height: 1.35),
                      ),
                      const SizedBox(height: 12),
                      const Divider(height: 1),
                      const SizedBox(height: 12),

                      // Download Progress Bar
                      if (isDownloading) ...[
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text(
                                  'Downloading model weights...',
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

                      // Actions Row
                      Row(
                        children: [
                          if (!pack.isInstalled && !isDownloading)
                            ElevatedButton.icon(
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppTheme.primaryNavy,
                                foregroundColor: Colors.white,
                              ),
                              icon: const Icon(Icons.download_rounded, size: 16),
                              label: const Text('Download Pack'),
                              onPressed: () => _handleDownload(pack),
                            ),
                          if (pack.isInstalled && !isCurrent) ...[
                            ElevatedButton.icon(
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppTheme.primaryNavy,
                                foregroundColor: Colors.white,
                              ),
                              icon: const Icon(Icons.check_rounded, size: 16),
                              label: const Text('Select Pipeline'),
                              onPressed: () => _handleSelect(pack),
                            ),
                            if (!pack.isDefault) ...[
                              const Spacer(),
                              IconButton(
                                icon: const Icon(Icons.delete_outline_rounded, color: AppTheme.errorRed, size: 20),
                                tooltip: 'Delete Pack from Device',
                                onPressed: () => _handleDelete(pack),
                              ),
                            ],
                          ],
                          if (isCurrent)
                            const Text(
                              'Loaded in RAM & Ready for Attendance',
                              style: TextStyle(fontSize: 12, color: AppTheme.statusMatched, fontWeight: FontWeight.w600),
                            ),
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
