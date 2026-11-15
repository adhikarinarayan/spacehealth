import { defineConfig } from 'vite';
import { resolve } from 'node:path';
import { writePrecache } from './scripts/offline-build.mjs';
const base=process.env.BASE_PATH||'/';
if(!/^\/(?:[A-Za-z0-9._~-]+\/)*$/.test(base))throw new Error('BASE_PATH must be an absolute directory path with leading/trailing slashes, e.g. /spacehealth/');
export default defineConfig({base,plugins:[{name:'spacehealth-offline-precache',apply:'build',closeBundle(){writePrecache(resolve('dist'));}}]});
