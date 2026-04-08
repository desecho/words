import Foundation

@MainActor
final class APIService: ObservableObject {
    @Published var errorMessage: String?
    @Published var isAuthenticated: Bool
    @Published var isLoading = false

    private static let accessTokenKey = "words_access_token"
    private static let refreshTokenKey = "words_refresh_token"

    #if DEBUG
    private let baseURL = URL(string: "http://127.0.0.1:8000")!
    #else
    private let baseURL = URL(string: "https://api.words.example.com")!
    #endif

    private let decoder = JSONDecoder()
    private let encoder = JSONEncoder()

    init() {
        isAuthenticated = UserDefaults.standard.string(forKey: Self.accessTokenKey) != nil
    }

    private var accessToken: String? {
        get { UserDefaults.standard.string(forKey: Self.accessTokenKey) }
        set {
            UserDefaults.standard.set(newValue, forKey: Self.accessTokenKey)
            isAuthenticated = !(newValue?.isEmpty ?? true)
        }
    }

    private var refreshToken: String? {
        get { UserDefaults.standard.string(forKey: Self.refreshTokenKey) }
        set { UserDefaults.standard.set(newValue, forKey: Self.refreshTokenKey) }
    }

    func login(username: String, password: String) async {
        guard !username.isEmpty, !password.isEmpty else {
            errorMessage = "Enter a username and password."
            return
        }

        isLoading = true
        errorMessage = nil

        defer {
            isLoading = false
        }

        do {
            let payload = try encoder.encode(
                LoginRequest(username: username, password: password)
            )
            let response: LoginResponse = try await performRequest(
                path: "token/",
                method: "POST",
                body: payload,
                authorize: false,
                allowRefresh: false
            )

            accessToken = response.access
            refreshToken = response.refresh
            errorMessage = nil
        } catch {
            accessToken = nil
            refreshToken = nil
            errorMessage = error.localizedDescription
        }
    }

    func logout() {
        accessToken = nil
        refreshToken = nil
        errorMessage = nil
    }

    func fetchStudySummary() async throws -> StudySummaryResponse {
        try await performRequest(path: "study/summary/")
    }

    func fetchNextCard(language: StudyLanguage) async throws -> StudyCard? {
        let response: StudyCardResponse = try await performRequest(
            path: "study/next-card/",
            queryItems: [URLQueryItem(name: "language", value: language.rawValue)]
        )
        return response.card
    }

    func submitReview(
        recordId: Int,
        language: StudyLanguage,
        grade: StudyGrade
    ) async throws -> StudyReviewResponse {
        let payload = try encoder.encode(
            StudyReviewRequest(grade: grade, language: language, recordId: recordId)
        )
        return try await performRequest(
            path: "study/review/",
            method: "POST",
            body: payload
        )
    }

    func fetchIncorrectWords(language: StudyLanguage) async throws -> [LearnWordItem] {
        let response: LearnListResponse = try await performRequest(
            path: "study/incorrect-words/",
            queryItems: [URLQueryItem(name: "language", value: language.rawValue)]
        )
        return response.words
    }

    private func performRequest<T: Decodable>(
        path: String,
        method: String = "GET",
        queryItems: [URLQueryItem] = [],
        body: Data? = nil,
        authorize: Bool = true,
        allowRefresh: Bool = true
    ) async throws -> T {
        do {
            let request = try makeRequest(
                path: path,
                method: method,
                queryItems: queryItems,
                body: body,
                authorize: authorize
            )
            return try await send(
                request,
                decode: T.self,
                treatUnauthorizedAsAuthFailure: authorize,
                clearSessionOnUnauthorized: authorize && !allowRefresh
            )
        } catch let error as APIError {
            if case .unauthorized = error, authorize, allowRefresh {
                try await refreshAccessToken()
                let request = try makeRequest(
                    path: path,
                    method: method,
                    queryItems: queryItems,
                    body: body,
                    authorize: true
                )
                return try await send(
                    request,
                    decode: T.self,
                    treatUnauthorizedAsAuthFailure: true,
                    clearSessionOnUnauthorized: true
                )
            }

            throw error
        } catch {
            throw APIError.network(error.localizedDescription)
        }
    }

