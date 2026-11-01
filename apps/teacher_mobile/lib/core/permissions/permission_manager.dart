/// Permission states conforming to Checklist Control 19-N001.
enum AppPermissionStatus {
  notRequested,
  granted,
  denied,
  permanentlyDenied,
  restricted,
}

/// Abstract hardware permission checker interface for testability.
abstract class PermissionPlatformDelegate {
  Future<AppPermissionStatus> checkCameraPermission();
  Future<AppPermissionStatus> requestCameraPermission();
  Future<void> openAppSettings();
}

/// In-memory/platform permission manager adhering to Checklist Controls 19-N001 & 19-N002.
class PermissionManager {
  final PermissionPlatformDelegate delegate;
  AppPermissionStatus _cachedCameraStatus = AppPermissionStatus.notRequested;

  PermissionManager({required this.delegate});

  AppPermissionStatus get cachedCameraStatus => _cachedCameraStatus;

  /// Returns current camera permission status.
  /// When [forceRefresh] is true (e.g. on app resume from settings per 19-N002),
  /// the real hardware/system state is re-queried rather than trusting stale cache.
  Future<AppPermissionStatus> getCameraPermission({bool forceRefresh = false}) async {
    if (forceRefresh || _cachedCameraStatus == AppPermissionStatus.notRequested) {
      _cachedCameraStatus = await delegate.checkCameraPermission();
    }
    return _cachedCameraStatus;
  }

  /// Explicitly requests camera permission from user.
  Future<AppPermissionStatus> requestCameraPermission() async {
    _cachedCameraStatus = await delegate.requestCameraPermission();
    return _cachedCameraStatus;
  }

  /// App lifecycle hook called on resume (e.g. user returns from system settings per 19-N002).
  Future<AppPermissionStatus> onAppResumed() async {
    _cachedCameraStatus = await delegate.checkCameraPermission();
    return _cachedCameraStatus;
  }

  /// Determines whether hardware photo capture should gracefully fall back to manual roll call (IDE-20).
  bool shouldFallbackToManualRollCall() {
    return _cachedCameraStatus == AppPermissionStatus.denied ||
        _cachedCameraStatus == AppPermissionStatus.permanentlyDenied ||
        _cachedCameraStatus == AppPermissionStatus.restricted;
  }

  /// Navigates to system settings when permanently denied.
  Future<void> openSettings() async {
    await delegate.openAppSettings();
  }
}
