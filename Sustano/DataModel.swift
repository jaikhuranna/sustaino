import Foundation
import UIKit

class DataModel {
    let bucketName: String
    let accessToken: String
    var uploadedImageURL: String?  // Stores the uploaded image URL
    
    static var lastScansImages: [UIImage] = []

    
    init(bucketName: String, accessToken: String) {
        self.bucketName = bucketName
        self.accessToken = accessToken
    }
    
    /// List all images in the bucket
    func listImages(completion: @escaping ([String]?) -> Void) {
        let url = URL(string: "https://storage.googleapis.com/storage/v1/b/\(bucketName)/o")!
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.addValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        
        let task = URLSession.shared.dataTask(with: request) { data, _, error in
            guard let data = data, error == nil else {
                print("Error listing images: \(error?.localizedDescription ?? "Unknown error")")
                completion(nil)
                return
            }
            
            if let jsonResponse = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let items = jsonResponse["items"] as? [[String: Any]] {
                let imageNames = items.compactMap { $0["name"] as? String }
                completion(imageNames)
            } else {
                completion(nil)
            }
        }
        task.resume()
    }

    /// Upload an image to GCS
    func uploadImage(filePath: String, completion: @escaping (Bool, String?) -> Void) {
        let fileName = (filePath as NSString).lastPathComponent
        let url = URL(string: "https://storage.googleapis.com/upload/storage/v1/b/\(bucketName)/o?uploadType=media&name=\(fileName)")!
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.addValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        request.addValue("application/octet-stream", forHTTPHeaderField: "Content-Type")
        
        do {
            let fileData = try Data(contentsOf: URL(fileURLWithPath: filePath))
            request.httpBody = fileData
        } catch {
            print("Error reading file: \(error)")
            completion(false, nil)
            return
        }
        
        let task = URLSession.shared.dataTask(with: request) { [weak self] data, _, error in
            if let error = error {
                print("Upload failed: \(error.localizedDescription)")
                completion(false, nil)
                return
            }
            
            let imageURL = "https://storage.googleapis.com/\(self?.bucketName ?? "")/\(fileName)"
            self?.uploadedImageURL = imageURL
            completion(true, imageURL)
        }
        task.resume()
    }
    
    /// Handle button tap to upload image
    func checkButtonTapped(filePath: String, completion: @escaping (String?) -> Void) {
        uploadImage(filePath: filePath) { [weak self] success, url in
            DispatchQueue.main.async {
                if success, let url = url {
                    print("✅ Upload successful: \(url)")
                    self?.uploadedImageURL = url
//                    self?.showConfirmation()
                    completion(url)
                    
                    
                } else {
                    print("❌ Upload failed")
                    completion(nil)
                }
            }
        }
    }
    
    /// Show confirmation alert
//    private func showConfirmation() {
//        let alert = UIAlertController(title: "Success", message: "Image uploaded successfully!", preferredStyle: .alert)
//        alert.addAction(UIAlertAction(title: "OK", style: .default))
//        
//        if let rootVC = UIApplication.shared.windows.first?.rootViewController {
//            rootVC.present(alert, animated: true, completion: nil)
//        }
//    }
}
