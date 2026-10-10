'use strict';
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../mdvu/assets/theme.js'), 'utf8');
function browser({dark = false, saved = null, blocked = false, lang = 'en'} = {}) {
  let ready = false;
  const events = {}, mediaEvents = {}, clicks = {}, attributes = {};
  const root = {dataset:{},lang,classList:{add(){}}};
  const media = {matches:dark,addEventListener(name,fn){mediaEvents[name]=fn;}};
  const button = {setAttribute(name,value){attributes[name]=value;},addEventListener(name,fn){clicks[name]=fn;}};
  const meta = {setAttribute(name,value){this[name]=value;}};
  const storage = {getItem(){if(blocked) throw Error('Disabled');return saved;},setItem(key,value){if(blocked) throw Error('Disabled');assert.equal(key,'mdvu-theme');saved=value;}};
  const document = {documentElement:root,querySelector(){return meta;},querySelectorAll(){return ready?[button]:[];},addEventListener(name,fn){events[name]=fn;}};
  const window = {matchMedia(query){assert.equal(query,'(prefers-color-scheme: dark)');return media;},addEventListener(name,fn){events[name]=fn;}};
  vm.runInNewContext(source,{window,document,localStorage:storage});
  return {
    theme:()=>root.dataset.theme,label:()=>attributes['aria-label'],saved:()=>saved,color:()=>meta.content,
    ready(){ready=true;events.DOMContentLoaded();},toggle(){clicks.click();},
    system(dark){media.matches=dark;mediaEvents.change();},
    storage(value,key='mdvu-theme'){events.storage({key,newValue:value});}
  };
}
for (const dark of [false,true]) {
  const b=browser({dark});
  assert.equal(b.theme(),dark?'dark':'light','System theme must apply before DOM ready');
  b.ready();b.system(!dark);assert.equal(b.theme(),dark?'light':'dark','Follow system changes before manual selection');
}
const chosen=browser({dark:false,saved:'dark'});assert.equal(chosen.theme(),'dark');chosen.ready();
assert.equal(chosen.label(),'Switch to light theme');assert.equal(chosen.color(),'#0d1624');
chosen.system(true);chosen.toggle();assert.equal(chosen.theme(),'light');assert.equal(chosen.saved(),'light');
chosen.system(true);assert.equal(chosen.theme(),'light','Manual choice must override system preference');
chosen.storage('dark');assert.equal(chosen.theme(),'dark','Sync choice made in another tab');
chosen.storage(null);assert.equal(chosen.theme(),'dark');chosen.system(false);assert.equal(chosen.theme(),'light','Clearing saved choice restores automatic mode');
const disabled=browser({dark:true,blocked:true,lang:'ru'});disabled.ready();disabled.toggle();assert.equal(disabled.theme(),'light');assert.equal(disabled.label(),'Переключить на тёмную тему');
assert.equal(browser({dark:true,saved:'invalid'}).theme(),'dark');
console.log('PASS themes: initial system mode, system changes, saved choice, manual override, tab sync, blocked storage and labels');
