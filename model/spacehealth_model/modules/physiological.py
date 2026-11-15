"""M1 fixed-baseline persistence rules. No scenario ID or truth input."""
from ..baseline.fixed import fit_baselines, usable

# Neutral computation/status labels, not medical advice. Action wording is from research.
def evaluate(readings, crew_id, day, config, baselines=None):
    if day<1:raise ValueError('Only mission days are evaluated')
    history={r['missionDay']:r for r in readings if r['crewId']==crew_id and r['missionDay']<=day}
    baseline=baselines or fit_baselines(list(history.values()),crew_id,config)
    today=history.get(day)
    spec=config['rules']['physiological_change']
    evidence=[]; evaluable=[]; invalid=[]; missing=[]; insufficient=[]
    def shifted(d,threshold):
        row=history.get(d)
        found=[]
        if row is None:return found
        for signal,direction in spec['signals'].items():
            b=baseline[signal]; value=row.get(signal)
            if b.quality!='valid' or not usable(value,config['signals'][signal]):continue
            z=(value-b.center)/b.scale
            if (z if direction=='up' else -z)>threshold:found.append(signal)
        return found
    for signal,direction in spec['signals'].items():
        b=baseline[signal]; value=today.get(signal) if today else None
        e={'signalId':signal,'value':value,'unit':config['signals'][signal]['unit'],'direction':direction}
        if value is None:missing.append(signal)
        elif not usable(value,config['signals'][signal]):invalid.append(signal)
        if b.quality!='valid':insufficient.append(signal)
        elif usable(value,config['signals'][signal]):
            evaluable.append(signal);e.update(baseline=b.center,z=(value-b.center)/b.scale)
            run=0
            for previous in range(day,0,-1):
                if signal not in shifted(previous,config['watch_z']):break
                run+=1
            e['persistenceDays']=run
        evidence.append(e)
    def persistent(threshold,count,nights):
        return all(len(shifted(d,threshold))>=count for d in range(day-nights+1,day+1))
    symptoms=today['symptoms'] if today and today['checkin_completed'] else []
    red=[s for s in symptoms if s in spec['symptom_only']['red_flag']]
    status='nominal'; card=None; reason='No configured sustained change rule triggered.'; quality='valid'
    if red:
        status='act';card='symptom-escalation'
    elif len(evaluable)<config['watch_count']:
        status='unknown';quality='missing' if missing else 'insufficient'
        reason='Fewer than the required physiological signals are evaluable.'
    else:
        watch=persistent(config['watch_z'],config['watch_count'],config['watch_days'])
        strong=persistent(config['act_z'],config['act_count'],config['act_days'])
        if strong:status='act';card='physiological-change-act'
        elif watch:status='watch';card='physiological-change'
        elif symptoms:reason+=' Symptoms logged.'
        if invalid:quality='suspect'
    if red and (invalid or missing or insufficient):quality='suspect'
    sources=[];assumptions=['A6','A7']
    if card:
        c=config['cards'][card]
        changed=shifted(day,config['watch_z'])
        reason=c['why'].format(signals=', '.join(changed),days=config['watch_days'],symptoms=', '.join(symptoms) or 'none reported')
        sources=list(c['source_ids']);assumptions=list(c['assumption_ids'])
    if 'rhr_bpm' in evaluable and 'hrv_rmssd_ms' in evaluable:
        reason+=' RHR and HRV share a wearable source and are correlated.'
    if insufficient:reason+=' Baseline insufficient for: '+', '.join(insufficient)+'.'
    if missing:reason+=' Missing readings: '+', '.join(missing)+'.'
    if today is None or not today['checkin_completed']:reason+=' Symptom check-in not collected.'
    elif not symptoms:reason+=' No symptoms reported.'
    if invalid:reason+=' Implausible readings excluded: '+', '.join(invalid)+'.'
    for word in spec['forbidden_words']:
        if word.lower() in reason.lower():raise ValueError('Forbidden wording in generated reason')
    result={'crewId':crew_id,'missionDay':day,'moduleId':'physiological_change','status':status,'dataQuality':quality,'reason':reason,'evidence':evidence,'sourceIds':sources,'assumptionIds':assumptions}
    if card:result['cardId']=card
    return result

# evaluate above remains the historical M1 reference imported by detectors.M1.
# Production explicitly calls evaluate_production, avoiding any change to that record.
def production_results(readings,crew_id,config,baselines=None):
    from ..detectors.candidates import get_detector
    from ..evaluate.frozen import read_frozen
    data=[r for r in readings if r['crewId']==crew_id]
    baseline=baselines or fit_baselines(data,crew_id,config)
    params=config.get('_production') or read_frozen()[0]['_production']
    context={'research':config,'stage1':params}
    return ({r.missionDay:r for r in get_detector('M3').detect(data,baseline,context)},
            {r.missionDay:r for r in get_detector('M5').detect(data,baseline,context)})

def evaluate_production(readings,crew_id,day,config,baselines=None,prepared=None):
    if day<1:raise ValueError('Only mission days are evaluated')
    if prepared is None:
        prepared=production_results([r for r in readings if r['missionDay']<=day],crew_id,config,baselines)
    primary,agreement=prepared[0][day],prepared[1][day]
    evidence=[]
    allowed=('signalId','value','unit','baseline','z')
    for item in primary.evidence:
        e={k:item[k] for k in allowed if k in item}
        e['direction']=config['rules']['physiological_change']['signals'][e['signalId']]
        evidence.append(e)
    if 'distance_squared' not in agreement.metrics:
        agreement_label='not evaluable'
    else:
        m3watch=primary.metrics.get('ewma',0)>primary.metrics.get('threshold',float('inf'))
        m5watch=agreement.metrics['consecutive']>=config.get('_production',{}).get('M5',{}).get('consecutive_days',2)
        agreement_label='agree' if m3watch==m5watch else 'disagree'
    evidence.append({'signalId':'rhr_bpm','value':agreement_label,'unit':'info-only: multi-signal agreement (M5); never changes status'})
    row=next((r for r in readings if r['crewId']==crew_id and r['missionDay']==day),None)
    rhr=next(e for e in primary.evidence if e['signalId']=='rhr_bpm')
    quality='valid'
    if primary.status=='unknown':quality='missing' if rhr['value'] is None else 'insufficient'
    elif not rhr.get('evaluable'):quality='suspect'
    card=None;reason='Within your usual range.' if primary.status=='nominal' else 'Not enough reliable resting heart rate data to assess this area.';source_ids=[];assumption_ids=['A6','A7']
    if primary.status=='act':card='symptom-escalation'
    elif primary.status=='watch':card='physiological-change'
    if card:
        template=config['cards'][card]
        days=0
        for d in range(day,0,-1):
            if d not in prepared[0] or prepared[0][d].status not in ('watch','act'):break
            days+=1
        reason=template['why'].format(signals='Resting heart rate readings',days=days,symptoms=', '.join(row['symptoms']) if row and row['checkin_completed'] else 'not collected')
        if days==1:reason=reason.replace('1 nights','1 night')
        source_ids=list(template['source_ids']);assumption_ids=list(template['assumption_ids'])
    if row is None or not row['checkin_completed']:reason+=' Symptom check-in not collected.'
    for word in config['rules']['physiological_change']['forbidden_words']:
        if word.lower() in reason.lower():raise ValueError('Forbidden production reason wording')
    result={'crewId':crew_id,'missionDay':day,'moduleId':'physiological_change','status':primary.status,'dataQuality':quality,'reason':reason,'evidence':evidence,'sourceIds':source_ids,'assumptionIds':assumption_ids}
    if card:result['cardId']=card
    return result
