import React, { useState, useMemo, useRef, useEffect, useCallback } from "react";

/* ===========================================================================
   PreventFire — Générateur de rapports de prévention incendie
   Référentiel : AR 07/07/1994 — Annexes 2/1 (BB) et 3/1 (BM)
   =========================================================================== */

const STYLES = `
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700;800;900&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

.pf-root{
  --ink:#15181C; --ink-2:#2A2F36; --paper:#EEEFE9; --surface:#FFFFFF;
  --line:#DCDED6; --line-2:#C7CABF; --mut:#6B7079;
  --green:#1B6E47; --green-2:#2FA968; --green-soft:#E7F2EB;
  --red:#C0252C; --red-soft:#FAE9E9;
  --amber:#C5810A; --amber-soft:#FAF1DD;
  --slate:#5B6470; --slate-soft:#ECEEF1;
  --hazard:#F4C20D;
  color:var(--ink);
  font-family:'Inter',system-ui,sans-serif;
  -webkit-font-smoothing:antialiased;
  line-height:1.45;
}
.pf-root *{box-sizing:border-box;}
.pf-mono{font-family:'IBM Plex Mono',ui-monospace,monospace;}
.pf-disp{font-family:'Archivo','Inter',sans-serif;}

.pf-shell{background:var(--paper);min-height:600px;border:1px solid var(--line-2);
  border-radius:4px;overflow:hidden;display:flex;flex-direction:column;}

.pf-hazard{height:6px;background:repeating-linear-gradient(45deg,
  var(--ink) 0 16px,var(--hazard) 16px 32px);}

.pf-top{background:var(--ink);color:#F4F4F0;display:flex;align-items:center;
  gap:14px;padding:14px 20px;}
.pf-mark{width:34px;height:34px;border-radius:3px;background:var(--green-2);
  display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.pf-wordmark{font-family:'Archivo';font-weight:900;letter-spacing:-0.02em;
  font-size:18px;line-height:1;}
.pf-wordmark span{color:var(--green-2);}
.pf-sub{font-family:'IBM Plex Mono';font-size:10.5px;color:#9CA2A0;
  letter-spacing:0.04em;text-transform:uppercase;margin-top:3px;}
.pf-topmeta{margin-left:auto;text-align:right;font-family:'IBM Plex Mono';
  font-size:11px;color:#9CA2A0;}
.pf-topmeta b{color:#F4F4F0;font-weight:600;}

.pf-body{display:flex;flex:1;min-height:0;}

.pf-rail{width:248px;flex-shrink:0;background:var(--surface);
  border-right:1px solid var(--line);padding:14px 0;overflow-y:auto;}
.pf-rail-h{font-family:'IBM Plex Mono';font-size:10px;letter-spacing:0.12em;
  text-transform:uppercase;color:var(--mut);padding:0 18px 10px;}
.pf-step{display:flex;gap:12px;align-items:flex-start;padding:11px 18px;
  cursor:pointer;border-left:3px solid transparent;position:relative;
  transition:background .12s;}
.pf-step:hover{background:var(--paper);}
.pf-step.on{background:var(--green-soft);border-left-color:var(--green);}
.pf-step.done .pf-num{background:var(--green);color:#fff;border-color:var(--green);}
.pf-num{width:26px;height:26px;border-radius:50%;border:1.5px solid var(--line-2);
  font-family:'Archivo';font-weight:800;font-size:12px;display:flex;
  align-items:center;justify-content:center;flex-shrink:0;color:var(--ink-2);
  background:var(--surface);}
.pf-step.on .pf-num{border-color:var(--green);color:var(--green);}
.pf-step-t{font-size:13px;font-weight:600;line-height:1.25;}
.pf-step-meta{font-family:'IBM Plex Mono';font-size:10px;color:var(--mut);
  margin-top:3px;display:flex;gap:7px;align-items:center;}
.pf-dot{width:7px;height:7px;border-radius:50%;display:inline-block;}

.pf-rail-stats{margin:14px 18px 0;padding-top:14px;border-top:1px solid var(--line);}
.pf-bar{height:8px;border-radius:4px;background:var(--line);overflow:hidden;
  display:flex;margin-bottom:8px;}
.pf-statline{display:flex;justify-content:space-between;font-size:11px;
  color:var(--mut);margin-top:5px;}
.pf-statline b{color:var(--ink);font-family:'IBM Plex Mono';}

.pf-main{flex:1;min-width:0;overflow-y:auto;padding:26px 30px 40px;}
.pf-eyebrow{font-family:'IBM Plex Mono';font-size:11px;letter-spacing:0.1em;
  text-transform:uppercase;color:var(--green);font-weight:600;}
.pf-h{font-family:'Archivo';font-weight:800;font-size:25px;letter-spacing:-0.02em;
  margin:5px 0 4px;line-height:1.1;}
.pf-lede{color:var(--mut);font-size:13.5px;max-width:62ch;margin-bottom:22px;}

.pf-card{background:var(--surface);border:1px solid var(--line);border-radius:4px;
  padding:18px;margin-bottom:16px;}
.pf-field{margin-bottom:14px;}
.pf-label{display:block;font-size:11px;font-weight:600;letter-spacing:0.04em;
  text-transform:uppercase;color:var(--ink-2);margin-bottom:6px;
  font-family:'IBM Plex Mono';}
.pf-input,.pf-textarea,.pf-select{width:100%;border:1px solid var(--line-2);border-radius:3px;
  padding:9px 11px;font-size:13.5px;font-family:'Inter';background:var(--surface);
  color:var(--ink);}
.pf-input:focus,.pf-textarea:focus,.pf-select:focus{outline:none;border-color:var(--green);
  box-shadow:0 0 0 3px var(--green-soft);}
.pf-textarea{resize:vertical;min-height:60px;line-height:1.5;}
.pf-grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.pf-grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;}

.pf-types{display:flex;gap:10px;}
.pf-type{flex:1;border:1.5px solid var(--line-2);border-radius:4px;padding:14px;
  cursor:pointer;background:var(--surface);transition:all .12s;}
.pf-type.on{border-color:var(--green);background:var(--green-soft);}
.pf-type-t{font-family:'Archivo';font-weight:800;font-size:15px;}
.pf-type-c{font-family:'IBM Plex Mono';font-size:11px;color:var(--green);
  font-weight:600;margin-top:2px;}
.pf-type-d{font-size:12px;color:var(--mut);margin-top:6px;line-height:1.4;}

/* hypotheses toggles */
.pf-hyp-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px;}
.pf-hyp-item{display:flex;align-items:center;justify-content:space-between;
  padding:8px 11px;border:1px solid var(--line);border-radius:4px;
  background:var(--paper);font-size:12.5px;}
.pf-hyp-item.on{border-color:var(--green);background:var(--green-soft);}
.pf-sw{width:34px;height:18px;border-radius:9px;background:var(--line-2);
  position:relative;cursor:pointer;transition:.15s;flex-shrink:0;}
.pf-sw.on{background:var(--green);}
.pf-sw::after{content:"";position:absolute;width:12px;height:12px;border-radius:50%;
  background:#fff;top:3px;left:3px;transition:.15s;}
.pf-sw.on::after{left:19px;}

/* upload */
.pf-drop{border:2px dashed var(--line-2);border-radius:5px;padding:26px;
  text-align:center;cursor:pointer;transition:all .12s;background:var(--paper);}
.pf-drop:hover{border-color:var(--green);background:var(--green-soft);}
.pf-drop-t{font-weight:600;font-size:13.5px;margin-top:8px;}
.pf-drop-s{font-size:12px;color:var(--mut);margin-top:3px;}
.pf-file{display:flex;align-items:center;gap:12px;background:var(--green-soft);
  border:1px solid var(--green);border-radius:4px;padding:11px 14px;
  font-size:13px;margin-top:12px;}
.pf-file b{font-weight:600;}

/* buttons */
.pf-btn{font-family:'Inter';font-weight:600;font-size:13.5px;padding:10px 18px;
  border-radius:4px;border:1px solid transparent;cursor:pointer;
  display:inline-flex;align-items:center;gap:8px;transition:all .12s;}
.pf-btn:disabled{opacity:.45;cursor:not-allowed;}
.pf-btn-primary{background:var(--green);color:#fff;}
.pf-btn-primary:hover:not(:disabled){background:#155939;}
.pf-btn-ghost{background:var(--surface);color:var(--ink);border-color:var(--line-2);}
.pf-btn-ghost:hover:not(:disabled){border-color:var(--ink-2);}
.pf-btn-ink{background:var(--ink);color:#fff;}
.pf-btn-ink:hover:not(:disabled){background:#000;}
.pf-btn-red{background:var(--red);color:#fff;}
.pf-btn-red:hover:not(:disabled){background:#9a1e23;}
.pf-nav{display:flex;justify-content:space-between;margin-top:8px;}

/* AI panel */
.pf-ai{border:1px solid var(--slate);border-radius:5px;overflow:hidden;
  margin-top:16px;}
.pf-ai-h{background:var(--ink);color:#fff;padding:11px 16px;display:flex;
  align-items:center;gap:9px;font-size:13px;font-weight:600;}
.pf-ai-b{padding:16px;background:var(--surface);}
.pf-ai-syn{font-size:13px;line-height:1.55;color:var(--ink-2);
  border-left:3px solid var(--green-2);padding-left:12px;margin-bottom:14px;}
.pf-obs{display:flex;gap:11px;padding:11px 0;border-top:1px solid var(--line);}
.pf-obs-grav{flex-shrink:0;width:6px;border-radius:3px;}
.pf-obs-cat{font-family:'IBM Plex Mono';font-size:10px;text-transform:uppercase;
  letter-spacing:0.06em;color:var(--mut);}
.pf-obs-pt{font-weight:600;font-size:13px;margin:2px 0;}
.pf-obs-c{font-size:12.5px;color:var(--ink-2);line-height:1.5;}
.pf-spin{width:15px;height:15px;border:2px solid rgba(255,255,255,.3);
  border-top-color:#fff;border-radius:50%;animation:pf-rot .7s linear infinite;}
@keyframes pf-rot{to{transform:rotate(360deg)}}

/* checklist items */
.pf-toolbar{display:flex;align-items:center;justify-content:space-between;
  margin-bottom:14px;gap:12px;flex-wrap:wrap;}
.pf-toggle{display:flex;align-items:center;gap:8px;font-size:12.5px;
  color:var(--ink-2);cursor:pointer;font-weight:500;}
.pf-switch{width:36px;height:20px;border-radius:10px;background:var(--line-2);
  position:relative;transition:.15s;flex-shrink:0;}
.pf-switch.on{background:var(--green);}
.pf-switch::after{content:"";position:absolute;width:16px;height:16px;
  border-radius:50%;background:#fff;top:2px;left:2px;transition:.15s;}
.pf-switch.on::after{left:18px;}

.pf-item{background:var(--surface);border:1px solid var(--line);border-radius:4px;
  margin-bottom:10px;overflow:hidden;}
.pf-item.nc{border-color:var(--red);}
.pf-item.cf{border-color:var(--green);}
.pf-item.na{opacity:.55;}
.pf-item-top{display:flex;gap:13px;padding:14px 16px;align-items:flex-start;}
.pf-ref{font-family:'IBM Plex Mono';font-size:11px;font-weight:600;color:#fff;
  background:var(--ink-2);padding:3px 7px;border-radius:3px;flex-shrink:0;
  white-space:nowrap;}
.pf-item.na .pf-ref{background:var(--mut);}
.pf-art{font-family:'IBM Plex Mono';font-size:10px;color:var(--mut);
  margin-top:3px;letter-spacing:0.02em;}
.pf-item-main{flex:1;min-width:0;}
.pf-item-l{font-weight:600;font-size:14px;line-height:1.35;}
.pf-item-h{font-size:12px;color:var(--mut);margin-top:3px;line-height:1.45;}
.pf-status{display:flex;gap:6px;margin-top:11px;flex-wrap:wrap;}
.pf-sbtn{font-size:11.5px;font-weight:600;padding:6px 11px;border-radius:3px;
  border:1.5px solid var(--line-2);background:var(--surface);cursor:pointer;
  color:var(--mut);transition:all .1s;font-family:'Inter';}
.pf-sbtn.s-conforme.on{background:var(--green);border-color:var(--green);color:#fff;}
.pf-sbtn.s-non_conforme.on{background:var(--red);border-color:var(--red);color:#fff;}
.pf-sbtn.s-verifier.on{background:var(--amber);border-color:var(--amber);color:#fff;}
.pf-sbtn.s-so.on{background:var(--slate);border-color:var(--slate);color:#fff;}
.pf-item-exp{padding:0 16px 14px;border-top:1px solid var(--line);
  margin-top:0;padding-top:13px;}

/* projects list */
.pf-proj-item{display:flex;align-items:center;gap:12px;padding:12px 16px;
  border:1px solid var(--line);border-radius:4px;background:var(--surface);
  margin-bottom:8px;cursor:pointer;transition:border-color .12s;}
.pf-proj-item:hover{border-color:var(--green-2);}
.pf-proj-meta{flex:1;min-width:0;}
.pf-proj-name{font-weight:600;font-size:13.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.pf-proj-sub{font-size:11.5px;color:var(--mut);margin-top:2px;font-family:'IBM Plex Mono';}
.pf-badge{display:inline-block;font-family:'IBM Plex Mono';font-size:10px;
  padding:2px 7px;border-radius:3px;font-weight:600;}
.pf-badge.BB{background:var(--slate-soft);color:var(--slate);}
.pf-badge.BM{background:var(--amber-soft);color:var(--amber);}

/* report */
.pf-report{background:var(--surface);border:1px solid var(--line);border-radius:4px;
  padding:0;overflow:hidden;}
.pf-rep-hd{background:var(--ink);color:#fff;padding:22px 28px;display:flex;
  justify-content:space-between;align-items:flex-start;}
.pf-rep-title{font-family:'Archivo';font-weight:900;font-size:21px;letter-spacing:-0.02em;}
.pf-rep-ref{font-family:'IBM Plex Mono';font-size:11px;color:#9CA2A0;margin-top:4px;}
.pf-stamp{border:3px solid;border-radius:6px;padding:9px 16px;text-align:center;
  transform:rotate(-3deg);}
.pf-stamp-t{font-family:'Archivo';font-weight:900;font-size:17px;line-height:1;
  letter-spacing:0.02em;}
.pf-stamp-s{font-family:'IBM Plex Mono';font-size:9px;letter-spacing:0.1em;
  margin-top:3px;text-transform:uppercase;}
.pf-stamp.fav{border-color:var(--green-2);color:var(--green-2);}
.pf-stamp.cond{border-color:var(--hazard);color:var(--hazard);}
.pf-stamp.def{border-color:#FF6B6B;color:#FF6B6B;}

.pf-rep-body{padding:24px 28px;}
.pf-rep-meta{display:grid;grid-template-columns:1fr 1fr;gap:6px 24px;
  font-size:13px;margin-bottom:22px;padding-bottom:20px;
  border-bottom:1px solid var(--line);}
.pf-rep-meta div{display:flex;gap:8px;}
.pf-rep-meta span{color:var(--mut);min-width:90px;font-size:12px;
  font-family:'IBM Plex Mono';}
.pf-sec-h{font-family:'Archivo';font-weight:800;font-size:14px;text-transform:uppercase;
  letter-spacing:0.04em;margin:20px 0 12px;display:flex;align-items:center;gap:9px;}
.pf-sec-h .pf-tag{font-family:'IBM Plex Mono';font-size:11px;padding:2px 8px;
  border-radius:10px;font-weight:600;}
.pf-tag.red{background:var(--red-soft);color:var(--red);}
.pf-tag.amber{background:var(--amber-soft);color:var(--amber);}
.pf-tag.green{background:var(--green-soft);color:var(--green);}
.pf-finding{border-left:3px solid;padding:12px 0 12px 14px;margin-bottom:12px;}
.pf-finding.nc{border-color:var(--red);}
.pf-finding.vf{border-color:var(--amber);}
.pf-finding-top{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap;}
.pf-finding-ref{font-family:'IBM Plex Mono';font-size:11px;font-weight:600;
  color:var(--ink-2);}
.pf-finding-l{font-weight:700;font-size:13.5px;}
.pf-finding-ann{font-family:'IBM Plex Mono';font-size:10px;color:var(--mut);
  text-transform:uppercase;}
.pf-finding-c{font-size:13px;color:var(--ink-2);margin-top:5px;line-height:1.5;}
.pf-finding-m{font-size:12.5px;margin-top:7px;background:var(--paper);
  border-radius:3px;padding:8px 11px;line-height:1.5;}
.pf-finding-m b{font-family:'IBM Plex Mono';font-size:10px;text-transform:uppercase;
  letter-spacing:0.05em;color:var(--green);display:block;margin-bottom:3px;}
.pf-empty{font-size:13px;color:var(--mut);font-style:italic;padding:6px 0;}

.pf-note{background:var(--amber-soft);border:1px solid var(--amber);border-radius:4px;
  padding:11px 14px;font-size:12px;color:#7a5208;line-height:1.5;margin-top:16px;
  display:flex;gap:9px;}

.pf-save-bar{display:flex;align-items:center;gap:10px;padding:10px 0;
  border-top:1px solid var(--line);margin-top:12px;}
.pf-save-msg{font-size:12px;color:var(--green);font-family:'IBM Plex Mono';}

@media print{
  .pf-no-print{display:none !important;}
  .pf-shell{border:none;}
  .pf-main{padding:0;overflow:visible;}
  .pf-report{border:none;}
  .pf-finding{break-inside:avoid;}
}
@media(max-width:760px){
  .pf-rail{display:none;}
  .pf-grid2,.pf-grid3{grid-template-columns:1fr;}
  .pf-types{flex-direction:column;}
  .pf-hyp-grid{grid-template-columns:1fr;}
}
`;

