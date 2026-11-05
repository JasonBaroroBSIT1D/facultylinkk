/// Display-only mirror of backend Table 3.1 and rank ladder (verified toggle UI).
abstract final class SimulationDisplayRules {
  static const scoreBrackets = <({double min, double max, int increment})>[
    (min: 41, max: 50, increment: 1),
    (min: 51, max: 60, increment: 2),
    (min: 61, max: 70, increment: 3),
    (min: 71, max: 80, increment: 4),
    (min: 81, max: 90, increment: 5),
    (min: 91, max: 100, increment: 6),
  ];

  static const rankLadder = <String>[
    'Instructor I',
    'Instructor II',
    'Instructor III',
    'Assistant Professor I',
    'Assistant Professor II',
    'Assistant Professor III',
    'Assistant Professor IV',
    'Associate Professor I',
    'Associate Professor II',
    'Associate Professor III',
    'Associate Professor IV',
    'Associate Professor V',
    'Professor I',
    'Professor II',
    'Professor III',
    'Professor IV',
    'Professor V',
    'Professor VI',
    'College/University Professor',
  ];

  static int subrankIncrementForScore(double? score) {
    if (score == null) return 0;
    for (final row in scoreBrackets) {
      if (score >= row.min && score <= row.max) return row.increment;
    }
    return 0;
  }

  static String? possibleRankAfterIncrement(String currentRank, int increment) {
    if (increment <= 0) return null;
    final normalized = currentRank.trim().toLowerCase();
    var idx = -1;
    for (var i = 0; i < rankLadder.length; i++) {
      if (rankLadder[i].toLowerCase() == normalized) {
        idx = i;
        break;
      }
    }
    if (idx < 0) {
      final compact = normalized.replaceAll('asst.', 'assistant').replaceAll('  ', ' ');
      for (var i = 0; i < rankLadder.length; i++) {
        if (rankLadder[i].toLowerCase() == compact) {
          idx = i;
          break;
        }
      }
    }
    if (idx < 0) return null;

    var cursor = idx;
    var remaining = increment;
    while (remaining > 0 && cursor < rankLadder.length - 1) {
      final fromCat = _category(rankLadder[cursor]);
      final toCat = _category(rankLadder[cursor + 1]);
      if (fromCat != toCat) break;
      cursor++;
      remaining--;
    }
    return cursor == idx ? null : rankLadder[cursor];
  }

  static String _category(String rank) {
    if (rank.startsWith('Instructor')) return 'Instructor';
    if (rank.startsWith('Assistant')) return 'Assistant Professor';
    if (rank.startsWith('Associate')) return 'Associate Professor';
    if (rank.startsWith('Professor')) return 'Professor';
    return 'College/University Professor';
  }
}
