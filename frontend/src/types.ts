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
export type StudyGrade = "incorrect" | "correct" | "ignore";

export interface StudyLanguageSummary {
    due: number;
    label: string;
    unseen: number;
}

export interface StudySummary {
    summary: Record<StudyLanguage, StudyLanguageSummary>;
}

export interface LearnWordItem {
    language: StudyLanguage;
    last_reviewed_at: string;
    part_of_speech_label: string;
    prompt: string;
    record_id: number;
    ru: string;
}

export interface LearnListResponse {
    words: LearnWordItem[];
}

export interface StatsOverview {
    records_total: number;
    review_success_rate: number;
    reviews_successful: number;
    reviews_total: number;
    texts_total: number;
    words_total: number;
}

export interface StatsLanguageSummary {
    active: number;
    due: number;
    ignored: number;
    label: string;
    reviewed_total: number;
    success_rate: number;
    successful_reviews: number;
    unseen: number;
}

export interface StatsActivity {
    recent_reviews_7d: number;
    recent_texts_added_7d: number;
    recent_words_added_7d: number;
}

export interface StatsPartOfSpeechCount {
    count: number;
    label: string;
}

export interface StatsLanguageCoverage {
    with_both: number;
    with_english: number;
    with_french: number;
}

export interface StatsCollection {
    language_coverage: StatsLanguageCoverage;
    parts_of_speech: StatsPartOfSpeechCount[];
}

export interface StatsResponse {
    activity: StatsActivity;
    collection: StatsCollection;
    overview: StatsOverview;
    study: Record<StudyLanguage, StatsLanguageSummary>;
}

export interface StudyCard {
    answer: string;
    can_ignore: boolean;
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
        quality: number | null;
        record_id: number;
        repetition: number;
    };
}

export interface PartOfSpeechOption {
    abbreviation: string;
    id: number;
    name: string;
}

export interface PartOfSpeechListResponse {
    parts_of_speech: PartOfSpeechOption[];
}

export interface CreateWordRequest {
    comment: string;
    en: string;
    fr: string;
    part_of_speech_id: number | null;
    ru: string;
}

export interface WordItem {
    comment: string;
    date_added: string;
    en: string;
    fr: string;
    id: number;
    part_of_speech: PartOfSpeechOption;
    ru: string;
}

export interface CreateWordResponse {
    record_id: number;
    word: WordItem;
}

export interface WordResponse {
    word: WordItem;
}

export interface WordListResponse {
    words: WordItem[];
}

export type UpdateWordRequest = CreateWordRequest;

export interface TextItem {
    content: string;
    date_added: string;
    id: number;
    language: StudyLanguage;
    name: string;
}

export interface TextListResponse {
    texts: TextItem[];
}

export interface TextResponse {
    text: TextItem;
}

export interface CreateTextRequest {
    content: string;
    language: StudyLanguage | null;
    name: string;
}

export interface TextPlainSegment {
    type: "text";
    value: string;
}

export interface TextMatchSegment {
    match_kind: "article" | "contraction" | "number_word" | "record";
    normalized: string;
    record_id: number | null;
    type: "match";
    value: string;
}

export type TextSegment = TextPlainSegment | TextMatchSegment;

export interface TextDetailResponse {
    segments: TextSegment[];
    text: TextItem;
}
