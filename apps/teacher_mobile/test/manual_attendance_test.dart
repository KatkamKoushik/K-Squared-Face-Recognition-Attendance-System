import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frs_teacher_app/presentation/screens/manual_attendance_screen.dart';

void main() {
  testWidgets('ManualAttendanceScreen renders roll-call interface and search bar', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(
          home: ManualAttendanceScreen(),
        ),
      ),
    );

    // Verify AppBar title
    expect(find.text('Manual Roll-Call Attendance'), findsOneWidget);

    // Verify search field exists
    expect(find.byType(TextField), findsOneWidget);

    // Verify summary counters exist (Present, Absent, Denominator)
    expect(find.text('Present'), findsOneWidget);
    expect(find.text('Absent'), findsOneWidget);
  });
}