/* ---------- icons ---------- */
const I = {
  flame: (c = "#fff", s = 18) => (
    <svg width={s} height={s} viewBox="0 0 24 24" fill="none">
      <path d="M12 2c1 3-1 4-2 6-1.5 3 0 5 0 5s-2-1-2-4c-2 1.5-3 4-3 6a7 7 0 0014 0c0-4-3-6-4-9-1-2.5-3-3-3-4z" fill={c} /></svg>
  ),
  exit: (c = "#fff", s = 18) => (
    <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" /><path d="M16 17l5-5-5-5" /><path d="M21 12H9" /></svg>
  ),
  building: (c = "#fff", s = 18) => (
    <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="3" width="16" height="18" rx="1" /><path d="M9 7h.01M15 7h.01M9 11h.01M15 11h.01M9 15h.01M15 15h.01" /></svg>
  ),
  shield: (c = "#fff", s = 18) => (
    <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
  ),
  doc: (c = "#fff", s = 18) => (
    <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><path d="M14 2v6h6M9 13h6M9 17h6" /></svg>
  ),
  spark: (c = "#fff", s = 18) => (
    <svg width={s} height={s} viewBox="0 0 24 24" fill={c}>
      <path d="M12 2l1.8 5.4L19 9l-5.2 1.6L12 16l-1.8-5.4L5 9l5.2-1.6L12 2z" /></svg>
  ),
  upload: (c = "#1B6E47", s = 26) => (
    <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" /></svg>
  ),
  save: (c = "#fff", s = 16) => (
    <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z" /><polyline points="17,21 17,13 7,13 7,21" /><polyline points="7,3 7,8 15,8" /></svg>
  ),
  folder: (c = "#fff", s = 16) => (
    <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" /></svg>
  ),
  trash: (c = "#fff", s = 14) => (
    <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3,6 5,6 21,6" /><path d="M19,6v14a2,2 0 01-2,2H7a2,2 0 01-2-2V6m3,0V4a2,2 0 012-2h4a2,2 0 012,2v2" /></svg>
  ),
  word: (c = "#fff", s = 16) => (
    <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><path d="M14 2v6h6" /><path d="M8 13l2 6 2-4 2 4 2-6" /></svg>
  ),
};

