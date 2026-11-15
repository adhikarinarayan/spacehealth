import React from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import './styles/tokens.css';
import './style.css';
createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);

import './theme/theme.css';

import { registerOffline } from './offline';
void registerOffline().catch(()=>{});

import './styles/mission-control.css';

import './cosmos/solar.css';
import './cosmos/cosmos.css';

import './styles/typography.css';
