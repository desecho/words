/* eslint import/no-unassigned-import: 0 */
import "axios";

declare module "axios" {
    interface AxiosRequestConfig {
        hasRetriedAuthentication?: boolean;
        metadata?: {
            requestId: string;
            startTime: number;
        };
    }
}
