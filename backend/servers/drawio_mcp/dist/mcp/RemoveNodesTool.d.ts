import { GraphFileManager } from "../GraphFileManager.js";
import { Tool } from "./McpServer.js";
export declare class RemoveNodesTool implements Tool {
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
                ids: {
                    type: string;
                    description: string;
                    items: {
                        type: string;
                        description: string;
                    };
                };
            };
            required: string[];
        };
    };
    execute({ file_path, ids }: {
        file_path: any;
        ids: any;
    }): Promise<{
        content: {
            type: string;
            text: string;
        }[];
    }>;
}
//# sourceMappingURL=RemoveNodesTool.d.ts.map