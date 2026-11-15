export function shouldRegisterOffline(production:boolean,mode:string){return production&&mode!=='test';}
export async function registerOffline(){
 if(!shouldRegisterOffline(import.meta.env.PROD,import.meta.env.MODE)||!('serviceWorker' in navigator))return;
 return navigator.serviceWorker.register(`${import.meta.env.BASE_URL}sw.js`,{scope:import.meta.env.BASE_URL});
}
