import { JSDOM } from "jsdom";
import { installDomGlobals } from "./installGlobals.js";
import type { DomLikeWindow } from "./installGlobals.js";

const dom = new JSDOM();
installDomGlobals(dom.window as unknown as DomLikeWindow);
