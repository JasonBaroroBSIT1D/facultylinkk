// KRA I Criterion C — structure + dynamic points from published scoring configuration.
import 'scoring_configuration.dart';

abstract final class CriterionCCatalog {
  static const criterionId = 'kra1-c';
  static const mentorIndicator = 'kra1-c-mentor';

  /// Annex A reference fallbacks — used only when no applicable published config is loaded (mock/offline tests).
  static const double _annexMaxPoints = 10.0;
  static const Map<String, double> _annexIndicatorPoints = {
    'kra1-c-adviser-sp': 3,
    'kra1-c-panel-sp': 1,
    'kra1-c-adviser-ut': 5,
    'kra1-c-panel-ut': 1,
    'kra1-c-adviser-mt': 8,
    'kra1-c-panel-mt': 2,
    'kra1-c-adviser-dd': 10,
    'kra1-c-panel-dd': 2,
    'kra1-c-mentor': 3,
  };

  static ScoringConfiguration? get _config => ScoringConfigurationHolder.current;

  static bool get usesPublishedConfiguration =>
      _config?.hasApplicableConfiguration == true;

  static bool get configurationIncompleteLive =>
      _config != null && !_config!.hasApplicableConfiguration;

  static double get maxPoints {
    final cfg = _config;
    if (cfg?.hasApplicableConfiguration == true) {
      return cfg!.criterionMax(criterionId) ?? _annexMaxPoints;
    }
    return _annexMaxPoints;
  }

  static double get mentorshipPoints =>
      officialPointsForIndicator(mentorIndicator) ?? _annexIndicatorPoints[mentorIndicator]!;

  static const researchTypes = <CriterionCResearchType>[
    CriterionCResearchType(
      id: 'sp_cp',
      label: 'Special Project / Capstone Project',
      adviserIndicator: 'kra1-c-adviser-sp',
      panelIndicator: 'kra1-c-panel-sp',
    ),
    CriterionCResearchType(
      id: 'ut',
      label: 'Undergraduate Thesis',
      adviserIndicator: 'kra1-c-adviser-ut',
      panelIndicator: 'kra1-c-panel-ut',
    ),
    CriterionCResearchType(
      id: 'mt',
      label: "Master's Thesis",
      adviserIndicator: 'kra1-c-adviser-mt',
      panelIndicator: 'kra1-c-panel-mt',
    ),
    CriterionCResearchType(
      id: 'dd',
      label: 'Doctoral Dissertation',
      adviserIndicator: 'kra1-c-adviser-dd',
      panelIndicator: 'kra1-c-panel-dd',
    ),
  ];

  static bool isCriterionCIndicator(String? indicatorId) {
    if (indicatorId == null || indicatorId.isEmpty) return false;
    return indicatorId.startsWith('kra1-c-');
  }

  static const slotLabels = <String, String>{
    'approval_sheet': 'Signed approval sheet',
    'rrpa_copc': 'RRPA or COPC for the academic program',
    'mentor_designation': 'Official mentor/coach designation',
    'award_certificate': 'Award, certificate, or photo of major prize',
    'competition_mechanics': 'Competition mechanics (major awards/winners)',
    'awarding_organization': 'Award-giving organization profile',
  };

  static String slotLabel(String slotId) =>
      slotLabels[slotId] ?? slotId.replaceAll('_', ' ');

  static List<String> requiredSlots({required bool mentorship}) {
    if (mentorship) {
      return [
        'mentor_designation',
        'award_certificate',
        'competition_mechanics',
        'awarding_organization',
      ];
    }
    return ['approval_sheet', 'rrpa_copc'];
  }

  /// Published indicator points when configuration is applicable; Annex fallback for mock/tests only.
  static double? officialPointsForIndicator(String indicatorId) {
    final cfg = _config;
    if (cfg?.hasApplicableConfiguration == true) {
      return cfg!.indicatorPoints(indicatorId);
    }
    if (cfg != null && !cfg.hasApplicableConfiguration) {
      return null;
    }
    return _annexIndicatorPoints[indicatorId];
  }

  static bool get criterionCScoringReady {
    final cfg = _config;
    if (cfg == null) return true;
    if (!cfg.hasApplicableConfiguration) return false;
    return cfg.criterionCIndicatorsComplete;
  }
}

class CriterionCResearchType {
  const CriterionCResearchType({
    required this.id,
    required this.label,
    required this.adviserIndicator,
    required this.panelIndicator,
  });

  final String id;
  final String label;
  final String adviserIndicator;
  final String panelIndicator;

  String indicatorForRole(CriterionCRole role) =>
      role == CriterionCRole.adviser ? adviserIndicator : panelIndicator;

  double? pointsForRole(CriterionCRole role) =>
      CriterionCCatalog.officialPointsForIndicator(indicatorForRole(role));

  double get adviserPoints => pointsForRole(CriterionCRole.adviser) ?? 0;

  double get panelPoints => pointsForRole(CriterionCRole.panel) ?? 0;
}

enum CriterionCServiceKind { research, mentorship }

enum CriterionCRole { adviser, panel }
