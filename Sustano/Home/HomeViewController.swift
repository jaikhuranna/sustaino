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
        
        performSegue(withIdentifier: "onboarding", sender: self)
        
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
    
    // MARK: - Collection View Methods
    func collectionView(_ collectionView: UICollectionView, didSelectItemAt indexPath: IndexPath) {
        performSegue(withIdentifier: "showDetails", sender: self)
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
        guard let imageData = photo.fileDataRepresentation(),
              let image = UIImage(data: imageData) else {
            self.dismiss(animated: true)
            return
        }
        
        HomeViewController.capturedImage = image
        DataModel.lastScansImages.insert(image, at: 0)
        if DataModel.lastScansImages.count > 10 {
            DataModel.lastScansImages.removeLast()
        }
        
        DispatchQueue.main.async {
            self.collectionView.reloadData()
        }
        
        self.sendImageToAPI(imageData: imageData) { success in
            DispatchQueue.main.async {
                self.dismiss(animated: true) {
                    if success {
                        self.performSegue(withIdentifier: "showDetails", sender: self)
                    }
                }
            }
        }
    }
    
    private func sendImageToAPI(imageData: Data, completion: @escaping (Bool) -> Void) {
        guard let url = URL(string: "http://10.9.168.56:8000/analyze-product/") else {
            completion(false)
            return
        }

        let boundary = UUID().uuidString
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"image.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        URLSession.shared.dataTask(with: request) { data, response, error in
            guard let data = data, error == nil else {
                print("❌ API Error: \(error?.localizedDescription ?? "Unknown error")")
                completion(false)
                return
            }

            // 🚀 Print raw response
            if let responseString = String(data: data, encoding: .utf8) {
                print("🚀 Raw API Response: \n\(responseString)")
            }

            do {
                let jsonResponse = try JSONSerialization.jsonObject(with: data, options: .allowFragments)
                print("✅ Parsed JSON: \(jsonResponse)")

                if let jsonDict = jsonResponse as? [String: Any] {
                    DataModel.productDetails = DataModel().processJSONResponse(data)
                    DataModel.alternativeProduct = DataModel().processAlternativesJSON(data)
                    DataModel.diyIdeas = DataModel().processDIYIdeasJSON(data)
                }

                completion(true)
            } catch {
                print("❌ Failed to parse API response: \(error.localizedDescription)")
                completion(false)
            }
        }.resume()
    }
    override func prepare(for segue: UIStoryboardSegue, sender: Any?) {
        if segue.identifier == "showDetails",
           let destinationVC = segue.destination as? ProductDetailsViewController {
            
            destinationVC.productDetails = DataModel.productDetails
            destinationVC.alternativeProduct = DataModel.alternativeProduct
            destinationVC.diyIdeas = DataModel.diyIdeas

            ProductDetailsViewController.jason = DataModel.lastScansTexts.last
        }
    }
}
