import UIKit
import FirebaseStorage
import AVFoundation

class HomeViewController: UIViewController, UICollectionViewDelegate, UICollectionViewDataSource, AVCapturePhotoCaptureDelegate {
    
    var dataModel = DataModel()
    let storage = Storage.storage()
    
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
        setupCameraSession()
        checkCameraPermissions()
        viewportView.layer.cornerRadius = 12
    }
    
    func generateLayout() -> UICollectionViewLayout {
        let layout = UICollectionViewCompositionalLayout { (sectionIndex, environment) -> NSCollectionLayoutSection? in
            let itemSize = NSCollectionLayoutSize(widthDimension: .fractionalWidth(1), heightDimension: .absolute(151))
            let item = NSCollectionLayoutItem(layoutSize: itemSize)
            let groupSize = NSCollectionLayoutSize(widthDimension: .fractionalWidth(1), heightDimension: .fractionalHeight(1))
            let group = NSCollectionLayoutGroup.vertical(layoutSize: groupSize, repeatingSubitem: item, count: 1)
            let section = NSCollectionLayoutSection(group: group)
            section.interGroupSpacing = 10
            section.contentInsets = NSDirectionalEdgeInsets(top: 0, leading: 10, bottom: 10, trailing: 10)
            return section
        }
        return layout
    }
    
    private func setupCameraSession() {
        captureSession = AVCaptureSession()
        captureSession.sessionPreset = .photo
        
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
            
            captureSession.startRunning()
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
                    print("Camera permission denied")
                }
            }
        case .denied, .restricted:
            print("Camera permission denied")
        @unknown default:
            print("Unknown camera permission state")
        }
    }
    
    func collectionView(_ collectionView: UICollectionView, numberOfItemsInSection section: Int) -> Int {
        return DataModel.lastScansImages.count
    }
    
    func collectionView(_ collectionView: UICollectionView, cellForItemAt indexPath: IndexPath) -> UICollectionViewCell {
        guard let cell = collectionView.dequeueReusableCell(withReuseIdentifier: "lastScan", for: indexPath) as? LastScanCollectionViewCell else {
            return UICollectionViewCell()
        }
        
        cell.lastScanImageView.image = DataModel.lastScansImages[indexPath.item]
        cell.lastScanImageView.layer.cornerRadius = 10
        return cell
    }
    
    @IBAction func checkButtonTapped(_ sender: Any) {
        let loadingAlert = UIAlertController(title: "Loading", message: "Please wait...", preferredStyle: .alert)
        present(loadingAlert, animated: true)
        
        let photoSettings = AVCapturePhotoSettings()
        photoSettings.isHighResolutionPhotoEnabled = false
        photoSettings.flashMode = .auto
        
        photoOutput.capturePhoto(with: photoSettings, delegate: self)
    }
    
    func photoOutput(_ output: AVCapturePhotoOutput, didFinishProcessingPhoto photo: AVCapturePhoto, error: Error?) {
        // Get image data
        guard let imageData = photo.fileDataRepresentation(),
              let image = UIImage(data: imageData) else {
            self.dismiss(animated: true)
            return
        }
        
        // Store captured image
        HomeViewController.capturedImage = image
        
        // Add to recent scans
        DataModel.lastScansImages.insert(image, at: 0)
        if DataModel.lastScansImages.count > 10 {
            DataModel.lastScansImages.removeLast()
        }
        
        // Update UI
        DispatchQueue.main.async {
            self.collectionView.reloadData()
        }
        
        // Upload to Firebase and continue with API call
        self.uploadImageToFirebase(imageData: imageData) { imageURL in
            if let url = imageURL {
                self.fetchAPIData(imageURL: url) {
                    // Completion handler after API call
                }
            }
            DispatchQueue.main.async {
                self.dismiss(animated: true)
            }
        }
    }
    
    func uploadImageToFirebase(imageData: Data, completion: @escaping (String?) -> Void) {
        let fileName = "sustain/\(UUID().uuidString).jpg"
        let storageRef = storage.reference().child(fileName)
        
        storageRef.putData(imageData, metadata: nil) { _, error in
            if let error = error {
                print("Failed to upload image: \(error.localizedDescription)")
                completion(nil)
                return
            }
            
            storageRef.downloadURL { url, error in
                if let error = error {
                    print("Failed to get download URL: \(error.localizedDescription)")
                    completion(nil)
                } else {
                    completion(url?.absoluteString)
                }
            }
        }
    }
    
    private func fetchAPIData(imageURL: String, completion: @escaping () -> Void) {
        guard let url = URL(string: "http://10.9.137.188:8000/analyze-product/") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = ["image_url": imageURL]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                self.dismiss(animated: true, completion: nil) // Dismiss loading alert
            }
            
            guard let data = data, error == nil else {
                DispatchQueue.main.async {
                    let errorAlert = UIAlertController(title: "Error", message: "Failed to fetch data: \(error?.localizedDescription ?? "Unknown error")", preferredStyle: .alert)
                    errorAlert.addAction(UIAlertAction(title: "OK", style: .default))
                    self.present(errorAlert, animated: true)
                }
                return
            }
            
            do {
                let jsonResponse = try JSONSerialization.jsonObject(with: data, options: [])
                print("API Response: \(jsonResponse)")
            } catch {
                print("Failed to parse API response")
            }
            
            completion()
        }.resume()
    }
}