    private func refreshAccessToken() async throws {
        guard let refreshToken, !refreshToken.isEmpty else {
            handleUnauthorizedAccess()
            throw APIError.unauthorized
        }

        let payload = try encoder.encode(RefreshTokenRequest(refresh: refreshToken))

        do {
            let response: RefreshTokenResponse = try await performRequest(
                path: "token/refresh/",
                method: "POST",
                body: payload,
                authorize: false,
                allowRefresh: false
            )
            accessToken = response.access
            errorMessage = nil
        } catch {
            handleUnauthorizedAccess()
            throw APIError.unauthorized
        }
    }

    private func makeRequest(
        path: String,
        method: String,
        queryItems: [URLQueryItem],
        body: Data?,
        authorize: Bool
    ) throws -> URLRequest {
        guard var components = URLComponents(
            url: baseURL.appendingPathComponent(path),
            resolvingAgainstBaseURL: false
        ) else {
            throw APIError.invalidURL
        }

        if !queryItems.isEmpty {
            components.queryItems = queryItems
        }

        guard let url = components.url else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue("XMLHttpRequest", forHTTPHeaderField: "X-Requested-With")
        request.httpBody = body

        if authorize {
            guard let accessToken, !accessToken.isEmpty else {
                throw APIError.unauthorized
            }
            request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        }

        return request
    }

    private func send<T: Decodable>(
        _ request: URLRequest,
        decode type: T.Type,
        treatUnauthorizedAsAuthFailure: Bool,
        clearSessionOnUnauthorized: Bool
    ) async throws -> T {
        let data: Data
        let response: URLResponse

        do {
            (data, response) = try await URLSession.shared.data(for: request)
        } catch {
            throw APIError.network("Network connection error. Please try again.")
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.network("The server response was invalid.")
        }

        switch httpResponse.statusCode {
        case 200 ..< 300:
            do {
                return try decoder.decode(T.self, from: data)
            } catch {
                throw APIError.decoding
            }
        case 401:
            if treatUnauthorizedAsAuthFailure {
                if clearSessionOnUnauthorized {
                    handleUnauthorizedAccess()
                }
                throw APIError.unauthorized
            }
            throw APIError.server(serverMessage(from: data) ?? "Authentication failed.")
        case 400, 403, 404, 422:
            throw APIError.server(serverMessage(from: data) ?? "The request could not be completed.")
        case 500 ..< 600:
            throw APIError.server("The server is unavailable right now. Try again later.")
        default:
            throw APIError.unexpectedStatus(httpResponse.statusCode, serverMessage(from: data))
        }
    }

    private func handleUnauthorizedAccess() {
        accessToken = nil
        refreshToken = nil
        errorMessage = APIError.unauthorized.localizedDescription
    }

    private func serverMessage(from data: Data) -> String? {
        guard !data.isEmpty else {
            return nil
        }

        guard let json = try? JSONSerialization.jsonObject(with: data) else {
            return String(data: data, encoding: .utf8)
        }

        return flattenMessage(json)
    }

    private func flattenMessage(_ value: Any) -> String? {
        switch value {
        case let string as String:
            return string.isEmpty ? nil : string
        case let array as [Any]:
            for item in array {
                if let message = flattenMessage(item) {
                    return message
                }
            }
            return nil
        case let dictionary as [String: Any]:
            if let detail = dictionary["detail"], let message = flattenMessage(detail) {
                return message
            }

            for key in dictionary.keys.sorted() {
                guard let nestedValue = dictionary[key], let message = flattenMessage(nestedValue) else {
                    continue
                }
                return key == "non_field_errors" ? message : "\(key): \(message)"
            }

            return nil
        default:
            return nil
        }
    }
}
