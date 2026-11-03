import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// One UI group covering one or more official indicators (sole/co variants).
class Kra2AccomplishmentGroup {
  const Kra2AccomplishmentGroup({
    required this.key,
    required this.title,
    required this.description,
    required this.icon,
    required this.indicatorIds,
  });

  final String key;
  final String title;
  final String description;
  final IconData icon;
  final List<String> indicatorIds;

  bool get needsAuthorshipChoice => indicatorIds.length > 1;

  String? get soleIndicatorId {
    for (final id in indicatorIds) {
      if (id.endsWith('-sole') || Kra2Catalog.contributionMode(id) == 'sole') return id;
    }
    return indicatorIds.length == 1 ? indicatorIds.first : null;
  }

  String? get coIndicatorId {
    for (final id in indicatorIds) {
      if (id.endsWith('-co') || Kra2Catalog.contributionMode(id) == 'declared') return id;
    }
    return null;
  }
}

/// KRA II indicator catalog (synced from backend `kra2_indicators.json`).
abstract final class Kra2Catalog {
  static const criterionA = 'kra2-a';
  static const criterionB = 'kra2-b';
  static const criterionC = 'kra2-c';

  static List<Map<String, dynamic>> _indicators = const [];
  static bool _loaded = false;
  static Future<void>? _loadFuture;

  /// Call from `main()` so first KRA II screen does not wait on asset I/O.
  static Future<void> preload() => ensureLoaded();

  static Future<void> ensureLoaded() {
    if (_loaded) return Future.value();
    return _loadFuture ??= _loadFromAssets();
  }

  static Future<void> _loadFromAssets() async {
    final raw = await rootBundle.loadString('assets/kra2_indicators.json');
    final decoded = jsonDecode(raw);
    if (decoded is Map && decoded['indicators'] is List) {
      _indicators = (decoded['indicators'] as List)
          .whereType<Map>()
          .map((e) => Map<String, dynamic>.from(e))
          .toList();
    }
    _loaded = true;
  }

  static List<Map<String, dynamic>> indicatorsFor(String criterionId) {
    final cid = criterionId.trim();
    return _indicators.where((r) => r['criterionId'] == cid).toList();
  }

  static Map<String, dynamic>? indicatorById(String? indicatorId) {
    final id = (indicatorId ?? '').trim();
    for (final row in _indicators) {
      if (row['id'] == id) return row;
    }
    return null;
  }

  static String mainHubCardTitle(String criterionId) {
    switch (criterionId) {
      case criterionA:
        return 'Publications';
      case criterionB:
        return 'Inventions';
      case criterionC:
        return 'Creative Works & Research Impact';
      default:
        return 'KRA II';
    }
  }

  static String mainHubCardDescription(String criterionId) {
    switch (criterionId) {
      case criterionA:
        return 'Books, research papers, and journal articles';
      case criterionB:
        return 'Patents, new ideas, and useful inventions';
      case criterionC:
        return 'Creative works, performances, and other recognized research contributions';
      default:
        return '';
    }
  }

  static String criterionBadge(String criterionId) {
    switch (criterionId) {
      case criterionA:
        return 'Criterion A';
      case criterionB:
        return 'Criterion B';
      case criterionC:
        return 'Criterion C';
      default:
        return '';
    }
  }

  static String criterionTitle(String criterionId) {
    return mainHubCardTitle(criterionId);
  }

  static String criterionHubSubtitle(String criterionId) {
    switch (criterionId) {
      case criterionA:
        return 'What would you like to add?';
      case criterionB:
        return 'What would you like to add?';
      case criterionC:
        return 'What would you like to add?';
      default:
        return 'Choose an accomplishment type to begin';
    }
  }

  static IconData criterionIcon(String criterionId) {
    switch (criterionId) {
      case criterionA:
        return Icons.menu_book_outlined;
      case criterionB:
        return Icons.lightbulb_outline;
      case criterionC:
        return Icons.emoji_events_outlined;
      default:
        return Icons.folder_outlined;
    }
  }

