//
//  HomeViewController.swift
//  Sustano
//
//  Created by Jai Khurana on 10/03/25.
//

import UIKit
import AVFoundation

class HomeViewController: UIViewController, UICollectionViewDelegate, UICollectionViewDataSource {
    
    
    
    @IBOutlet var collectionView: UICollectionView!
    public static var capturedImage: UIImage?
    
    private let previewLayer = AVCaptureVideoPreviewLayer()
    private var captureSession: AVCaptureSession!
    private var photoOutput: AVCapturePhotoOutput!
    
    @IBOutlet var viewportView: UIView!
    
    @IBOutlet var checkButton: UIButton!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
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
        if let error = error {
            print("Error capturing photo: \(error.localizedDescription)")
            return
        }
        
        guard let imageData = photo.fileDataRepresentation(),
              let image = UIImage(data: imageData) else {
            print("Error: Could not convert photo to UIImage")
            return
        }
        
        HomeViewController.capturedImage = image
        
        DataModel.lastScansImages.append(image)
        
        DispatchQueue.main.async {
            self.collectionView.reloadData()
        }
        
        print("Image captured and saved to capturedImage")
    }
    
}
