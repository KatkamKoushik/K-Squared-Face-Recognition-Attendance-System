import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frs_teacher_app/main.dart';
import 'package:frs_teacher_app/logic/auth_provider.dart';
import 'package:frs_teacher_app/logic/session_provider.dart';

class MockAuthenticatedAuthNotifier extends AuthNotifier {
  @override
  AuthState build() {
    return const AuthState(
      isAuthenticated: true,
      email: 'soujanyavedh@gmail.com',
      role: 'FACULTY',
      userId: 'FAC-IT-001',
    );
  }
}

void main() {
  testWidgets('FRS Teacher App launches and displays Faculty Sign In when unauthenticated', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: FrsTeacherApp(),
      ),
    );

    // Initial unauthenticated launch defaults to LoginScreen
    expect(find.text('Faculty Sign In'), findsOneWidget);
    expect(find.text('FRS V7.1 Faculty Portal'), findsOneWidget);
  });

  testWidgets('FRS Teacher App renders KUCET Faculty Portal when authenticated', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authProvider.overrideWith(() => MockAuthenticatedAuthNotifier()),
          assignedOfferingsProvider.overrideWith((ref) async => [
            {
              'offeringId': 'OFF-001',
              'subjectCode': 'CS401',
              'subjectName': 'Cloud Computing',
              'cohort': 'IV/IV CSE Sec A',
              'term': 'VII Sem',
              'enrolledCount': 66,
            }
          ]),
        ],
        child: const FrsTeacherApp(),
      ),
    );

    // Authenticated state renders HomeScreen
    expect(find.text('KUCET Faculty Portal'), findsOneWidget);
  });
}
