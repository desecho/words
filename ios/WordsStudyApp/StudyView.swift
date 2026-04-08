import SwiftUI

struct StudyScreen: View {
    @EnvironmentObject private var apiService: APIService

    @State private var alertMessage: String?
    @State private var card: StudyCard?
    @State private var hasLoaded = false
    @State private var isLoadingCard = false
    @State private var isLoadingSummary = false
    @State private var pendingGrade: StudyGrade?
    @State private var revealed = false
    @State private var selectedLanguage: StudyLanguage = .en
    @State private var summary = StudySummaryResponse.empty

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Flashcards")
                            .font(.system(size: 32, weight: .bold, design: .rounded))

                        Text("Pick a study language, reveal the Russian translation, and grade your recall.")
                            .foregroundStyle(.secondary)
                    }

                    Picker("Language", selection: $selectedLanguage) {
                        ForEach(StudyLanguage.allCases) { language in
                            Text(language.title)
                                .tag(language)
                        }
                    }
                    .pickerStyle(.segmented)

                    LazyVGrid(
                        columns: [
                            GridItem(.flexible(), spacing: 12),
                            GridItem(.flexible(), spacing: 12),
                        ],
                        spacing: 12
                    ) {
                        ForEach(StudyLanguage.allCases) { language in
                            StudySummaryTile(
                                isSelected: language == selectedLanguage,
                                language: language,
                                summary: summaryValue(for: language)
                            )
                            .onTapGesture {
                                selectedLanguage = language
                            }
                        }
                    }

                    if isLoadingCard, card == nil {
                        ProgressView("Loading the next card...")
                            .frame(maxWidth: .infinity, alignment: .center)
                            .padding(.vertical, 48)
                    } else if let card {
                        VStack(alignment: .leading, spacing: 16) {
                            Text(summaryValue(for: selectedLanguage).label)
                                .font(.headline)
                                .foregroundStyle(.secondary)

                            Text(card.prompt)
                                .font(.system(size: 28, weight: .semibold, design: .rounded))
                                .frame(maxWidth: .infinity, alignment: .leading)

                            VStack(alignment: .leading, spacing: 8) {
                                Text("Russian")
                                    .font(.caption.weight(.semibold))
                                    .foregroundStyle(.secondary)

                                Text(revealed ? card.answer : "Translation hidden")
                                    .font(.title3.weight(.medium))
                                    .foregroundStyle(revealed ? .primary : .secondary)
                            }
                            .padding()
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(.white.opacity(0.78), in: RoundedRectangle(cornerRadius: 20))

                            if !revealed {
                                Button("Show Translation") {
                                    revealed = true
                                }
                                .buttonStyle(.borderedProminent)
                                .tint(.blue)
                            }

                            HStack(spacing: 12) {
                                GradeButton(
                                    grade: .incorrect,
                                    isDisabled: !revealed || pendingGrade != nil,
                                    isLoading: pendingGrade == .incorrect
                                ) {
                                    submitGrade(.incorrect)
                                }

                                GradeButton(
                                    grade: .correct,
                                    isDisabled: !revealed || pendingGrade != nil,
                                    isLoading: pendingGrade == .correct
                                ) {
                                    submitGrade(.correct)
                                }
                            }

                            GradeButton(
                                grade: .ignore,
                                isDisabled: !revealed || !card.canIgnore || pendingGrade != nil,
                                isLoading: pendingGrade == .ignore
                            ) {
                                submitGrade(.ignore)
                            }
                        }
                        .padding(20)
                        .background(
                            LinearGradient(
                                colors: [
                                    Color.white.opacity(0.92),
                                    Color(red: 0.88, green: 0.95, blue: 1.0),
                                ],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            ),
                            in: RoundedRectangle(cornerRadius: 28)
                        )
                    } else {
                        ContentUnavailableView(
                            "No cards are available",
                            systemImage: "checkmark.circle",
                            description: Text("This language has no due or unseen study cards right now.")
                        )
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 32)
                    }
                }
                .padding(20)
            }
            .background(
                LinearGradient(
                    colors: [
                        Color(red: 0.95, green: 0.98, blue: 1.0),
                        Color(red: 0.97, green: 0.94, blue: 0.88),
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()
            )
            .navigationTitle("Study")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Logout") {
                        apiService.logout()
                    }
                }

                ToolbarItem(placement: .topBarLeading) {
                    if isLoadingSummary {
                        ProgressView()
                    }
                }
            }
            .refreshable {
                await reloadAll()
            }
            .task {
                guard !hasLoaded else {
                    return
                }

                hasLoaded = true
                await reloadAll()
            }
            .onChange(of: selectedLanguage) { _, newLanguage in
                guard hasLoaded else {
                    return
                }

                Task {
                    await loadCard(for: newLanguage)
                }
            }
            .alert("Study Error", isPresented: alertIsPresented) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(alertMessage ?? "")
            }
        }
    }

    private var alertIsPresented: Binding<Bool> {
        Binding(
            get: { alertMessage != nil },
            set: { newValue in
                if !newValue {
                    alertMessage = nil
                }
            }
        )
    }

    private func summaryValue(for language: StudyLanguage) -> StudyLanguageSummary {
        summary.summary[language] ?? StudySummaryResponse.empty.summary[language]!
    }

    private func reloadAll() async {
        await loadSummary()
        await loadCard(for: selectedLanguage)
    }

    private func loadSummary(showErrors: Bool = true) async {
        isLoadingSummary = true

        defer {
            isLoadingSummary = false
        }

        do {
            summary = try await apiService.fetchStudySummary()
        } catch {
            if showErrors {
                alertMessage = error.localizedDescription
            }
        }
    }

    private func loadCard(for language: StudyLanguage, showErrors: Bool = true) async {
        let requestedLanguage = language
        isLoadingCard = true
        revealed = false

        defer {
            if selectedLanguage == requestedLanguage {
                isLoadingCard = false
            }
        }

        do {
            let nextCard = try await apiService.fetchNextCard(language: language)

            if selectedLanguage == requestedLanguage {
                card = nextCard
            }
        } catch {
            if selectedLanguage == requestedLanguage {
                card = nil
            }

            if showErrors {
                alertMessage = error.localizedDescription
            }
        }
    }

    private func submitGrade(_ grade: StudyGrade) {
        guard let card, revealed else {
            return
        }

        if grade == .ignore, !card.canIgnore {
            return
        }

        Task {
            pendingGrade = grade

            defer {
                pendingGrade = nil
            }

            do {
                let response = try await apiService.submitReview(
                    recordId: card.recordId,
                    language: selectedLanguage,
                    grade: grade
                )
                self.card = response.nextCard
                revealed = false
                await loadSummary(showErrors: false)
            } catch {
                alertMessage = error.localizedDescription
            }
        }
    }
}

