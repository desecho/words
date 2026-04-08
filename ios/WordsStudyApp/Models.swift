import Foundation

enum StudyLanguage: String, Codable, CaseIterable, Identifiable {
    case en
    case fr

    var id: String { rawValue }

    var title: String {
        switch self {
        case .en:
            return "English"
        case .fr:
            return "French"
        }
    }

    var cue: String {
        switch self {
        case .en:
            return "English to Russian"
        case .fr:
            return "French to Russian"
        }
    }
}

enum StudyGrade: String, Codable, CaseIterable, Identifiable {
    case incorrect
    case correct
    case ignore

    var id: String { rawValue }

    var label: String {
        switch self {
        case .incorrect:
            return "Incorrect"
        case .correct:
            return "Correct"
        case .ignore:
            return "Ignore"
        }
    }
}

struct LoginRequest: Codable {
    let username: String
    let password: String
}

struct LoginResponse: Codable {
    let access: String
    let refresh: String
}

struct RefreshTokenRequest: Codable {
    let refresh: String
}

struct RefreshTokenResponse: Codable {
    let access: String
}

struct StudyLanguageSummary: Codable {
    let due: Int
    let label: String
    let unseen: Int
}

struct StudySummaryResponse: Decodable {
    let summary: [StudyLanguage: StudyLanguageSummary]

    private enum CodingKeys: String, CodingKey {
        case summary
    }

    private enum SummaryKeys: String, CodingKey {
        case en
        case fr
    }

    init(summary: [StudyLanguage: StudyLanguageSummary]) {
        self.summary = summary
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let summaryContainer = try container.nestedContainer(
            keyedBy: SummaryKeys.self,
            forKey: .summary
        )

        summary = [
            .en: try summaryContainer.decode(StudyLanguageSummary.self, forKey: .en),
            .fr: try summaryContainer.decode(StudyLanguageSummary.self, forKey: .fr),
        ]
    }

    static let empty = StudySummaryResponse(
        summary: [
            .en: StudyLanguageSummary(due: 0, label: "English", unseen: 0),
            .fr: StudyLanguageSummary(due: 0, label: "French", unseen: 0),
        ]
    )
}

struct StudyCard: Codable, Identifiable {
    let answer: String
    let canIgnore: Bool
    let comment: String
    let language: StudyLanguage
    let partOfSpeechAbbreviation: String
    let prompt: String
    let recordId: Int

    var id: Int { recordId }

    enum CodingKeys: String, CodingKey {
        case answer
        case canIgnore = "can_ignore"
        case comment
        case language
        case partOfSpeechAbbreviation = "part_of_speech_abbreviation"
        case prompt
        case recordId = "record_id"
    }
}

struct StudyCardResponse: Codable {
    let card: StudyCard?
}

struct StudyReviewRequest: Codable {
    let grade: StudyGrade
    let language: StudyLanguage
    let recordId: Int

    enum CodingKeys: String, CodingKey {
        case grade
        case language
        case recordId = "record_id"
    }
}

struct StudyReview: Codable {
    let dueAt: String
    let easinessFactor: Double
    let grade: StudyGrade
    let intervalDays: Int
    let language: StudyLanguage
    let quality: Int?
    let recordId: Int
    let repetition: Int

    enum CodingKeys: String, CodingKey {
        case dueAt = "due_at"
        case easinessFactor = "easiness_factor"
        case grade
        case intervalDays = "interval_days"
        case language
        case quality
        case recordId = "record_id"
        case repetition
    }
}

struct StudyReviewResponse: Codable {
    let nextCard: StudyCard?
    let review: StudyReview

    enum CodingKeys: String, CodingKey {
        case nextCard = "next_card"
        case review
    }
}

struct LearnWordItem: Codable, Identifiable {
    let language: StudyLanguage
    let lastReviewedAt: String
    let partOfSpeechLabel: String
    let prompt: String
    let recordId: Int
    let ru: String

    var id: String { "\(language.rawValue)-\(recordId)" }

    enum CodingKeys: String, CodingKey {
        case language
        case lastReviewedAt = "last_reviewed_at"
        case partOfSpeechLabel = "part_of_speech_label"
        case prompt
        case recordId = "record_id"
        case ru
    }
}

struct LearnListResponse: Codable {
    let words: [LearnWordItem]
}

enum APIError: LocalizedError {
    case invalidURL
    case network(String)
    case decoding
    case unauthorized
    case server(String)
    case unexpectedStatus(Int, String?)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "The app could not build a valid request."
        case .network(let message):
            return message.isEmpty ? "Network request failed." : message
        case .decoding:
            return "The app could not process the server response."
        case .unauthorized:
            return "Your session has expired. Please log in again."
        case .server(let message):
            return message
        case .unexpectedStatus(let statusCode, let message):
            if let message, !message.isEmpty {
                return message
            }
            return "Request failed with status \(statusCode)."
        }
    }
}
