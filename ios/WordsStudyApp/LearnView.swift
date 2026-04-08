import SwiftUI

struct LearnScreen: View {
    @EnvironmentObject private var apiService: APIService

    @State private var alertMessage: String?
    @State private var hasLoaded = false
    @State private var isLoading = false
    @State private var selectedLanguage: StudyLanguage = .en
    @State private var words: [LearnWordItem] = []

    var body: some View {
        NavigationStack {
            List {
                Section {
                    VStack(alignment: .leading, spacing: 16) {
                        Text("Incorrect words")
                            .font(.system(size: 30, weight: .bold, design: .rounded))

                        Text("Review the words whose most recent Study result was incorrect.")
                            .foregroundStyle(.secondary)

                        Picker("Language", selection: $selectedLanguage) {
                            ForEach(StudyLanguage.allCases) { language in
                                Text(language.title)
                                    .tag(language)
                            }
                        }
                        .pickerStyle(.segmented)

                        Text(resultsLabel)
                            .font(.subheadline.weight(.semibold))
                            .foregroundStyle(.secondary)
                    }
                    .listRowInsets(EdgeInsets(top: 18, leading: 20, bottom: 18, trailing: 20))
                    .listRowBackground(Color.clear)
                }

                if isLoading, words.isEmpty {
                    Section {
                        HStack {
                            Spacer()
                            ProgressView("Loading incorrect words...")
                            Spacer()
                        }
                        .padding(.vertical, 24)
                    }
                } else if words.isEmpty {
                    Section {
                        ContentUnavailableView(
                            "No incorrect words",
                            systemImage: "text.book.closed",
                            description: Text("\(selectedLanguage.title) words will appear here after they are graded as incorrect in Study.")
                        )
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 20)
                    }
                } else {
                    Section {
                        ForEach(words) { word in
                            VStack(alignment: .leading, spacing: 8) {
                                Text(word.prompt)
                                    .font(.headline)

                                Text(word.ru)
                                    .font(.title3.weight(.semibold))

                                Text(word.partOfSpeechLabel)
                                    .font(.caption.weight(.medium))
                                    .foregroundStyle(.secondary)
                            }
                            .padding(.vertical, 6)
                        }
                    } header: {
                        Text(selectedLanguage.cue)
                    }
                }
            }
            .listStyle(.insetGrouped)
            .scrollContentBackground(.hidden)
            .background(
                LinearGradient(
                    colors: [
                        Color(red: 0.96, green: 0.97, blue: 1.0),
                        Color(red: 0.92, green: 0.98, blue: 0.93),
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()
            )
            .navigationTitle("Learn")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Logout") {
                        apiService.logout()
                    }
                }

                ToolbarItem(placement: .topBarLeading) {
                    if isLoading {
                        ProgressView()
                    }
                }
            }
            .refreshable {
                await loadWords(for: selectedLanguage)
            }
            .task {
                guard !hasLoaded else {
                    return
                }

                hasLoaded = true
                await loadWords(for: selectedLanguage)
            }
            .onChange(of: selectedLanguage) { _, newLanguage in
                guard hasLoaded else {
                    return
                }

                Task {
                    await loadWords(for: newLanguage)
                }
            }
            .alert("Learn Error", isPresented: alertIsPresented) {
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

    private var resultsLabel: String {
        words.count == 1 ? "1 incorrect word" : "\(words.count) incorrect words"
    }

    private func loadWords(for language: StudyLanguage) async {
        let requestedLanguage = language
        isLoading = true

        defer {
            if selectedLanguage == requestedLanguage {
                isLoading = false
            }
        }

        do {
            let fetchedWords = try await apiService.fetchIncorrectWords(language: language)

            if selectedLanguage == requestedLanguage {
                words = fetchedWords
            }
        } catch {
            if selectedLanguage == requestedLanguage {
                words = []
            }

            alertMessage = error.localizedDescription
        }
    }
}
