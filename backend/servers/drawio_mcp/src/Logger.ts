import { appendFileSync, mkdirSync } from "fs";
import { dirname, resolve } from "path";
import { fileURLToPath } from "url";

export class Logger {
  static main = new Logger("main");
  static baseDir = resolve(dirname(fileURLToPath(import.meta.url)), "../logs");

  constructor(public name: string) {}

  log(level: "info" | "error", message: string, data: any = {}) {
    const label = level === "info" ? "INFO" : "ERROR";
    const line = `[${new Date().toISOString()}] ${label} ${this.name} - ${message} ${JSON.stringify(data, null, 2)}`;
    mkdirSync(Logger.baseDir, { recursive: true });
    appendFileSync(resolve(Logger.baseDir, `${this.name}.log`), `${line}\n`);
  }

  info(message: string, data: any = {}) {
    this.log("info", message, data);
  }

  error(message: string, data: any = {}) {
    this.log("error", message, data);
  }
}
