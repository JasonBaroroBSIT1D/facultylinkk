import '../data/app_state.dart';
import '../models/enums.dart';
import '../models/models.dart';

enum SimulationRequirementAction { documents, assessment }

class FriendlyRequirementItem {
  const FriendlyRequirementItem({
    required this.title,
    required this.subtitle,
    required this.isComplete,
    this.actionLabel,
    this.action = SimulationRequirementAction.documents,
  });

  final String title;
  final String subtitle;
  final bool isComplete;
  final String? actionLabel;
  final SimulationRequirementAction action;
}

abstract final class SimulationFriendlyRequirements {
  static List<FriendlyRequirementItem> fromSimulation(
    RankSimulation sim,
    AppState state,
  ) {
    final items = <FriendlyRequirementItem>[];
    final seen = <String>{};

    for (final raw in sim.missingRequirements) {
      final id = (raw['id'] as String?) ?? '';
      final category = (raw['category'] as String?) ?? '';
      if (category == 'configuration') continue;
      if (id == 'target_rank') continue;
      if (seen.contains(id)) continue;
      seen.add(id);

      final friendly = _friendly(raw, state);
      if (friendly != null) items.add(friendly);
    }

    for (final row in sim.readinessChecklist) {
      if (row['applicable'] != true || row['completed'] == true) continue;
      final id = (row['id'] as String?) ?? '';
      if (seen.contains('prep_$id')) continue;
      seen.add('prep_$id');
      final label = (row['label'] as String?) ?? 'Complete this requirement';
      items.add(
        FriendlyRequirementItem(
          title: _shortPrepTitle(label),
          subtitle: 'This item is not complete yet.',
          isComplete: false,
          actionLabel: _actionForPrepId(id),
          action: _actionTypeForPrepId(id),
        ),
      );
    }

    if (items.isEmpty && sim.areasToImprove.isNotEmpty) {
      final first = sim.areasToImprove.first;
      items.add(
        FriendlyRequirementItem(
          title: 'Strengthen ${first.kra.shortLabel}',
          subtitle: first.guidance,
          isComplete: false,
          actionLabel: 'Upload evidence',
          action: SimulationRequirementAction.documents,
        ),
      );
    }

    return items;
  }

  static FriendlyRequirementItem? _friendly(
    Map<String, dynamic> raw,
    AppState state,
  ) {
    final id = (raw['id'] as String?) ?? '';
    final category = (raw['category'] as String?) ?? '';
    final text = (raw['text'] as String?) ?? '';

    if (id.startsWith('missing_set') || text.startsWith('SET:')) {
      return _teachingItem('Teaching evaluation (SET)', 'set', state, text);
    }
    if (id.startsWith('missing_sef') || text.startsWith('SEF:')) {
      return _teachingItem('Supervisor evaluation (SEF)', 'sef', state, text);
    }
    if (id.startsWith('pending_set') || id.startsWith('pending_sef')) {
      final kind = id.contains('sef') ? 'SEF' : 'SET';
      return FriendlyRequirementItem(
        title: 'Wait for reviewer verification',
        subtitle: '$kind records are uploaded but not fully verified yet.',
        isComplete: false,
        actionLabel: 'View documents',
        action: SimulationRequirementAction.documents,
      );
    }
    if (id == 'no_kra1') {
      return _kraItem(KraType.instruction, state);
    }
    if (id == 'no_kra2') {
      return _kraItem(KraType.research, state);
    }
    if (id == 'no_kra3') {
      return _kraItem(KraType.extension, state);
    }
    if (id == 'no_kra4') {
      return _kraItem(KraType.professionalDevelopment, state);
    }
    if (category == 'review') {
      return FriendlyRequirementItem(
        title: 'Wait for reviewer verification',
        subtitle: _plain(text),
        isComplete: false,
        actionLabel: 'View documents',
        action: SimulationRequirementAction.documents,
      );
    }
    if (category == 'kra') {
      return FriendlyRequirementItem(
        title: 'Upload supporting documents',
        subtitle: _plain(text),
        isComplete: false,
        actionLabel: 'Open documents',
        action: SimulationRequirementAction.documents,
      );
    }
    return FriendlyRequirementItem(
      title: 'Complete a preparation item',
      subtitle: _plain(text),
      isComplete: false,
      actionLabel: 'Continue',
      action: SimulationRequirementAction.documents,
    );
  }

  static FriendlyRequirementItem _kraItem(KraType kra, AppState state) {
    return FriendlyRequirementItem(
      title: 'Upload ${kra.shortLabel} evidence',
      subtitle: 'Add documents so this KRA can be scored.',
      isComplete: false,
      actionLabel: 'Upload',
      action: SimulationRequirementAction.documents,
    );
  }

  static FriendlyRequirementItem _teachingItem(
    String title,
    String blockKey,
    AppState state,
    String fallbackText,
  ) {
    final te = state.criterionA;
    String subtitle = _plain(fallbackText);
    if (te != null) {
      final block = te[blockKey];
      if (block is Map) {
        final cov = block['coverageSummary'];
        if (cov is Map) {
          final required = cov['requiredPeriods'];
          final included = cov['includedPeriods'] ?? cov['acceptedPeriods'] ?? 0;
          if (required is num && required > 0) {
            subtitle =
                '$title: ${included.toString()} of ${required.toString()} semesters completed.';
          }
        }
      }
    }
    return FriendlyRequirementItem(
      title: 'Complete teaching effectiveness records',
      subtitle: subtitle,
      isComplete: false,
      actionLabel: 'Open assessment',
      action: SimulationRequirementAction.assessment,
    );
  }

  static String _plain(String text) {
    return text
        .replaceAll(RegExp(r'\s+'), ' ')
        .replaceAll('divisor', 'required total')
        .trim();
  }

  static String _shortPrepTitle(String label) {
    if (label.length <= 48) return label;
    return '${label.substring(0, 45)}…';
  }

  static String? _actionForPrepId(String id) {
    if (id == 'set' || id == 'sef' || id == 'kra1') return 'Open assessment';
    return 'Open documents';
  }

  static SimulationRequirementAction _actionTypeForPrepId(String id) {
    if (id == 'set' || id == 'sef' || id == 'kra1') {
      return SimulationRequirementAction.assessment;
    }
    return SimulationRequirementAction.documents;
  }
}
