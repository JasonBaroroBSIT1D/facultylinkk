import 'criterion_c_catalog.dart';

abstract final class CriterionCMapper {
  static String indicatorId({
    required CriterionCServiceKind kind,
    CriterionCResearchType? researchType,
    CriterionCRole? role,
  }) {
    if (kind == CriterionCServiceKind.mentorship) {
      return CriterionCCatalog.mentorIndicator;
    }
    final type = researchType;
    final r = role;
    if (type == null || r == null) {
      throw ArgumentError('Research type and role required');
    }
    return type.indicatorForRole(r);
  }

  static double? previewPoints({
    required CriterionCServiceKind kind,
    CriterionCResearchType? researchType,
    CriterionCRole? role,
  }) {
    if (kind == CriterionCServiceKind.mentorship) {
      return CriterionCCatalog.officialPointsForIndicator(CriterionCCatalog.mentorIndicator);
    }
    final type = researchType;
    final r = role;
    if (type == null || r == null) return null;
    return type.pointsForRole(r);
  }
}