/* ---------- Checklist items ------------------------------------------------ */

/*
  Structure d'un item :
  { ref, label, applies:["BB","BM"], requiresHyp:"parking"|null,
    ann:{BB:"...",BM:"..."}, hint:string|{BB,BM} }
*/

const STEPS = [
  { id: "projet",     num: "01", title: "Projet & plans",                   kind: "setup"  },
  {
    id: "implantation", num: "02", title: "Implantation & accès",            kind: "check",
    items: [
      { ref:"1.1", label:"Accessibilité & stationnement des services d'incendie", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.1.1",BM:"Annexe 3/1 art.1.1"},
        hint:{BB:"Voie d'accès ≥ 4 m (libre), hauteur libre ≥ 4 m, rayon 11/15 m, pente ≤ 6 %, portance 13 t/essieu. Véhicule à ≤ 60 m d'une façade (plain-pied).",
              BM:"Idem BB, et voie permettant 3 véhicules de 15 t simultanément ; distance voie–façade entre 4 et 10 m. Accessible en permanence."} },
      { ref:"1.2", label:"Constructions annexes", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.1.2",BM:"Annexe 3/1 art.1.2"},
        hint:"Auvents, encorbellements et adjonctions ne peuvent compromettre ni l'évacuation ni l'action des secours." },
      { ref:"1.3", label:"Distance horizontale entre bâtiments", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.1.3",BM:"Annexe 3/1 art.1.3"},
        hint:{BB:"Distance ≥ (h+10)/2,5 · cos α ou rayonnement ≤ 15 kW/m². Parois contiguës REI 60 ou EI 60.",
              BM:"Distance ≥ (h+10)/2,5 · cos α ou rayonnement ≤ 15 kW/m². Parois contiguës REI 120 ou EI 120 ; sas EI 60."} },
      { ref:"1.4", label:"Accessibilité des façades (BM)", applies:["BM"],
        ann:{BM:"Annexe 3/1 art.1.4"},
        hint:{BM:"Au moins une longue façade longée par voie accessible ; distance bord de voie–façade entre 4 et 10 m. Sinon : baies réputées inaccessibles aux auto-échelles."} },
    ],
  },
  {
    id: "comparti", num: "03", title: "Compartimentage & sorties",          kind: "check",
    items: [
      { ref:"2.1", label:"Superficie maximale des compartiments", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.2.1",BM:"Annexe 3/1 art.2.1"},
        hint:{BB:"< 2500 m² (3500 m² pour plain-pied, L ≤ 90 m). Au-delà : sprinklage + EFC.",
              BM:"< 2500 m² ; un compartiment par niveau en principe. Au-delà : sprinklage + EFC."} },
      { ref:"2.2.1", label:"Nombre de sorties par compartiment", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.2.2.1",BM:"Annexe 3/1 art.2.2.1"},
        hint:{BB:"1 sortie si < 100 pers. ; 2 si 100–< 500 ; 2 + n si ≥ 500.",
              BM:"1 sortie si baie/terrasse accessible auto-échelle ; 2 dès 50 pers. (< 500) ; 2 + n si ≥ 500."} },
      { ref:"2.2.2", label:"Disposition des sorties", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.2.2.2",BM:"Annexe 3/1 art.2.2.2"},
        hint:"Sorties dans zones opposées du compartiment. Sous-sol : chemin vers extérieur, parois EI 30, portes EI₁ 30." },
    ],
  },
  {
    id: "elements", num: "04", title: "Éléments de construction & réaction au feu", kind: "check",
    items: [
      { ref:"3.1", label:"Traversées des parois RF — Annexe 7 ch.1", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.3.1 + Annexe 7 ch.1",BM:"Annexe 3/1 art.3.1 + Annexe 7 ch.1"},
        hint:"Traversées (fluides, électricité) et joints de dilatation ne peuvent altérer le Rf exigé. Manchons intumescents, mortier RF, caissons coupe-feu." },
      { ref:"3.2", label:"Éléments structuraux — stabilité au feu (R)", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.3.2 tableau 2.1",BM:"Annexe 3/1 art.3.2 tableau 3.1"},
        hint:{BB:"Au-dessus Ei : R 30 (1 niveau) / R 60 (plusieurs). Sous Ei : R 60. Toiture : R 30 sauf si séparée par EI 30.",
              BM:"Au-dessus Ei : R 60. Sous Ei (plancher Ei compris) : R 120. Attestation ingénieur en stabilité à remettre."} },
      { ref:"3.3", label:"Parois verticales — locaux à occupation nocturne", applies:["BB","BM"], requiresHyp:"logements",
        ann:{BB:"Annexe 2/1 art.3.3",BM:"Annexe 3/1 art.3.3"},
        hint:{BB:"Parois EI 30 (1 niveau) / EI 60 (plusieurs) ; EI 60 sous Ei. Porte d'entrée EI₁ 30.",
              BM:"Parois EI 60 ; porte d'entrée de logement EI₁ 30."} },
      { ref:"3.4", label:"Faux-plafonds dans chemins d'évacuation", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.3.4",BM:"Annexe 3/1 art.3.4"},
        hint:"Faux-plafonds EI 30 dans les chemins d'évacuation et locaux accessibles au public. Espace sous faux-plafond divisé en volumes ≤ 25 × 25 m (écrans EI 30, classe A1/A2-s1,d0)." },
      { ref:"3.5.1.1", label:"Façade simple paroi — jonction compartiment/plancher", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.3.5.1.1",BM:"Annexe 3/1 art.3.5.1.1"},
        hint:"Fixations ossature R 60 à chaque niveau. Liaison parois de compartiment/façade EI 60. Joints dalle/façade EI 60 au droit des séparations horizontales." },
      { ref:"3.5.1.2", label:"Façades en vis-à-vis — propagation entre compartiments", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.3.5.1.2",BM:"Annexe 3/1 art.3.5.1.2"},
        hint:{BB:"Parties sans E 30 : distance ≥ (h+10)/2,5 · cos α, ou rayonnement ≤ 15 kW/m².",
              BM:"Parties sans E 60 : distance ≥ (h+10)/2,5 · cos α, ou rayonnement ≤ 15 kW/m²."} },
      { ref:"3.5.2", label:"Façade double paroi — cavité interrompue", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.3.5.2",BM:"Annexe 3/1 art.3.5.2"},
        hint:"Cavité interrompue par un élément E 60 au droit de chaque paroi de compartiment et des planchers." },
      { ref:"5/1 art.2", label:"Réaction au feu — type d'occupation (1/2/3)", applies:["BB","BM"],
        ann:{BB:"Annexe 5/1 art.2",BM:"Annexe 5/1 art.2"},
        hint:"Type 1 (non-autonomes), type 2 (autonomes dormants), type 3 (autonomes vigilants). Le MO détermine le type et le communique à l'autorité compétente." },
      { ref:"5/1 tab.I", label:"Réaction au feu — locaux à risque accru", applies:["BB","BM"],
        ann:{BB:"Annexe 5/1 art.3 tableau I",BM:"Annexe 5/1 art.3 tableau I"},
        hint:"Locaux techniques, parkings, cuisines, gaines : revêtements A2-s3,d2 (parois), A2-s3,d0 (plafonds), A2FL-s2 (sols). Preuve à la réception." },
      { ref:"5/1 tab.II", label:"Réaction au feu — locaux selon occupation", applies:["BB","BM"],
        ann:{BB:"Annexe 5/1 art.3 tableau II",BM:"Annexe 5/1 art.3 tableau II"},
        hint:"Classes de réaction au feu selon tableau II. Preuve à la réception : marquage CE, classement ou BENOR/ATG + attestation de pose." },
      { ref:"5/1 tab.III", label:"Réaction au feu — chemins d'évacuation & cages d'escalier", applies:["BB","BM"],
        ann:{BB:"Annexe 5/1 art.4/1 tableau III",BM:"Annexe 5/1 art.4/1 tableau III"},
        hint:"Classes de réaction au feu selon tableau III pour les chemins et cages. Attestations à remettre à la réception." },
      { ref:"5/1 art.6", label:"Réaction au feu — façades extérieures", applies:["BB","BM"],
        ann:{BB:"Annexe 5/1 art.6.1.1",BM:"Annexe 5/1 art.6.1.1"},
        hint:"Revêtement ext. ≥ B-s3,d1. Composants substantiels ≥ A2-s3,d0. Montants ossature A1. Attestations à remettre à la réception." },
      { ref:"5/1 art.8", label:"Réaction au feu — toitures BROOF(t1)", applies:["BB","BM"],
        ann:{BB:"Annexe 5/1 art.8.1+8.3",BM:"Annexe 5/1 art.8.1+8.3"},
        hint:"Produits de toiture : classe BROOF(t1). Idem pour balcons, terrasses, lanterneaux, panneaux PV. Attestations à remettre à la réception." },
    ],
  },
  {
    id: "evacuation", num: "05", title: "Cages d'escalier & chemins d'évacuation", kind: "check",
    items: [
      { ref:"4.1", label:"Parois entre compartiments", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.4.1",BM:"Annexe 3/1 art.4.1"},
        hint:{BB:"EI 30 (1 niveau au-dessus Ei) / EI 60 (plusieurs ou sous Ei). Communication : porte EI₁ 30 FA.",
              BM:"EI 120. Communication : sas (parois EI 120, portes EI₁ 30 FA, ≥ 2 m²)."} },
      { ref:"4.2.1", label:"Encloisonnement des cages d'escalier", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.4.2.1",BM:"Annexe 3/1 art.4.2.1"},
        hint:"Escaliers reliant plusieurs compartiments : encloisonnés. Prescriptions de compartimentage applicables." },
      { ref:"4.2.2.1", label:"Parois intérieures des cages", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.4.2.2.1",BM:"Annexe 3/1 art.4.2.2.1"},
        hint:{BB:"Parois intérieures des cages d'escalier : EI 60.",BM:"Parois intérieures des cages d'escalier : EI 120."} },
      { ref:"4.2.2.2", label:"Accès au niveau d'évacuation depuis chaque cage", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.4.2.2.2",BM:"Annexe 3/1 art.4.2.2.2"},
        hint:"Chaque cage donne accès, directement ou par chemin d'évacuation, à un niveau d'évacuation." },
      { ref:"4.2.2.3", label:"Communication compartiment/cage — porte EI₁ 30", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.4.2.2.3",BM:"Annexe 3/1 art.4.2.2.3"},
        hint:"À chaque niveau : porte EI₁ 30 FA entre compartiment et cage d'escalier." },
      { ref:"4.2.2.4", label:"Cages communes à plusieurs compartiments", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.4.2.2.4",BM:"Annexe 3/1 art.4.2.2.4"},
        hint:"Cage commune à plusieurs compartiments : chaque compartiment y accède par une porte EI₁ 30 FA." },
      { ref:"4.2.2.5", label:"Séparation cages sous-sol / cages niveaux supérieurs", applies:["BB","BM"], requiresHyp:"ss",
        ann:{BB:"Annexe 2/1 art.4.2.2.5",BM:"Annexe 3/1 art.4.2.2.5"},
        hint:"Cages sous-sol ≠ prolongement des cages supérieures. Si superposées : parois EI 60, portes EI₁ 30." },
      { ref:"4.2.2.6", label:"Baie de ventilation ≥ 1 m² en tête de cage", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.4.2.2.6",BM:"Annexe 3/1 art.4.2.2.6"},
        hint:"Baie à l'air libre ≥ 1 m² (0,5 m² si cage ≤ 300 m², max 2 niveaux) en tête de cage. Commande manuelle au niveau Ei (entre 1,4 et 2 m, à ≤ 2 m de la porte cage). Conforme NBN S21-208/3." },
      { ref:"4.2.3.1", label:"Escaliers — stabilité au feu, giron, hauteur de marche, pente", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.4.2.3.1",BM:"Annexe 3/1 art.4.2.3.1"},
        hint:{BB:"R 30. Giron ≥ 20 cm. Marche ≤ 18 cm. Pente ≤ 75 %. Mains courantes (une seule si largeur < 120 cm).",
              BM:"R 60. Contre-marches pleines. Giron ≥ 20 cm. Marche ≤ 18 cm. Pente ≤ 75 %. Mains courantes."} },
      { ref:"4.2.3.2", label:"Largeur utile escaliers & paliers ≥ 0,80 m", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.4.2.3.2",BM:"Annexe 3/1 art.4.2.3.2"},
        hint:"Largeur utile ≥ 0,80 m. Différence ≤ 1 unité de passage entre volées et paliers d'une même cage." },
      { ref:"4.3", label:"Escaliers extérieurs — classe A1", applies:["BB","BM"], requiresHyp:"esc_ext",
        ann:{BB:"Annexe 2/1 art.4.3",BM:"Annexe 3/1 art.4.3"},
        hint:"Donnent accès au niveau d'évacuation. Aucune stabilité au feu requise, mais matériau de classe A1. BM : cages à parois, communication porte EI₁ 30, aucun point à < 1 m d'une façade sans EI 60." },
      { ref:"4.4.1.1", label:"Largeur utile chemins d'évacuation ≥ 0,80 m", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.4.4.1.1",BM:"Annexe 3/1 art.4.4.1.1"},
        hint:"Chemins et portes d'évacuation ≥ 0,80 m. Coursives ≥ 0,60 m. Largeur ≥ unité de passage requise par le nombre d'occupants." },
      { ref:"4.4.1.2", label:"Définition d'une sortie de compartiment", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.4.4.1.2",BM:"Annexe 3/1 art.4.4.1.2"},
        hint:"Sortie = cage int. (art.4.2), cage ext. (art.4.3), accès direct extérieur au niveau Ei, ou chemin d'évacuation au niveau Ei conforme à art.4.4.2." },
      { ref:"4.4.1.3", label:"Portes — pas de verrouillage côté évacuation", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.4.4.1.3",BM:"Annexe 3/1 art.4.4.1.3"},
        hint:"Sur parcours d'évacuation : portes s'ouvrant facilement et immédiatement dans le sens de l'évacuation, sans clé." },
      { ref:"4.4.2", label:"Chemins d'évacuation au niveau d'évacuation (Ei)", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.4.4.2",BM:"Annexe 3/1 art.4.4.2"},
        hint:{BB:"Parois verticales intérieures EI 60. Portes EI₁ 30 FA.",
              BM:"Parois verticales intérieures EI 120. Portes EI₁ 60 FA."} },
      { ref:"4.4.3", label:"Chemins d'évacuation aux autres niveaux", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.4.4.3",BM:"Annexe 3/1 art.4.4.3"},
        hint:"Parois EI 30 ; portes EI₁ 30 FA. Exception : occupation exclusivement diurne, superficie < 1250 m²." },
      { ref:"4.4.4", label:"Sas d'accès à la cage (> 6 appts/niveau) — BM", applies:["BM"],
        ann:{BM:"Annexe 3/1 art.4.4.4"},
        hint:{BM:"Si > 6 appartements par cage et par niveau : sas (parois EI 60, deux portes EI₁ 30 FA)."} },
      { ref:"4.5", label:"Signalisation — numéros de niveaux dans les cages", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.4.5",BM:"Annexe 3/1 art.4.5"},
        hint:"Numéro de niveau visible à chaque accès à la cage d'escalier, sur les paliers et dans les dégagements." },
    ],
  },
  {
    id: "locaux", num: "06", title: "Locaux & espaces techniques", kind: "check",
    items: [
      { ref:"5.1.1", label:"Local technique = compartiment distinct", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.5.1.1",BM:"Annexe 3/1 art.5.1.1"},
        hint:"Local technique = compartiment distinct. Parois REI 60 ou EI 60 ; portes EI₁ 30 FA. Distinct des caves." },
      { ref:"5.1.2.2", label:"Chaufferie — Annexe 7, point 4", applies:["BB","BM"], requiresHyp:"chaufferie",
        ann:{BB:"Annexe 2/1 art.5.1.2.2",BM:"Annexe 3/1 art.5.1.2.2"},
        hint:"Chaufferies (locaux de chauffe ≥ 30 kW) conformes aux dispositions de l'Annexe 7, point 4." },
      { ref:"5.1.3", label:"Cabine haute tension — NBN C18-200", applies:["BB","BM"], requiresHyp:"ht",
        ann:{BB:"Annexe 2/1 art.5.1.3",BM:"Annexe 3/1 art.5.1.3"},
        hint:"Cabines HT : compartiment distinct, conformes à NBN C18-200." },
      { ref:"5.1.4", label:"Gaines verticales & horizontales (BM)", applies:["BM"],
        ann:{BM:"Annexe 3/1 art.5.1.4"},
        hint:{BM:"Gaines verticales EI 120, portillons EI₁ 60. Gaines horizontales EI 120 au droit des parois de compartiment."} },
      { ref:"5.2.1", label:"Parking — éléments structuraux, EFC, cloisonnement", applies:["BB","BM"], requiresHyp:"parking",
        ann:{BB:"Annexe 2/1 art.5.2.1",BM:"Annexe 3/1 art.5.2.1"},
        hint:"R 120. Si > 625 m² : EFC. Paroi parking/bâtiment EI 60 + sas (EI 60 + portes EI₁ 30) ou porte EI₁ 60. ≥ 2 cages d'escalier, distance ≤ 45 m." },
      { ref:"5.2.4", label:"Parking — DAI si superficie > 1250 m²", applies:["BB","BM"], requiresHyp:"parking",
        ann:{BB:"Annexe 2/1 art.5.2.4",BM:"Annexe 3/1 art.5.2.4"},
        hint:"Parking > 1250 m² : installation de détection automatique d'incendie conforme NBN S21-100." },
      { ref:"5.3", label:"Salles > 500 personnes", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.5.3",BM:"Annexe 3/1 art.5.3"},
        hint:{BB:"Sous-sol : ≤ 3 m. Parois = parois de compartiment ; portes EI₁ 30. Sorties comme pour les compartiments.",
              BM:"Sous-sol : ≤ 3 m, évacuation par escaliers/rampes (≤ 10 %). Parois EI 120 ; communication porte EI₁ 60 ou sas."} },
    ],
  },
  {
    id: "equipements", num: "07", title: "Équipement des immeubles", kind: "check",
    items: [
      { ref:"6.4", label:"Ascenseurs — gaine EI 60, rappel au niveau Ei", applies:["BB","BM"], requiresHyp:"ascenseur",
        ann:{BB:"AR 09/03/2009 + Annexe 2/1 art.6.4",BM:"AR 09/03/2009 + Annexe 3/1 art.6.4"},
        hint:{BB:"Gaine + paliers EI 60. Portes palières E 30. Rappel au niveau Ei (NBN EN 81-73).",
              BM:"Gaine + paliers EI 60 formant sas à tous les niveaux. Portes d'accès sas EI₁ 30. Portes palières E 30. Rappel au niveau Ei."} },
      { ref:"6.5.1", label:"Installations électriques BT — conformité RGIE", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.6.5.1",BM:"Annexe 3/1 art.6.5.1"},
        hint:"Conformité RGIE. Contrôle par organisme agréé avant mise en service. Copie PV à remettre à la zone de secours." },
      { ref:"6.5.2", label:"Canalisations circuits de sécurité PH 60 (BM)", applies:["BM"],
        ann:{BM:"Annexe 3/1 art.6.5.2"},
        hint:{BM:"Canalisations des circuits de sécurité (éclairage urgence, alarme, détection, désenfumage) : PH 60 ou Rf 1 h (NBN 713-020)."} },
      { ref:"6.5.4", label:"Éclairage de sécurité ≥ 1 lux / 5 lux aux endroits dangereux", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.6.5.4",BM:"Annexe 3/1 art.6.5.4"},
        hint:"Éclairage sécurité ≥ 1 lux (5 lux aux endroits dangereux). Appareils autonomes admis. Conformité NBN EN 1838/50172. Copie attestation à remettre." },
      { ref:"6.6", label:"Installations de gaz — NBN D 51-003", applies:["BB","BM"], requiresHyp:"gaz",
        ann:{BB:"Annexe 2/1 art.6.6",BM:"Annexe 3/1 art.6.6"},
        hint:"Conformité NBN D 51-003. Attestation à remettre. Canalisation jaune ocre (RAL 1004). Vanne trottoir signalée 'G'." },
      { ref:"6.7", label:"Installations aérauliques — clapets RF, arrêt sur détection", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.6.7",BM:"Annexe 3/1 art.6.7"},
        hint:"Clapets RF aux traversées, clapets coupe-fumée, arrêt des groupes sur détection. Contrôle organisme indépendant, copie PV à remettre." },
      { ref:"6.8.1", label:"Dispositifs d'extinction obligatoires", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.6.8.1",BM:"Annexe 3/1 art.6.8.1"},
        hint:"Type, nombre et emplacement déterminés avec les services d'incendie. ≥ 1 dévidoir par compartiment > 500 m². Bouches/bornes incendie ≤ 100 m zone dense." },
      { ref:"6.8.4", label:"Alarme incendie — signal perceptible en tout point", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.6.8.4",BM:"Annexe 3/1 art.6.8.4"},
        hint:"Boutons-poussoirs sous vitre + sirène audible partout. Boutons à proximité des baies vers extérieur, paliers, dégagements. Fonctionne sans alimentation principale." },
      { ref:"6.8.5.2", label:"Extincteurs portatifs ≥ 6 kg ABC / 6 L eau pulvérisée", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.6.8.5.2",BM:"Annexe 3/1 art.6.8.5.2"},
        hint:"≥ 1 extincteur 6 kg poudre ABC ou 6 L eau pulv. + additif par 150 m² et par niveau. Marquage CE (BENOR recommandé). Fixé au mur et signalé." },
      { ref:"6.8.5.3", label:"Robinets d'incendie armés (RIA) — BM", applies:["BM"],
        ann:{BM:"Annexe 3/1 art.6.8.5.3"},
        hint:{BM:"RIA conformes EN 671-1. Pression ≥ 2,5 bar, débit ≥ 72 L/min (3 RIA simultanés, 30 min). Canalisations rouges (RAL 3000)."} },
      { ref:"6.8.5.4.2", label:"Borne incendie ≤ 100 m (zone commerciale) / 200 m", applies:["BB","BM"],
        ann:{BB:"Annexe 2/1 art.6.8.5.4.2",BM:"Annexe 3/1 art.6.8.5.4.2"},
        hint:"Borne/bouche aérienne ≤ 100 m (zone commerciale) ou ≤ 200 m (ailleurs) de l'entrée. Sinon : installer borne conforme NBN S21-019." },
      { ref:"AGW", label:"Détecteurs de fumée dans les logements", applies:["BB","BM"], requiresHyp:"logements",
        ann:{BB:"AGW du 21/10/2004",BM:"AGW du 21/10/2004"},
        hint:"≥ 1 détecteur optique certifié BOSEC par niveau de logement. ≥ 2 si > 80 m². Si ≥ 4 détecteurs : interconnectés ou sur centrale. Conformité AGW art.4." },
    ],
  },
  { id: "rapport", num: "08", title: "Synthèse & rapport", kind: "report" },
];

