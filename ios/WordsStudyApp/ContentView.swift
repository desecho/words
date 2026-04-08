import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var apiService: APIService

    var body: some View {
        Group {
            if apiService.isAuthenticated {
                AppShellView()
            } else {
                LoginView()
            }
        }
    }
}

private struct AppShellView: View {
    var body: some View {
        TabView {
            StudyScreen()
                .tabItem {
                    Label("Study", systemImage: "rectangle.stack.fill")
                }

            LearnScreen()
                .tabItem {
                    Label("Learn", systemImage: "list.bullet.clipboard")
                }
        }
    }
}
