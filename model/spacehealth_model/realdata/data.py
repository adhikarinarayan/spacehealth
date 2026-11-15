"""Checksum-verified input readers and fixed overnight preprocessing."""
import hashlib
import re
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from ..config import ROOT

ZIP=ROOT/'research/data/raw/stanford_covid_wearables_mishra2020/COVID-19-Wearables.zip'
TABLES=ROOT/'research/papers/Mishra2020_SupplementaryTables.xlsx'
CHECKSUMS=ROOT/'research/checksums.sha256'

def verify_checksum(path,manifest=CHECKSUMS,key=None):
    path=Path(path);key=key or path.relative_to(ROOT/'research').as_posix()
    expected=next((line.split(maxsplit=1)[0] for line in Path(manifest).read_text().splitlines() if len(line.split(maxsplit=1))==2 and line.split(maxsplit=1)[1].lstrip('*')==key),None)
    if expected is None:raise ValueError(f'Checksum entry missing: {key}')
    digest=hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda:source.read(1024*1024),b''):digest.update(block)
    if digest.hexdigest()!=expected:raise ValueError(f'Checksum mismatch: {key}')
    return digest.hexdigest()

def parse_dates(cell):
    """Parse Timestamp lists without evaluating spreadsheet text; retain list order."""
    if cell is None or cell is pd.NaT:return []
    if isinstance(cell,(datetime,pd.Timestamp)):return [pd.Timestamp(cell).normalize()]
    values=re.findall(r"Timestamp\(['\"]([^'\"]+)['\"]\)",str(cell))
    return [pd.Timestamp(v).normalize() for v in values if not pd.isna(pd.Timestamp(v))]

def base_id(value):return str(value).split('_')[0]

def read_tables(path=TABLES):
    import openpyxl
    workbook=openpyxl.load_workbook(path,read_only=True,data_only=True)
    def records(sheet):
        iterator=workbook[sheet].values
        for row in iterator:
            if row[0]=='ParticipantID':
                headers=row;break
        else:raise ValueError(f'ParticipantID header missing: {sheet}')
        return [dict(zip(headers,row)) for row in iterator if row[0] is not None]
    table3=records('SuppTable3_Fig2a_COVID-19');table4=records('SuppTable4_Fig2a_Illnesses');workbook.close()
    return table3,table4

def minute_series(frame,column,aggregation):
    times=pd.to_datetime(frame['datetime'],errors='coerce')
    series=pd.Series(pd.to_numeric(frame[column],errors='coerce').to_numpy(),index=pd.DatetimeIndex(times).floor('min'))
    series=series[~series.index.isna()].replace([np.inf,-np.inf],np.nan)
    # Count minutes once: mean duplicate HR, conservative max duplicate steps.
    return series.groupby(level=0).agg(aggregation).sort_index()

def nightly_rhr(hr,steps,min_minutes=60):
    heart=minute_series(hr,'heartrate','mean');activity=minute_series(steps,'steps','max')
    if heart.empty:return pd.DataFrame(columns=['rhr_bpm','valid_rest_minutes'])
    # Eleven distinct zero-step minute bins in (t-11min,t] require t and every
    # preceding ten minutes. Missing step bins and nonzero/negative steps fail.
    resting=activity.eq(0).astype(int).rolling('11min',min_periods=11).sum().eq(11)
    eligible=(heart.index.hour<7)&resting.reindex(heart.index,fill_value=False).to_numpy()&heart.notna().to_numpy()
    night_values=heart[eligible].groupby(heart[eligible].index.normalize()).agg(['mean','count'])
    dates=pd.date_range(heart.index.min().normalize(),heart.index.max().normalize(),freq='D')
    result=night_values.reindex(dates).rename(columns={'mean':'rhr_bpm','count':'valid_rest_minutes'})
    result['valid_rest_minutes']=result['valid_rest_minutes'].fillna(0).astype(int)
    result.loc[result['valid_rest_minutes']<min_minutes,'rhr_bpm']=np.nan
    result.index.name='date'
    return result

def read_nightly(archive,record_id):
    folder='COVID-19-Wearables/'
    with archive.open(folder+record_id+'_hr.csv') as source:hr=pd.read_csv(source,usecols=['datetime','heartrate'])
    with archive.open(folder+record_id+'_steps.csv') as source:steps=pd.read_csv(source,usecols=['datetime','steps'])
    return nightly_rhr(hr,steps)
