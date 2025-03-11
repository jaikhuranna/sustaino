//
//  ViewController.swift
//  Sustano
//
//  Created by Jai Khurana on 10/03/25.
//

import UIKit
import AVFoundation

class ViewController: UIViewController {

    override func viewDidLoad() {
        super.viewDidLoad()
        guard let camera = AVCaptureDevice.default(for: .video) else {
            print("No camera available")
            return
        }

        // Get the active format (or set one explicitly)
        let activeFormat = camera.activeFormat

        // Get the supported max photo dimensions
        let supportedDimensions = activeFormat.supportedMaxPhotoDimensions

        // Print them out for inspection
        for dimension in supportedDimensions {
            print("Supported Max Photo Dimension: \(dimension.width) x \(dimension.height)")
        }
    }
    

}
