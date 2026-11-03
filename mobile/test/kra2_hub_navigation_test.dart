import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:facultylink_app/data/kra2_catalog.dart';
import 'package:facultylink_app/screens/kra2/kra2_criterion_hub_screen.dart';
import 'package:facultylink_app/screens/kra2/kra2_main_hub_screen.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() async {
    await Kra2Catalog.preload();
  });

  testWidgets('main hub shows three criterion cards immediately', (tester) async {
    final sw = Stopwatch()..start();
    await tester.pumpWidget(
      const MaterialApp(home: Kra2MainHubScreen()),
    );
    await tester.pump();
    sw.stop();

    expect(find.text('What have you accomplished?'), findsOneWidget);
    expect(find.text('Publications'), findsOneWidget);
    expect(find.text('Inventions'), findsOneWidget);
    expect(find.text('Creative Works & Research Impact'), findsOneWidget);
    expect(sw.elapsedMilliseconds, lessThan(2000));
  });

  testWidgets('criterion hub shows accomplishment types without waiting on API', (tester) async {
    final sw = Stopwatch()..start();
    await tester.pumpWidget(
      const MaterialApp(
        home: Kra2CriterionHubScreen(criterionId: Kra2Catalog.criterionA),
      ),
    );
    await tester.pump();
    sw.stop();

    expect(find.text('Add something new'), findsOneWidget);
    expect(find.text('Journal article'), findsOneWidget);
    expect(find.text('Book'), findsOneWidget);
    expect(find.text('What would you like to add?'), findsOneWidget);
    expect(sw.elapsedMilliseconds, lessThan(2000));
  });
}
