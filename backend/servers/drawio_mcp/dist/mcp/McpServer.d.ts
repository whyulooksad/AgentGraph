import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { Transport } from "@modelcontextprotocol/sdk/shared/transport.js";
import { Logger } from '../Logger.js';
export interface Tool {
    schema: () => {
        name: string;
        description: string;
        inputSchema: object;
    };
    execute: (args: any) => Promise<any>;
}
export interface McpServerConfig {
    tools: Tool[];
    name: string;
    version: string;
}
export declare class McpServer {
    logger: Logger;
    tools: Tool[];
    server: Server;
    constructor({ tools, name, version }: McpServerConfig, logger?: Logger);
    run(transport?: Transport): Promise<void>;
}
//# sourceMappingURL=McpServer.d.ts.map