import { appendFileSync, mkdirSync } from "fs";
import { dirname, resolve } from "path";
import { fileURLToPath } from "url";
export class Logger {
    constructor(name) {
        this.name = name;
    }
    log(level, message, data = {}) {
        const label = level === "info" ? "INFO" : "ERROR";
        const line = `[${new Date().toISOString()}] ${label} ${this.name} - ${message} ${JSON.stringify(data, null, 2)}`;
        mkdirSync(Logger.baseDir, { recursive: true });
        appendFileSync(resolve(Logger.baseDir, `${this.name}.log`), `${line}\n`);
    }
    info(message, data = {}) {
        this.log("info", message, data);
    }
    error(message, data = {}) {
        this.log("error", message, data);
    }
}
Logger.main = new Logger("main");
Logger.baseDir = resolve(dirname(fileURLToPath(import.meta.url)), "../logs");
//# sourceMappingURL=Logger.js.map