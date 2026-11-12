import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frs_teacher_app/presentation/screens/demo_visualizer_screen.dart';

void main() {
  testWidgets('DemoVisualizerScreen renders empty state and action buttons', (tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(
          home: DemoVisualizerScreen(),
        ),
      ),
    );

    // Initial render
    expect(find.text('Face Visualizer'), findsOneWidget);
    expect(find.text('Ground-Truth Face Visualizer'), findsOneWidget);
    expect(find.text('Take Photo'), findsOneWidget);
    expect(find.text('Pick Gallery'), findsOneWidget);
    expect(find.byIcon(Icons.tune), findsOneWidget);
  });
}
