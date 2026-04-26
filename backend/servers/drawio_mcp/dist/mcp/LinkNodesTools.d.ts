import { GraphFileManager } from "../GraphFileManager.js";
import { Tool } from './McpServer.js';
export declare class LinkNodesTool implements Tool {
    private fileManager;
    constructor(fileManager?: GraphFileManager);
    schema(): {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                file_path: {
                    type: string;
                    description: string;
                };
                edges: {
                    type: string;
                    description: string;
                    items: {
                        type: string;
                        properties: {
                            from: {
                                type: string;
                                description: string;
                            };
                            to: {
                                type: string;
                                description: string;
                            };
                            title: {
                                type: string;
                                description: string;
                            };
                            dashed: {
                                type: string;
                                description: string;
                            };
                            reverse: {
                                type: string;
                                description: string;
                            };
                            undirected: {
                                type: string;
                                description: string;
                            };
                        };
                        required: string[];
                    };
                };
            };
            required: string[];
        };
    };
    execute({ file_path, edges }: {
        file_path: any;
        edges: any;
    }): Promise<{
        content: {
            type: string;
            text: string;
        }[];
    }>;
}
//# sourceMappingURL=LinkNodesTools.d.ts.map