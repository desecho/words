import SwiftUI

@main
struct WordsStudyAppApp: App {
    @StateObject private var apiService = APIService()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(apiService)
        }
    }
}
