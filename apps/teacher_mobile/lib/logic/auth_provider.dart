import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/network/api_service.dart';
import 'session_provider.dart';

class AuthState {
  final bool isAuthenticated;
  final bool isLoading;
  final String? email;
  final String? userId;
  final String? role;
  final String? token;
  final String? errorMessage;
  final bool isOfflineDemo;

  const AuthState({
    this.isAuthenticated = false,
    this.isLoading = false,
    this.email,
    this.userId,
    this.role,
    this.token,
    this.errorMessage,
    this.isOfflineDemo = false,
  });

  AuthState copyWith({
    bool? isAuthenticated,
    bool? isLoading,
    String? email,
    String? userId,
    String? role,
    String? token,
    String? errorMessage,
    bool? isOfflineDemo,
  }) {
    return AuthState(
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      isLoading: isLoading ?? this.isLoading,
      email: email ?? this.email,
      userId: userId ?? this.userId,
      role: role ?? this.role,
      token: token ?? this.token,
      errorMessage: errorMessage,
      isOfflineDemo: isOfflineDemo ?? this.isOfflineDemo,
    );
  }
}

class AuthNotifier extends Notifier<AuthState> {
  FrsApiService get _api => ref.read(apiProvider);

  @override
  AuthState build() {
    return const AuthState();
  }

  Future<bool> login(String email, String password) async {
    state = state.copyWith(isLoading: true, errorMessage: null);

    try {
      final res = await _api.login(email: email.trim(), password: password);
      if (res != null && res['access_token'] != null) {
        final token = res['access_token'] as String;
        final userId = res['user_id'] as String?;
        final role = res['role'] as String?;
        _api.authToken = token;

        state = state.copyWith(
          isAuthenticated: true,
          isLoading: false,
          email: email.trim(),
          userId: userId,
          role: role,
          token: token,
          isOfflineDemo: false,
        );
        return true;
      }
    } catch (e) {
      if (_api.liveDemoMode) {
        state = state.copyWith(
          isLoading: false,
          errorMessage: 'Connection to ${_api.baseUrl} failed. Tap Settings to verify host IP.',
        );
        return false;
      }
    }

    // Explicit offline demo fallback only when liveDemoMode is disabled
    if (!_api.liveDemoMode && email.trim() == 'ramana.vrb@gmail.com' && password == 'KucetFaculty@2026') {
      const demoToken = 'jwt-kucet-offline-demo-ramana';
      _api.authToken = demoToken;
      state = state.copyWith(
        isAuthenticated: true,
        isLoading: false,
        email: email.trim(),
        userId: 'USR-KUCET-FAC-001',
        role: 'FACULTY',
        token: demoToken,
        isOfflineDemo: true,
      );
      return true;
    }

    state = state.copyWith(
      isLoading: false,
      errorMessage: 'Invalid institutional credentials or server (${_api.baseUrl}) unreachable.',
    );
    return false;
  }

  void logout() {
    _api.logout();
    state = const AuthState();
  }
}

final authProvider = NotifierProvider<AuthNotifier, AuthState>(() {
  return AuthNotifier();
});