private struct StudySummaryTile: View {
    let isSelected: Bool
    let language: StudyLanguage
    let summary: StudyLanguageSummary

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(language.title)
                .font(.headline)

            Text(language.cue)
                .font(.caption)
                .foregroundStyle(.secondary)

            HStack(spacing: 14) {
                Label("\(summary.due) due", systemImage: "clock")
                Label("\(summary.unseen) unseen", systemImage: "sparkles.rectangle.stack")
            }
            .font(.caption.weight(.medium))
            .foregroundStyle(.secondary)
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: 20)
                .fill(isSelected ? Color.blue.opacity(0.18) : Color.white.opacity(0.78))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 20)
                .stroke(isSelected ? Color.blue.opacity(0.45) : Color.white.opacity(0.0), lineWidth: 1.5)
        )
    }
}

private struct GradeButton: View {
    let grade: StudyGrade
    let isDisabled: Bool
    let isLoading: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack {
                Spacer()

                if isLoading {
                    ProgressView()
                }

                Text(grade.label)
                    .fontWeight(.semibold)

                Spacer()
            }
            .padding()
        }
        .buttonStyle(.borderedProminent)
        .tint(tintColor)
        .disabled(isDisabled)
    }

    private var tintColor: Color {
        switch grade {
        case .incorrect:
            return .orange
        case .correct:
            return .green
        case .ignore:
            return .gray
        }
    }
}
