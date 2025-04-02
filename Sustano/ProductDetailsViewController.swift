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

    var productDetails: DataModel.ProductDetails?
    var alternativeProduct: DataModel.AlternativeProduct?
    var diyIdeas: [DataModel.DIYIdea] = []

    @IBOutlet var productDescriptionLabel: UILabel! // Renamed for clarity
    @IBOutlet var productImageView: UIImageView! // Renamed for clarity

    override func viewDidLoad() {
        super.viewDidLoad()
        

        // Set up image view
        productImageView.layer.cornerRadius = 16
        productImageView.image = HomeViewController.capturedImage
        ProductDetailsViewController.productImage = productImageView.image

        // Display product details
        updateProductDetails()
    }
    
    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        
        // Ensure product details are displayed
        updateProductDetails()
    }
    
    @IBAction func tapRescan(_ sender: Any) {
        dismiss(animated: true)
    }
    
    // Single method to update UI with product details
    private func updateProductDetails() {
        // First try to use the details passed through segue
        if let details = productDetails {
            displayStructuredProductDetails(details)
            print("✅ Product Details from segue: \(details.name)")
        }
        // Fall back to static property if segue data is missing
        else if let staticDetails = DataModel.productDetails {
            displayStructuredProductDetails(staticDetails)
            print("✅ Product Details from static: \(staticDetails.name)")
        }
        // Last resort fallback
        else {
            productDescriptionLabel.text = "Product details not available"
            print("❌ No product details available")
        }
        
    }

    func displayStructuredProductDetails(_ details: DataModel.ProductDetails) {
//        let formattedText = """
//        Product Name: \(details.name)
//        
//        Description: \(details.description)
//        
//        Health Score: \(details.healthScore)/100
//        Sustainability Score: \(details.sustainabilityScore)/100
//        """

        self.navigationItem.title = details.name
        productDescriptionLabel.text  = details.description;
//        productDescriptionLabel.text = formattedText
    }
}
