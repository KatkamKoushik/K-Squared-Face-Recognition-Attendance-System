import 'package:flutter/material.dart';
import '../../data/models/domain_contracts.dart';
import '../theme/app_theme.dart';

/// Reusable Evidence Status Badge
/// Satisfies Tastegate: Always pairs color with explicit semantic icon & text.
class EvidenceStatusChip extends StatelessWidget {
  final EvidenceState state;
  final bool compact;

  const EvidenceStatusChip({
    super.key,
    required this.state,
    this.compact = false,
  });

  @override
  Widget build(BuildContext context) {
    final config = _getConfig(state);

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: compact ? 8 : 12,
        vertical: compact ? 4 : 6,
      ),
      decoration: BoxDecoration(
        color: config.color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: config.color.withValues(alpha: 0.4), width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(config.icon, size: compact ? 13 : 16, color: config.color),
          const SizedBox(width: 6),
          Text(
            config.label,
            style: TextStyle(
              color: config.color,
              fontSize: compact ? 11 : 13,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  _StatusConfig _getConfig(EvidenceState state) {
    switch (state) {
      case EvidenceState.candidate:
        return const _StatusConfig(
          label: 'Proposed Present',
          color: AppTheme.statusMatched,
          icon: Icons.check_circle_rounded,
        );
      case EvidenceState.review:
        return const _StatusConfig(
          label: 'Needs Review',
          color: AppTheme.statusReview,
          icon: Icons.error_rounded,
        );
      case EvidenceState.recaptureRequired:
        return const _StatusConfig(
          label: 'Recapture Needed',
          color: AppTheme.statusRecapture,
          icon: Icons.camera_alt_rounded,
        );
      case EvidenceState.unknown:
        return const _StatusConfig(
          label: 'Unrecognized Face',
          color: AppTheme.statusUnknown,
          icon: Icons.help_rounded,
        );
      case EvidenceState.insufficientEvidence:
        return const _StatusConfig(
          label: 'Low Quality',
          color: AppTheme.statusRecapture,
          icon: Icons.blur_on_rounded,
        );
      case EvidenceState.pipelineError:
      case EvidenceState.securityFail:
        return const _StatusConfig(
          label: 'Security / Pipeline Error',
          color: AppTheme.statusError,
          icon: Icons.cancel_rounded,
        );
      case EvidenceState.captured:
      case EvidenceState.validating:
      case EvidenceState.queued:
      case EvidenceState.processing:
      case EvidenceState.securityUncertain:
        return const _StatusConfig(
          label: 'Processing Probe',
          color: AppTheme.secondaryBlue,
          icon: Icons.hourglass_top_rounded,
        );
    }
  }
}

class _StatusConfig {
  final String label;
  final Color color;
  final IconData icon;

  const _StatusConfig({
    required this.label,
    required this.color,
    required this.icon,
  });
}
