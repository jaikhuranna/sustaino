import Foundation
import FirebaseStorage
import UIKit

class DataModel {
    static var lastScansImages: [UIImage] = []
    var uploadedImageURL: String?
    
    /// Upload an image to Firebase Storage
    func uploadImage(filePath: String, completion: @escaping (Bool, String?) -> Void) {
        let storage = Storage.storage()
        let storageRef = storage.reference()
        let fileName = URL(fileURLWithPath: filePath).lastPathComponent
        let imageRef = storageRef.child("sustain/" + fileName)
        let fileURL = URL(fileURLWithPath: filePath)
        
        imageRef.putFile(from: fileURL, metadata: nil) { metadata, error in
            if let error = error {
                print("❌ Upload failed: \(error.localizedDescription)")
                completion(false, nil)
                return
            }
            
            imageRef.downloadURL { (url, error) in
                if let error = error {
                    print("❌ Failed to retrieve download URL: \(error.localizedDescription)")
                    completion(false, nil)
                } else if let imageURL = url {
                    print("✅ Upload successful: \(imageURL)")
                    self.uploadedImageURL = imageURL.absoluteString
                    completion(true, imageURL.absoluteString)
                }
            }
        }
    }
    
    /// Handle button tap to upload image
    func checkButtonTapped(filePath: String, completion: @escaping (String?) -> Void) {
        uploadImage(filePath: filePath) { success, url in
            DispatchQueue.main.async {
                if success, let url = url {
                    print("✅ Image uploaded: \(url)")
                    completion(url)
                } else {
                    print("❌ Upload failed")
                    completion(nil)
                }
            }
        }
    }
}
