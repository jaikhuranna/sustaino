//
//  ProductDetailsViewController.swift
//  Sustano
//
//  Created by Jai Khurana on 10/03/25.
//

import UIKit

class ProductDetailsViewController: UIViewController {
    
    public static var productImage: UIImage?
    public static var jason: String?

    // Additional properties for structured data
    var productDetails: DataModel.ProductDetails?
    var alternativeProduct: DataModel.AlternativeProduct?
    var diyIdeas: [DataModel.DIYIdea] = []

    @IBOutlet var tunharaTExt: UILabel!
    @IBOutlet var ProductUIimageView: UIImageView!

    override func viewDidLoad() {
        super.viewDidLoad()
        
        ProductUIimageView.layer.cornerRadius = 16
        ProductUIimageView.image = HomeViewController.capturedImage
        ProductDetailsViewController.productImage = ProductUIimageView.image
        
        // Update UI with raw JSON or structured data
        if let details = productDetails {
            displayStructuredProductDetails(details)
        } else {
            tunharaTExt.text = ProductDetailsViewController.jason ?? "Data unavailable"
        }
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)

        if productDetails == nil {
            tunharaTExt.text = ProductDetailsViewController.jason ?? "Data unavailable"
        }
    }

    @IBAction func tapRescan(_ sender: Any) {
        dismiss(animated: true)
    }

    /// Updates UI with structured product details
    func displayStructuredProductDetails(_ details: DataModel.ProductDetails) {
        let formattedText = """
        Product Name: \(details.name)
        
        Description: \(details.description)
        
        Health Score: \(details.healthScore)/100
        Sustainability Score: \(details.sustainabilityScore)/100
        """

        tunharaTExt.text = formattedText
    }
}
