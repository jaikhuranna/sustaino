import Foundation
import FirebaseStorage
import UIKit

// MARK: - Data Model
class DataModel {
    
    static var lastScansImages: [UIImage] = []
    
    static var lastScansText : [String] = []
    static var lastScansTexts: [String] = ["Lays"]
    
    static var productDetails: ProductDetails?
    static var alternativeProduct: AlternativeProduct?
    static var diyIdeas: [DIYIdea] = []
    
    var uploadedImageURL: String?
    
    struct ProductDetails {
        let name: String
        let description: String
        let healthScore: Int
        let sustainabilityScore: Int
    }
    
//    func processJSONResponse(_ jsonData: Data) -> ProductDetails? {
//        do {
//            if let outerJSON = try JSONSerialization.jsonObject(with: jsonData, options: []) as? [String: Any],
//               let resultString = outerJSON["result"] as? String {
//                
//                if let innerData = resultString.data(using: .utf8),
//                   let innerJSON = try JSONSerialization.jsonObject(with: innerData, options: []) as? [String: Any] {
//                    
//                    if let productInfo = innerJSON["product_info"] as? [String: Any],
//                       let name = productInfo["name"] as? String,
//                       let description = productInfo["description"] as? String,
//                       let healthScore = innerJSON["health_score"] as? Int,
//                       let sustainabilityScore = innerJSON["sustainability_score"] as? Int {
//                        
//                        return ProductDetails(
//                            name: name,
//                            description: description,
//                            healthScore: healthScore,
//                            sustainabilityScore: sustainabilityScore
//                        )
//                    }
//                }
//            }
//        } catch {
//            print(" Error processing JSON: \(error.localizedDescription)")
//        }
//        return nil
//    }
    
    func processJSONResponse(_ jsonData: Data) -> ProductDetails? {
        do {
            // Try to parse the JSON directly first
            if let json = try JSONSerialization.jsonObject(with: jsonData, options: []) as? [String: Any],
               let productInfo = json["product_info"] as? [String: Any],
               let name = productInfo["name"] as? String,
               let description = productInfo["description"] as? String,
               let healthScore = json["health_score"] as? Int,
               let sustainabilityScore = json["sustainability_score"] as? Int {
                
                return ProductDetails(
                    name: name,
                    description: description,
                    healthScore: healthScore,
                    sustainabilityScore: sustainabilityScore
                )
            }
        } catch {
            print("Error processing direct JSON: \(error.localizedDescription)")
        }
        
        return nil
    }
    
    struct AlternativeProduct {
        let productName: String
        let reason: String
    }
    
    func processAlternativesJSON(_ jsonData: Data) -> AlternativeProduct? {
        do {
            if let outerJSON = try JSONSerialization.jsonObject(with: jsonData, options: []) as? [String: Any],
               let alternativesString = outerJSON["alternatives"] as? String {
                
                if let innerData = alternativesString.data(using: .utf8),
                   let innerJSON = try JSONSerialization.jsonObject(with: innerData, options: []) as? [String: Any] {
                    
                    if let productName = innerJSON["alternative_product"] as? String,
                       let reason = innerJSON["reason"] as? String {
                        
                        return AlternativeProduct(productName: productName, reason: reason)
                    }
                }
            }
        } catch {
            print(" Error processing Alternatives JSON: \(error.localizedDescription)")
        }
        return nil
    }
    
    struct DIYIdea {
        let name: String
        let youtubeLink: String
        let thumbnail: String
    }
    
    func processDIYIdeasJSON(_ jsonData: Data) -> [DIYIdea] {
        var diyIdeas: [DIYIdea] = []
        
        do {
            if let outerJSON = try JSONSerialization.jsonObject(with: jsonData, options: []) as? [String: Any],
               let diyArray = outerJSON["diy_ideas"] as? [[String: Any]] {
                
                for idea in diyArray {
                    if let name = idea["name"] as? String,
                       let youtubeLink = idea["youtube_link"] as? String,
                       let thumbnail = idea["thumbnail"] as? String {
                        
                        diyIdeas.append(DIYIdea(name: name, youtubeLink: youtubeLink, thumbnail: thumbnail))
                    }
                }
            }
        } catch {
            print(" Error processing DIY Ideas JSON: \(error.localizedDescription)")
        }
        return diyIdeas
    }
    
    func uploadImage(filePath: String, completion: @escaping (Bool, String?) -> Void) {
        let storage = Storage.storage()
        let storageRef = storage.reference()
        let fileName = URL(fileURLWithPath: filePath).lastPathComponent
        let imageRef = storageRef.child("sustain/" + fileName)
        let fileURL = URL(fileURLWithPath: filePath)
        
        imageRef.putFile(from: fileURL, metadata: nil) { metadata, error in
            if let error = error {
                print(" Upload failed: \(error.localizedDescription)")
                completion(false, nil)
                return
            }
            
            imageRef.downloadURL { (url, error) in
                if let error = error {
                    print(" Failed to retrieve download URL: \(error.localizedDescription)")
                    completion(false, nil)
                } else if let imageURL = url {
                    print(" Upload successful: \(imageURL)")
                    self.uploadedImageURL = imageURL.absoluteString
                    completion(true, imageURL.absoluteString)
                }
            }
        }
    }
    
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
