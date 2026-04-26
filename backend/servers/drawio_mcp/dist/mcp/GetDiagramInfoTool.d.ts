import { GraphFileManager } from "../GraphFileManager.js";
import { Tool } from "./McpServer.js";
export declare class GetDiagramInfoTool implements Tool {
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
            };
            required: string[];
        };
    };
    execute({ file_path }: {
        file_path: any;
    }): Promise<{
        content: {
            type: string;
            text: string;
        }[];
    }>;
}
//# sourceMappingURL=GetDiagramInfoTool.d.ts.map