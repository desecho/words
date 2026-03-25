/* eslint import/no-unassigned-import: 0 */
import "axios";

declare module "axios" {
    interface AxiosRequestConfig {
        metadata?: {
            requestId: string;
            startTime: number;
        };
    }
}
