// Resolve browser tooling from installed packages or explicit local configuration.
import {createRequire} from 'node:module';
import {existsSync} from 'node:fs';
const require=createRequire(import.meta.url);
export function loadPlaywright(){
 try{return require(process.env.PLAYWRIGHT_MODULE_PATH||'playwright');}
 catch(error){throw new Error('Install Playwright with npm install --no-save playwright, or set PLAYWRIGHT_MODULE_PATH to its local module path.',{cause:error});}
}
export function browserLaunchOptions(){
 const macChrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
 const executablePath=process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||(existsSync(macChrome)?macChrome:undefined);
 return {headless:true,...(executablePath?{executablePath}:{})};
}
