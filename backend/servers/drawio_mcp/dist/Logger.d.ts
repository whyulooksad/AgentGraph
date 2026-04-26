export declare class Logger {
    name: string;
    static main: Logger;
    static baseDir: string;
    constructor(name: string);
    log(level: "info" | "error", message: string, data?: any): void;
    info(message: string, data?: any): void;
    error(message: string, data?: any): void;
}
//# sourceMappingURL=Logger.d.ts.map