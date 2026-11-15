"""Fixed-baseline sleep persistence and accumulated relative debt (R3)."""
import re
from ..baseline.fixed import fit_baselines,usable

def evaluate(readings,crew_id,day,config,baselines=None):
    if day<1:raise ValueError('Sleep evaluation requires a mission day')
    rows={r['missionDay']:r for r in readings if r['crewId']==crew_id and r['missionDay']<=day}
    b=(baselines or fit_baselines(list(rows.values()),crew_id,config))['sleep_hours']
    rules=config['rules']['sleep_alertness'];spec=config['signals']['sleep_hours']
    watch_match=re.search(r'z ≤ -([\d.]+) on (\d+) consecutive',rules['watch'])
    window_size=int(re.search(r'last (\d+) nights',rules['act'])[1])
    threshold=float(re.search(r'>= ([\d.]+) h',rules['act'])[1])
    minimum=int(re.search(r'<(\d+) of \d+ nights valid',rules['act'])[1])
    absolute_reference=float(re.search(r'max\(0, ([\d.]+) -',rules['context_absolute_debt'])[1])
    start=config['scenarios']['mission']['preflight_days'][0]
    days=[d for d in range(start,day+1) if d!=0]
    window=days[-window_size:]
    valid={d:rows[d]['sleep_hours'] for d in window if d in rows and usable(rows[d].get('sleep_hours'),spec)}
    today=rows.get(day,{}).get('sleep_hours')
    current=usable(today,spec)
    relative=sum(max(0,b.center-v) for v in valid.values()) if b.quality=='valid' else None
    absolute=sum(max(0,absolute_reference-v) for v in valid.values())
    evidence=[{'signalId':'sleep_hours','value':today,'unit':spec['unit']},
              {'signalId':'sleep_hours','value':relative,'unit':f'h relative debt over {window_size} nights; observed nights {len(valid)}'},
              {'signalId':'sleep_hours','value':absolute,'unit':f'h absolute excess wakefulness over {window_size} nights (info-only)'}]
    if b.quality=='valid':evidence[0].update(baseline=b.center)
    if b.quality=='valid' and current:evidence[0]['z']=(today-b.center)/b.scale
    status='nominal';quality='valid';reason='No configured sleep rule triggered.';card=None
    if b.quality!='valid' or not current:
        status='unknown';quality='missing' if today is None else 'insufficient';reason='Sleep measurement or fixed baseline is unavailable or unusable.'
    else:
        n=int(watch_match[2]);recent=days[-n:]
        watch_evaluable=len(recent)==n and all(d in rows and usable(rows[d].get('sleep_hours'),spec) for d in recent)
        watch=watch_evaluable and all((rows[d]['sleep_hours']-b.center)/b.scale<=-float(watch_match[1]) for d in recent)
        act_evaluable=len(valid)>=minimum
        if act_evaluable and relative>=threshold:status='act';card='sleep-debt'
        elif watch:status='watch';card='sleep-short'
        elif not watch_evaluable and not act_evaluable:status='unknown';quality='insufficient';reason='Insufficient nights to evaluate sleep persistence or debt.'
        if status!='unknown' and len(valid)<len(window):quality='suspect'
    sources=[];assumptions=['A6','A7']
    if card:
        c=config['cards'][card];reason=c['why'].format(hours=f'{today:.2f}',nights=int(watch_match[2]),debt_h=f'{relative:.2f}')
        sources=c['source_ids'];assumptions=c['assumption_ids']
    if len(valid)<len(window):reason+=f' Partial sleep window: {len(valid)}/{len(window)} observed nights; missing nights were not filled with zero.'
    result={'crewId':crew_id,'missionDay':day,'moduleId':'sleep_alertness','status':status,'dataQuality':quality,'reason':reason,'evidence':evidence,'sourceIds':list(sources),'assumptionIds':list(assumptions)}
    if card:result['cardId']=card
    return result
