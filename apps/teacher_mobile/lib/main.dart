import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/database/local_database_service.dart';
import 'core/theme/app_theme.dart';
import 'logic/auth_provider.dart';
import 'presentation/screens/home_screen.dart';
import 'presentation/screens/login_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await LocalDatabaseService().init();
  runApp(
    const ProviderScope(
      child: FrsTeacherApp(),
    ),
  );
}

class FrsTeacherApp extends ConsumerWidget {
  const FrsTeacherApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);

    return MaterialApp(
      title: 'FRS KUCET Faculty Attendance',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: authState.isAuthenticated ? const HomeScreen() : const LoginScreen(),
    );
  }
}
