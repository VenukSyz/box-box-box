#!/usr/bin/env python3
"""
Box Box Box -- F1 Race Simulator
Reads race JSON from stdin, writes finishing positions JSON to stdout.

Model (B-residual absolute lap number):
  score(d) = n_pits * P + L_S * oS + L_H * oH
           + SumN_S * dS + SumN_H * dH

Where:
  L_C    = total laps on compound C
  SumN_C = sum of absolute race lap numbers for stints on C
  Br     = B - round(2*B)/2  (B-residual: distance from nearest 0.5 multiple)
  dS     = dS_base + dS_Br * Br  (effective degradation diff SOFT vs MEDIUM)
  dH     = dH_base + dH_Br * Br  (effective degradation diff HARD vs MEDIUM)
  oS     = SOFT per-lap offset (negative: SOFT is faster)
  oH     = HARD per-lap offset (positive: HARD is slower)
  MEDIUM offset = 0 (baseline reference)
  Ties broken by starting grid position (lower grid wins)
"""

import json, sys

# Best parameters found: 19/100 test accuracy
PARAMS = {
    'oS': -7.9,
    'oH': 6.3,
    'dS_base': 0.0,
    'dS_Br': 0.0,
    'dH_base': 0.0005,
    'dH_Br': 0.030,
}


def get_stints(strat, total_laps):
    pits = sorted(strat['pit_stops'], key=lambda x: x['lap'])
    stints, cur, last = [], strat['starting_tire'], 0
    for p in pits:
        if p['lap'] > last:
            stints.append((cur, last + 1, p['lap']))
        cur, last = p['to_tire'], p['lap']
    stints.append((cur, last + 1, total_laps))
    return stints


def simulate(race_config, strategies):
    B = race_config['base_lap_time']
    L = race_config['total_laps']
    P = race_config['pit_lane_time']

    Br = B - round(2 * B) / 2
    oS = PARAMS['oS']
    oH = PARAMS['oH']
    dS = PARAMS['dS_base'] + PARAMS['dS_Br'] * Br
    dH = PARAMS['dH_base'] + PARAMS['dH_Br'] * Br

    times, spos = {}, {}
    for pos, strat in strategies.items():
        d = strat['driver_id']
        stints = get_stints(strat, L)
        t = len(strat['pit_stops']) * P

        for c, s, e in stints:
            n = e - s + 1
            sumN = (s + e) * n / 2.0
            if c == 'SOFT':
                t += n * oS + sumN * dS
            elif c == 'HARD':
                t += n * oH + sumN * dH
            # MEDIUM: no offset, no degradation diff (baseline)

        times[d] = t
        spos[d] = int(pos[3:])

    return sorted(times, key=lambda d: (times[d], spos[d]))


def main():
    test_case = json.load(sys.stdin)
    finishing = simulate(test_case['race_config'], test_case['strategies'])
    print(json.dumps({'race_id': test_case['race_id'], 'finishing_positions': finishing}))


if __name__ == '__main__':
    main()
