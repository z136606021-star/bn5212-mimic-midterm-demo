export type Task={id:string;title:string;question:string;label:string;window:string;type:string}
export type Summary={cohort:{stays:number;patients:number;window_hours:number};features:string[];missingness:Record<string,number>;tasks:Record<string,any>;robustness:{task:string;mask_rate:number;auroc:number;auprc:number;f1:number}[];demo_samples:Record<string,number|null>[];};
