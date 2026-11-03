import 'criterion_b_catalog.dart';

/// Maps simple faculty choices to existing indicator IDs and bundle fields.
abstract final class CriterionBMapper {
  static String teachingIndicatorId({
    required String materialKind,
    required bool withOthers,
  }) {
    final suffix = withOthers ? '-co' : '-sole';
    switch (materialKind) {
      case 'book':
        return 'kra1-b-textbook$suffix';
      case 'module':
        return 'kra1-b-module$suffix';
      case 'manual':
        return 'kra1-b-manual$suffix';
      case 'multimedia':
        return 'kra1-b-multimedia$suffix';
      default:
        return 'kra1-b-module$suffix';
    }
  }

  static String materialTypeForKind(String materialKind) {
    switch (materialKind) {
      case 'book':
        return 'textbook';
      case 'module':
        return 'module';
      case 'manual':
        return 'instructional_manual';
      case 'multimedia':
        return 'multimedia';
      default:
        return 'module';
    }
  }

  static String programIndicatorId({required bool isLead}) {
    return isLead ? 'kra1-b-program-lead' : 'kra1-b-program-contributor';
  }

  static String facultyRoleForProgram({required bool isLead}) {
    return isLead ? 'lead' : 'contributor';
  }

  static bool showCompleteSetQuestion(String materialKind) {
    return materialKind == 'module' || materialKind == 'manual';
  }

  static bool needsContributionPercent(String indicatorId) {
    return CriterionBCatalog.isCoAuthorIndicator(indicatorId);
  }
}
