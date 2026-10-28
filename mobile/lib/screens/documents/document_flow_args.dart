import '../../models/enums.dart';

/// Opens [KraExplorerScreen] at KRA, criterion, or indicator level.
class KraExplorerLaunch {
  const KraExplorerLaunch({
    required this.kra,
    this.criterionId,
    this.indicatorId,
  });

  final KraType kra;
  final String? criterionId;
  final String? indicatorId;
}

/// Pre-selects KRA hierarchy on the upload form.
class UploadDocumentLaunch {
  const UploadDocumentLaunch({
    this.kra,
    this.criterionId,
    this.indicatorId,
  });

  final KraType? kra;
  final String? criterionId;
  final String? indicatorId;
}
