const SUBTITLE_INDEX_RE = /^\d+$/u;
const SUBTITLE_TIMESTAMP_RE =
    /^\d{2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?\s+-->\s+\d{2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?(?:\s+.*)?$/u;
const WEBVTT_HEADER_RE = /^WEBVTT(?:\s.*)?$/u;

function isSubtitleTimestampLine(value: string): boolean {
    return SUBTITLE_TIMESTAMP_RE.test(value);
}

function nextNonEmptyLine(lines: string[], startIndex: number): string | null {
    for (let index = startIndex + 1; index < lines.length; index += 1) {
        const trimmedLine = lines[index].trim();
        if (trimmedLine.length > 0) {
            return trimmedLine;
        }
    }
    return null;
}

function isSubtitleIndexLine(value: string, nextLine: string | null): boolean {
    return SUBTITLE_INDEX_RE.test(value) && nextLine !== null && isSubtitleTimestampLine(nextLine);
}

export function processSubtitleText(value: string): string {
    const lines = value.split(/\r?\n/u);
    const cleanedLines: string[] = [];

    for (let index = 0; index < lines.length; index += 1) {
        const trimmedLine = lines[index].trim();

        if (trimmedLine.length === 0 || WEBVTT_HEADER_RE.test(trimmedLine)) {
            continue;
        }
        if (isSubtitleTimestampLine(trimmedLine)) {
            continue;
        }
        if (isSubtitleIndexLine(trimmedLine, nextNonEmptyLine(lines, index))) {
            continue;
        }

        cleanedLines.push(trimmedLine);
    }

    return cleanedLines.join(" ").replace(/\s+/gu, " ").trim();
}
