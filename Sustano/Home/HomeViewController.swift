//
//  HomeViewController.swift
//  Sustano
//
//  Created by Jai Khurana on 10/03/25.
//

import UIKit
import AVFoundation

class HomeViewController: UIViewController {
    
    private var capturedImage: UIImage?
    
    private let previewLayer = AVCaptureVideoPreviewLayer()
    private var captureSession: AVCaptureSession!
    private var photoOutput: AVCapturePhotoOutput!
    
    @IBOutlet var viewportView: UIView!
    
    @IBOutlet var checkButton: UIButton!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        viewportView.layer.cornerRadius = 12
        print("KMS i will")
        
        setupCameraSession()
        checkCameraPermissions()
        
        // Do any additional setup after loading the view.
    }
    
    @IBAction func checkButtonTapped(_ sender: Any) {
        let photoSettings = AVCapturePhotoSettings()
        // Optional: Add other settings if needed
        photoSettings.flashMode = .auto
        photoSettings.isHighResolutionPhotoEnabled = false // Default is false anyway
        
        // No maxPhotoDimensions set — uses default resolution
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
            
        } catch {
            print("Error setting up camera input: \(error.localizedDescription)")
            return
        }
    }
    
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
        captureSession.stopRunning()
    }
    
    /*
     // MARK: - Navigation
     
     // In a storyboard-based application, you will often want to do a little preparation before navigation
     override func prepare(for segue: UIStoryboardSegue, sender: Any?) {
     // Get the new view controller using segue.destination.
     // Pass the selected object to the new view controller.
     }
     */
    
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
        
        capturedImage = image
        print("Image captured and saved to capturedImage")
    }
    
}
