export interface AuthProps {
    userId: number;
    timestamp: number;
    signature: string;
}

export interface JWTDecoded {
    exp: number;
    token_type: string;
}

export type StudyLanguage = "en" | "fr";
export type StudyGrade = "again" | "hard" | "easy";

export interface StudyLanguageSummary {
    due: number;
    label: string;
    unseen: number;
}

export interface StudySummary {
    summary: Record<StudyLanguage, StudyLanguageSummary>;
}

export interface StudyCard {
    answer: string;
    comment: string;
    language: StudyLanguage;
    part_of_speech_abbreviation: string;
    prompt: string;
    record_id: number;
}

export interface StudyCardResponse {
    card: StudyCard | null;
}

export interface StudyReviewRequest {
    grade: StudyGrade;
    language: StudyLanguage;
    record_id: number;
}

export interface StudyReviewResponse {
    next_card: StudyCard | null;
    review: {
        due_at: string;
        easiness_factor: number;
        grade: StudyGrade;
        interval_days: number;
        language: StudyLanguage;
        quality: number;
        record_id: number;
        repetition: number;
    };
}
