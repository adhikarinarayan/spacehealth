import type { Mission } from '../data/load';
import { PanelIntro } from './PanelIntro';
import { uiText } from '../data/ui';
export function MissionHeader({mission,day}:{mission:Mission;day:number}){
 const profile=mission.missionProfile;const blackout=profile.blackouts.find(b=>b.startDay<=day&&day<=b.endDay);
 return <section className="mission-status panel" aria-label="Mission status"><PanelIntro panel="mission_header" values={{day,duration:profile.durationDays}} extraHelpKeys={['theme.trajectory_note']}/><div className="mission-metrics"><div><span>Mission day</span><strong>{day} / {profile.durationDays}</strong></div><div><span>Profile</span><strong>{profile.label}</strong></div><div><span>Comms one-way delay</span><strong>{profile.comms_one_way_delay_min.min}–{profile.comms_one_way_delay_min.max} min <small>(illustrative)</small></strong></div><div className={blackout?'blackout-active':undefined}><span>Blackout</span><strong>{!profile.blackouts.length?'none simulated':uiText(`panels.mission_header.${blackout?'blackout_active':'blackout_inactive'}`)}</strong>{blackout&&<small>MOCK · {blackout.startDay}–{blackout.endDay}</small>}</div></div></section>;
}
