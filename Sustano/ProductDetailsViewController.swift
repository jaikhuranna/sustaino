//
//  ProductDetailsViewController.swift
//  Sustano
//
//  Created by Jai Khurana on 10/03/25.
//

import UIKit

class ProductDetailsViewController: UIViewController {
    
    public static var productImage : UIImage?

    @IBOutlet var ProductUIimageView: UIImageView!
    override func viewDidLoad() {
        super.viewDidLoad()
        ProductUIimageView.layer.cornerRadius = 16
    }
    
    override func viewDidAppear(_ animated: Bool) {
        ProductUIimageView.image = HomeViewController.capturedImage
        ProductDetailsViewController.productImage = ProductUIimageView.image
        DataModel.lastScansImages.append(ProductDetailsViewController.productImage!);
    }
}
