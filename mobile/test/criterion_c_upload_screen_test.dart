import 'package:facultylink_app/models/enums.dart';
import 'package:facultylink_app/screens/documents/document_flow_args.dart';
import 'package:facultylink_app/screens/documents/upload_document_screen.dart';
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

  Future<void> pumpUpload(WidgetTester tester, UploadDocumentScreen screen) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(MaterialApp(theme: AppTheme.light, home: screen));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));
    for (var i = 0; i < 60; i++) {
      await tester.pump(const Duration(milliseconds: 100));
      final ready = find.text('Upload signed approval sheet').evaluate().isNotEmpty ||
          find.text('Upload your main teaching material file').evaluate().isNotEmpty ||
          find.text('Select KRA *').evaluate().isNotEmpty;
      if (ready) break;
    }
    expect(captured, isEmpty, reason: captured.map((e) => e.exceptionAsString()).join('\n'));
  }

  testWidgets('Criterion C research primary upload shows approval sheet copy not Criterion B', (tester) async {
    await pumpUpload(
      tester,
      UploadDocumentScreen(
        initialKra: KraType.instruction,
        initialCriterionId: 'kra1-c',
        initialIndicatorId: 'kra1-c-adviser-ut',
        criterionCPrimaryFlow: true,
        criterionCOcrFirstResearch: true,
        criterionCDraft: const CriterionCAddWorkDraft(
          serviceKind: 'research',
          indicatorId: 'kra1-c-adviser-ut',
          ocrFirstResearch: true,
        ),
      ),
    );
    expect(find.text('Upload signed approval sheet'), findsOneWidget);
    expect(find.text('Upload your main teaching material file'), findsNothing);
    expect(find.textContaining('IMDC'), findsNothing);
    expect(find.textContaining('Instructional material'), findsNothing);
    expect(find.textContaining('library certification'), findsNothing);
  });

}
