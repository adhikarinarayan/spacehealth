import type { Indicator } from '../contracts';
import { statusNames,statusIcons } from '../data/presentation';
export function Status({status}:{status:Indicator['status']}){return <span className={`status status-${status}`}><span aria-hidden="true">{statusIcons[status]}</span> {statusNames[status]}</span>;}
