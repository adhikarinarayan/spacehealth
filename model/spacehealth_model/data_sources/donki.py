"""NASA DONKI near-Earth GOES onsets: timing evidence, never crew dose data."""
from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
import hashlib
import json
from pathlib import Path
from ..config import ROOT,load_config
DEFAULT=ROOT/'research/data/raw/nasa_donki_sep/SEP_2017-08-15_2017-10-10.json'
CHECKSUMS=ROOT/'research/checksums.sha256'
KEY='data/raw/nasa_donki_sep/SEP_2017-08-15_2017-10-10.json'
@dataclass(frozen=True)
class Event:
    sepID:str
    eventTime:datetime
    instruments:tuple[str,...]
@dataclass(frozen=True)
class Episode:
    onset:datetime
    events:tuple[Event,...]

def load_events(path=DEFAULT,checksums=CHECKSUMS):
    lines=Path(checksums).read_text().splitlines()
    expected=next((line.split(maxsplit=1)[0] for line in lines if len(line.split(maxsplit=1))==2 and line.split(maxsplit=1)[1].lstrip('*')==KEY),None)
    if expected is None:raise ValueError('DONKI checksum entry missing')
    data=Path(path).read_bytes();actual=hashlib.sha256(data).hexdigest()
    if actual!=expected:raise ValueError(f'DONKI checksum mismatch: expected {expected}, got {actual}')
    raw=json.loads(data);events=[]
    if not isinstance(raw,list):raise ValueError('DONKI events must be an array')
    for event in raw:
        time=datetime.fromisoformat(event['eventTime'].replace('Z','+00:00'))
        if time.tzinfo is None:raise ValueError('DONKI timestamp must be UTC-aware')
        events.append(Event(event['sepID'],time.astimezone(timezone.utc),tuple(i['displayName'] for i in event['instruments'])))
    return events,actual

def goes_episodes(events,group_hours=None,selection=None):
    selection=selection or load_config()['stage']['s3_donki']
    group_hours=selection['group_hours'] if group_hours is None else group_hours
    if group_hours<=0:raise ValueError('Grouping interval must be positive')
    selected=sorted((e for e in events if datetime.fromisoformat(selection['window_start_utc'].replace('Z','+00:00'))<=e.eventTime<datetime.fromisoformat(selection['window_end_exclusive_utc'].replace('Z','+00:00')) and any(i.upper().startswith('GOES') for i in e.instruments)),key=lambda e:e.eventTime)
    groups=[]
    for event in selected:
        if not groups or event.eventTime-groups[-1][-1].eventTime>=timedelta(hours=group_hours):groups.append([event])
        else:groups[-1].append(event)
    return [Episode(group[0].eventTime,tuple(group)) for group in groups]

def map_episodes(episodes,first_day=None):
    if first_day is None:first_day=load_config()['scenarios']['scenarios']['S3']['onsetDay']
    if not episodes:raise ValueError('No selected GOES episodes')
    first=episodes[0].onset;anchor=first.replace(hour=0,minute=0,second=0,microsecond=0)
    result=[]
    for episode in episodes:
        elapsed=episode.onset-anchor
        result.append({'missionDay':first_day+elapsed.days,'timeHoursFromDayStart':elapsed.seconds/3600+elapsed.microseconds/3.6e9,'onsetUtc':episode.onset.isoformat().replace('+00:00','Z'),'sepIDs':[e.sepID for e in episode.events]})
    return result

def timing(first_day=None,config=None):
    config=config or load_config()
    events,digest=load_events();episodes=goes_episodes(events,selection=config['stage']['s3_donki']);mapped=map_episodes(episodes,first_day)
    if len(mapped)!=config['stage']['s3_donki']['expected_episodes']:raise ValueError(f'Expected three GOES episodes, got {len(mapped)}')
    source=f'NASA DONKI SEP (CCMC) — GOES onsets 2017-09-05/06/10, observed near Earth; timing replayed, dose from Zeitlin2013 Table 1; file sha256 {digest}'
    return mapped,source
