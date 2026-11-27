/// Model Pack Specification for K² FRS On-Device AI Subsystem.
/// Defines metadata, dimensions, namespaces, and runtime parameters
/// for modular, downloadable onnxruntime vision pipelines.
class ModelPack {
  final String id;
  final String name;
  final String shortName;
  final String description;
  final String detectorFileName;
  final String recognizerFileName;
  final String embeddingNamespace;
  final int dimension;
  final double defaultThreshold;
  final int packSizeBytes;
  final String badge;
  final bool isDefault;
  bool isInstalled;
  bool isActive;

  ModelPack({
    required this.id,
    required this.name,
    required this.shortName,
    required this.description,
    required this.detectorFileName,
    required this.recognizerFileName,
    required this.embeddingNamespace,
    required this.dimension,
    required this.defaultThreshold,
    required this.packSizeBytes,
    required this.badge,
    this.isDefault = false,
    this.isInstalled = false,
    this.isActive = false,
  });

  String get formattedSize {
    if (packSizeBytes < 1024 * 1024) {
      return '${(packSizeBytes / 1024).toStringAsFixed(1)} KB';
    }
    return '${(packSizeBytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  static List<ModelPack> get standardPacks => [
    ModelPack(
      id: 'option_1',
      name: 'Option 1: SCRFD-500M + ArcFace MobileFaceNet',
      shortName: 'Option 1 (512-D ArcFace)',
      description: 'Ultra-lightweight 512-D normalized ArcFace embeddings with SCRFD 5-keypoint affine alignment. Optimal for low memory and fast ARM CPU inference.',
      detectorFileName: 'scrfd_500m_kps.onnx',
      recognizerFileName: 'mobilefacenet_w600k.onnx',
      embeddingNamespace: 'mobilefacenet_512d_v1',
      dimension: 512,
      defaultThreshold: 0.380,
      packSizeBytes: 6291456, // ~6.0 MB
      badge: '512-D High Speed',
      isDefault: false,
      isInstalled: true,
      isActive: false,
    ),
    ModelPack(
      id: 'option_3',
      name: 'Option 3: SCRFD-2.5G + OpenCV Zoo SFace',
      shortName: 'Option 3 (128-D SFace)',
      description: 'High-recall 128-D official OpenCV Zoo SFace embeddings with SCRFD-2.5G detector. Delivers enhanced precision for distant and angled classroom faces.',
      detectorFileName: 'scrfd_2.5g_kps.onnx',
      recognizerFileName: 'face_recognition_sface_2021dec.onnx',
      embeddingNamespace: 'sface_128d_v1',
      dimension: 128,
      defaultThreshold: 0.363,
      packSizeBytes: 40894464, // ~39 MB
      badge: '128-D OpenCV Zoo',
      isDefault: false,
      isInstalled: true,
      isActive: false,
    ),
    ModelPack(
      id: 'finetuned_v2',
      name: 'Multi-Dataset Fine-Tuned: YuNet + KUCET SFace',
      shortName: 'Fine-Tuned SFace (128-D)',
      description: 'Domain fine-tuned SFace pipeline calibrated specifically for KUCET lecture halls, Indian facial distributions, and verified enrollment portraits.',
      detectorFileName: 'face_detection_yunet_2023mar.onnx',
      recognizerFileName: 'kucet_frs_sface_finetuned.onnx',
      embeddingNamespace: 'kucet_frs_sface_finetuned_v2',
      dimension: 128,
      defaultThreshold: 0.482,
      packSizeBytes: 44969984, // ~43 MB
      badge: '128-D Indian-Face Tuned',
      isDefault: true,
      isInstalled: true,
      isActive: true,
    ),
  ];
}
