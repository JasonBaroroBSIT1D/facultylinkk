import 'dart:convert';

/// In-memory holder for the applicable published scoring configuration (Phase C6).
/// Updated by [AppState]; read by catalogs and UI without importing [AppState].
class ScoringConfigurationHolder {
  ScoringConfigurationHolder._();

  static ScoringConfiguration? current;

  static void clear() {
    current = null;
  }
}

/// Parsed Phase C5 `GET /api/faculty/me/scoring-configuration` payload.
class ScoringConfiguration {
  ScoringConfiguration({
    required this.loadedAt,
    this.configuration,
    required this.kraSettings,
    required this.metadata,
    this.rankWeightsPolicy,
    this.message,
  });

  final DateTime loadedAt;
  final ScoringConfigurationHeader? configuration;
  final KraSettingsBlob kraSettings;
  final ScoringConfigurationMetadata metadata;
  final Map<String, dynamic>? rankWeightsPolicy;
  final String? message;

  bool get hasApplicableConfiguration => configuration != null;

  bool get isEvaluationBound =>
      metadata.provenance == 'explicit_id' ||
      metadata.provenance == 'evaluation_period';

  factory ScoringConfiguration.fromApi(Map<String, dynamic> json) {
    final configRaw = json['configuration'];
    ScoringConfigurationHeader? header;
    if (configRaw is Map) {
      header = ScoringConfigurationHeader.fromJson(Map<String, dynamic>.from(configRaw));
    }
    final ksRaw = json['kraSettings'];
    final metaRaw = json['metadata'];
    return ScoringConfiguration(
      loadedAt: DateTime.now(),
      configuration: header,
      kraSettings: KraSettingsBlob.fromJson(
        ksRaw is Map ? Map<String, dynamic>.from(ksRaw) : const {},
      ),
      metadata: ScoringConfigurationMetadata.fromJson(
        metaRaw is Map ? Map<String, dynamic>.from(metaRaw) : const {},
      ),
      rankWeightsPolicy: json['rankWeightsPolicy'] is Map
          ? Map<String, dynamic>.from(json['rankWeightsPolicy'] as Map)
          : null,
      message: json['message'] as String?,
    );
  }

  double? indicatorPoints(String indicatorId) {
    return kraSettings.indicatorPoints(indicatorId);
  }

  double? criterionMax(String criterionId) {
    return kraSettings.criterionMax(criterionId);
  }

  double? kraMax(String kraId) {
    return kraSettings.kraMax(kraId);
  }

  String? criterionLabel(String criterionId) {
    return kraSettings.criterionLabel(criterionId);
  }

  String? kraLabel(String kraId) {
    return kraSettings.kraLabel(kraId);
  }

  bool hasIndicatorPoints(String indicatorId) {
    return indicatorPoints(indicatorId) != null;
  }

  /// Required Criterion C service indicators present in published config.
  bool get criterionCIndicatorsComplete {
    const ids = [
      'kra1-c-adviser-sp',
      'kra1-c-panel-sp',
      'kra1-c-adviser-ut',
      'kra1-c-panel-ut',
      'kra1-c-adviser-mt',
      'kra1-c-panel-mt',
      'kra1-c-adviser-dd',
      'kra1-c-panel-dd',
      'kra1-c-mentor',
    ];
    if (!hasApplicableConfiguration) return false;
    if (criterionMax('kra1-c') == null) return false;
    for (final id in ids) {
      if (!hasIndicatorPoints(id)) return false;
    }
    return true;
  }
}

class ScoringConfigurationHeader {
  ScoringConfigurationHeader({
    required this.id,
    this.status,
    this.guidelineLabel,
    this.publishedAt,
    this.metadata,
  });

  final int id;
  final String? status;
  final String? guidelineLabel;
  final String? publishedAt;
  final Map<String, dynamic>? metadata;

  factory ScoringConfigurationHeader.fromJson(Map<String, dynamic> json) {
    final idRaw = json['id'];
    return ScoringConfigurationHeader(
      id: idRaw is int ? idRaw : int.tryParse('$idRaw') ?? 0,
      status: json['status'] as String?,
      guidelineLabel: json['guidelineLabel'] as String?,
      publishedAt: json['publishedAt'] as String?,
      metadata: json['metadata'] is Map
          ? Map<String, dynamic>.from(json['metadata'] as Map)
          : null,
    );
  }
}

class ScoringConfigurationMetadata {
  ScoringConfigurationMetadata({
    this.configurationId,
    this.version,
    this.guidelineLabel,
    this.effectiveFrom,
    this.effectiveTo,
    this.publishedAt,
    this.provenance,
    this.asOfDate,
    this.scoringVersionProvenance,
  });

