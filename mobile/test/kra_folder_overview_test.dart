import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:facultylink_app/theme/app_theme.dart';
import 'package:facultylink_app/widgets/kra_folder_overview.dart';

void main() {
  Future<void> pumpOverview(
    WidgetTester tester, {
    required Size size,
    TextScaler textScaler = TextScaler.noScaling,
  }) async {
    await tester.binding.setSurfaceSize(size);
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(
      MediaQuery(
        data: MediaQueryData(size: size, textScaler: textScaler),
        child: MaterialApp(
          theme: AppTheme.light,
          home: Scaffold(
            body: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: const KraFolderOverview(documents: []),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  test('useTwoColumns respects width and text scale', () {
    expect(KraFolderOverview.useTwoColumns(360, TextScaler.noScaling), isFalse);
    expect(KraFolderOverview.useTwoColumns(400, TextScaler.noScaling), isTrue);
    expect(
      KraFolderOverview.useTwoColumns(400, TextScaler.linear(1.3)),
      isFalse,
    );
  });

  testWidgets('KRA cards do not overflow at 360px width', (tester) async {
    await pumpOverview(tester, size: const Size(360, 900));
    expect(tester.takeException(), isNull);
    expect(find.text('KRA I'), findsOneWidget);
    expect(find.text('KRA IV'), findsOneWidget);
    expect(find.text('Professional Development'), findsOneWidget);
    expect(find.text('Extension or Community Services'), findsOneWidget);
  });

  testWidgets('KRA cards do not overflow at 390px width (two columns)', (tester) async {
    await pumpOverview(tester, size: const Size(390, 900));
    expect(tester.takeException(), isNull);
    expect(find.text('KRA III'), findsOneWidget);
  });

  testWidgets('KRA cards do not overflow with large text scale', (tester) async {
    await pumpOverview(
      tester,
      size: const Size(390, 1200),
      textScaler: TextScaler.linear(1.4),
    );
    expect(tester.takeException(), isNull);
    expect(find.text('Browse by KRA'), findsOneWidget);
  });

  testWidgets('KRA cards do not overflow on wide layout', (tester) async {
    await pumpOverview(tester, size: const Size(820, 900));
    expect(tester.takeException(), isNull);
  });
}
