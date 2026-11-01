import 'package:flutter_test/flutter_test.dart';
import 'package:frs_teacher_app/core/permissions/permission_manager.dart';

class MockPermissionDelegate implements PermissionPlatformDelegate {
  AppPermissionStatus currentStatus = AppPermissionStatus.notRequested;
  bool openedSettings = false;

  @override
  Future<AppPermissionStatus> checkCameraPermission() async => currentStatus;

  @override
  Future<AppPermissionStatus> requestCameraPermission() async {
    currentStatus = AppPermissionStatus.granted;
    return currentStatus;
  }

  @override
  Future<void> openAppSettings() async {
    openedSettings = true;
  }
}

void main() {
  group('PermissionManager Lifecycle & Fallback (Checklist Controls 19-N001, 19-N002)', () {
    late MockPermissionDelegate delegate;
    late PermissionManager manager;

    setUp(() {
      delegate = MockPermissionDelegate();
      manager = PermissionManager(delegate: delegate);
    });

    test('Initial status is notRequested and triggers initial query', () async {
      delegate.currentStatus = AppPermissionStatus.denied;
      final status = await manager.getCameraPermission();
      expect(status, AppPermissionStatus.denied);
      expect(manager.cachedCameraStatus, AppPermissionStatus.denied);
      expect(manager.shouldFallbackToManualRollCall(), isTrue);
    });

    test('onAppResumed re-checks hardware permission and busts stale cache (19-N002)', () async {
      delegate.currentStatus = AppPermissionStatus.denied;
      await manager.getCameraPermission();
      expect(manager.cachedCameraStatus, AppPermissionStatus.denied);

      // User went to system settings and granted permission
      delegate.currentStatus = AppPermissionStatus.granted;

      // Resuming the app must refresh state immediately
      final refreshed = await manager.onAppResumed();
      expect(refreshed, AppPermissionStatus.granted);
      expect(manager.cachedCameraStatus, AppPermissionStatus.granted);
      expect(manager.shouldFallbackToManualRollCall(), isFalse);
    });

    test('Graceful fallback triggers on restricted or permanentlyDenied status', () {
      delegate.currentStatus = AppPermissionStatus.permanentlyDenied;
      expect(manager.shouldFallbackToManualRollCall(), isFalse); // Not cached yet

      manager = PermissionManager(delegate: delegate);
      delegate.currentStatus = AppPermissionStatus.permanentlyDenied;
    });

    test('Open settings delegates to platform implementation', () async {
      await manager.openSettings();
      expect(delegate.openedSettings, isTrue);
    });
  });
}
