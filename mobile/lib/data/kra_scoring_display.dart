import 'scoring_configuration.dart';

/// Display-only KRA/criterion caps and labels from published configuration (Phase C6).
abstract final class KraScoringDisplay {
  static KraSettingsBlob? get _settings => ScoringConfigurationHolder.current?.kraSettings;

  static double? kraMaxPoints(String kraId) {
    return ScoringConfigurationHolder.current?.kraMax(kraId) ?? _settings?.kraMax(kraId);
  }

  static double? criterionMaxPoints(String criterionId) {
    return ScoringConfigurationHolder.current?.criterionMax(criterionId) ??
        _settings?.criterionMax(criterionId);
  }

  static String? criterionDisplayName(String criterionId, {String? fallback}) {
    return ScoringConfigurationHolder.current?.criterionLabel(criterionId) ??
        _settings?.criterionLabel(criterionId) ??
        fallback;
  }

  static String formatMaxLabel(double? max) {
    if (max == null) return '';
    final rounded = max == max.roundToDouble() ? max.toInt().toString() : max.toStringAsFixed(1);
    return ' (max $rounded pts)';
  }
}
