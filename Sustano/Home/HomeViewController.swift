//
//  HomeViewController.swift
//  Sustano
//
//  Created by Jai Khurana on 10/03/25.
//

import UIKit
import AVFoundation

class HomeViewController: UIViewController, UICollectionViewDelegate, UICollectionViewDataSource {
    
    
    var gcsManager  = DataModel(bucketName: "sustaino", accessToken: "ya29.c.c0ASRK0Gbd5m9xOgFasUpdp8QVsNU8MCqIUouCvcoQqZcVbOqsRFDNq5NMsbIf8sXsK-3BSliqUECKJaGSendPyXtE8-lAABX964N0_kR9GZTq00XtJrSmxTnXjhOTuR8a4HXgHX2gbW1KJZ3JbfoQ5lO52L2Y7MMHxYP_OdH_GRwumHF1yDgQSL1GqhYH3L0HP7O2Zg3QykTxC36TPrxm5XWnncibAIZbjS5bIdAJfsIwCAejnkBlH-w2ztHAEa6TpZMraSdfEhB1GAqoJ7x7_fBwzeYIkNBR7KJQctk1_XzwZpSfgDpX-va5-Za-AYLeIRpC9pT-cKgoUhf4MJHhmj3EijaHRIckgihpFmw3Y2WB53A4UntXkj4gj70gzpOmO7p9-wE399KpfwM8iXuoowe77FBynkFq-joj2FnfuzxeB_j8t7-Y8a1J1xaSefZViX7W3Op45dXptdS5_OV1rldBuZR0sZStVFkRMmbiYsIcbMqJjVXnSmMJrsFZYucIr1mBRp3yx5BJp1d5_aOVaBWVajSF_4YobWv1g41RJ83Zc-bsqYs4JR85wUxOh_FvnyRmYMsfM6a2olUjpF6747Fqwkxv4w9_wnRhVQ5ijz9_3MgOIJx1lvc_JwmSc8bBkWZ51xbzXRbXhBvtmZu9OBrgmkzgppJo66njpt61pvO7JY_XtqwmQ74gWbnnMXtm2pkB2ccpJJr4xz-4jUdu3R2c1MrX_eeQQMF3V-I4hnkpyXauS4OJe-SzwrndlWM-tduYSIbm92IViaBu5b_zyYXlU52VfW1ZRrIl9SBWZgwlbjVwFkqItgf1g09ecm3frB5gMliWonMq8MWSzzXvhwxOp2eZin43QZ9VRXWYgghimzgQJXgk4Jwry9MWI0tZzFJiIpli74kV73zSBjhkoYJX7sjg-kZR5Uy1SVWlOn70MWY0beOQ-bQwhIZnr-kQfc0S5zQ4zI15d3wIkshuUY5Sai86emtva9eYtFSYnbOJ-FJ_zJB-Ugl")
    
    @IBOutlet var collectionView: UICollectionView!
    public static var capturedImage: UIImage?
    
    private let previewLayer = AVCaptureVideoPreviewLayer()
    private var captureSession: AVCaptureSession!
    private var photoOutput: AVCapturePhotoOutput!
    
    @IBOutlet var viewportView: UIView!
    
    @IBOutlet var checkButton: UIButton!
    
    override func viewDidLoad() {
        super.viewDidLoad()

        print(gcsManager)
        
        collectionView.delegate = self
        collectionView.dataSource = self
        
        collectionView.collectionViewLayout = generateLayout()
        
        navigationController?.navigationBar.backItem?.hidesBackButton = true
        print("KMS i will")
        setupCameraSession()
        checkCameraPermissions()
        viewportView.layer.cornerRadius = 12
    }
    
    @IBAction func checkButtonTapped(_ sender: Any) {
        let photoSettings = AVCapturePhotoSettings()
        photoSettings.flashMode = .auto
        photoSettings.isHighResolutionPhotoEnabled = false // Default is false anyway IDK YE KYO CHAHIYE
        
        photoOutput.capturePhoto(with: photoSettings, delegate: self)
    }
    
    
    private func setupCameraSession() {
        captureSession = AVCaptureSession()
        captureSession.sessionPreset = .medium
        
        guard let backCamera = AVCaptureDevice.default(for: .video) else {
            print("Error: Unable to access back camera")
            return
        }
        
        do {
            let cameraInput = try AVCaptureDeviceInput(device: backCamera)
            
            if captureSession.canAddInput(cameraInput) {
                captureSession.addInput(cameraInput)
            } else {
                print("Error: Cannot add camera input to session")
                return
            }
            
            photoOutput = AVCapturePhotoOutput()
            if captureSession.canAddOutput(photoOutput) {
                captureSession.addOutput(photoOutput)
            } else {
                print("Error: Cannot add photo output to session")
                return
            }
            
            previewLayer.session = captureSession
            previewLayer.videoGravity = .resizeAspectFill
            previewLayer.frame = viewportView.bounds
            
            viewportView.layer.addSublayer(previewLayer)
            viewportView.clipsToBounds = true
            
        } catch {
            print("Error setting up camera input: \(error.localizedDescription)")
            return
        }
    }
    
