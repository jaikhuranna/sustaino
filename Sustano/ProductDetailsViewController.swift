//
//  ProductDetailsViewController.swift
//  Sustano
//
//  Created by Jai Khurana on 10/03/25.
//

import UIKit

class ProductDetailsViewController: UIViewController {
    
    public static var productImage : UIImage?

    public static var jason : String?
    
    @IBOutlet var tunharaTExt: UILabel!
    

    @IBOutlet var ProductUIimageView: UIImageView!
    override func viewDidLoad() {
        super.viewDidLoad()
        ProductUIimageView.layer.cornerRadius = 16
        tunharaTExt.text = ProductDetailsViewController.jason
    }
    
    override func viewDidAppear(_ animated: Bool) {
        tunharaTExt.text = ProductDetailsViewController.jason ?? """
    Result = "{\n  \"product_info\": {\n    \"name\": \"Yellow Liquid Bottle\",\n    \"description\": \"A bottle containing a a yellow liquid, likely a beverage. Based on the provided text, it's unclear what the exact product is, but it could be a sports drink, energy drink, or a fruit-based beverage. \"\n  },\n  \"health_score\": 60,\n  \"sustainability_score\": 50\n}</s>";
"""
        ProductUIimageView.image = HomeViewController.capturedImage
        ProductDetailsViewController.productImage = ProductUIimageView.image
//        DataModel.lastScansImages.append(ProductDetailsViewController.productImage!);
    }
}