  static Color criterionIconBackground(String criterionId) {
    switch (criterionId) {
      case criterionA:
        return const Color(0xFFE8F0FE);
      case criterionB:
        return const Color(0xFFFFF4E5);
      case criterionC:
        return const Color(0xFFECFDF5);
      default:
        return const Color(0xFFEEF2F6);
    }
  }

  /// Stable group key for UI clustering (does not change official indicator IDs).
  static String groupKeyForIndicator(String indicatorId) {
    final parts = indicatorId.split('-');
    if (parts.length < 3) return indicatorId;
    final tail = parts.sublist(2);
    if (tail.isNotEmpty && (tail.last == 'sole' || tail.last == 'co')) {
      tail.removeLast();
    }
    return tail.join('-');
  }

  static List<Kra2AccomplishmentGroup> accomplishmentGroups(String criterionId) {
    final rows = indicatorsFor(criterionId);
    final byKey = <String, List<String>>{};
    for (final row in rows) {
      final id = row['id']?.toString() ?? '';
      if (id.isEmpty) continue;
      final key = groupKeyForIndicator(id);
      byKey.putIfAbsent(key, () => []).add(id);
    }
    final keys = byKey.keys.toList()..sort(_groupSortOrder);
    return keys.map((key) {
      final ids = byKey[key]!..sort();
      final meta = _groupMeta(key, criterionId);
      return Kra2AccomplishmentGroup(
        key: key,
        title: meta.$1,
        description: meta.$2,
        icon: meta.$3,
        indicatorIds: ids,
      );
    }).toList();
  }

  static Kra2AccomplishmentGroup? groupByKey(String criterionId, String groupKey) {
    for (final g in accomplishmentGroups(criterionId)) {
      if (g.key == groupKey) return g;
    }
    return null;
  }

  static int _groupSortOrder(String a, String b) {
    const order = [
      'book',
      'chapter',
      'journal',
      'monograph',
      'translation',
      'cite',
      'patent-a',
      'patent-p',
      'patent-g',
      'comm-local',
      'comm-intl',
      'um',
      'id',
      'sw-new',
      'sw-upd',
      'variety',
    ];
    final ia = order.indexOf(a);
    final ib = order.indexOf(b);
    if (ia >= 0 && ib >= 0) return ia.compareTo(ib);
    if (ia >= 0) return -1;
    if (ib >= 0) return 1;
    return a.compareTo(b);
  }

