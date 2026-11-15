"""Synthetic experiment metrics. Truth is used here, never by detectors."""
import statistics

CANDIDATES=('M0','M1','M1b','M2','M3','M4','M5','M6')

def candidate_metrics(candidate,seed,by_crew,cfg):
    research=cfg['research'];ev=cfg['stage1']['evaluation'];scenario=research['scenarios']['scenarios']['S2']
    low,high=ev['s2_window'];s2=[r for r in by_crew[scenario['crew']] if low<=r.missionDay<=high]
    first_watch=next((r.missionDay for r in s2 if r.status=='watch'),None)
    first_act=next((r.missionDay for r in s2 if r.status=='act'),None)
    flags=[r.missionDay for r in s2 if r.status in ('watch','act')]
    first=min(flags) if flags else None
    radius=ev['n1_radius_days']
    windows={d+shift for d in ev['n1_days'] for shift in range(-radius,radius+1)}
    n1=[r for r in by_crew[research['scenarios']['scenarios']['N1']['crew']] if r.missionDay in windows]
    n2={r.missionDay:r for r in by_crew[research['scenarios']['scenarios']['N2']['crew']]}
    gaplow,gaphigh=ev['n2_gap_days'];skiplo,skiphi=ev['n2_skipped_checkin_days']
    excludedlo,excludedhi=ev['false_alert_exclude_s2_window']
    quiet=[r for crew,rows in by_crew.items() for r in rows if r.status!='unknown' and not (crew==scenario['crew'] and excludedlo<=r.missionDay<=excludedhi)]
    false_alerts=sum(r.status in ('watch','act') for r in quiet)
    # Descriptive per-signal explanations are distinguished from feature attribution in reports.
    flagged=[r for rows in by_crew.values() for r in rows if r.status in ('watch','act')]
    example=next(iter(s2),None)
    example=next((r for r in s2 if r.status in ('watch','act')),example)
    explainable=all(bool(r.reason) and any(e.get('value') is not None and 'baseline' in e and 'z' in e for e in r.evidence) for r in flagged)
    return {'candidate':candidate,'seed':seed,'s2_first_watch_day':first_watch,'s2_first_act_day':first_act,'s2_first_flag_day':first,
            's2_detected_by_day42':first is not None and first<=scenario['symptomDay'],
            's2_delay_vs_onset_days':first-scenario['onsetDay'] if first is not None else None,
            's2_delay_vs_symptom_days':first-scenario['symptomDay'] if first is not None else None,'s2_flagged_days':flags,
            'n1_any_watch':any(r.status=='watch' for r in n1),'n1_any_act':any(r.status=='act' for r in n1),
            'n1_watch_days':[r.missionDay for r in n1 if r.status=='watch'],'n1_act_days':[r.missionDay for r in n1 if r.status=='act'],
            'n2_gap_all_unknown':all(n2[d].status=='unknown' for d in range(gaplow,gaphigh+1)),
            'n2_skipped_checkins_explicit':all('not collected' in n2[d].reason.lower() and 'no symptoms' not in n2[d].reason.lower() for d in range(skiplo,skiphi+1)),
            'unknown_days':sum(r.status=='unknown' for rows in by_crew.values() for r in rows),
            'routine_false_alerts':false_alerts,'evaluable_crew_days':len(quiet),'false_alerts_per100_crew_days':100*false_alerts/len(quiet) if quiet else None,
            'explanation_available':explainable and bool(example and example.evidence), 'explanation_example':(example.reason+'; evidence='+str(example.evidence)) if example else '',
            'explanation_kind':'descriptive feature deviations; not causal attribution' if candidate in ('M5','M6') else 'per-signal rule/statistic evidence'}

def summarize(rows,cfg):
    result=[]
    for candidate in CANDIDATES:
        selected=[r for r in rows if r['candidate']==candidate]
        if not selected:continue
        misses=sum(not r['s2_detected_by_day42'] for r in selected)
        reasons=[]
        if misses>=cfg['stage1']['discard']['misses_in_three']:reasons.append(f'S2 missed by symptom day in {misses}/{len(selected)} seeds')
        if any(r['n1_any_act'] for r in selected):reasons.append('act in N1')
        if any(not r['n2_gap_all_unknown'] for r in selected):reasons.append('N2 gap not unknown')
        if any(not r['explanation_available'] for r in selected):reasons.append('no per-signal explanation')
        denominator=sum(r['evaluable_crew_days'] for r in selected)
        alerts=sum(r['routine_false_alerts'] for r in selected)
        watchdays=[r['s2_first_watch_day'] for r in selected if r['s2_first_watch_day'] is not None]
        result.append({'candidate':candidate,'detected':len(selected)-misses,'runs':len(selected),'median_first_watch_day':statistics.median(watchdays) if watchdays else None,
                       'n1_watches':sum(len(r['n1_watch_days']) for r in selected),'n1_acts':sum(len(r['n1_act_days']) for r in selected),
                       'false_alerts':alerts,'evaluable_crew_days':denominator,'false_alerts_per100_crew_days':100*alerts/denominator if denominator else None,
                       'verdict':'discarded' if reasons else 'kept for next-stage review','discard_reasons':reasons,
                       'skipped_checkin_checks_pass':all(r['n2_skipped_checkins_explicit'] for r in selected)})
    return result
