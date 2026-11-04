import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:facultylink_app/data/kra2_ocr_sync.dart';

void main() {
  test('sync replaces placeholder title with OCR value', () {
    final bundle = {
      'indicatorTitle': 'Sole author of a journal article',
      'outputTitle': 'Sole author of a journal article',
    };
    final ocrFields = {
      'outputTitle': {'value': 'Real Title', 'status': 'extracted'},
    };
    final controller = TextEditingController(text: 'Sole author of a journal article');
    Kra2OcrSync.syncController(
      controller: controller,
      fieldId: 'outputTitle',
      bundle: bundle,
      ocrFields: ocrFields,
      userEditedFields: {},
    );
    expect(controller.text, 'Real Title');
  });

  test('fieldHelper explains partial OCR dates', () {
    final helper = Kra2OcrSync.fieldHelper(
      fieldId: 'registrationDate',
      controllerText: '2025',
      ocrFields: {
        'registrationDate': {'value': '2025', 'status': 'partial'},
      },
      bundle: {},
      userEditedFields: {},
      reviewFlags: [],
    );
    expect(helper, contains('check'));
  });

  test('fieldHasValue uses controller text when bundle empty', () {
    expect(
      Kra2OcrSync.fieldHasValue(
        fieldId: 'authorsLine',
        controllerText: 'Jason Baroro',
        bundle: {},
        ocrFields: {},
      ),
      isTrue,
    );
  });

  test('sync replaces year-only date with full OCR date', () {
    final controller = TextEditingController(text: '2025');
    Kra2OcrSync.syncController(
      controller: controller,
      fieldId: 'registrationDate',
      bundle: {'registrationDate': '2025'},
      ocrFields: {
        'registrationDate': {'value': '2025-02-12', 'status': 'extracted'},
      },
      userEditedFields: {},
    );
    expect(controller.text, '2025-02-12');
  });

  test('metadata label values are detected', () {
    expect(
      Kra2OcrSync.isMetadataLabelValue('Journal / publisher / issuing organization /'),
      isTrue,
    );
    expect(
      Kra2OcrSync.isMetadataLabelValue('page and publication information', fieldId: 'outputTitle'),
      isTrue,
    );
    expect(Kra2OcrSync.isMetadataLabelValue('Jason Baroro', fieldId: 'authorsLine'), isFalse);
    expect(
      Kra2OcrSync.isMetadataLabelValue('University Learning Press (FICTIONAL)', fieldId: 'outputVenue'),
      isFalse,
    );
  });

  test('disclaimer title is treated as placeholder', () {
    expect(
      Kra2OcrSync.isPlaceholderTitle(null, 'FICTIONAL — FOR SYSTEM TESTING ONLY'),
      isTrue,
    );
  });

  test('sync replaces disclaimer title with OCR value', () {
    final controller = TextEditingController(text: 'FICTIONAL — FOR SYSTEM TESTING ONLY');
    Kra2OcrSync.syncController(
      controller: controller,
      fieldId: 'outputTitle',
      bundle: {'outputTitle': 'FICTIONAL — FOR SYSTEM TESTING ONLY'},
      ocrFields: {
        'outputTitle': {'value': 'Real Article Title', 'status': 'extracted'},
      },
      userEditedFields: {},
    );
    expect(controller.text, 'Real Article Title');
  });

  test('sync replaces generic patent application title', () {
    final bundle = {
      'indicatorId': 'kra2-b-patent-a-sole',
      'outputTitle': 'Patent application',
    };
    final controller = TextEditingController(text: 'Patent application');
    Kra2OcrSync.syncController(
      controller: controller,
      fieldId: 'outputTitle',
      bundle: bundle,
      ocrFields: {
        'outputTitle': {'value': 'Sample Innovation Device 01', 'status': 'extracted'},
      },
      userEditedFields: {},
    );
    expect(controller.text, 'Sample Innovation Device 01');
  });

  test('sync preserves user-edited fields', () {
    final controller = TextEditingController(text: 'My edit');
    Kra2OcrSync.syncController(
      controller: controller,
      fieldId: 'outputTitle',
      bundle: {},
      ocrFields: {'outputTitle': {'value': 'OCR Title'}},
      userEditedFields: {'outputTitle'},
    );
    expect(controller.text, 'My edit');
  });
}
