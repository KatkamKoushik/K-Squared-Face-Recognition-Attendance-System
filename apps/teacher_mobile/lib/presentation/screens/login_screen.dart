import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../data/kucet_faculty_directory.dart';
import '../../logic/auth_provider.dart';
import '../../logic/session_provider.dart';
import 'demo_visualizer_screen.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _fillDemoCredentials([String email = 'soujanyavedh@gmail.com']) {
    _emailController.text = email;
    _passwordController.clear();
  }

  void _showCoordinatorsDirectoryDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Row(
          children: [
            Icon(Icons.badge_outlined, color: AppTheme.primaryNavy),
            SizedBox(width: 10),
            Expanded(
              child: Text(
                'KUCET Coordinators Directory',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
            ),
          ],
        ),
        content: SizedBox(
          width: double.maxFinite,
          child: ListView.separated(
            shrinkWrap: true,
            itemCount: KucetFacultyDirectory.academicCoordinators.length,
            separatorBuilder: (_, __) => const Divider(height: 1),
            itemBuilder: (context, index) {
              final coord = KucetFacultyDirectory.academicCoordinators[index];
              final hasEmail = coord.emailId != null && coord.emailId!.isNotEmpty;
              return ListTile(
                dense: true,
                leading: CircleAvatar(
                  radius: 16,
                  backgroundColor: coord.department == 'IT'
                      ? AppTheme.secondaryBlue
                      : AppTheme.primaryNavy.withValues(alpha: 0.15),
                  child: Text(
                    coord.department.substring(0, coord.department.length > 2 ? 2 : coord.department.length),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: coord.department == 'IT' ? Colors.white : AppTheme.primaryNavy,
                    ),
                  ),
                ),
                title: Text(
                  coord.name,
                  style: TextStyle(
                    fontWeight: coord.department == 'IT' ? FontWeight.bold : FontWeight.w600,
                    fontSize: 13,
                  ),
                ),
                subtitle: Text(
                  '${coord.department} • ${coord.emailId ?? "No email"}',
                  style: const TextStyle(fontSize: 11),
                ),
                trailing: hasEmail
                    ? const Icon(Icons.arrow_forward_ios, size: 12, color: AppTheme.secondaryBlue)
                    : null,
                onTap: hasEmail
                    ? () {
                        _fillDemoCredentials(coord.emailId!);
                        Navigator.pop(ctx);
                      }
                    : null,
              );
            },
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  void _showServerConfigDialog() {
    final api = ref.read(apiProvider);
    final urlController = TextEditingController(text: api.baseUrl);
    String? testResult;
    bool isTesting = false;

    showDialog(
      context: context,
      builder: (dialogCtx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          title: const Row(
            children: [
              Icon(Icons.dns_outlined, color: AppTheme.primaryNavy),
              SizedBox(width: 10),
              Text('Server Endpoint', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Configure the FastAPI control plane endpoint URL (e.g. host machine LAN IP on Wi-Fi or public tunnel):',
                style: TextStyle(fontSize: 13, color: AppTheme.textMutedLight),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: urlController,
                decoration: InputDecoration(
                  labelText: 'API Base URL',
                  hintText: 'https://straddle-deflate-footwear.ngrok-free.dev/api/v1',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                ),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 6,
                runSpacing: 4,
                children: [
                  ActionChip(
                    label: const Text('Ngrok Tunnel', style: TextStyle(fontSize: 11)),
                    onPressed: () {
                      setDialogState(() {
                        urlController.text = 'https://straddle-deflate-footwear.ngrok-free.dev/api/v1';
                        testResult = null;
                      });
                    },
                  ),
                  ActionChip(
                    label: const Text('Wi-Fi LAN', style: TextStyle(fontSize: 11)),
                    onPressed: () {
                      setDialogState(() {
                        urlController.text = 'http://192.168.0.3:8000/api/v1';
                        testResult = null;
                      });
                    },
                  ),
                  ActionChip(
                    label: const Text('ADB Reverse', style: TextStyle(fontSize: 11)),
                    onPressed: () {
                      setDialogState(() {
                        urlController.text = 'http://127.0.0.1:8000/api/v1';
                        testResult = null;
                      });
                    },
                  ),
                  ActionChip(
                    label: const Text('Emulator', style: TextStyle(fontSize: 11)),
                    onPressed: () {
                      setDialogState(() {
                        urlController.text = 'http://10.0.2.2:8000/api/v1';
                        testResult = null;
                      });
                    },
                  ),
                ],
              ),
              const SizedBox(height: 12),
              if (isTesting) ...[
                const Row(
                  children: [
                    SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
                    SizedBox(width: 10),
                    Text('Pinging server...', style: TextStyle(fontSize: 12)),
                  ],
                ),
              ] else if (testResult != null) ...[
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  decoration: BoxDecoration(
                    color: testResult!.startsWith('Connected')
                        ? AppTheme.statusMatched.withValues(alpha: 0.1)
                        : AppTheme.errorRed.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        testResult!.startsWith('Connected') ? Icons.check_circle : Icons.error_outline,
                        size: 16,
                        color: testResult!.startsWith('Connected') ? AppTheme.statusMatched : AppTheme.errorRed,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          testResult!,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: testResult!.startsWith('Connected') ? AppTheme.statusMatched : AppTheme.errorRed,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
          actions: [
            TextButton(
              onPressed: isTesting
                  ? null
                  : () async {
                      setDialogState(() {
                        isTesting = true;
                        testResult = null;
                      });
                      final prev = api.baseUrl;
                      api.baseUrl = urlController.text.trim();
                      final ok = await api.checkConnection();
                      setDialogState(() {
                        isTesting = false;
                        testResult = ok
                            ? 'Connected successfully (HTTP 200)'
                            : (api.lastConnectionError != null
                                ? 'Unreachable: ${api.lastConnectionError}'
                                : 'Server unreachable. Verify host IP & port.');
                        if (!ok) api.baseUrl = prev;
                      });
                    },
              child: const Text('Test Connection'),
            ),
            ElevatedButton(
              onPressed: () {
                setState(() {
                  api.baseUrl = urlController.text.trim();
                });
                Navigator.pop(dialogCtx);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Endpoint updated: ${api.baseUrl}'),
                    backgroundColor: AppTheme.primaryNavy,
                  ),
                );
              },
              child: const Text('Apply'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _handleLogin() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text;

    if (email.isEmpty || password.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please enter institutional email and password.'),
          backgroundColor: AppTheme.errorRed,
        ),
      );
      return;
    }

    ref.read(apiProvider).liveDemoMode = true;
    final success = await ref.read(authProvider.notifier).login(email, password);
    if (!success && mounted) {
      final err = ref.read(authProvider).errorMessage ?? 'Login failed.';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(err),
          backgroundColor: AppTheme.errorRed,
          duration: const Duration(seconds: 4),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final api = ref.watch(apiProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundLight,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined, color: AppTheme.primaryNavy),
            tooltip: 'Server Connection Settings',
            onPressed: _showServerConfigDialog,
          ),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Institutional Crest Header
                  Center(
                    child: Container(
                      width: 72,
                      height: 72,
                      decoration: BoxDecoration(
                        color: AppTheme.primaryNavy,
                        borderRadius: BorderRadius.circular(16),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.08),
                            blurRadius: 12,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      alignment: Alignment.center,
                      child: const Text(
                        'K²',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.5,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Title and Subtitle
                  const Center(
                    child: Text(
                      'K² FRS Faculty Portal',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.primaryNavy,
                      ),
                    ),
                  ),
                  const SizedBox(height: 6),
                  const Center(
                    child: Text(
                      'Institutional Classroom Attendance Proposal System',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 13,
                        color: AppTheme.textMutedLight,
                      ),
                    ),
                  ),
                  const SizedBox(height: 28),

                  // Card Container for Login Form
                  Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: AppTheme.surfaceLight,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppTheme.borderLight),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.04),
                          blurRadius: 16,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        const Text(
                          'Faculty Sign In',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.primaryNavy,
                          ),
                        ),
                        const SizedBox(height: 16),

                        // Institutional Email Field
                        TextField(
                          controller: _emailController,
                          keyboardType: TextInputType.emailAddress,
                          autocorrect: false,
                          decoration: InputDecoration(
                            labelText: 'Institutional Email',
                            hintText: 'name@kucet.ac.in',
                            prefixIcon: const Icon(Icons.email_outlined, size: 20),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                            contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                          ),
                        ),
                        const SizedBox(height: 16),

                        // Password Field
                        TextField(
                          controller: _passwordController,
                          obscureText: _obscurePassword,
                          decoration: InputDecoration(
                            labelText: 'Password',
                            prefixIcon: const Icon(Icons.lock_outline, size: 20),
                            suffixIcon: IconButton(
                              icon: Icon(
                                _obscurePassword ? Icons.visibility_off : Icons.visibility,
                                size: 20,
                              ),
                              onPressed: () {
                                setState(() {
                                  _obscurePassword = !_obscurePassword;
                                });
                              },
                            ),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                            contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                          ),
                        ),
                        const SizedBox(height: 24),

                        // Sign In Button
                        ElevatedButton(
                          onPressed: authState.isLoading ? null : _handleLogin,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.primaryNavy,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                            elevation: 0,
                          ),
                          child: authState.isLoading
                              ? const SizedBox(
                                  height: 20,
                                  width: 20,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                                  ),
                                )
                              : const Text(
                                  'Sign In',
                                  style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Two Distinct Operating Modes: Dr. Soujanya vs Demo Visualizer
                  const Text(
                    'SELECT OPERATING MODE',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.1,
                      color: AppTheme.textMutedLight,
                    ),
                  ),
                  const SizedBox(height: 10),

                  // Mode 1: Dr. M. Soujanya Official Faculty Login
                  InkWell(
                    onTap: () => _fillDemoCredentials('soujanyavedh@gmail.com'),
                    borderRadius: BorderRadius.circular(12),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppTheme.primaryNavy.withValues(alpha: 0.3)),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.04),
                            blurRadius: 6,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: AppTheme.primaryNavy.withValues(alpha: 0.08),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.school, size: 20, color: AppTheme.primaryNavy),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: const [
                                Text(
                                  'Dr. M. Soujanya (Official Portal)',
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.bold,
                                    color: AppTheme.primaryNavy,
                                  ),
                                ),
                                SizedBox(height: 2),
                                Text(
                                  'soujanyavedh@gmail.com • CSE Academic Faculty',
                                  style: TextStyle(
                                    fontSize: 11,
                                    color: AppTheme.textMutedLight,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const Icon(Icons.touch_app_outlined, size: 16, color: AppTheme.secondaryBlue),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 10),

                  // Mode 2: Universal Demo Testing & Ground-Truth Visualizer
                  InkWell(
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => const DemoVisualizerScreen(),
                        ),
                      );
                    },
                    borderRadius: BorderRadius.circular(12),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF0FDF4), // Light emerald tint
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0xFF10B981).withValues(alpha: 0.5)),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF10B981).withValues(alpha: 0.08),
                            blurRadius: 8,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: const Color(0xFF10B981).withValues(alpha: 0.15),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.camera_enhance_rounded, size: 20, color: Color(0xFF059669)),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: const [
                                Text(
                                  'Demo Testing & Face Visualizer',
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.bold,
                                    color: Color(0xFF065F46),
                                  ),
                                ),
                                SizedBox(height: 2),
                                Text(
                                  'Universal Sandbox • Branch-Agnostic Test Gallery',
                                  style: TextStyle(
                                    fontSize: 11,
                                    color: Color(0xFF047857),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const Icon(Icons.arrow_forward_ios, size: 14, color: Color(0xFF059669)),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),

                  // Browse Other Academic Coordinators Button
                  OutlinedButton.icon(
                    onPressed: _showCoordinatorsDirectoryDialog,
                    icon: const Icon(Icons.badge_outlined, size: 16),
                    label: const Text(
                      'Browse All KUCET Academic Coordinators',
                      style: TextStyle(fontSize: 12),
                    ),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppTheme.primaryNavy,
                      side: const BorderSide(color: AppTheme.borderLight),
                      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                  ),
                  const SizedBox(height: 14),

                  // Live Server Endpoint Indicator & Configure Link
                  InkWell(
                    onTap: _showServerConfigDialog,
                    borderRadius: BorderRadius.circular(8),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.wifi_tethering, size: 14, color: AppTheme.textMutedLight),
                          const SizedBox(width: 6),
                          Flexible(
                            child: Text(
                              'Server: ${api.baseUrl}',
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(fontSize: 12, color: AppTheme.textMutedLight),
                            ),
                          ),
                          const SizedBox(width: 6),
                          const Text(
                            '[Change]',
                            style: TextStyle(
                              fontSize: 12,
                              color: AppTheme.secondaryBlue,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
