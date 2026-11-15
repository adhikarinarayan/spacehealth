"""Fixed, untuned real-data check of frozen M3 on Stanford civilian wearables."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import time
import zipfile
import pandas as pd
from .data import ZIP,TABLES,verify_checksum,read_tables,parse_dates,base_id,read_nightly
from .protocol import baseline_window,detect_frozen,participant_metrics,bootstrap,BOOTSTRAP_SEED,BOOTSTRAP_SAMPLES
from ..config import ROOT
from ..evaluate.frozen import read_frozen,DEFAULT

PROTOCOL={
 'nightly_rhr':'Mean HR, file-local 00:00–06:59, current and preceding ten minute step bins all explicitly zero; >=60 distinct qualifying HR minutes. Missing steps are not zero.',
 'duplicates':'Floor timestamps to minute; duplicate HR averaged, duplicate steps max; invalid numeric/timestamps excluded. No overnight or detector imputation.',
 'cases':'Table 3 Category exactly COVID-19, first listed valid symptom timestamp (original cell order, not sorted). Other dates are not searched for better performance.',
 'case_baseline':'First 14 calendar nights starting at first HR record date, including partial/missing nights; >=10 plausible RHR nights; final baseline date <= onset minus seven days. No later-window search.',
 'control_baseline':'Participants whose base ID appears in neither Table 3 nor Table 4; first 14 plausible valid nightly RHR values; evaluate only after the last selected baseline date.',
 'identity':'Match base participant ID before any underscore; repeated illness files are excluded from controls together. Standard *_hr.csv files only; *_longterm files not added as independent participants.',
 'detector':'Unchanged frozen M3; median / max(1.4826*MAD,1.5 bpm) fixed baseline; lambda .2, control_sigma 3 (EWMA threshold 1); unknown nights reset state. No symptoms, HRV or temperature inferred.',
 'primary':'Any watch in inclusive relative days -7..+7; first watch within that window; by-onset metric uses the same window through day 0. A watch may be ongoing from before the window.',
 'false_alerts':'Contiguous watch episodes on calendar nights after baseline and before day -7 for cases, all post-baseline for controls; unknown breaks an episode. Denominator: valid/evaluable person-nights; no-reported-illness does not mean confirmed healthy.',
 'bootstrap':{'unit':'participant','samples':BOOTSTRAP_SAMPLES,'seed':BOOTSTRAP_SEED,'interval':'percentile 95%; summed event/exposure ratio for false alerts'},
 'no_tuning':True,
}

def versions():
    return {name:importlib.metadata.version(name) for name in ['numpy','pandas','scipy','scikit-learn','openpyxl','et-xmlfile','matplotlib']}

def example_plot(nightly,detected,baseline,onset,participant,path):
    os.environ.setdefault('MPLCONFIGDIR','/tmp/spacehealth-realdata-matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    x=(nightly.index-onset).days;y=(detected.index-onset).days
    fig,axes=plt.subplots(2,1,figsize=(11,7),sharex=True)
    axes[0].plot(x,nightly.rhr_bpm,'.-',ms=3,lw=.8,label='Observed overnight resting HR (gaps = missing)')
    axes[0].axhline(baseline.center,color='black',ls='--',lw=1,label='Fixed baseline median')
    axes[0].axhspan(baseline.center-baseline.scale,baseline.center+baseline.scale,color='gray',alpha=.18,label='Baseline ±1 robust SD (min scale 1.5 bpm)')
    axes[0].set_ylabel('Nightly resting HR (bpm)');axes[0].legend(fontsize=8,loc='upper left')
    axes[1].plot(y,detected.ewma,label='Frozen M3 EWMA',color='#235d7d')
    axes[1].axhline(1,color='#b54d21',ls='--',label='Frozen watch limit = 1')
    watch=detected[detected.status=='watch'];axes[1].scatter((watch.index-onset).days,watch.ewma,s=12,color='#b54d21',label='Watch')
    axes[1].set_ylabel('EWMA of baseline-normalized RHR');axes[1].set_xlabel('Days relative to first listed symptom onset (shifted dates)');axes[1].legend(fontsize=8)
    for ax in axes:
        ax.axvline(0,color='#8d3232',ls=':',label='Symptom day 0');ax.axvspan(-7,7,color='#235d7d',alpha=.05);ax.grid(alpha=.15)
    axes[1].set_xlim(-28,21)
    fig.suptitle(f'Civilian wearable sanity check · {participant} · unchanged frozen M3\nIllustrative detected case; not clinical validation')
    fig.tight_layout();fig.savefig(path,dpi=160);plt.close(fig)

def write_results(out,rows,metadata,example,complete):
    pd.DataFrame(rows).to_csv(out/'results.csv',index=False)
    cases=[r for r in rows if r['group']=='covid' and r['evaluable']]
    controls=[r for r in rows if r['group']=='no_reported_illness' and r['evaluable']]
    metrics={'cases_detected':bootstrap(cases,'detected'),'cases_detected_by_day0':bootstrap(cases,'detected_by_day0'),
             'case_false_alerts':bootstrap(cases,'false_alert_episodes','false_alert_person_nights'),
             'control_false_alerts':bootstrap(controls,'false_alert_episodes','false_alert_person_nights')}
    distribution=Counter(r['first_watch_relative_day'] for r in cases if r['detected'])
    summary={**metadata,'complete':complete,'processedParticipants':len(rows),'caseEvaluable':len(cases),'controlEvaluable':len(controls),'excludedReasons':dict(Counter(r['exclusion_reason'] for r in rows if not r['evaluable'])),
             'firstWatchDayDistribution':dict(sorted(distribution.items())),'metrics':metrics,'versions':versions(),'protocol':PROTOCOL}
    (out/'metrics.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    def ci(metric,percent=False):
        x=metrics[metric];scale=100 if percent else 1
        return 'not estimable' if x['estimate'] is None else f"{scale*x['estimate']:.2f} [{scale*x['ci95'][0]:.2f}, {scale*x['ci95'][1]:.2f}]"
    lines=['# Frozen M3 — real civilian wearable sanity check','', '**Separate from astronaut simulations. No tuning, parameter search or clinical-validation claim.**', '',
           f"Run complete: **{complete}**. Verified input SHA256 values and frozen config SHA256 are in metrics.json. Started {metadata['startedUtc']}.", '',
           '## Cohort and exclusions','',f"Table 3: {metadata['table3Rows']} rows, {metadata['covidRows']} Category COVID-19, {metadata['covidWithSymptomDate']} with a valid listed symptom date, {metadata['covidWithHR']} COVID rows with a standard HR member. Available standard archive HR records: {metadata['hrRecords']} ({metadata['distinctBaseParticipants']} distinct base IDs).", '',
           f"COVID evaluable: **{len(cases)}**; no-reported-illness candidates: {metadata['controlCandidates']}, evaluable: **{len(controls)}**. Processed {len(rows)} selected participant records; excluded {sum(not r['evaluable'] for r in rows)}. Reasons:", '']
    for reason,n in summary['excludedReasons'].items():lines.append(f'- {reason}: {n}')
    lines+=['','All participant-level eligibility decisions, baseline dates/counts/scales, coverage and denominators are retained in results.csv. Non-COVID illness participants are excluded from the control cohort by membership in either supplementary table.','',
            '## Detection (participant bootstrap 95% CI)','', '| Metric | Detected / evaluable | Percent [95% CI] |','|---|---|---|',
            f"| Watch in day −7…+7 | {sum(r['detected'] for r in cases)} / {len(cases)} | {ci('cases_detected',True)} |",
            f"| Watch at/before day 0 within −7…0 | {sum(r['detected_by_day0'] for r in cases)} / {len(cases)} | {ci('cases_detected_by_day0',True)} |", '',
            'First watch day distribution within the primary window (detected cases only): '+', '.join(f'{k:+d}: {v}' for k,v in sorted(distribution.items()))+'.', '',
            f"Detection-window coverage: {sum(r['detection_window_valid_nights'] for r in cases)} valid nights out of {15*len(cases)} possible participant-window nights. Missing nights are never replaced by zero or a healthy status. Baseline eligibility alone defines the evaluable cohort; an absent follow-up window would be counted as not detected and exposed in the coverage column.", '',
            '## Watch episode costs','', '| Group / period | Participants with exposure | Episodes / evaluable person-nights | Episodes per 100 nights [95% CI] |','|---|---|---|---|']
    for group,key,label in [(cases,'case_false_alerts','COVID: after baseline, before day −7'),(controls,'control_false_alerts','No reported illness: all post-baseline')]:
        lines.append(f"| {label} | {sum(r['false_alert_person_nights']>0 for r in group)} | {sum(r['false_alert_episodes'] for r in group)} / {sum(r['false_alert_person_nights'] for r in group)} | {ci(key)} |")
    lines+=['',f"Bootstrap: {BOOTSTRAP_SAMPLES} resamples of participants, fixed RNG seed {BOOTSTRAP_SEED}; false-alert intervals resample whole participant episode/exposure pairs. Unknown nights break episodes and are excluded from person-night denominators. These are watch costs, not adjudicated clinical false positives.", '',
            '## Fixed protocol and causal use','',
            'Overnight RHR uses 00:00–06:59 file-local minutes with explicitly zero steps in that minute and the preceding ten minutes, requiring at least 60 distinct qualifying minutes. Missing step bins do not imply rest. Duplicate HR minutes are averaged, duplicate step minutes take the maximum; no missing-night imputation is used.', '',
            'For COVID cases the first 14 calendar nights of the record are the only baseline candidate, with at least 10 plausible nights, ending no later than relative day −7. Controls use their first 14 valid nights. Baseline fitting calls the existing frozen median/MAD/min-scale code. Detection starts the next calendar night, calls unchanged M3 with the exact frozen parameters, and resets on missing nights. No future measurements or symptom dates enter the detector. Synthetic tests compare prefixes against full-record results.', '',
            'Multiple symptom dates: the **first listed valid timestamp in the original cell order** is used, not a date selected by outcome and not a sorted/earliest-date search. Some cells list multiple illness dates out of chronological order; attribution to a particular illness is uncertain. Baseline dates, follow-up dates and labels are consistently PHI-shifted. Earlier illness episodes are not retrospectively removed from the fixed baseline or pre-onset watch-cost window.', '',
            '## Comparison with published studies','',
            'Mishra et al. (2020) reported physiological alterations in 26/32 COVID cases, detection at or before symptom onset in 22/25 cases with symptom information using offline methods, and 63% detectable before symptom onset with their real-time two-tier RHR alerting. Our frozen EWMA, eligibility, first-date rule, −7…+7 window and fixed baseline differ. Our estimates above are a sanity check on an existing untuned detector, **not a replication**, a clinical sensitivity estimate, or evidence of astronaut illness detection.', '',
            'Alavi et al. (2022), Methods, “NightSignal” / “Data pre-processing”, supports averaging resting HR overnight (24:00–07:00) after zero-step filtering. The ten-minute inactivity mask and ≥60-minute eligibility rule are the TASK-016 protocol; they are not claimed as an exact Alavi replication. Unlike Alavi’s described missing-night interpolation, this evaluation performs no interpolation.', '',
            'Sources: [Mishra 2020](https://doi.org/10.1038/s41551-020-00640-6); [Alavi 2022](https://doi.org/10.1038/s41591-021-01593-2). Local checksum-verified supplementary workbook and archive supplied by the project; methods checked against the local paper texts.','',
            '## Limitations','',
            '- Civilian participants on Earth during the COVID-19 era, Fitbit-derived HR, shifted dates, small selected cohort; no astronaut, microgravity or clinical deployment inference.',
            '- Symptoms and other illnesses are self-reported; no entry in either table does not establish health. Other infections, medication, activity, stress and prior illness can explain watches.',
            '- Overnight availability and fixed baseline restrictions create selection effects. Missing nights reset EWMA; a watch already active before day −7 can count inside the primary window.',
            '- Minimum 1.5 bpm scale and all detector parameters come unchanged from the frozen simulator model. A successful example plot is selected only for illustration, never for a headline denominator.',
            '- No tuning or parameter search was performed on these data. Aggregate confidence intervals describe participant resampling of this cohort, not transportability.', '',
            'Example: '+('example.png (lexicographically first detected participant)' if example is not None else 'No detected case available for the requested example; no replacement success was fabricated.')+'.']
    (out/'summary.md').write_text('\n'.join(lines)+'\n')
    return summary

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,default=Path('reports/realdata'));parser.add_argument('--time-limit-minutes',type=float,default=75)
    args=parser.parse_args();started=time.monotonic();deadline=started+args.time_limit_minutes*60
    if args.time_limit_minutes<=0 or args.time_limit_minutes>90:parser.error('Time limit must be in (0,90] minutes')
    config,document,digest=read_frozen();source_hashes={str(p.relative_to(ROOT)):verify_checksum(p) for p in (ZIP,TABLES)}
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'protocol.json').write_text(json.dumps({'fixedBeforeOutcomeAnalysis':True,'startedUtc':datetime.now(timezone.utc).isoformat(),'configHash':digest,'sourceHashes':source_hashes,'protocol':PROTOCOL},indent=2)+'\n')
    table3,table4=read_tables();covid=[r for r in table3 if r['Category']=='COVID-19']
    illness_ids={base_id(r['ParticipantID']) for r in table3+table4}
    rows=[];example=None
    with zipfile.ZipFile(ZIP) as archive:
        names=set(archive.namelist());ids=sorted(Path(n).name[:-7] for n in names if n.endswith('_hr.csv'))
        controls=[pid for pid in ids if base_id(pid) not in illness_ids]
        assert len({base_id(pid) for pid in controls})==len(controls),'Control IDs must be unique participants'
        jobs=[(r['ParticipantID'],'covid',parse_dates(r['Symptom_dates'])) for r in sorted(covid,key=lambda r:r['ParticipantID'])]+[(pid,'no_reported_illness',[]) for pid in controls]
        metadata={'startedUtc':datetime.now(timezone.utc).isoformat(),'frozenConfigSha256':digest,'sourceHashes':source_hashes,'table3Rows':len(table3),'covidRows':len(covid),'covidWithSymptomDate':sum(bool(parse_dates(r['Symptom_dates'])) for r in covid),'covidWithHR':sum(r['ParticipantID'] in ids for r in covid),'hrRecords':len(ids),'distinctBaseParticipants':len({base_id(pid) for pid in ids}),'controlCandidates':len(controls)}
        for pid,group,dates in jobs:
            if time.monotonic()>deadline:break
            onset=dates[0] if dates else None
            row={'participantId':pid,'group':group,'evaluable':False,'exclusion_reason':'','symptom_date':str(onset.date()) if onset is not None else None}
            if group=='covid' and onset is None:row['exclusion_reason']='COVID category without valid symptom date'
            elif f'COVID-19-Wearables/{pid}_hr.csv' not in names:row['exclusion_reason']='no matching standard HR file'
            elif f'COVID-19-Wearables/{pid}_steps.csv' not in names:row['exclusion_reason']='no matching steps file (rest cannot be verified)'
            else:
                nightly=read_nightly(archive,pid);baseline,reason=baseline_window(nightly,config,onset)
                row.update(record_start=str(nightly.index[0].date()) if len(nightly) else None,record_end=str(nightly.index[-1].date()) if len(nightly) else None,record_calendar_nights=len(nightly),record_valid_nights=int(nightly.rhr_bpm.notna().sum()))
                row['exclusion_reason']=reason
                if baseline is not None:
                    detected,fixed=detect_frozen(nightly,baseline,config,pid)
                    row.update(evaluable=True,baseline_start=str(baseline.index[0].date()),baseline_end=str(baseline.index[-1].date()),baseline_valid_nights=fixed.count,baseline_median_bpm=fixed.center,baseline_scale_bpm=fixed.scale)
                    row.update(participant_metrics(nightly,detected,onset))
                    if example is None and group=='covid' and row['detected']:
                        example=pid;example_plot(nightly,detected,fixed,onset,pid,args.out/'example.png')
            rows.append(row)
            pd.DataFrame(rows).to_csv(args.out/'results.csv',index=False)
            print(f"{len(rows)}/{len(jobs)} {pid} {group}: "+('evaluable' if row['evaluable'] else row['exclusion_reason']),flush=True)
        complete=len(rows)==len(jobs)
    summary=write_results(args.out,rows,metadata,example,complete)
    print(json.dumps({'complete':complete,'caseEvaluable':summary['caseEvaluable'],'controlEvaluable':summary['controlEvaluable'],'metrics':summary['metrics']},indent=2),flush=True)
    if not complete:print('Timebox reached; partial results retained, not a complete cohort.',flush=True)

if __name__=='__main__':main()