  static (String, String, IconData) _groupMeta(String key, String criterionId) {
    const meta = <String, (String, String, IconData)>{
      'book': ('Book', 'A book you wrote or co-wrote.', Icons.auto_stories_outlined),
      'chapter': ('Book chapter', 'A chapter in an edited academic book.', Icons.library_books_outlined),
      'journal': ('Journal article', 'A research paper published in a journal.', Icons.article_outlined),
      'monograph': ('Monograph', 'A scholarly monograph you authored.', Icons.menu_book),
      'translation': ('Translation', 'A translated academic work.', Icons.translate),
      'cite': ('Citation received', 'Your work was cited by another publication.', Icons.format_quote),
      'patent-a': ('Patent application', 'Your invention was accepted or filed with the patent office.', Icons.gavel_outlined),
      'patent-p': ('Patent publication', 'Your patent application was published.', Icons.hourglass_top_outlined),
      'patent-g': ('Patent certificate', 'Your patent was granted.', Icons.verified_outlined),
      'comm-local': ('Commercialization (local)', 'Your invention was commercialized locally.', Icons.storefront_outlined),
      'comm-intl': ('Commercialization (international)', 'Your invention was commercialized abroad.', Icons.public_outlined),
      'um': ('Utility model', 'A registered utility model.', Icons.build_outlined),
      'id': ('Industrial design', 'A registered industrial design.', Icons.design_services_outlined),
      'sw-new': ('New software / algorithm', 'Original software or algorithm you developed.', Icons.code_outlined),
      'sw-upd': ('Updated software / algorithm', 'A major update to software or an algorithm.', Icons.system_update_alt_outlined),
      'variety': ('New plant variety', 'A registered new plant variety.', Icons.eco_outlined),
      'music-comp': ('Musical composition', 'An original musical composition.', Icons.music_note_outlined),
      'music-arr': ('Musical arrangement', 'An arrangement of music you created.', Icons.queue_music_outlined),
      'music-perf': ('Musical performance', 'A documented musical performance.', Icons.piano_outlined),
      'conducting': ('Conducting', 'Conducting a musical performance.', Icons.leaderboard_outlined),
      'music-prod': ('Music production', 'Producing a musical recording or work.', Icons.album_outlined),
      'choreo': ('Choreography', 'Original dance choreography.', Icons.directions_run_outlined),
      'dance-perf': ('Dance performance', 'A documented dance performance.', Icons.accessibility_new_outlined),
      'playwright': ('Play / script', 'A play or theatrical script you wrote.', Icons.theater_comedy_outlined),
      'directing': ('Stage or film directing', 'Directing a stage or film production.', Icons.movie_creation_outlined),
      'acting': ('Acting performance', 'A lead or supporting acting performance.', Icons.person_outline),
      'prod-design': ('Production design', 'Design for stage, film, or media production.', Icons.palette_outlined),
      'visual': ('Visual artwork', 'Visual art such as painting or sculpture.', Icons.brush_outlined),
      'arch-design': ('Architectural design', 'An architectural or built-environment design.', Icons.architecture_outlined),
      'film': ('Film or audiovisual work', 'A film or audiovisual creative work.', Icons.videocam_outlined),
      'novel': ('Novel or long fiction', 'A novel or long-form literary work.', Icons.import_contacts_outlined),
      'story': ('Short story', 'A published short story.', Icons.short_text_outlined),
      'poetry': ('Poetry', 'Published poetry.', Icons.format_italic_outlined),
      'essay': ('Essay or literary work', 'An essay or similar literary contribution.', Icons.description_outlined),
    };
    final hit = meta[key];
    if (hit != null) return hit;
    String? sampleId;
    for (final row in indicatorsFor(criterionId)) {
      if (groupKeyForIndicator(row['id']?.toString() ?? '') == key) {
        sampleId = row['id']?.toString();
        break;
      }
    }
    final sample = indicatorById(sampleId);
    final name = (sample?['name'] ?? key).toString();
    return (name, userFacingSummary(sampleId ?? ''), Icons.task_outlined);
  }

  static String workflowFamily(String indicatorId) {
    final parts = indicatorId.split('-');
    final familyToken = parts.length >= 3 ? parts[2] : '';
    final crit = parts.length >= 2 ? '${parts[0]}-${parts[1]}' : '';
    if (familyToken == 'cite') return 'citation_impact';
    if (crit == criterionB) {
      if (familyToken.startsWith('comm')) return 'commercialization';
      return 'invention_ip';
    }
    if (crit == criterionC) {
      const perf = {'music-perf', 'dance-perf', 'conducting', 'acting', 'directing'};
      if (perf.contains(familyToken) || indicatorId.contains('-perf')) {
        return 'performance_work';
      }
      return 'creative_work';
    }
    return 'publication_output';
  }

  static String contributionMode(String indicatorId) {
    final row = indicatorById(indicatorId);
    final c = (row?['contribution'] ?? '').toString().trim().toLowerCase();
    if (c == 'declared' || c == 'sole' || c == 'not-applicable') return c;
    final parts = indicatorId.split('-');
    if (parts.isNotEmpty && parts.last == 'co') return 'declared';
    if (parts.isNotEmpty && parts.last == 'sole') return 'sole';
    return 'not-applicable';
  }

