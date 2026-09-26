export type Task={id:string;title:string;question:string;label:string;window:string;type:string}
export type Metric={auroc:number;auprc:number;f1:number;sensitivity:number;specificity:number;positive_rate:number;test_samples:number;status:string}
export type FeatureValue=number|null
export type DemoSample=Record<string,unknown>
export type Summary={cohort:{stays:number;patients:number;window_hours:number};features:string[];missingness:Record<string,number>;tasks:Record<string,Metric>;robustness:{task:string;mask_rate:number;auroc:number;auprc:number;f1:number}[];demo_samples:DemoSample[]}
export type Prediction={task:string;task_title:string;ranking_score:number;risk_band:string;source:string;top_contributors:{feature:string;direction:string;contribution:number}[];disclaimer:string}
async function request<T>(path:string,init?:RequestInit):Promise<T>{const r=await fetch(path,init);if(!r.ok){let m=`Request failed (${r.status})`;try{m=(await r.json()).detail??m}catch{}throw new Error(m)}return r.json()}
export function selectModelFeatures(sample:DemoSample,featureNames:readonly string[]):Record<string,FeatureValue>{return Object.fromEntries(featureNames.flatMap(name=>{const value=sample[name];return value===null||typeof value==='number'?[[name,value]]:[]}))}
export const api={tasks:()=>request<{tasks:Task[];disclaimer:string}>('/api/tasks'),summary:()=>request<Summary>('/api/summary'),predict:(task:string,sample:DemoSample,featureNames:readonly string[])=>request<Prediction>('/api/demo/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task,features:selectModelFeatures(sample,featureNames)})})}
