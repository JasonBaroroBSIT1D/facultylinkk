import 'package:facultylink_app/screens/criterion_b/criterion_b_add_work_screen.dart';
import 'package:facultylink_app/screens/criterion_b/criterion_b_hub_screen.dart';
import 'package:facultylink_app/screens/documents/document_flow_args.dart';
import 'package:facultylink_app/theme/app_theme.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final captured = <FlutterErrorDetails>[];

  setUp(() {
    captured.clear();
    final prior = FlutterError.onError;
    FlutterError.onError = (details) {
      captured.add(details);
      prior?.call(details);
    };
  });

  tearDown(() {
    FlutterError.onError = FlutterError.presentError;
  });

  Future<void> pumpMobile(WidgetTester tester, Widget home) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(MaterialApp(theme: AppTheme.light, home: home));
    await tester.pumpAndSettle();
    expect(captured, isEmpty, reason: _errors(captured));
  }

  testWidgets('Teaching Material — first step visible with production theme', (tester) async {
    await pumpMobile(
      tester,
      const CriterionBAddWorkScreen(kind: CriterionBWorkKind.teaching),
    );
    expect(find.text('What type of material?'), findsOneWidget);
    expect(find.text('Book or textbook'), findsOneWidget);
    expect(find.text('Next'), findsOneWidget);
    expect(find.text('Back'), findsOneWidget);
  });

  testWidgets('Teaching Material — tap type and advance', (tester) async {
    await pumpMobile(
      tester,
      const CriterionBAddWorkScreen(kind: CriterionBWorkKind.teaching),
    );
    await tester.tap(find.text('Module'));
    await tester.pumpAndSettle();
    expect(captured, isEmpty, reason: _errors(captured));
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    expect(find.text('What is its title?'), findsOneWidget);
    expect(captured, isEmpty, reason: _errors(captured));
  });

  testWidgets('Academic Program — first step visible with production theme', (tester) async {
    await pumpMobile(
      tester,
      const CriterionBAddWorkScreen(kind: CriterionBWorkKind.program),
    );
    expect(find.text('What is the program name?'), findsOneWidget);
    expect(find.byType(TextField), findsOneWidget);
  });

  Future<void> _advanceToAuthorship(WidgetTester tester) async {
    await tester.tap(find.text('Module'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'Test Module Title');
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
  }

  testWidgets('Co-authored module shows contribution then complete instructional material', (tester) async {
    await pumpMobile(
      tester,
      const CriterionBAddWorkScreen(kind: CriterionBWorkKind.teaching),
    );
    await _advanceToAuthorship(tester);
    await tester.tap(find.text('I worked with others'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    expect(find.text('What was your contribution?'), findsOneWidget);
    await tester.enterText(find.byType(TextField), '40');
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    expect(find.text('Complete Instructional Material'), findsOneWidget);
    expect(captured, isEmpty, reason: _errors(captured));
  });

  testWidgets('Sole manual shows complete instructional material step', (tester) async {
    await pumpMobile(
      tester,
      const CriterionBAddWorkScreen(kind: CriterionBWorkKind.teaching),
    );
    await tester.tap(find.text('Instructional manual'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'Lab Manual');
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('I created it alone'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    expect(find.text('Complete Instructional Material'), findsOneWidget);
  });

  testWidgets('Complete set step requires confirmation before Next', (tester) async {
    await pumpMobile(
      tester,
      const CriterionBAddWorkScreen(kind: CriterionBWorkKind.teaching),
    );
    await _advanceToAuthorship(tester);
    await tester.tap(find.text('I created it alone'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    expect(find.text('Complete Instructional Material'), findsOneWidget);
    await tester.tap(find.byType(SwitchListTile));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    expect(find.text('Ready to upload'), findsOneWidget);
  });

  testWidgets('Hub → Teaching Material shows add work body', (tester) async {
    await pumpMobile(tester, const CriterionBHubScreen());
    await tester.tap(find.text('Teaching Material'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 32));
    await tester.pumpAndSettle();
    expect(captured, isEmpty, reason: _errors(captured));
    expect(find.text('What type of material?'), findsOneWidget);
  });
}

String _errors(List<FlutterErrorDetails> details) {
  if (details.isEmpty) return '';
  return details.map((d) => '${d.exceptionAsString()}\n${d.stack}').join('\n---\n');
}
