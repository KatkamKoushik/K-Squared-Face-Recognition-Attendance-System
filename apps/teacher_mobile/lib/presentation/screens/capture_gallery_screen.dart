import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';
import '../../data/models/domain_contracts.dart';
import '../../core/theme/app_theme.dart';
import '../../logic/session_provider.dart';
import 'proposal_review_screen.dart';

class CaptureGalleryScreen extends ConsumerStatefulWidget {
  const CaptureGalleryScreen({super.key});

  @override
  ConsumerState<CaptureGalleryScreen> createState() => _CaptureGalleryScreenState();
}

class _CaptureGalleryScreenState extends ConsumerState<CaptureGalleryScreen> {
  final _uuid = const Uuid();

  void _simulateCapture() {
    final frameId = 'FRM-${_uuid.v4().substring(0, 8).toUpperCase()}';
    final timestamp = DateTime.now().toIso8601String();
    final bytes = utf8.encode('$frameId-$timestamp-${DateTime.now().microsecondsSinceEpoch}');
    final hash = sha256.convert(bytes).toString();

    ref.read(sessionProvider.notifier).addCapturedFrame(
      frameId: frameId,
      hash: hash,
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final sessionState = ref.watch(sessionProvider);
    final frames = sessionState.capturedFrames;
    final isProcessing = sessionState.state == SessionState.processing;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Classroom Photo Capture'),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Framing Guidance Box
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppTheme.surfaceLight,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: AppTheme.borderLight),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: AppTheme.secondaryBlue.withValues(alpha: 0.1),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.wb_sunny_outlined, color: AppTheme.secondaryBlue, size: 22),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Framing & Coverage Guidance', style: theme.textTheme.titleLarge?.copyWith(fontSize: 15)),
                          const SizedBox(height: 4),
                          Text(
                            'Capture 2–4 wide photos. Pan across left, center, and back rows in landscape orientation.',
                            style: theme.textTheme.bodyMedium,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              // Captured Frames Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Captured Frames (${frames.length})',
                    style: theme.textTheme.headlineMedium?.copyWith(fontSize: 18),
                  ),
                  TextButton.icon(
                    icon: const Icon(Icons.add_a_photo, size: 18),
                    label: const Text('Add Photo'),
                    onPressed: isProcessing ? null : _simulateCapture,
                  ),
                ],
              ),

              const SizedBox(height: 12),

              // Frames List / Empty state
              Expanded(
                child: frames.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.camera_alt_outlined, size: 64, color: AppTheme.borderLight),
                            const SizedBox(height: 16),
                            Text('No photos captured yet', style: theme.textTheme.titleLarge),
                            const SizedBox(height: 8),
                            Text(
                              'Tap the button below to capture classroom views.',
                              style: theme.textTheme.bodyMedium,
                            ),
                            const SizedBox(height: 20),
                            ElevatedButton.icon(
                              icon: const Icon(Icons.camera_rounded),
                              label: const Text('Capture First Photo'),
                              onPressed: _simulateCapture,
                            ),
                          ],
                        ),
                      )
                    : ListView.builder(
                        itemCount: frames.length,
                        itemBuilder: (context, index) {
                          final frame = frames[index];
                          return Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            child: Padding(
                              padding: const EdgeInsets.all(14.0),
                              child: Row(
                                children: [
                                  Container(
                                    width: 56,
                                    height: 56,
                                    decoration: BoxDecoration(
                                      color: AppTheme.primaryNavy.withValues(alpha: 0.08),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Center(
                                      child: Text(
                                        '#${index + 1}',
                                        style: const TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: 18,
                                          color: AppTheme.primaryNavy,
                                        ),
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 14),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          frame['frameId'] ?? 'FRAME',
                                          style: const TextStyle(
                                            fontWeight: FontWeight.bold,
                                            fontSize: 14,
                                          ),
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          'SHA-256: ${frame['hash']?.substring(0, 16)}...',
                                          style: const TextStyle(
                                            fontFamily: 'monospace',
                                            fontSize: 11,
                                            color: AppTheme.textMutedLight,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  IconButton(
                                    icon: const Icon(Icons.delete_outline, color: AppTheme.errorRed),
                                    onPressed: isProcessing
                                        ? null
                                        : () {
                                            ref.read(sessionProvider.notifier).removeFrame(index);
                                          },
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
              ),

              // Processing indicator or Submit button
              if (isProcessing) ...[
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppTheme.surfaceLight,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppTheme.borderLight),
                  ),
                  child: Column(
                    children: [
                      const LinearProgressIndicator(color: AppTheme.secondaryBlue),
                      const SizedBox(height: 12),
                      Text(
                        'Uploading frames & vision worker matching roster...',
                        style: theme.textTheme.bodyMedium?.copyWith(color: AppTheme.primaryNavy),
                      ),
                    ],
                  ),
                ),
              ] else ...[
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.analytics_outlined),
                    label: Text(frames.isEmpty ? 'Capture at Least 1 Photo' : 'Process ${frames.length} Photos'),
                    onPressed: frames.isEmpty
                        ? null
                        : () async {
                            await ref.read(sessionProvider.notifier).submitBatchForProcessing();
                            if (context.mounted) {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => const ProposalReviewScreen(),
                                ),
                              );
                            }
                          },
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

