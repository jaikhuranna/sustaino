//
//  DataModel.swift
//  Sustano
//
//  Created by Jai Khurana on 10/03/25.
//

import Foundation
import UIKit

class DataModel {
    static var lastScansImages: [UIImage] = []
}


struct GCSImageManager {
    let bucketName: String
    let accessToken: String

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
    func uploadImage(filePath: String, completion: @escaping (Bool) -> Void) {
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
            completion(false)
            return
        }
        
        let task = URLSession.shared.dataTask(with: request) { data, _, error in
            completion(error == nil)
        }
        task.resume()
    }

    /// Get the public URL of an image
    func getImageURL(imageName: String) -> String {
        return "https://storage.googleapis.com/\(bucketName)/\(imageName)"
    }

    /// Delete an image from GCS
    func deleteImage(imageName: String, completion: @escaping (Bool) -> Void) {
        let url = URL(string: "https://storage.googleapis.com/storage/v1/b/\(bucketName)/o/\(imageName)")!
        
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        request.addValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        
        let task = URLSession.shared.dataTask(with: request) { _, response, error in
            let success = (response as? HTTPURLResponse)?.statusCode == 204
            completion(success && error == nil)
        }
        task.resume()
    }
}
