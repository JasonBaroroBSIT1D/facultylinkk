import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:facultylink_app/data/mock_data.dart';
import 'package:facultylink_app/theme/app_theme.dart';
import 'package:facultylink_app/widgets/kra_dashboard_section.dart';
import 'package:facultylink_app/widgets/kra_module_card.dart';

void main() {
  Future<void> pumpSection(
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
              child: KraDashboardSection(kraScores: MockData.kraScores),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('KRA dashboard modules render without overflow at 320px', (
    tester,
  ) async {
    await pumpSection(tester, size: const Size(320, 1100));
    expect(tester.takeException(), isNull);
    expect(find.byType(KraModuleCard), findsNWidgets(4));
    expect(find.text('Professional Development'), findsOneWidget);
  });

  testWidgets('KRA dashboard modules render without overflow at 360px', (
    tester,
  ) async {
    await pumpSection(tester, size: const Size(360, 1100));
    expect(tester.takeException(), isNull);
  });

  testWidgets('KRA dashboard modules render without overflow at 393px', (
    tester,
  ) async {
    await pumpSection(tester, size: const Size(393, 1100));
    expect(tester.takeException(), isNull);
    expect(find.text('Extension Services'), findsOneWidget);
  });

  testWidgets('KRA dashboard modules render without overflow at 430px', (
    tester,
  ) async {
    await pumpSection(tester, size: const Size(430, 1100));
    expect(tester.takeException(), isNull);
  });

  testWidgets('KRA dashboard modules handle large text scale', (tester) async {
    await pumpSection(
      tester,
      size: const Size(360, 1400),
      textScaler: TextScaler.linear(1.4),
    );
    expect(tester.takeException(), isNull);
    expect(
      KraDashboardSection.useTwoColumns(360, TextScaler.linear(1.4)),
      isFalse,
    );
  });

  testWidgets('tablet width uses two-column layout', (tester) async {
    await pumpSection(tester, size: const Size(820, 900));
    expect(tester.takeException(), isNull);
    expect(
      KraDashboardSection.useTwoColumns(820, TextScaler.noScaling),
      isTrue,
    );
  });
}