const CHECK_STEPS = STEPS.filter((s) => s.kind === "check");
const STATUS = [
  { k: "conforme",     l: "Conforme",       c: "var(--green)" },
  { k: "non_conforme", l: "Non conforme",    c: "var(--red)"   },
  { k: "verifier",     l: "À vérifier",      c: "var(--amber)" },
  { k: "so",           l: "Sans objet",      c: "var(--slate)" },
];

const HYP_LABELS = {
  logements:  "Logements",
  ss:         "Sous-sol",
  parking:    "Parking",
  ascenseur:  "Ascenseur",
  gaz:        "Installation gaz",
  chaufferie: "Chaufferie (≥ 30 kW)",
  esc_ext:    "Escalier extérieur",
  ht:         "Cabine haute tension",
};

const DEFAULT_HYP = {
  logements: true, ss: false, parking: false, ascenseur: false,
  gaz: false, chaufferie: false, esc_ext: false, ht: false,
};

function fileToBase64(file) {
  return new Promise((res, rej) => {
    const r = new FileReader();
    r.onload = () => res(r.result.split(",")[1]);
    r.onerror = () => rej(new Error("Lecture impossible"));
    r.readAsDataURL(file);
  });
}

const LS_KEY = "preventfire_state";

function saveLocal(state) {
  try { localStorage.setItem(LS_KEY, JSON.stringify(state)); } catch (_) {}
}