  static List<String> metadataFieldIds(String indicatorId) {
    final family = workflowFamily(indicatorId);
    const base = ['outputTitle', 'authorsLine', 'outputVenue', 'publicationDate'];
    if (family == 'citation_impact') {
      return ['outputTitle', 'citationContext', 'publicationDate'];
    }
    if (family == 'invention_ip') {
      final fields = [
        'outputTitle',
        'registrationNumber',
        'registrationDate',
        'authorsLine',
        'outputVenue',
      ];
      if (contributionMode(indicatorId) == 'declared') {
        fields.add('declaredContributionPercent');
      }
      return fields;
    }
    if (family == 'commercialization') {
      return ['outputTitle', 'outputVenue', 'publicationDate', 'authorsLine'];
    }
    if (contributionMode(indicatorId) == 'declared') {
      return [...base, 'declaredContributionPercent'];
    }
    return base;
  }

  static String metadataLabel(String fieldId, [String? indicatorId]) {
    if (indicatorId != null && indicatorId.isNotEmpty) {
      return metadataLabelForIndicator(fieldId, indicatorId);
    }
    return _genericMetadataLabel(fieldId);
  }

  static String metadataLabelForIndicator(String fieldId, String indicatorId) {
    final family = workflowFamily(indicatorId);
    switch (fieldId) {
      case 'outputTitle':
        if (family == 'invention_ip') return 'Name of your invention';
        if (family == 'citation_impact') return 'Title of your published work';
        if (family == 'creative_work' || family == 'performance_work') {
          return 'Title of your work';
        }
        return 'Title of your article';
      case 'authorsLine':
        if (family == 'invention_ip') return 'Inventor names';
        if (family == 'creative_work' || family == 'performance_work') {
          return 'Creator names';
        }
        return 'Author names';
      case 'outputVenue':
        if (family == 'invention_ip') return 'Patent office or registry';
        if (family == 'commercialization') return 'Company or market';
        return 'Journal name';
      case 'publicationDate':
        if (family == 'invention_ip') return 'Patent date';
        if (family == 'creative_work' || family == 'performance_work') {
          return 'Date of the work';
        }
        return 'Publication date';
      case 'publicationReference':
        return 'DOI (if you have one)';
      case 'registrationNumber':
        return 'Patent or registration number';
      case 'registrationDate':
        return 'Filing or registration date';
      case 'citationContext':
        return 'Where your work was cited';
      case 'declaredContributionPercent':
        return 'Your share of the work (%)';
      default:
        return _genericMetadataLabel(fieldId);
    }
  }

  static String _genericMetadataLabel(String fieldId) {
    switch (fieldId) {
      case 'outputTitle':
        return 'Title';
      case 'authorsLine':
        return 'Names';
      case 'outputVenue':
        return 'Journal or venue';
      case 'publicationDate':
        return 'Date';
      case 'publicationReference':
        return 'DOI (optional)';
      case 'registrationNumber':
        return 'Registration number';
      case 'registrationDate':
        return 'Registration date';
      case 'citationContext':
        return 'Citation details';
      case 'declaredContributionPercent':
        return 'Your share (%)';
      default:
        return fieldId.replaceAll(RegExp(r'([A-Z])'), ' ').trim();
    }
  }

  /// Plain name for lists (not raw upload filenames).
  static String accomplishmentGroupTitle(String indicatorId) {
    final id = indicatorId.trim();
    if (id.isEmpty) return 'Your accomplishment';
    final crit = indicatorById(id)?['criterionId']?.toString() ?? criterionA;
    return _groupMeta(groupKeyForIndicator(id), crit).$1;
  }

  static String friendlyUploadTitle(String indicatorId) {
    return accomplishmentGroupTitle(indicatorId);
  }