  final int? configurationId;
  final dynamic version;
  final String? guidelineLabel;
  final String? effectiveFrom;
  final String? effectiveTo;
  final String? publishedAt;
  final String? provenance;
  final String? asOfDate;
  final String? scoringVersionProvenance;

  factory ScoringConfigurationMetadata.fromJson(Map<String, dynamic> json) {
    return ScoringConfigurationMetadata(
      configurationId: json['configurationId'] is int
          ? json['configurationId'] as int
          : int.tryParse('${json['configurationId']}'),
      version: json['version'],
      guidelineLabel: json['guidelineLabel'] as String?,
      effectiveFrom: json['effectiveFrom'] as String?,
      effectiveTo: json['effectiveTo'] as String?,
      publishedAt: json['publishedAt'] as String?,
      provenance: json['provenance'] as String?,
      asOfDate: json['asOfDate'] as String?,
      scoringVersionProvenance: json['scoringVersionProvenance'] as String?,
    );
  }

  String get versionLabel {
    if (version == null) return '—';
    return version.toString();
  }
}

class KraSettingsBlob {
  KraSettingsBlob({
    required this.kras,
    required this.criteria,
    required this.indicators,
  });

  final Map<String, Map<String, dynamic>> kras;
  final Map<String, Map<String, dynamic>> criteria;
  final Map<String, Map<String, dynamic>> indicators;

  factory KraSettingsBlob.fromJson(Map<String, dynamic> json) {
    return KraSettingsBlob(
      kras: _mapOfMaps(json['kras']),
      criteria: _mapOfMaps(json['criteria']),
      indicators: _mapOfMaps(json['indicators']),
    );
  }

  static Map<String, Map<String, dynamic>> _mapOfMaps(Object? raw) {
    if (raw is! Map) return {};
    final out = <String, Map<String, dynamic>>{};
    raw.forEach((key, value) {
      if (value is Map) {
        out['$key'] = Map<String, dynamic>.from(value);
      }
    });
    return out;
  }

  double? _num(dynamic raw) {
    if (raw is num) return raw.toDouble();
    if (raw is String) return double.tryParse(raw);
    return null;
  }

  double? indicatorPoints(String indicatorId) {
    final entry = indicators[indicatorId];
    if (entry == null) return null;
    return _num(entry['points']) ?? _num(entry['maxPoints']);
  }

  double? criterionMax(String criterionId) {
    final entry = criteria[criterionId];
    if (entry == null) return null;
    return _num(entry['maxPoints']);
  }

  String? criterionLabel(String criterionId) {
    final entry = criteria[criterionId];
    if (entry == null) return null;
    return (entry['name'] ?? entry['label']) as String?;
  }

  double? kraMax(String kraId) {
    final entry = kras[kraId];
    if (entry != null) {
      final max = _num(entry['maxPoints']);
      if (max != null) return max;
    }
    return null;
  }

  String? kraLabel(String kraId) {
    final entry = kras[kraId];
    if (entry == null) return null;
    return (entry['name'] ?? entry['label']) as String?;
  }
}

/// Sample JSON for unit tests (matches Phase C5 contract).
Map<String, dynamic> scoringConfigurationFixture() {
  return jsonDecode(r'''
{
  "configuration": {
    "id": 6,
    "status": "published",
    "guidelineLabel": "DBM–CHED Joint Circular No. 01, s. 2026",
    "publishedAt": "2024-01-01T00:00:00+00:00",
    "metadata": {"version": 5, "effectiveFrom": "2023-08-01"}
  },
  "kraSettings": {
    "kras": {"kra1": {"maxPoints": 100}, "kra2": {"maxPoints": 100}},
    "criteria": {"kra1-c": {"maxPoints": 10, "name": "Criterion C"}},
    "indicators": {
      "kra1-c-adviser-sp": {"points": 3},
      "kra1-c-panel-sp": {"points": 1},
      "kra1-c-adviser-ut": {"points": 5},
      "kra1-c-panel-ut": {"points": 1},
      "kra1-c-adviser-mt": {"points": 8},
      "kra1-c-panel-mt": {"points": 2},
      "kra1-c-adviser-dd": {"points": 10},
      "kra1-c-panel-dd": {"points": 2},
      "kra1-c-mentor": {"points": 3}
    }
  },
  "metadata": {
    "configurationId": 6,
    "version": 5,
    "effectiveFrom": "2023-08-01",
    "provenance": "applicable_as_of",
    "asOfDate": "2026-11-03",
    "scoringVersionProvenance": "applicable_as_of"
  },
  "rankWeightsPolicy": {
    "source": "table_22_defaults_in_engine",
    "publishedRankWeightsPresent": false
  }
}
''') as Map<String, dynamic>;
}
