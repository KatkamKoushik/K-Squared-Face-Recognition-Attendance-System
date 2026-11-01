import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frs_teacher_app/main.dart';

void main() {
  testWidgets('FRS Teacher App launches and shows Faculty Portal title', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: FrsTeacherApp(),
      ),
    );

    expect(find.text('FRS Attendance — Faculty Portal'), findsOneWidget);
  });
}
