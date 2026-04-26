import { JSDOM } from "jsdom";
import { installDomGlobals } from "./installGlobals.js";
const dom = new JSDOM();
installDomGlobals(dom.window);
//# sourceMappingURL=jsdom.js.map