function loadLocal() {
  try { return JSON.parse(localStorage.getItem(LS_KEY) || "null"); } catch (_) { return null; }
}

/* ============================================================= */
export default function PreventFire() {
  const [step, setStep] = useState(0);
  const [project, setProject] = useState({
    id: null, reference: "", name: "", address: "", type: "BB",
    date: new Date().toISOString().slice(0, 10), agent: "", zone: "ZSBW",
    hyp: { ...DEFAULT_HYP },
  });
  const [items, setItems] = useState({});
  const [files, setFiles] = useState([]);   // [{name, base64, mediaType, isPdf, size}]
  const [ai, setAi] = useState({ status: "idle", synthese: "", obs: [], err: "" });
  const [onlyDef, setOnlyDef] = useState(() => {
    try { return JSON.parse(localStorage.getItem("pf_onlyDef") || "false"); } catch { return false; }
  });
  const [saveMsg, setSaveMsg] = useState("");
  const [projList, setProjList] = useState([]);
  const [zones, setZones] = useState(["ZSBW", "NAGE", "DINAPHI"]);
  const [docxStatus, setDocxStatus] = useState("idle");
  const fileRef = useRef(null);

  const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? "" : "http://localhost:5000");

  /* --- Persist onlyDef --- */
  useEffect(() => {
    try { localStorage.setItem("pf_onlyDef", JSON.stringify(onlyDef)); } catch (_) {}
  }, [onlyDef]);

  /* --- Auto-save to localStorage on change --- */
  useEffect(() => {
    saveLocal({ project, items, step });
  }, [project, items, step]);

  /* --- Load saved state on mount --- */
  useEffect(() => {
    const saved = loadLocal();
    if (saved?.project) {
      setProject((p) => ({ ...p, ...saved.project, hyp: { ...DEFAULT_HYP, ...(saved.project.hyp || {}) } }));
      if (saved.items) setItems(saved.items);
      // Don't restore step — always start at step 0
    }
    // Fetch available zones
    fetch(`${API_URL}/api/zones`).then((r) => r.ok ? r.json() : null).then((z) => { if (z?.length) setZones(z); }).catch(() => {});
    // Fetch project list
    refreshProjList();
  }, []);

  const refreshProjList = useCallback(() => {
    fetch(`${API_URL}/api/projets`).then((r) => r.ok ? r.json() : []).then(setProjList).catch(() => {});
  }, [API_URL]);

  const setItem = (id, patch) =>
    setItems((p) => ({ ...p, [id]: { status: "", comment: "", measure: "", ...p[id], ...patch } }));

  /* Is an item auto-NA for the current project? */
  const isAutoNa = (it) => {
    if (!it.applies.includes(project.type)) return true;
    if (it.requiresHyp && !project.hyp[it.requiresHyp]) return true;
    return false;
  };

  /* Visible items for a step (all, but auto-na ones grayed) */
  const stepItems = (s) => (s.items || []);

  /* Items to count for stats (exclude auto-na) */
  const activeItems = (s) => (s.items || []).filter((it) => !isAutoNa(it));

  /* Stats per step */
  const stepStat = (s) => {
    const its = activeItems(s);
    let nc = 0, cf = 0, vf = 0;
    its.forEach((it) => {
      const st = items[`${s.id}.${it.ref}`]?.status;
      if (st === "non_conforme") nc++;
      else if (st === "conforme") cf++;
      else if (st === "verifier") vf++;
    });
    return { total: its.length, nc, cf, vf, done: cf + nc + vf };
  };

  const globalStat = useMemo(() => {
    let nc = 0, cf = 0, vf = 0, total = 0;
    CHECK_STEPS.forEach((s) => {
      activeItems(s).forEach((it) => {
        total++;
        const st = items[`${s.id}.${it.ref}`]?.status;
        if (st === "non_conforme") nc++;
        else if (st === "conforme") cf++;
        else if (st === "verifier") vf++;
      });
    });
    return { nc, cf, vf, total, done: nc + cf + vf };
  }, [items, project.type, project.hyp]);

  const verdict = useMemo(() => {
    if (globalStat.nc > 0) return { t: "AVIS DÉFAVORABLE",      s: "Manquements à lever",      cls: "def" };
    if (globalStat.vf > 0) return { t: "FAVORABLE SOUS CONDITIONS", s: "Points à vérifier",    cls: "cond" };
    if (globalStat.done > 0) return { t: "AVIS FAVORABLE",       s: "Aucun manquement relevé", cls: "fav" };
    return { t: "EN COURS", s: "Inspection non finalisée", cls: "cond" };
  }, [globalStat]);

  /* ----- File upload (multiple) ----- */
  const MAX_FILES = 8;

  const onFiles = async (fileList) => {
    if (!fileList?.length) return;
    const toAdd = Array.from(fileList).slice(0, MAX_FILES - files.length);
    if (!toAdd.length) return;
    const loaded = [];
    for (const f of toAdd) {
      try {
        const b64 = await fileToBase64(f);
        loaded.push({ name: f.name, base64: b64, mediaType: f.type, isPdf: f.type === "application/pdf", size: f.size });
      } catch { /* skip unreadable */ }
    }
    setFiles((prev) => [...prev, ...loaded].slice(0, MAX_FILES));
    setAi({ status: "idle", synthese: "", obs: [], err: "" });
  };

  const removeFile = (idx) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx));
    setAi({ status: "idle", synthese: "", obs: [], err: "" });
  };

  const CATS = CHECK_STEPS.map((s) => ({ id: s.id, title: s.title }));

  const filesPayload = () => files.map((f) => ({ base64: f.base64, mediaType: f.mediaType, isPdf: f.isPdf }));

  /* ----- AI pre-analysis (free summary) ----- */
  const analyse = async () => {
    if (!files.length) return;
    setAi({ status: "loading", synthese: "", obs: [], err: "" });
    try {
      const r = await fetch(`${API_URL}/api/analyze`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ files: filesPayload(), buildingType: project.type, categories: CATS }),
      });
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || `Erreur ${r.status}`);
      const data = await r.json();
      setAi({ status: "done", synthese: data.synthese || "", obs: Array.isArray(data.observations) ? data.observations : [], err: "" });
    } catch (e) {
      setAi({ status: "error", synthese: "", obs: [], err: e.message?.includes("fetch")
        ? "Backend injoignable (port 5000)." : (e.message || "Analyse échouée.") });
    }
  };

  /* ----- AI article-by-article analysis ----- */
  const analyseArticles = async () => {
    if (!files.length) return;
    setAi((a) => ({ ...a, status: "loading_articles" }));
    try {
      const r = await fetch(`${API_URL}/api/analyze_plans`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ files: filesPayload(), buildingType: project.type, hyp: project.hyp }),
      });
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || `Erreur ${r.status}`);
      const data = await r.json();
      // Map AI statuses to frontend statuses
      const map = { ok: "conforme", nok: "non_conforme", q: "verifier", na: "so" };
      const newItems = { ...items };
      if (data.statuses) {
        CHECK_STEPS.forEach((s) => {
          (s.items || []).forEach((it) => {
            const aiSt = data.statuses[it.ref];
            if (aiSt) {
              const id = `${s.id}.${it.ref}`;
              newItems[id] = { ...(newItems[id] || {}), status: map[aiSt] || "" };
            }
          });
        });
      }
      setItems(newItems);
      setAi((a) => ({ ...a, status: "articles_done",
        articlesObs: data.observations || "" }));
    } catch (e) {
      setAi((a) => ({ ...a, status: "error", err: e.message || "Analyse article par article échouée." }));
    }
  };

  /* ----- Save project to backend ----- */
  const saveProject = async () => {
    try {
      const r = await fetch(`${API_URL}/api/projets`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...project, items }),
      });
      const data = await r.json();
      if (data.id) {
        setProject((p) => ({ ...p, id: data.id }));
        setSaveMsg("Dossier sauvegardé ✓");
        setTimeout(() => setSaveMsg(""), 3000);
        refreshProjList();
      }
    } catch {
      setSaveMsg("Erreur de sauvegarde");
      setTimeout(() => setSaveMsg(""), 3000);
    }
  };

  /* ----- Load project from backend ----- */
  const loadProject = async (id) => {
    try {
      const r = await fetch(`${API_URL}/api/projets/${id}`);
      const data = await r.json();
      if (data.id) {
        setProject({
          id: data.id, reference: data.reference || "", name: data.name || "",
          address: data.address || "", type: data.type || "BB", date: data.date || "",
          agent: data.agent || "", zone: data.zone || "ZSBW",
          hyp: { ...DEFAULT_HYP, ...(data.hyp || {}) },
        });
        setItems(data.items || {});
        setStep(1);
      }
    } catch { /* noop */ }
  };

  const deleteProject = async (id, e) => {
    e.stopPropagation();
    if (!confirm("Supprimer ce dossier ?")) return;
    await fetch(`${API_URL}/api/projets/${id}`, { method: "DELETE" }).catch(() => {});
    refreshProjList();
  };

  const newProject = () => {
    if (!confirm("Commencer un nouveau dossier ? Les données non sauvegardées seront perdues.")) return;
    setProject({ id: null, reference: "", name: "", address: "", type: "BB",
      date: new Date().toISOString().slice(0, 10), agent: "", zone: "ZSBW", hyp: { ...DEFAULT_HYP } });
    setItems({});
    setFiles([]);
    setAi({ status: "idle", synthese: "", obs: [], err: "" });
    setStep(0);
  };

  /* ----- Export .docx ----- */
  const exportDocx = async () => {
    setDocxStatus("loading");
    try {
      const r = await fetch(`${API_URL}/api/generate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          zone: project.zone, type_batiment: project.type,
          nom: project.name, adresse: project.address, reference: project.reference,
          agent: project.agent, commune: project.address, date: project.date,
        }),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.error || "Erreur génération");
      }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `PreventFire_${project.zone}_${project.type}_${project.reference || "rapport"}.docx`;
      a.click();
      URL.revokeObjectURL(url);
      setDocxStatus("done");
      setTimeout(() => setDocxStatus("idle"), 3000);
    } catch (e) {
      setDocxStatus("error_" + (e.message || "erreur"));
      setTimeout(() => setDocxStatus("idle"), 5000);
    }
  };

  const gravColor = (g) =>
    g === "manquement" ? "var(--red)" : g === "attention" ? "var(--amber)" : "var(--slate)";

  const cur = STEPS[step];
  const annRef = (it) => (it.ann?.[project.type] || (it.ann ? Object.values(it.ann)[0] : ""));
  const hintText = (it) => (typeof it.hint === "string" ? it.hint : (it.hint?.[project.type] || it.hint?.BB || ""));

  /* ========================= render ========================= */
  return (
    <div className="pf-root">
      <style>{STYLES}</style>
      <div className="pf-shell">
        <div className="pf-hazard pf-no-print" />

        {/* top bar */}
        <div className="pf-top pf-no-print">
          <div className="pf-mark">{I.flame("#15181C", 20)}</div>
          <div>
            <div className="pf-wordmark">Prevent<span>Fire</span></div>
            <div className="pf-sub">AR 07/07/1994 · Annexes 2/1 & 3/1</div>
          </div>
          <div className="pf-topmeta">
            {project.reference ? <div><b>{project.reference}</b></div> : <div>Nouveau dossier</div>}
            <div>{project.type === "BB" ? "Bâtiment Bas" : "Bâtiment Moyen"} · {project.zone}</div>
          </div>
        </div>

        <div className="pf-body">
          {/* rail */}
          <nav className="pf-rail pf-no-print">
            <div className="pf-rail-h">Workflow d'inspection</div>
            {STEPS.map((s, i) => {
              const st = s.kind === "check" ? stepStat(s) : null;
              const done = s.kind === "check" && st.total > 0 && st.done === st.total;
              return (
                <div key={s.id}
                  className={`pf-step${i === step ? " on" : ""}${done ? " done" : ""}`}
                  onClick={() => setStep(i)}>
                  <div className="pf-num">{done ? "✓" : s.num}</div>
                  <div>
                    <div className="pf-step-t">{s.title}</div>
                    {st && st.total > 0 && (
                      <div className="pf-step-meta">
                        {st.cf > 0 && <span><i className="pf-dot" style={{ background: "var(--green)" }} />{st.cf}</span>}
                        {st.nc > 0 && <span><i className="pf-dot" style={{ background: "var(--red)" }} />{st.nc}</span>}
                        {st.vf > 0 && <span><i className="pf-dot" style={{ background: "var(--amber)" }} />{st.vf}</span>}
                        <span style={{ color: "var(--mut)" }}>{st.done}/{st.total}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
            {globalStat.total > 0 && (
              <div className="pf-rail-stats">
                <div className="pf-bar">
                  <div style={{ width: `${(globalStat.cf / globalStat.total) * 100}%`, background: "var(--green)" }} />
                  <div style={{ width: `${(globalStat.nc / globalStat.total) * 100}%`, background: "var(--red)" }} />
                  <div style={{ width: `${(globalStat.vf / globalStat.total) * 100}%`, background: "var(--amber)" }} />
                </div>
                <div className="pf-statline"><span>Évalués</span><b>{globalStat.done}/{globalStat.total}</b></div>
                <div className="pf-statline"><span>Manquements</span><b style={{ color: "var(--red)" }}>{globalStat.nc}</b></div>
              </div>
            )}
          </nav>

          {/* main */}
          <main className="pf-main">

            {/* ───── ÉTAPE 1 : PROJET ───── */}
            {cur.kind === "setup" && (
              <>
                <div className="pf-eyebrow">Étape 01 · Identification</div>
                <h1 className="pf-h">Projet & plans</h1>
                <p className="pf-lede">Renseignez le dossier, classez le bâtiment, configurez les hypothèses
                  puis chargez le plan pour une pré-analyse assistée.</p>

                {/* type bâtiment */}
                <div className="pf-card">
                  <div className="pf-field">
                    <label className="pf-label">Type de bâtiment</label>
                    <div className="pf-types">
                      {[
                        { t: "BB", title: "Bâtiment Bas", code: "ANNEXE 2/1 · h < 10 m", desc: "Hauteur du niveau le plus haut sous 10 m." },
                        { t: "BM", title: "Bâtiment Moyen", code: "ANNEXE 3/1 · 10–25 m", desc: "Hauteur comprise entre 10 m et 25 m." },
                      ].map(({ t, title, code, desc }) => (
                        <div key={t} className={`pf-type${project.type === t ? " on" : ""}`}
                          onClick={() => setProject((p) => ({ ...p, type: t }))}>
                          <div className="pf-type-t">{title}</div>
                          <div className="pf-type-c">{code}</div>
                          <div className="pf-type-d">{desc}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Hypothèses */}
                  <div className="pf-field" style={{ marginBottom: 0 }}>
                    <label className="pf-label">Hypothèses du projet</label>
                    <div className="pf-hyp-grid">
                      {Object.entries(HYP_LABELS).map(([k, l]) => {
                        const on = !!project.hyp[k];
                        return (
                          <div key={k} className={`pf-hyp-item${on ? " on" : ""}`}
                            onClick={() => setProject((p) => ({ ...p, hyp: { ...p.hyp, [k]: !p.hyp[k] } }))}>
                            <span>{l}</span>
                            <div className={`pf-sw${on ? " on" : ""}`} />
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Infos dossier */}
                <div className="pf-card">
                  <div className="pf-grid2">
                    <div className="pf-field">
                      <label className="pf-label">Référence du dossier</label>
                      <input className="pf-input" value={project.reference} placeholder="PREV-2026-001"
                        onChange={(e) => setProject((p) => ({ ...p, reference: e.target.value }))} />
                    </div>
                    <div className="pf-field">
                      <label className="pf-label">Date d'inspection</label>
                      <input className="pf-input" type="date" value={project.date}
                        onChange={(e) => setProject((p) => ({ ...p, date: e.target.value }))} />
                    </div>
                  </div>
                  <div className="pf-field">
                    <label className="pf-label">Dénomination du projet</label>
                    <input className="pf-input" value={project.name} placeholder="Ex. Immeuble collectif Le Parc"
                      onChange={(e) => setProject((p) => ({ ...p, name: e.target.value }))} />
                  </div>
                  <div className="pf-field">
                    <label className="pf-label">Adresse</label>
                    <input className="pf-input" value={project.address} placeholder="Rue, n°, commune"
                      onChange={(e) => setProject((p) => ({ ...p, address: e.target.value }))} />
                  </div>
                  <div className="pf-grid2">
                    <div className="pf-field" style={{ marginBottom: 0 }}>
                      <label className="pf-label">Agent rapporteur</label>
                      <input className="pf-input" value={project.agent} placeholder="Nom de l'agent"
                        onChange={(e) => setProject((p) => ({ ...p, agent: e.target.value }))} />
                    </div>
                    <div className="pf-field" style={{ marginBottom: 0 }}>
                      <label className="pf-label">Zone de secours</label>
                      <select className="pf-select" value={project.zone}
                        onChange={(e) => setProject((p) => ({ ...p, zone: e.target.value }))}>
                        {zones.map((z) => <option key={z} value={z}>{z}</option>)}
                      </select>
                    </div>
                  </div>
                </div>

                {/* Upload + IA — multi-fichiers */}
                <div className="pf-card">
                  <label className="pf-label">
                    Plans d'architecte — PDF ou images
                    <span style={{ fontWeight: 400, color: "var(--mut)", marginLeft: 8 }}>
                      ({files.length}/{MAX_FILES} fichier{files.length !== 1 ? "s" : ""})
                    </span>
                  </label>

                  {/* Zone de dépôt toujours visible si slots restants */}
                  {files.length < MAX_FILES && (
                    <div className="pf-drop"
                      onClick={() => fileRef.current?.click()}
                      onDragOver={(e) => { e.preventDefault(); e.currentTarget.style.borderColor = "var(--green)"; }}
                      onDragLeave={(e) => { e.currentTarget.style.borderColor = ""; }}
                      onDrop={(e) => { e.preventDefault(); e.currentTarget.style.borderColor = ""; onFiles(e.dataTransfer.files); }}>
                      {I.upload()}
                      <div className="pf-drop-t">Cliquer ou glisser-déposer des plans</div>
                      <div className="pf-drop-s">PDF, PNG ou JPG · jusqu'à {MAX_FILES} fichiers · plusieurs niveaux possibles</div>
                    </div>
                  )}

                  {/* Liste des fichiers chargés */}
                  {files.map((f, idx) => (
                    <div key={idx} className="pf-file" style={{ marginTop: 8 }}>
                      {I.doc("var(--green)", 16)}
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <b style={{ display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{f.name}</b>
                        <div style={{ fontSize: 11, color: "var(--mut)", fontFamily: "IBM Plex Mono" }}>
                          {(f.size / 1024).toFixed(0)} ko · {f.isPdf ? "PDF" : "image"}
                        </div>
                      </div>
                      <button className="pf-btn pf-btn-ghost" style={{ padding: "4px 10px", fontSize: 12, flexShrink: 0 }}
                        onClick={() => removeFile(idx)}>
                        Retirer
                      </button>
                    </div>
                  ))}

                  {files.length > 0 && (
                    <div style={{ display: "flex", gap: 10, marginTop: 14, flexWrap: "wrap" }}>
                      <button className="pf-btn pf-btn-primary"
                        disabled={ai.status === "loading"} onClick={analyse}>
                        {ai.status === "loading" ? <><span className="pf-spin" />Analyse…</>
                          : <>{I.spark("#fff", 15)} Pré-analyse libre ({files.length} plan{files.length > 1 ? "s" : ""})</>}
                      </button>
                      <button className="pf-btn pf-btn-ghost"
                        disabled={ai.status === "loading_articles"} onClick={analyseArticles}
                        title="Analyse article par article et pré-remplit la checklist">
                        {ai.status === "loading_articles" ? <><span className="pf-spin" style={{ borderTopColor: "var(--ink)" }} />Analyse articles…</>
                          : <>{I.doc("var(--ink)", 15)} Analyser les articles</>}
                      </button>
                    </div>
                  )}

                  <input ref={fileRef} type="file" accept="application/pdf,image/*" multiple
                    style={{ display: "none" }} onChange={(e) => onFiles(e.target.files)} />

                  {ai.status === "error" && (
                    <div className="pf-note" style={{ background: "var(--red-soft)", borderColor: "var(--red)", color: "var(--red)", marginTop: 12 }}>
                      {I.shield("var(--red)", 16)}<div>{ai.err}</div>
                    </div>
                  )}

                  {ai.status === "articles_done" && (
                    <div className="pf-note" style={{ marginTop: 12 }}>
                      {I.spark("var(--amber)", 16)}
                      <div><b>Checklist pré-remplie.</b> {ai.articlesObs && <span> — {ai.articlesObs}</span>} Vérifiez et ajustez chaque statut avant de générer le rapport.</div>
                    </div>
                  )}

                  {ai.status === "done" && (
                    <div className="pf-ai">
                      <div className="pf-ai-h">{I.spark("#fff", 15)} Pré-analyse du plan</div>
                      <div className="pf-ai-b">
                        {ai.synthese && <div className="pf-ai-syn">{ai.synthese}</div>}
                        {ai.obs.length === 0 && <div className="pf-empty">Aucune observation extraite.</div>}
                        {ai.obs.map((o, i) => {
                          const s = CHECK_STEPS.find((x) => x.id === o.cat);
                          return (
                            <div className="pf-obs" key={i}>
                              <div className="pf-obs-grav" style={{ background: gravColor(o.gravite) }} />
                              <div>
                                <div className="pf-obs-cat">{s ? s.title : o.cat} · {o.gravite}</div>
                                <div className="pf-obs-pt">{o.point}</div>
                                <div className="pf-obs-c">{o.constat}</div>
                              </div>
                            </div>
                          );
                        })}
                        <div className="pf-note" style={{ marginTop: 14 }}>
                          {I.shield("var(--amber)", 16)}
                          <div>Pré-analyse indicative. L'IA ne lit que le plan fourni et ne se substitue pas à l'examen des pièces et rapports.</div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Save bar */}
                <div className="pf-save-bar pf-no-print">
                  <button className="pf-btn pf-btn-ghost" onClick={saveProject}>
                    {I.save("var(--ink)", 15)} Sauvegarder
                  </button>
                  <button className="pf-btn pf-btn-ghost" onClick={newProject}>
                    Nouveau dossier
                  </button>
                  {saveMsg && <span className="pf-save-msg">{saveMsg}</span>}
                </div>

                {/* Mes dossiers */}
                {projList.length > 0 && (
                  <div className="pf-card" style={{ marginTop: 16 }}>
                    <label className="pf-label" style={{ marginBottom: 12 }}>Mes dossiers sauvegardés</label>
                    {projList.map((p) => (
                      <div key={p.id} className="pf-proj-item" onClick={() => loadProject(p.id)}>
                        {I.folder("var(--mut)", 16)}
                        <div className="pf-proj-meta">
                          <div className="pf-proj-name">{p.name || p.reference || "Sans titre"}</div>
                          <div className="pf-proj-sub">
                            {p.reference && <span>{p.reference} · </span>}
                            {p.date} · {p.zone}
                          </div>
                        </div>
                        <span className={`pf-badge ${p.type}`}>{p.type}</span>
                        <button style={{ background: "none", border: "none", cursor: "pointer", padding: "4px 6px", color: "var(--mut)", flexShrink: 0 }}
                          onClick={(e) => deleteProject(p.id, e)} title="Supprimer">
                          {I.trash("var(--mut)", 14)}
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                <div className="pf-nav pf-no-print" style={{ marginTop: 16 }}>
                  <span />
                  <button className="pf-btn pf-btn-primary" onClick={() => setStep(1)}>
                    Commencer l'inspection →
                  </button>
                </div>
              </>
            )}

            {/* ───── ÉTAPES CHECKLIST ───── */}
            {cur.kind === "check" && (() => {
              const its = stepItems(cur);
              const obsForStep = ai.obs.filter((o) => o.cat === cur.id);
              const shown = onlyDef
                ? its.filter((it) => {
                  if (isAutoNa(it)) return false;
                  const st = items[`${cur.id}.${it.ref}`]?.status;
                  return st === "non_conforme" || st === "verifier" || !st;
                })
                : its;

              return (
                <>
                  <div className="pf-eyebrow">Étape {cur.num} · Vérification</div>
                  <h1 className="pf-h">{cur.title}</h1>
                  <p className="pf-lede">Statuez chaque point. Les manquements appellent un constat et une
                    mesure corrective qui alimenteront le rapport.</p>

                  {obsForStep.length > 0 && (
                    <div className="pf-ai" style={{ marginTop: 0, marginBottom: 16 }}>
                      <div className="pf-ai-h" style={{ background: "var(--slate)" }}>
                        {I.spark("#fff", 14)} Repères issus du plan
                      </div>
                      <div className="pf-ai-b" style={{ padding: "10px 16px" }}>
                        {obsForStep.map((o, i) => (
                          <div key={i} style={{ fontSize: 12.5, padding: "5px 0", color: "var(--ink-2)" }}>
                            <span style={{ display: "inline-block", width: 6, height: 6, borderRadius: 3,
                              background: gravColor(o.gravite), marginRight: 8, verticalAlign: "middle" }} />
                            <b>{o.point} :</b> {o.constat}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="pf-toolbar">
                    <div className="pf-toggle" onClick={() => setOnlyDef(!onlyDef)}>
                      <div className={`pf-switch${onlyDef ? " on" : ""}`} />
                      Manquements & non statués uniquement
                    </div>
                    <div style={{ fontFamily: "IBM Plex Mono", fontSize: 12, color: "var(--mut)" }}>
                      {shown.filter((it) => !isAutoNa(it)).length} / {its.filter((it) => !isAutoNa(it)).length} point{its.length > 1 ? "s" : ""}
                    </div>
                  </div>

                  {shown.length === 0 && (
                    <div className="pf-card pf-empty" style={{ textAlign: "center" }}>
                      {onlyDef ? "Tous les points actifs sont conformes sur cette rubrique." : "Rien à afficher."}
                    </div>
                  )}

                  {shown.map((it) => {
                    const id = `${cur.id}.${it.ref}`;
                    const d = items[id] || {};
                    const na = isAutoNa(it);
                    const cls = na ? " na" : d.status === "non_conforme" ? " nc" : d.status === "conforme" ? " cf" : "";
                    return (
                      <div className={`pf-item${cls}`} key={id}>
                        <div className="pf-item-top">
                          <div>
                            <div className="pf-ref">{it.ref}</div>
                          </div>
                          <div className="pf-item-main">
                            <div className="pf-item-l">{it.label}</div>
                            <div className="pf-art">{annRef(it)}</div>
                            {!na && <div className="pf-item-h">{hintText(it)}</div>}
                            {na && <div className="pf-item-h" style={{ fontStyle: "italic" }}>
                              Sans objet pour ce projet ({it.applies.length === 1 && it.applies[0] !== project.type ? `${it.applies[0]} uniquement` : `nécessite : ${it.requiresHyp}`})
                            </div>}
                            {!na && (
                              <div className="pf-status">
                                {STATUS.map((s) => (
                                  <button key={s.k}
                                    className={`pf-sbtn s-${s.k}${d.status === s.k ? " on" : ""}`}
                                    onClick={() => setItem(id, { status: d.status === s.k ? "" : s.k })}>
                                    {s.l}
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                        {!na && (d.status === "non_conforme" || d.status === "verifier") && (
                          <div className="pf-item-exp">
                            <div className="pf-field" style={{ marginBottom: 10 }}>
                              <label className="pf-label">Constat</label>
                              <textarea className="pf-textarea" placeholder="Description du manquement constaté…"
                                value={d.comment || ""} onChange={(e) => setItem(id, { comment: e.target.value })} />
                            </div>
                            <div className="pf-field" style={{ marginBottom: 0 }}>
                              <label className="pf-label">Mesure corrective</label>
                              <textarea className="pf-textarea" placeholder="Mesure à mettre en œuvre…"
                                value={d.measure || ""} onChange={(e) => setItem(id, { measure: e.target.value })} />
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}

                  {/* Save bar inline */}
                  <div className="pf-save-bar pf-no-print">
                    <button className="pf-btn pf-btn-ghost" style={{ padding: "8px 14px", fontSize: 12 }} onClick={saveProject}>
                      {I.save("var(--ink)", 13)} Sauvegarder
                    </button>
                    {saveMsg && <span className="pf-save-msg">{saveMsg}</span>}
                  </div>

                  <div className="pf-nav pf-no-print">
                    <button className="pf-btn pf-btn-ghost" onClick={() => setStep(step - 1)}>← Précédent</button>
                    <button className="pf-btn pf-btn-primary" onClick={() => setStep(step + 1)}>
                      {step === STEPS.length - 2 ? "Générer le rapport →" : "Suivant →"}
                    </button>
                  </div>
                </>
              );
            })()}

            {/* ───── ÉTAPE 8 : RAPPORT ───── */}
            {cur.kind === "report" && (() => {
              const findings = [], toVerify = [];
              CHECK_STEPS.forEach((s) => {
                activeItems(s).forEach((it) => {
                  const id = `${s.id}.${it.ref}`;
                  const d = items[id];
                  const ann = annRef(it);
                  if (d?.status === "non_conforme") findings.push({ cat: s.title, ann, ...it, ...d });
                  else if (d?.status === "verifier") toVerify.push({ cat: s.title, ann, ...it, ...d });
                });
              });

              const docxErr = docxStatus.startsWith("error_") ? docxStatus.slice(6) : "";

              return (
                <>
                  <div className="pf-eyebrow pf-no-print">Étape 08 · Conclusion</div>
                  <h1 className="pf-h pf-no-print">Synthèse & rapport</h1>
                  <div className="pf-nav pf-no-print" style={{ marginBottom: 18, justifyContent: "flex-end", gap: 10 }}>
                    <button className="pf-btn pf-btn-ghost" onClick={() => setStep(step - 1)}>← Modifier</button>
                    <button className="pf-btn pf-btn-ghost" onClick={saveProject}>
                      {I.save("var(--ink)", 15)} {saveMsg || "Sauvegarder"}
                    </button>
                    <button className="pf-btn pf-btn-ghost" onClick={exportDocx}
                      disabled={docxStatus === "loading"} title={`Générer le .docx via le template ${project.zone}`}>
                      {docxStatus === "loading"
                        ? <><span className="pf-spin" style={{ borderTopColor: "var(--ink)" }} />Génération…</>
                        : docxStatus === "done" ? <>{I.word("var(--green)", 15)} .docx généré ✓</>
                        : <>{I.word("var(--ink)", 15)} Export .docx ({project.zone})</>}
                    </button>
                    <button className="pf-btn pf-btn-ink" onClick={() => window.print()}>
                      {I.doc("#fff", 15)} Imprimer / PDF
                    </button>
                  </div>
                  {docxErr && (
                    <div className="pf-note pf-no-print" style={{ background: "var(--red-soft)", borderColor: "var(--red)", color: "var(--red)", marginBottom: 14 }}>
                      {I.shield("var(--red)", 16)}<div>Erreur .docx : {docxErr}. Vérifiez que le template {project.zone}/{project.type} est présent dans app/templates/.</div>
                    </div>
                  )}

                  <div className="pf-report">
                    <div className="pf-rep-hd">
                      <div>
                        <div className="pf-rep-title">Rapport de prévention incendie</div>
                        <div className="pf-rep-ref">
                          {project.reference || "—"} · AR 07/07/1994 · {project.type === "BB" ? "Annexe 2/1" : "Annexe 3/1"} · Zone {project.zone}
                        </div>
                      </div>
                      <div className={`pf-stamp ${verdict.cls}`}>
                        <div className="pf-stamp-t">{verdict.t}</div>
                        <div className="pf-stamp-s">{verdict.s}</div>
                      </div>
                    </div>

                    <div className="pf-rep-body">
                      <div className="pf-rep-meta">
                        <div><span>Projet</span>{project.name || "—"}</div>
                        <div><span>Type</span>{project.type === "BB" ? "Bâtiment Bas" : "Bâtiment Moyen"}</div>
                        <div><span>Adresse</span>{project.address || "—"}</div>
                        <div><span>Date</span>{project.date}</div>
                        <div><span>Agent</span>{project.agent || "—"}</div>
                        <div><span>Zone</span>{project.zone}</div>
                      </div>

                      <div className="pf-sec-h">
                        Manquements relevés
                        <span className="pf-tag red">{findings.length}</span>
                      </div>
                      {findings.length === 0 ? (
                        <div className="pf-empty">Aucune non-conformité relevée.</div>
                      ) : findings.map((f, i) => (
                        <div className="pf-finding nc" key={i}>
                          <div className="pf-finding-top">
                            <span className="pf-finding-ref">[{f.ref}]</span>
                            <span className="pf-finding-l">{f.label}</span>
                            <span className="pf-finding-ann">· {f.ann}</span>
                          </div>
                          {f.comment && <div className="pf-finding-c">{f.comment}</div>}
                          {f.measure && (
                            <div className="pf-finding-m"><b>Mesure corrective</b>{f.measure}</div>
                          )}
                        </div>
                      ))}

                      <div className="pf-sec-h">
                        Points à vérifier / informations manquantes
                        <span className="pf-tag amber">{toVerify.length}</span>
                      </div>
                      {toVerify.length === 0 ? (
                        <div className="pf-empty">Aucun point en suspens.</div>
                      ) : toVerify.map((f, i) => (
                        <div className="pf-finding vf" key={i}>
                          <div className="pf-finding-top">
                            <span className="pf-finding-ref">[{f.ref}]</span>
                            <span className="pf-finding-l">{f.label}</span>
                            <span className="pf-finding-ann">· {f.ann}</span>
                          </div>
                          {f.comment && <div className="pf-finding-c">{f.comment}</div>}
                        </div>
                      ))}

                      <div className="pf-sec-h">
                        Bilan de conformité
                        <span className="pf-tag green">{globalStat.cf} conformes</span>
                      </div>
                      <div style={{ fontSize: 13, color: "var(--ink-2)", lineHeight: 1.6 }}>
                        Sur {globalStat.total} points actifs examinés ({project.type === "BB" ? "Annexe 2/1" : "Annexe 3/1"}) :
                        {" "}<b style={{ color: "var(--green)" }}>{globalStat.cf} conformes</b>,
                        {" "}<b style={{ color: "var(--red)" }}>{globalStat.nc} non conformes</b>,
                        {" "}<b style={{ color: "var(--amber)" }}>{globalStat.vf} à vérifier</b>,
                        {" "}<b style={{ color: "var(--mut)" }}>{globalStat.total - globalStat.done} non statués</b>.
                      </div>

                      <div className="pf-note">
                        {I.shield("var(--amber)", 16)}
                        <div>Document généré comme aide à la rédaction. Les références d'articles
                          sont indicatives et doivent être validées au regard du texte en vigueur et
                          des modèles de votre zone de secours avant transmission officielle.</div>
                      </div>
                    </div>
                  </div>
                </>
              );
            })()}
          </main>
        </div>
      </div>
    </div>
  );
}
