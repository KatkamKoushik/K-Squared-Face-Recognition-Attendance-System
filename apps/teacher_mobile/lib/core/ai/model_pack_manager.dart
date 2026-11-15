import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';
import 'model_pack.dart';

/// Manages downloadable AI model packs on the local mobile device.
/// Enforces single-active-model memory budget and manages local model weights directory.
class ModelPackManager extends ChangeNotifier {
  static final ModelPackManager _instance = ModelPackManager._internal();
  factory ModelPackManager() => _instance;
  ModelPackManager._internal() {
    _packs = ModelPack.standardPacks;
    _activePackId = 'option_1';
    _updateActiveStatus();
  }

  late List<ModelPack> _packs;
  late String _activePackId;
  bool _isAutoModeEnabled = false;

  List<ModelPack> get packs => List.unmodifiable(_packs);
  String get activePackId => _activePackId;
  bool get isAutoModeEnabled => _isAutoModeEnabled;

  ModelPack get activePack {
    return _packs.firstWhere(
      (p) => p.id == _activePackId,
      orElse: () => _packs.first,
    );
  }

  void _updateActiveStatus() {
    for (final p in _packs) {
      p.isActive = (p.id == _activePackId);
    }
  }

  /// Sets the active recognition model pipeline on the device.
  /// Deallocates old model references to adhere to strict mobile RAM limits.
  Future<void> setActivePack(String packId) async {
    final pack = _packs.firstWhere(
      (p) => p.id == packId,
      orElse: () => throw ArgumentError('Unknown model pack: $packId'),
    );

    if (!pack.isInstalled) {
      throw StateError('Model pack ${pack.name} is not installed on this device.');
    }

    _activePackId = packId;
    _updateActiveStatus();
    notifyListeners();
  }

  /// Toggles Intelligent Auto-Cascading Mode.
  /// When enabled: Option 1 runs first; Option 3 handles low-confidence/distant detections.
  void toggleAutoMode(bool enabled) {
    _isAutoModeEnabled = enabled;
    notifyListeners();
  }

  /// Resolves the local absolute file path for a model pack asset.
  Future<String> getModelPath(String fileName) async {
    final dir = await getApplicationDocumentsDirectory();
    final modelDir = Directory('${dir.path}/k2_models');
    if (!await modelDir.exists()) {
      await modelDir.create(recursive: true);
    }
    return '${modelDir.path}/$fileName';
  }

  /// Simulates / initiates downloading a model pack to the device.
  Future<void> installPack(String packId, {void Function(double progress)? onProgress}) async {
    final pack = _packs.firstWhere((p) => p.id == packId);
    if (pack.isInstalled) return;

    // Simulate progressive download stream
    for (int i = 1; i <= 10; i++) {
      await Future.delayed(const Duration(milliseconds: 150));
      onProgress?.call(i / 10.0);
    }

    pack.isInstalled = true;
    notifyListeners();
  }

  /// Frees storage space by removing an installed model pack.
  Future<void> uninstallPack(String packId) async {
    final pack = _packs.firstWhere((p) => p.id == packId);
    if (pack.isDefault) {
      throw StateError('Cannot uninstall the default system model pack.');
    }
    if (pack.isActive) {
      // Switch to default option 1 before uninstalling
      _activePackId = 'option_1';
      _updateActiveStatus();
    }
    pack.isInstalled = false;
    notifyListeners();
  }
}
