import type { ActionEntry } from '../components/ActionCard';

/** Display the recorded instant in this device's local time, retaining its mission day. */
export function formatRecordedTime(entry:Pick<ActionEntry,'time'|'day'>):string{
 const date=new Date(entry.time);
 const time=Number.isNaN(date.getTime())?'—':`${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;
 return `${time} (day ${entry.day})`;
}
