import { $toast } from "../toast";

interface ErrorOptions {
    context?: string;
    showToast?: boolean;
}

export function handleError(error: unknown, options: ErrorOptions = {}): void {
    const context = options.context ?? "Unexpected error";
    const showToast = options.showToast ?? true;

    console.error(`[${context}]`, error);

    if (showToast) {
        $toast.error(context);
    }
}
