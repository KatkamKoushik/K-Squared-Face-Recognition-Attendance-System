import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
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
  final _picker = ImagePicker();

  Future<void> _capturePhoto() async {
    try {
      final photo = await _picker.pickImage(
        source: ImageSource.camera,
        maxWidth: 3840,
        maxHeight: 2160,
        imageQuality: 92,
      );

      if (photo != null) {
        final bytes = await photo.readAsBytes();
        if (bytes.isEmpty) {
          throw Exception('Captured photo was empty (0 bytes). Check camera/storage permissions and retry.');
        }
        final hash = sha256.convert(bytes).toString();
        final frameId = 'FRM-${_uuid.v4().substring(0, 8).toUpperCase()}';

        ref.read(sessionProvider.notifier).addCapturedFrame(
          frameId: frameId,
          hash: hash,
          path: photo.path,
          bytes: bytes,
        );
        return;
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Camera/Picker failed: ${e.toString().replaceFirst('Exception: ', '')}'),
            backgroundColor: AppTheme.errorRed,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    }
  }

  Future<void> _pickGalleryPhotos() async {
    try {
      final photos = await _picker.pickMultiImage(
        maxWidth: 3840,
        maxHeight: 2160,
        imageQuality: 92,
      );

      if (photos.isNotEmpty) {
        for (final photo in photos) {
          final bytes = await photo.readAsBytes();
          if (bytes.isNotEmpty) {
            final hash = sha256.convert(bytes).toString();
            final frameId = 'FRM-${_uuid.v4().substring(0, 8).toUpperCase()}';
            ref.read(sessionProvider.notifier).addCapturedFrame(
              frameId: frameId,
              hash: hash,
              path: photo.path,
              bytes: bytes,
            );
          }
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Gallery picker failed: ${e.toString().replaceFirst('Exception: ', '')}'),
            backgroundColor: AppTheme.errorRed,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    }
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
                          Text(
                            'Classroom Capture Guidance',
                            style: theme.textTheme.bodyMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: AppTheme.primaryNavy,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            'Hold device horizontally in landscape. Capture 2-3 overlapping sweeps to ensure full row-by-row coverage of all students.',
                            style: theme.textTheme.bodySmall?.copyWith(color: AppTheme.textMutedLight),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Error banner if any
              if (sessionState.errorMessage != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppTheme.errorRed.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppTheme.errorRed.withValues(alpha: 0.4)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline, color: AppTheme.errorRed, size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          sessionState.errorMessage!,
                          style: const TextStyle(color: AppTheme.errorRed, fontSize: 13),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // Classroom Capture Actions: Camera Sweep & Multi-Photo Gallery Pick
              Row(
                children: [
                  Expanded(
                    child: FilledButton.icon(
                      icon: const Icon(Icons.camera_alt),
                      label: const Text('Take Photo'),
                      style: FilledButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        backgroundColor: AppTheme.primaryNavy,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      onPressed: isProcessing ? null : () => _capturePhoto(),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton.icon(
                      icon: const Icon(Icons.photo_library_outlined),
                      label: const Text('Pick Sweep Photos'),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        side: const BorderSide(color: AppTheme.primaryNavy),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      onPressed: isProcessing ? null : () => _pickGalleryPhotos(),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // Multi-Angle Sweep Coverage Telemetry Card
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: frames.isEmpty
                      ? AppTheme.surfaceLight
                      : (frames.length >= 2 ? AppTheme.statusMatched.withValues(alpha: 0.1) : AppTheme.secondaryBlue.withValues(alpha: 0.1)),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: frames.isEmpty
                        ? AppTheme.borderLight
                        : (frames.length >= 2 ? AppTheme.statusMatched.withValues(alpha: 0.3) : AppTheme.secondaryBlue.withValues(alpha: 0.3)),
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      frames.length >= 2 ? Icons.check_circle_outline : Icons.info_outline,
                      size: 18,
                      color: frames.isEmpty
                          ? AppTheme.textMutedLight
                          : (frames.length >= 2 ? AppTheme.statusMatched : AppTheme.secondaryBlue),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        frames.isEmpty
                            ? 'Classroom Sweep: Capture 2-3 overlapping angles for full row coverage'
                            : (frames.length == 1
                                ? 'Angle 1 captured. Tap Pick or Take Photo to add side sweeps.'
                                : 'Multi-angle sweep active (${frames.length} frames). Cross-frame identity fusion enabled.'),
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: frames.isEmpty
                              ? AppTheme.textMutedLight
                              : (frames.length >= 2 ? AppTheme.statusMatched : AppTheme.secondaryBlue),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Photo List Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Captured Photos (${frames.length})',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: AppTheme.primaryNavy,
                    ),
                  ),
                  if (frames.isNotEmpty)
                    Text(
                      'Ready for upload',
                      style: theme.textTheme.bodySmall?.copyWith(color: AppTheme.statusMatched),
                    ),
                ],
              ),
              const SizedBox(height: 10),

              // Frame List View
              Expanded(
                child: frames.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.photo_camera_back_outlined, size: 48, color: AppTheme.borderLight),
                            const SizedBox(height: 12),
                            Text(
                              'No photos captured yet.',
                              style: theme.textTheme.bodyMedium?.copyWith(color: AppTheme.textMutedLight),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Tap Take Photo or Pick Image to begin attendance sweep.',
                              style: theme.textTheme.bodySmall?.copyWith(color: AppTheme.textMutedLight),
                            ),
                          ],
                        ),
                      )
                    : ListView.separated(
                        itemCount: frames.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 10),
                        itemBuilder: (context, index) {
                          final frame = frames[index];
                          final hashStr = (frame['hash'] as String? ?? '');
                          return Card(
                            elevation: 0,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                              side: const BorderSide(color: AppTheme.borderLight),
                            ),
                            child: Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                              child: Row(
                                children: [
                                  Container(
                                    width: 44,
                                    height: 44,
                                    decoration: BoxDecoration(
                                      color: AppTheme.primaryNavy.withValues(alpha: 0.08),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Center(
                                      child: Text(
                                        '#${index + 1}',
                                        style: const TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: 16,
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
                                          frame['frameId']?.toString() ?? 'FRAME',
                                          style: const TextStyle(
                                            fontWeight: FontWeight.bold,
                                            fontSize: 14,
                                          ),
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          hashStr.length >= 16 ? 'SHA-256: ${hashStr.substring(0, 16)}...' : hashStr,
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
                        sessionState.uploadProgress ?? 'Processing photos with vision worker...',
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: AppTheme.primaryNavy,
                          fontWeight: FontWeight.w600,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              ] else ...[
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.analytics_outlined),
                    label: Text(frames.isEmpty ? 'Capture at Least 1 Photo' : 'Upload & Process ${frames.length} Photos'),
                    onPressed: frames.isEmpty
                        ? null
                        : () async {
                            try {
                              await ref.read(sessionProvider.notifier).submitBatchForProcessing();
                              if (context.mounted) {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => const ProposalReviewScreen(),
                                  ),
                                );
                              }
                            } catch (e) {
                              if (context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(
                                    content: Text('Processing failed: ${e.toString().replaceFirst('Exception: ', '')}'),
                                    backgroundColor: AppTheme.errorRed,
                                    duration: const Duration(seconds: 5),
                                  ),
                                );
                              }
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