    func collectionView(_ collectionView: UICollectionView, numberOfItemsInSection section: Int) -> Int {
        DataModel.lastScansImages.count
    }
    
    func collectionView(_ collectionView: UICollectionView, cellForItemAt indexPath: IndexPath) -> UICollectionViewCell {
        guard let cell = collectionView.dequeueReusableCell(withReuseIdentifier: "lastScan", for: indexPath) as? LastScanCollectionViewCell else {
               return UICollectionViewCell()
           }
        
        cell.lastScanImageView.image = DataModel.lastScansImages[indexPath.item]
        cell.lastScanImageView.layer.cornerRadius = 10
        return cell
    }
    
    func generateLayout() -> UICollectionViewLayout {
        let layout = UICollectionViewCompositionalLayout{
            (Section, env) -> NSCollectionLayoutSection? in
            let itemSize = NSCollectionLayoutSize(widthDimension: .fractionalWidth(1), heightDimension: .absolute(151))
            let item = NSCollectionLayoutItem(layoutSize: itemSize)
            let groupSize = NSCollectionLayoutSize(widthDimension: .fractionalWidth(1), heightDimension: .fractionalHeight(1))
            let group = NSCollectionLayoutGroup.vertical(layoutSize: groupSize, repeatingSubitem: item, count: 1)
            let section = NSCollectionLayoutSection(group: group)
            section.interGroupSpacing = 10
            section.contentInsets = NSDirectionalEdgeInsets(top: 0, leading: 10, bottom: 10, trailing: 10)
            return section
        }
        return layout }
    
    private func checkCameraPermissions() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
                captureSession.startRunning()
                
            case .notDetermined:
                AVCaptureDevice.requestAccess(for: .video) { granted in
                    if granted {
                        DispatchQueue.main.async {
                            self.captureSession.startRunning()
                        }
                    } else {
                        print("lele nahi di permision")
                    }
                }
                
            case .denied, .restricted:
                print("lele nahi di permision")
                
            @unknown default:
                print("Unauthorised")
            }
        }
    
    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        previewLayer.frame = viewportView.bounds
    }
    
    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
//        captureSession.stopRunning()
    }
    
}

extension HomeViewController: AVCapturePhotoCaptureDelegate {
    func photoOutput(_ output: AVCapturePhotoOutput, didFinishProcessingPhoto photo: AVCapturePhoto, error: Error?) {
        guard error == nil else {
            print("Error capturing photo: \(error!.localizedDescription)")
            return
        }
        
        guard let imageData = photo.fileDataRepresentation(),
              let capturedImage = UIImage(data: imageData) else {
            print("Error converting photo data to image")
            return
        }
        
        // Store the captured image
        HomeViewController.capturedImage = capturedImage
        
        // Add to the lastScansImages array
        DataModel.lastScansImages.append(capturedImage)
        
        // Refresh collection view
        DispatchQueue.main.async {
            self.collectionView.reloadData()
        }
        
        // Save image to temporary file and upload
        saveAndUploadImage(image: capturedImage)
    }
    
    private func saveAndUploadImage(image: UIImage) {
        // Create a temporary file path
        let tempDirectoryURL = FileManager.default.temporaryDirectory
        let fileName = "captured_image_\(Date().timeIntervalSince1970).jpg"
        let fileURL = tempDirectoryURL.appendingPathComponent(fileName)
        
        // Save image to the file
        if let imageData = image.jpegData(compressionQuality: 0.8) {
            do {
                try imageData.write(to: fileURL)
                
                // Upload using the DataModel
                gcsManager.uploadImage(filePath: fileURL.path) { success, url in
                    if success, let imageURL = url {
                        print("✅ Image uploaded successfully: \(imageURL)")
                        
                        DispatchQueue.main.async {
                            // Show success alert or navigate to results screen
                            let alert = UIAlertController(title: "Success", message: "Image uploaded successfully!", preferredStyle: .alert)
                            alert.addAction(UIAlertAction(title: "OK", style: .default))
                            self.present(alert, animated: true)
                        }
                    } else {
                        print("❌ Failed to upload image")
                    }
                }
            } catch {
                print("Error saving image to temporary file: \(error.localizedDescription)")
            }
        }
    }
}