  static String submissionListTitle({
    required String? indicatorId,
    String? outputTitle,
  }) {
    final type = accomplishmentGroupTitle(indicatorId ?? '');
    final raw = (outputTitle ?? '').trim();
    if (raw.isEmpty || _looksLikeUploadFilename(raw) || _looksLikePlaceholderTitle(raw, indicatorId)) {
      return type;
    }
    return raw;
  }

  static bool _looksLikeUploadFilename(String value) {
    final t = value.trim();
    if (t.isEmpty) return false;
    if (RegExp(r'^KRA2[_\-]', caseSensitive: false).hasMatch(t)) return true;
    if (RegExp(r'\.pdf$', caseSensitive: false).hasMatch(t)) return true;
    if (RegExp(r'_\d{2}_', caseSensitive: false).hasMatch(t) && t.contains('_')) return true;
    return false;
  }

  static bool _looksLikePlaceholderTitle(String raw, String? indicatorId) {
    if (indicatorId == null || indicatorId.isEmpty) return false;
    final lower = raw.toLowerCase();
    if (lower == userFacingTitle(indicatorId).toLowerCase()) return true;
    if (lower == accomplishmentGroupTitle(indicatorId).toLowerCase()) return true;
    final row = indicatorById(indicatorId);
    final name = (row?['name'] ?? '').toString().toLowerCase();
    return name.isNotEmpty && lower == name;
  }

  /// Advisory hint when filename suggests a different accomplishment type than selected.
  static String? documentTypeMismatchHint(String indicatorId, String fileName) {
    final name = fileName.toLowerCase();
    if (name.isEmpty) return null;
    final key = groupKeyForIndicator(indicatorId);
    final mentionsGrant = name.contains('grant') || name.contains('certificate');
    final mentionsAccept = name.contains('accept');
    final mentionsPublication = name.contains('publication');
    final mentionsApplication = name.contains('application') || name.contains('filed');

    if (key == 'patent-a' && mentionsGrant && !mentionsAccept) {
      return 'This file looks like a patent certificate. You chose a patent application. Go back and pick "Patent certificate" if that is correct.';
    }
    if (key == 'patent-g' && mentionsAccept && !mentionsGrant) {
      return 'This file looks like an acceptance notice, not a grant certificate. Check that you picked the right accomplishment type.';
    }
    if (key == 'patent-a' && mentionsPublication && !mentionsApplication) {
      return 'This file looks like a publication notice. You may need "Patent publication" instead of "Patent application".';
    }
    if (key == 'patent-p' && mentionsGrant) {
      return 'This file looks like a grant certificate. You chose patent publication — pick "Patent certificate" if the patent was granted.';
    }
    return null;
  }

  static String primaryUploadLabel(String indicatorId) {
    switch (workflowFamily(indicatorId)) {
      case 'invention_ip':
        return 'Use a PDF from the patent office that matches this accomplishment.';
      case 'citation_impact':
        return 'Use a PDF that shows your work was cited.';
      case 'commercialization':
        return 'Use a PDF that shows your invention was commercialized.';
      case 'creative_work':
      case 'performance_work':
        return 'Use a PDF that shows your creative or performance work.';
      default:
        return 'Use a PDF of your published article or book.';
    }
  }

  static String slotLabel(String slotId) {
    switch (slotId) {
      case 'primary_output':
        return 'Your PDF';
      case 'contribution_certificate':
        return 'Shared authorship certificate';
      default:
        return slotId.replaceAll('_', ' ');
    }
  }

  static bool requiresContributionCertificate(String indicatorId) {
    return contributionMode(indicatorId) == 'declared';
  }

  static String userFacingTitle(String indicatorId) {
    return (indicatorById(indicatorId)?['name'] ?? indicatorId).toString();
  }

  static String userFacingSummary(String indicatorId) {
    final hints = indicatorById(indicatorId)?['evidenceHints'];
    if (hints is List && hints.isNotEmpty) {
      return hints.first.toString();
    }
    return primaryUploadLabel(indicatorId);
  }
}
