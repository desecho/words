import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var apiService: APIService

    @State private var password = ""
    @State private var username = ""

    var body: some View {
        NavigationStack {
            ZStack {
                LinearGradient(
                    colors: [
                        Color(red: 0.95, green: 0.97, blue: 1.0),
                        Color(red: 0.99, green: 0.96, blue: 0.9),
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()

                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        HStack {
                            Spacer()

                            Image("Logo")
                                .resizable()
                                .scaledToFit()
                                .frame(maxWidth: 280)
                                .shadow(color: .black.opacity(0.08), radius: 14, x: 0, y: 6)

                            Spacer()
                        }
                        .padding(.top, 8)

                        VStack(alignment: .leading, spacing: 10) {
                            Text("Words Study")
                                .font(.system(size: 34, weight: .bold, design: .rounded))

                            Text("Use the same account as the web app to review study cards and revisit missed words.")
                                .foregroundStyle(.secondary)
                        }

                        VStack(spacing: 16) {
                            TextField("Username", text: $username)
                                .textInputAutocapitalization(.never)
                                .autocorrectionDisabled()
                                .padding()
                                .background(.white.opacity(0.9), in: RoundedRectangle(cornerRadius: 18))

                            SecureField("Password", text: $password)
                                .padding()
                                .background(.white.opacity(0.9), in: RoundedRectangle(cornerRadius: 18))
                        }

                        if let errorMessage = apiService.errorMessage {
                            Text(errorMessage)
                                .font(.callout)
                                .foregroundStyle(.red)
                        }

                        Button {
                            Task {
                                await apiService.login(
                                    username: username.trimmingCharacters(in: .whitespacesAndNewlines),
                                    password: password
                                )
                            }
                        } label: {
                            HStack {
                                Spacer()

                                if apiService.isLoading {
                                    ProgressView()
                                        .tint(.white)
                                }

                                Text("Log In")
                                    .fontWeight(.semibold)

                                Spacer()
                            }
                            .padding()
                            .background(
                                LinearGradient(
                                    colors: [
                                        Color(red: 0.1, green: 0.33, blue: 0.81),
                                        Color(red: 0.0, green: 0.58, blue: 0.64),
                                    ],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                ),
                                in: RoundedRectangle(cornerRadius: 18)
                            )
                            .foregroundStyle(.white)
                        }
                        .disabled(username.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || password.isEmpty || apiService.isLoading)

                        Text("Debug builds connect to the local backend on 127.0.0.1:8000. Release builds use the deployed API.")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }
                    .padding(24)
                }
            }
            .navigationBarHidden(true)
        }
    }
}
