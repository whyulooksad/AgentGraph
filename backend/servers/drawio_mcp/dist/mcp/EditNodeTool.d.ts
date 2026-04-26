import { GraphFileManager } from "../GraphFileManager.js";
import { Tool } from "./McpServer.js";
export declare class EditNodeTool implements Tool {
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
                nodes: {
                    type: string;
                    description: string;
                    items: {
                        type: string;
                        properties: {
                            id: {
                                type: string;
                                description: string;
                            };
                            title: {
                                type: string;
                                description: string;
                            };
                            kind: {
                                type: string;
                                enum: string[];
                                description: string;
                            };
                            x: {
                                type: string;
                                description: string;
                            };
                            y: {
                                type: string;
                                description: string;
                            };
                            width: {
                                type: string;
                                description: string;
                            };
                            height: {
                                type: string;
                                description: string;
                            };
                            corner_radius: {
                                type: string;
                                minimum: number;
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
    execute({ file_path, nodes }: {
        file_path: any;
        nodes: any;
    }): Promise<{
        content: {
            type: string;
            text: string;
        }[];
    }>;
}
//# sourceMappingURL=EditNodeTool.d.ts.map