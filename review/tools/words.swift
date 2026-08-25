import Foundation
import Speech
import AVFoundation

@main
struct Main {
    static func main() async {
        let url = URL(fileURLWithPath: CommandLine.arguments[1])
        do {
            let transcriber = SpeechTranscriber(locale: Locale(identifier: "en-US"),
                                                transcriptionOptions: [],
                                                reportingOptions: [],
                                                attributeOptions: [.audioTimeRange])
            if let req = try await AssetInventory.assetInstallationRequest(supporting: [transcriber]) {
                try await req.downloadAndInstall()
            }
            let analyzer = SpeechAnalyzer(modules: [transcriber])
            let file = try AVAudioFile(forReading: url)
            let collector = Task {
                for try await result in transcriber.results where result.isFinal {
                    for run in result.text.runs {
                        let piece = String(result.text[run.range].characters)
                        if let tr = run.audioTimeRange {
                            print(String(format: "%.3f\t%.3f\t%@", tr.start.seconds, tr.end.seconds, piece))
                        } else {
                            print(String(format: "-\t-\t%@", piece))
                        }
                    }
                    fflush(stdout)
                }
            }
            if let last = try await analyzer.analyzeSequence(from: file) {
                try await analyzer.finalizeAndFinish(through: last)
            } else {
                await analyzer.cancelAndFinishNow()
            }
            _ = try await collector.value
        } catch {
            FileHandle.standardError.write("ERROR: \(error)\n".data(using:.utf8)!); exit(1)
        }
    }
}
