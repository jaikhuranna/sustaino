import SwiftUI

// DIY Video Model
struct DIYVideo: Identifiable {
    let id = UUID()
    let name: String
    let youtubeLink: String
    
    // Extracts YouTube video ID from the link
    var videoID: String? {
        if let url = URL(string: youtubeLink),
           let queryItems = URLComponents(url: url, resolvingAgainstBaseURL: true)?.queryItems {
            return queryItems.first(where: { $0.name == "v" })?.value
        }
        return youtubeLink.components(separatedBy: "/").last?.components(separatedBy: "?").first
    }
    
    // YouTube Thumbnail URL
    var thumbnailURL: String {
        "https://img.youtube.com/vi/\(videoID ?? "")/hqdefault.jpg"
    }
}

// DIY Categories Model
struct DIYCategory: Identifiable {
    let id = UUID()
    let category: String
    let videos: [DIYVideo]
}

// Sample Data
let diyData: [DIYCategory] = [
    DIYCategory(category: "Plastic Bottle", videos: [
        DIYVideo(name: "Bird Feeder", youtubeLink: "https://youtu.be/9DKzHucqY1I?si=OirtHI0-v22VEoJa"),
        DIYVideo(name: "Planter", youtubeLink: "https://youtube.com/shorts/TNmhYM4d3Z8?si=gve5k_GPGIh-oOZi"),
        DIYVideo(name: "Storage Container", youtubeLink: "https://youtu.be/N4aT-mN8Bb8?si=yuMtzeH7I05iOVUa")
    ]),
    DIYCategory(category: "Aluminum Can", videos: [
        DIYVideo(name: "Pen Holder", youtubeLink: "https://youtu.be/d8qPVmd3Wcw?si=zvx5j5wvBFdcECVZ"),
        DIYVideo(name: "Lantern", youtubeLink: "https://youtu.be/U9qBVGZnkyg?si=BsSrtE9Av7FdPTx0"),
        DIYVideo(name: "Wind Chime", youtubeLink: "https://youtube.com/shorts/Sj4OnEbPBjw?si=xfIKpP4f31bsHtAB")
    ]),
    DIYCategory(category: "Glass Bottle", videos: [
        DIYVideo(name: "Vase", youtubeLink: "https://youtu.be/WxKZ8hhcmvg?si=e19don-JeyShnqDL"),
        DIYVideo(name: "Candle Holder", youtubeLink: "https://youtube.com/shorts/yBcjV0TsVGM?si=HWBwgP-mMc7OhfUe"),
        DIYVideo(name: "Terrarium", youtubeLink: "https://youtube.com/shorts/YRuZ4-7E9v4?si=i0JjQPqlAMbYxo1v")
    ])
]

// DIY Video List View
struct DIYListView: View {
    var body: some View {
        NavigationView {
            List {
                ForEach(diyData) { category in
                    Section(header: Text(category.category).font(.headline)) {
                        ForEach(category.videos) { video in
                            DIYVideoRow(video: video)
                        }
                    }
                }
            }
            .navigationTitle("DIY Ideas")
        }
    }
}

// DIY Video Row
struct DIYVideoRow: View {
    let video: DIYVideo

    var body: some View {
        HStack {
            AsyncImage(url: URL(string: video.thumbnailURL)) { image in
                image.resizable().aspectRatio(contentMode: .fill)
            } placeholder: {
                ProgressView()
            }
            .frame(width: 100, height: 60)
            .cornerRadius(8)

            VStack(alignment: .leading) {
                Text(video.name).font(.headline)
                Text("Tap to watch").font(.subheadline).foregroundColor(.gray)
            }

            Spacer()
        }
        .padding(.vertical, 5)
        .onTapGesture {
            if let url = URL(string: video.youtubeLink) {
                UIApplication.shared.open(url)
            }
        }
    }
}

// Preview
struct DIYListView_Previews: PreviewProvider {
    static var previews: some View {
        DIYListView()
    }
}
