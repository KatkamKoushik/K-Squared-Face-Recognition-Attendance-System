import 'package:flutter/foundation.dart';
import 'class_pack.dart';

/// Manages authorized downloadable class database packs.
/// Caches authorized student rosters and vector templates for offline recognition.
class ClassPackManager extends ChangeNotifier {
  static final ClassPackManager _instance = ClassPackManager._internal();
  factory ClassPackManager() => _instance;
  ClassPackManager._internal() {
    _packs = ClassDataPack.sampleAuthorizedPacks;
  }

  late List<ClassDataPack> _packs;

  List<ClassDataPack> get packs => List.unmodifiable(_packs);
  int get downloadedCount => _packs.where((p) => p.isDownloaded).length;

  /// Simulates downloading authorized class roster and cryptographic embeddings into encrypted local storage.
  Future<void> downloadClassPack(String packId, {void Function(double progress)? onProgress}) async {
    final pack = _packs.firstWhere((p) => p.id == packId);
    if (pack.isDownloaded) return;

    for (int i = 1; i <= 8; i++) {
      await Future.delayed(const Duration(milliseconds: 120));
      onProgress?.call(i / 8.0);
    }

    pack.isDownloaded = true;
    pack.downloadedAt = DateTime.now();
    notifyListeners();
  }

  /// Removes an offline class pack to free local device space.
  Future<void> removeClassPack(String packId) async {
    final pack = _packs.firstWhere((p) => p.id == packId);
    pack.isDownloaded = false;
    pack.downloadedAt = null;
    notifyListeners();
  }
}
